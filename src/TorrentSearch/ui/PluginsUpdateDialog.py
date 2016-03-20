# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from gi.repository import Gtk, GLib

class PluginsUpdateDialog(Gtk.Dialog):
    def __init__(self, window, updater):
        Gtk.Dialog.__init__(self)
        
        self.set_title(_("Updating plugins"))
        
        self.set_transient_for(window)
        self.set_deletable(False)
        
        self.get_content_area().set_border_width(5)
        self.get_content_area().set_spacing(10)
        
        self.get_content_area().pack_start(Gtk.Label(_("Downloading plugin updates... Please wait...")), False, False, 0)
        self._progressbar = Gtk.ProgressBar()
        self.get_content_area().pack_start(self._progressbar, False, False, 0)
        
        self.connect("delete-event", lambda w, e: True)
    
    def set_fraction(self, fraction):
        GLib.idle_add(self._progressbar.set_fraction, fraction)
