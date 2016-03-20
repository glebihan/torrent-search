# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from gi.repository import Gtk
from . import SettingsWidgets

class SearchBox(Gtk.HBox):
    def __init__(self, application, window):
        Gtk.HBox.__init__(self)
        
        self.set_spacing(10)
        
        self._application = application
                
        l = Gtk.Label()
        l.set_markup("<b>%s</b>" % _("Search"))
        l.set_xalign(0)
        self.pack_start(l, False, False, 0)
        
        self._search_entry = Gtk.Entry()
        self.pack_start(self._search_entry, True, True, 0)
        self._entry_completion = Gtk.EntryCompletion()
        self._search_entry.set_completion(self._entry_completion)
        self._completion_lb = Gtk.ListStore(str)
        self._entry_completion.set_model(self._completion_lb)
        self._entry_completion.set_text_column(0)
        self._update_completion()
        
        self._filter_button = Gtk.Button.new_from_icon_name("emblem-system-symbolic", Gtk.IconSize.BUTTON)
        self.pack_end(self._filter_button, False, False, 0)
        
        self._popover = Gtk.Popover()
        self._popover.set_relative_to(self._filter_button)
        
        popover_main_vbox = Gtk.VBox()
        self._popover.add(popover_main_vbox)
        
        self._widgets = {}
        
        for section in application.configuration.get_filters_options():
            frame = Gtk.Frame()
            l = Gtk.Label()
            l.set_markup("<b>%s</b>" % section["section_label"])
            frame.set_label_widget(l)
            frame.set_border_width(5)
            frame.set_shadow_type(Gtk.ShadowType.IN)
            
            popover_main_vbox.pack_start(frame, False, False, 0)
            
            vbox = Gtk.VBox()
            frame.add(vbox)
            
            vbox.set_border_width(5)
            vbox.set_spacing(10)
            
            for i in range(len(section["items"])):
                hbox = Gtk.HBox()
                vbox.pack_start(hbox, False, False, 0)
                option = section["items"][i]
                label = Gtk.Label(option["label"])
                label.set_xalign(0)
                hbox.pack_start(label, True, True, 0)
                widget = option["widget_class"](application, "Search options", option["key"], option["save"], True)
                hbox.pack_start(widget, False, False, 0)
                self._widgets[option["key"]] = widget
        
        self._search_button = Gtk.Button.new_from_icon_name("system-search-symbolic", Gtk.IconSize.BUTTON)
        self.pack_end(self._search_button, False, False, 0)
        
        self._search_button.connect('clicked', lambda w:self.run_search())
        self._filter_button.connect('clicked', lambda w:self.show_filters())
        self._search_entry.connect('activate', lambda w:self.run_search())
    
    def run_search(self, keyword = None):
        if keyword:
            self._search_entry.set_text(keyword)
        else:
            keyword = self._search_entry.get_text().strip()
        self._application.run_search(keyword)
        self._search_entry.grab_focus()
        self._update_completion()
    
    def show_filters(self):
        self._popover.show_all()
    
    def get_search_filters(self):
        res = {}
        for i in self._widgets:
            res[i] = self._widgets[i].get_value()
        return res
        
    def focus_search_entry(self):
        self._search_entry.grab_focus()
    
    def _update_completion(self):
        self._completion_lb.clear()
        for i in self._application.search_history:
            self._completion_lb.append((i,))
