# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from lxml import etree

class HTMLNode(object):
    def __init__(self, xml_node):
        self._xml_node = xml_node
    
    def find(self, elname = None, maxdepth = -1, **params):
        res = []
        if elname == None or self._xml_node.tag == elname:
            add = True
            for i in params:
                if not i in self._xml_node.attrib or self._xml_node.attrib[i] != params[i]:
                    add = False
                    break
            if add:
                res.append(self)
        if maxdepth!=0:
            for child in self._xml_node.iterchildren():
                res += HTMLNode(child).find(elname, maxdepth - 1, **params)
        return res
    
    def _get_next(self):
        if self._xml_node.getnext() is not None:
            return HTMLNode(self._xml_node.getnext())
        else:
            return None
    next = property(_get_next)
    
    def getContent(self):
        return etree.tostring(self._xml_node, method = "text", encoding = "UTF-8")
    
    def prop(self, key):
        if key in self._xml_node.attrib:
            return self._xml_node.attrib[key]
        else:
            return None
    
    def _get_children(self):
        return [HTMLNode(i) for i in self._xml_node.iterchildren()]
    children = property(_get_children)
    
    def _get_parent(self):
        parent = self._xml_node.getparent()
        if parent is not None:
            return HTMLNode(parent)
        else:
            return parent
    parent = property(_get_parent)
    
    def _get_nodename(self):
        return self._xml_node.tag
    nodename = property(_get_nodename)
