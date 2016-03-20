# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from gi.repository import Gtk, GdkPixbuf
import datetime
import time
from .. import TorrentClient

class SettingsWidget(object):
    VALUE_TYPE = str
    def __init__(self, application, section, key, save, is_filter = False):
        self._application = application
        self._section = section
        self._key = key
        self._save = save
        self._is_filter = is_filter
        
        if self.VALUE_TYPE == bool:
            method = "getboolean"
        elif self.VALUE_TYPE == int:
            method = "getint"
        else:
            method = "get"
        self.set_value(getattr(application.configuration, method)(section, key))
    
    def _on_value_changed(self):
        if self._save:
            self._application.configuration.set(self._section, self._key, str(self.get_value()))
        
        if self._is_filter:
            self._application.update_search_filters()

class Switch(Gtk.Switch, SettingsWidget):
    VALUE_TYPE = bool
    def __init__(self, *args):
        Gtk.Switch.__init__(self)
        SettingsWidget.__init__(self, *args)
        
        self.connect("state-set", lambda w, s: self._on_value_changed())
    
    def set_value(self, value):
        self.set_active(value)
    
    def get_value(self):
        return self.get_active()

class SizeSelector(Gtk.HBox, SettingsWidget):
    VALUE_TYPE = int
    def __init__(self, *args):
        Gtk.HBox.__init__(self)
        
        self.set_spacing(10)
        
        self._switch = Gtk.Switch()
        self.pack_start(self._switch, False, False, 0)
        
        self._spin_button = Gtk.SpinButton()
        self.pack_start(self._spin_button, False, False, 0)
        self._spin_button.set_range(1, 1023)
        self._spin_button.set_increments(10, 100)
        
        self._unit_selector = Gtk.ComboBoxText()
        self.pack_start(self._unit_selector, False, False, 0)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            self._unit_selector.append_text(unit)
        
        SettingsWidget.__init__(self, *args)
        
        self._switch.connect("state-set", self._on_switch_state_set)
        self._spin_button.connect("value-changed", lambda w: self._on_value_changed())
        self._unit_selector.connect("changed", lambda w: self._on_value_changed())
    
    def _on_switch_state_set(self, switch, state):
        self._spin_button.set_sensitive(state)
        self._unit_selector.set_sensitive(state)
        self._on_value_changed()
    
    def set_value(self, value):
        self._switch.set_active(value > 0)
        self._spin_button.set_sensitive(value > 0)
        self._unit_selector.set_sensitive(value > 0)
        value = abs(value)
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        ui = 0
        while value >= 1024:
            value = value // 1024
            ui += 1
        self._spin_button.set_value(value)
        self._unit_selector.set_active(ui)
    
    def get_value(self):
        value = int(self._spin_button.get_value())
        ui = self._unit_selector.get_active()
        while ui > 0:
            value = value * 1024
            ui -= 1
        if not self._switch.get_active():
            value = -value
        return value

class DateSelector(Gtk.Entry, SettingsWidget):
    def __init__(self, *args):
        Gtk.Switch.__init__(self)
        
        self.set_editable(False)
        self._popover = Gtk.Popover()
        self._popover.set_relative_to(self)
        self._calendar = Gtk.Calendar()
        self._popover.add(self._calendar)
        self.set_can_focus(False)
        self.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "edit-clear-symbolic")
        self.set_icon_sensitive(Gtk.EntryIconPosition.SECONDARY, True)
        self.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, True)
        
        SettingsWidget.__init__(self, *args)
        
        self._calendar.connect('day-selected-double-click', self._on_day_selected)
        self.connect('button-press-event', self._on_button_press_event)
        self.connect('changed', lambda w: self._on_value_changed())
        self.connect('icon-press', self._on_icon_press)
    
    def _on_icon_press(self, entry, icon_pos, event):
        if event.button == 1:
            self.set_value(None)
    
    def _on_button_press_event(self, widget, event):
        if event.button == 1:
            self._popover.show_all()
    
    def _on_day_selected(self, widget):
        year, month, day = self._calendar.get_date()
        self.set_date(datetime.date(year, month + 1, day))
        self._popover.hide()
    
    def set_date(self, date):
        self.set_text(self._application.format_date(date))
      
    def get_date(self):
        text = self.get_text()
        if text != "":
            res = time.strptime(self.get_text(), self._application.configuration.get("Display", "date_format"))
            return datetime.date(res.tm_year, res.tm_mon, res.tm_mday)
        else:
            return None
    
    def get_value(self):
        return self.get_date()
    
    def set_value(self, value):
        if value == None:
            self.set_text("")
        else:
            date = time.strptime(value, self._application.configuration.get("Display", "date_format"))
            date = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
            self.set_date(date)
            self._calendar.select_month(date.tm_mon - 1, date.tm_year)
            self._calendar.select_day(date.tm_mday)

class Entry(Gtk.Entry, SettingsWidget):
    def __init__(self, *args):
        Gtk.Entry.__init__(self)
        
        SettingsWidget.__init__(self, *args)
        
        self.connect('changed', lambda w: self._on_value_changed())
    
    def set_value(self, value):
        self.set_text(value)
    
    def get_value(self):
        res = self.get_text()
        if self._key == "date_format":
            res = res.replace("%", "%%")
        return res

class TorrentClientCombo(Gtk.ComboBox, SettingsWidget):
    def __init__(self, *args):
        Gtk.ComboBox.__init__(self)
        
        self._liststore = Gtk.ListStore(object, str, GdkPixbuf.Pixbuf)
        self.set_model(self._liststore)
        for app in TorrentClient.TorrentClient.get_list():
            self._liststore.append((app, app.get_display_name(), app.get_icon_pixbuf(Gtk.IconSize.BUTTON)))
        
        r = Gtk.CellRendererPixbuf()
        self.pack_start(r, False)
        self.add_attribute(r, "pixbuf", 2)
        r = Gtk.CellRendererText()
        self.pack_start(r, True)
        self.add_attribute(r, "text", 1)
        
        SettingsWidget.__init__(self, *args)
        
        self.connect('changed', lambda w: self._on_value_changed())
    
    def set_value(self, value):
        for i in range(len(self._liststore)):
            if self._liststore[i][0].get_id() == value:
                self.set_active(i)
        
    def get_value(self):
        return self._liststore[self.get_active()][0].get_id()

class DownloadMethodCombo(Gtk.ComboBox, SettingsWidget):
    def __init__(self, *args):
        Gtk.ComboBox.__init__(self)
        
        self._liststore = Gtk.ListStore(str, str)
        self.set_model(self._liststore)
        self._liststore.append(("magnet", _("Magnet link")))
        self._liststore.append(("download", _("Download torrent file")))
        
        r = Gtk.CellRendererText()
        self.pack_start(r, True)
        self.add_attribute(r, "text", 1)
        
        SettingsWidget.__init__(self, *args)
        
        self.connect('changed', lambda w: self._on_value_changed())
    
    def set_value(self, value):
        for i in range(len(self._liststore)):
            if self._liststore[i][0] == value:
                self.set_active(i)
        
    def get_value(self):
        return self._liststore[self.get_active()][0]
