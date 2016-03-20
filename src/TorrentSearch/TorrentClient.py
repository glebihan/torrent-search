# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from gi.repository import Gio, Gtk
import platform

class TorrentClient(object):
    def get_list():
        res = []
        if platform.system() == "Windows":
            app_list = Gio.AppInfo.get_all_for_type(".torrent")
        else:
            app_list = Gio.AppInfo.get_all_for_type("application/x-bittorrent")
        for i in app_list:
            res.append(TorrentClient(gioappinfo = i))
        return res
        
    def get_default():
        if platform.system() == "Windows":
            default_app = Gio.AppInfo.get_default_for_type(".torrent", True)
        else:
            default_app = Gio.AppInfo.get_default_for_type("application/x-bittorrent", True)
        if default_app is not None:
            res = TorrentClient(gioappinfo = default_app)
        else:
            l = TorrentClient.get_list()
            if len(l) > 0:
                res = l[0]
            else:
                res = None
        return res
    
    def __init__(self, gioappinfo = None):
        self._gioappinfo = gioappinfo
    
    def get_id(self):
        if self._gioappinfo is not None:
            return self._gioappinfo.get_id()
        else:
            return ""
    
    def get_icon_pixbuf(self, size):
        app_icon = self._gioappinfo.get_icon()
        if app_icon:
            icon_names = app_icon.get_names()
            icon = Gtk.IconTheme.get_default().choose_icon(icon_names, Gtk.IconSize.lookup(size)[1], 0).load_icon()
        else:
            icon = None
        return icon
    
    def get_display_name(self):
        if platform.system() == "Windows":
            return self._gioappinfo.get_id()
        else:
            return self._gioappinfo.get_display_name()
    
    def launch(self, uris):
        self._gioappinfo.launch_uris(uris, None)
