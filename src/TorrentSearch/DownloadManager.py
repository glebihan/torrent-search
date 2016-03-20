# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import threading
import tempfile
import urllib.request
from gi.repository import GLib

DOWNLOAD_STATUS_WAITING, DOWNLOAD_STATUS_DOWNLOADING, DOWNLOAD_STATUS_FAILED, DOWNLOAD_STATUS_DONE = range(4)

class DownloadProcess(object):
    def __init__(self, application, manager, result, preferred_method):
        self._application = application
        self._manager = manager
        self._result = result
        self._status = DOWNLOAD_STATUS_WAITING
        self._lock = threading.Lock()
        if preferred_method == "download": 
            self._methods = ["download", "magnet"]
        else:
            self._methods = ["magnet", "download"]
    
    def _get_status(self):
        self._lock.acquire()
        res = self._status
        self._lock.release()
        return res
    def _set_status(self, status):
        self._lock.acquire()
        self._status = status
        self._lock.release()
    status = property(_get_status, _set_status)
    
    def _get_result(self):
        self._lock.acquire()
        res = self._result
        self._lock.release()
        return res
    result = property(_get_result)
    
    def _get_title(self):
        return self.result["title"]
    title = property(_get_title)

    def _get_next_method(self):
        self._lock.acquire()
        if len(self._methods) > 0:
            res = self._methods.pop(0)
        else:
            res = None
        self._lock.release()
        return res
    
    def download(self):
        method = self._get_next_method()
        if method is None:
            self.status = DOWNLOAD_STATUS_FAILED
            GLib.idle_add(self._manager.process_queue)
        else:
            self._do_download(method)
    
    def _do_download_thread(self, method, force = False):
        threading.Thread(target = self._do_download, args = (method ,force)).start()
    
    def _do_download(self, method, force = False):
        if ((method == "download" and not "download_link" in self.result) or (method == "magnet" and not "magnet_link" in self.result)) and not force:
            self._result.fetch_all(self._do_download_thread, method, True)
        elif (method == "download" and not "download_link" in self.result) or (method == "magnet" and not "magnet_link" in self.result):
            self.download()
        elif method == "download":
            try:
                res = self._application.http_get(self.result["download_link"])
                f = tempfile.NamedTemporaryFile(delete = False, suffix = ".torrent")
                f.write(res.content)
                f.close()
                if platform.system() == "Windows":
                    uri = urllib.request.pathname2url(f.name)
                else:
                    uri = "file://" + urllib.request.pathname2url(f.name)
                GLib.idle_add(self._application.get_selected_torrent_client().launch, [uri])
                self.status = DOWNLOAD_STATUS_DONE
                GLib.idle_add(self._manager.process_queue)
            except:
                self.download()
        elif method == "magnet":
            GLib.idle_add(self._application.get_selected_torrent_client().launch, [self.result["magnet_link"]])
            self.status = DOWNLOAD_STATUS_DONE
            GLib.idle_add(self._manager.process_queue)

class DownloadManager(object):
    def __init__(self, application):
        self._application = application
        
        self.queue = []
        self._queue_lock = threading.Lock()
        
        self._view = None
    
    def acquire_lock(self):
        self._queue_lock.acquire()
 
    def release_lock(self):
        self._queue_lock.release()
    
    def set_view(self, view):
        self._view = view
    
    def process_queue(self):
        if self._view is not None:
            self._view.update()
        
        self._queue_lock.acquire()
        for i in self.queue:
            if i.status == DOWNLOAD_STATUS_WAITING:
                i.status = DOWNLOAD_STATUS_DOWNLOADING
                threading.Thread(target = i.download).start()
        self._queue_lock.release()
    
    def append(self, result):
        self._queue_lock.acquire()
        self.queue.append(DownloadProcess(self._application, self, result, self._application.configuration.get("Downloads", "preferred_method")))
        self._queue_lock.release()
        
        if self._view is not None:
            self._view.update()
        
        self.process_queue()
