# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

class ResultFile(object):
    def __init__(self, **data):
        self._data = data
    
    def _get_filename(self):
        return self._data.setdefault("filename", "")
    filename = property(_get_filename)
    
    def _get_size(self):
        return self._data.setdefault("size", 0)
    size = property(_get_size)
