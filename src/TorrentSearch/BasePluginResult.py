# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import threading
import requests
import tempfile
from gi.repository import GLib, GdkPixbuf

class BasePluginResult(object):
    def __init__(self, plugin, **data):
        self._plugin = plugin
        self._data = data
        self._pixbuf = None
        self._fetch_all_done = threading.Event()
        self._fetch_all_running = threading.Event()
        self._data_lock = threading.Lock()
    
    def __contains__(self, key):
        self._data_lock.acquire()
        res = (key in self._data)
        self._data_lock.release()
        return res
    
    def __getitem__(self, key):
        self._data_lock.acquire()
        res = self._data[key]
        self._data_lock.release()
        return res

    def __setitem__(self, key, value):
        self._data_lock.acquire()
        self._data[key] = value
        self._data_lock.release()
    
    def setdefault(self, key, value):
        self._data_lock.acquire()
        res = self._data.setdefault(key, value)
        self._data_lock.release()
        return res
    
    def __repr__(self):
        self._data_lock.acquire()
        res = repr(self._data)
        self._data_lock.release()
        return res
    
    def fetch_details(self):
        pass
    
    def _do_fetch_all(self):
        pass
    
    def fetch_all(self, callback, *args):
        if self._fetch_all_done.is_set():
            callback(*args)
        else:
            threading.Thread(target = self._fetch_all, args = (callback,) + args).start()
    
    def _fetch_all(self, callback, *args):
        if self._fetch_all_running.is_set():
            self._fetch_all_done.wait()
        else:
            self._fetch_all_running.set()
            self._do_fetch_all()
            self.setdefault("files", [])
            self._fetch_all_done.set()
        GLib.idle_add(callback, *args)
    
    def http_get(self, url, params = None, **kwargs):
        return self._plugin.http_get(url, params, **kwargs)
    
    def http_post(self, url, data = None, json = None, **kwargs):
        return self._plugin.http_post(url, data, json, **kwargs)
