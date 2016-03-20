# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import threading
import logging
import traceback
from gi.repository import GLib
from .BasePluginResult import BasePluginResult

class SearchProcess(threading.Thread):
    NB_THREADS = 5
    REQUIRED_FIELDS = [
        "title",
        "hash",
        "url",
        "date"
    ]
    def __init__(self, application, search_id, keyword):
        threading.Thread.__init__(self, target = self.run_search)
        
        self._application = application
        self._search_id = search_id
        self._keyword = keyword
        
        self._hash_list = []
        
        self._operations_queue = []
        self._running_threads = 0
        self._operations_queue_lock = threading.Lock()
        self._stop_event = threading.Event()
    
    def run_search(self):
        for plugin in self._application.enabled_search_plugins:
            self._operations_queue.append({
                "plugin": plugin,
                "operation": "search"
            })
        
        for i in range(self.NB_THREADS):
            self._start_thread()
    
    def _on_operation_completed(self):
        self._operations_queue_lock.acquire()
        self._running_threads -= 1
        if len(self._operations_queue) > 0:
            start_new_thread = True
        else:
            start_new_thread = False
            if self._running_threads > 0:
                is_finished = False
            else:
                is_finished = True
        self._operations_queue_lock.release()
        
        if start_new_thread:
            self._start_thread()
        elif is_finished:
            logging.debug("Search complete")
    
    def _push_result(self, plugin, result):
        if self._result_needs_details(result):
            logging.warn("Incomplete result from plugin %s : %s" % (plugin, result))
            return
        
        GLib.idle_add(self._do_push_result, plugin, result)
    
    def _do_push_result(self, plugin, result):
        if result["hash"].lower() in self._hash_list:
            logging.debug("Ignoring duplicate result from plugin %s : %s" % (plugin, result))
        else:
            self._hash_list.append(result["hash"].lower())
            self._application.display_result(self._search_id, plugin, result)
    
    def _result_needs_details(self, result):
        for field in self.REQUIRED_FIELDS:
            if not field in result or not result[field]:
                return True
        return False
    
    def _process_search_operation(self, operation):
        results = operation["plugin"].run_search(self._keyword, url = operation.setdefault("url", None))
        
        if not results or type(results) != dict:
            logging.warn("Incorrect results from plugin %s : %s" % (operation["plugin"], results))
            return
            
        if  "continue_url" in results and results["continue_url"] != None:
            self._operations_queue_lock.acquire()
            self._operations_queue.append({
                "plugin": operation["plugin"],
                "operation": "search",
                "url": results["continue_url"]
            })
            self._operations_queue_lock.release()
        
        if "results" in results:
            for result in results["results"]:
                if isinstance(result, BasePluginResult):
                    if self._result_needs_details(result):
                        self._operations_queue_lock.acquire()
                        self._operations_queue.append({
                            "plugin": operation["plugin"],
                            "operation": "fetch_details",
                            "result": result
                        })
                        self._operations_queue_lock.release()
                    else:
                        self._push_result(operation["plugin"], result)
                else:
                    logging.warn("Incorrect result from plugin %s : %s" % (operation["plugin"], result))
    
    def _process_fetch_details_operation(self, operation):
        try:
            operation["result"].fetch_details()
            self._push_result(operation["plugin"], operation["result"])
        except:
            if self._application.cli_options.debug:
                traceback.print_exc()
        
    def _process_operation(self, operation):
        if self._stop_event.is_set():
            return
        
        try:
            if operation["operation"] == "search":
                self._process_search_operation(operation)
            elif operation["operation"] == "fetch_details":
                self._process_fetch_details_operation(operation)
        except:
            if self._application.cli_options.debug:
                traceback.print_exc()
            
        GLib.idle_add(self._on_operation_completed)
    
    def _start_thread(self):
        self._operations_queue_lock.acquire()
        if len(self._operations_queue) > 0:
            operation = self._operations_queue.pop(0)
            self._running_threads += 1
        else:
            operation = None
        self._operations_queue_lock.release()
        
        if operation:
            threading.Thread(target = self._process_operation, args = (operation,)).start()
    
    def stop(self):
        self._stop_event.set()
