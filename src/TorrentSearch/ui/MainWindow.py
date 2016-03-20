# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from gi.repository import Gtk, GLib
from ..metadata import *
from .MainMenuButton import MainMenuButton
from .Sidebar import Sidebar
from .SearchBox import SearchBox
from .ResultsPane import ResultsPane

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, application):
        Gtk.ApplicationWindow.__init__(self, application = application)
        
        self._application = application
        
        self.set_title(APPNAME)
        
        self.set_default_size(application.configuration.getint("Display", "window_width"), application.configuration.getint("Display", "window_height"))
        if application.configuration.getboolean("Display", "window_maximized"):
            self.maximize()
        
        headerbar = Gtk.HeaderBar()
        headerbar.set_show_close_button(True)
        self.set_titlebar(headerbar)
        headerbar.set_title(APPNAME)
        headerbar.pack_end(MainMenuButton(application, self))
        
        vbox = Gtk.VBox()
        self.add(vbox)
        vbox.set_border_width(5)
        
        self._search_box = SearchBox(application, self)
        vbox.pack_start(self._search_box, False, False, 5)
        
        sep = Gtk.HSeparator()
        vbox.pack_start(sep, False, False, 5)
        
        self._paned = Gtk.HPaned()
        vbox.pack_start(self._paned, True, True, 5)
        
        self._sidebar = Sidebar(application, self)
        self._paned.pack2(self._sidebar, True, True)
        
        self._results_pane = ResultsPane(application, self)
        scw = Gtk.ScrolledWindow()
        scw.add(self._results_pane)
        self._paned.pack1(scw, False, False)
        
        self._paned_placed = False
        self._paned_width = None
        self.connect("size-allocate", self._on_size_allocate)
        self._paned.connect("size-allocate", self._on_paned_size_allocate)
    
    def _on_size_allocate(self, window, rectangle):
        if self.is_maximized():
            self._application.configuration.set("Display", "window_maximized", "true")
        else:
            width, height = self.get_size()
            self._application.configuration.set("Display", "window_maximized", "false")            
            self._application.configuration.set("Display", "window_width", str(width))
            self._application.configuration.set("Display", "window_height", str(height))
    
    def _on_paned_size_allocate(self, widget, rectangle):
        paned_window = self._paned.get_window()
        if paned_window is not None:
            paned_width = paned_window.get_width()
            if self._paned_placed:
                self._application.configuration.set("Display", "paned_position", str(paned_width - self._paned.get_position()))
            else:
                GLib.timeout_add(100, self._paned.set_position, paned_width - self._application.configuration.getint("Display", "paned_position"))
                if paned_width == self._paned_width:
                    self._paned_placed = True
                else:
                    self._paned_width = paned_width
    
    def display_result(self, plugin, result):
        self._results_pane.display_result(plugin, result)
    
    def run_search(self, keyword):
        self._search_box.run_search(keyword)
    
    def clear_results(self):
        self._results_pane.clear_results()
    
    def update_search_filters(self, keyword):
        self._results_pane.update_search_filters(keyword, self._search_box.get_search_filters())
    
    def clear_torrent_details(self):
        self._sidebar.clear_torrent_details()
    
    def display_torrent_details(self, result):
        self._sidebar.display_torrent_details(result)
    
    def focus_search_entry(self):
        self._search_box.focus_search_entry()
