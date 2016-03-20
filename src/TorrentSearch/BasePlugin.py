# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

class BasePlugin(object):
    def __init__(self, application):
        self._application = application
    
    def http_get(self, url, params = None, **kwargs):
        return self._application.http_get(url, params, **kwargs)
    
    def http_post(self, url, data = None, json = None, **kwargs):
        return self._application.http_post(url, data, json, **kwargs)
