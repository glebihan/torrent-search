# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from gi.repository import Gtk, Gio, GdkPixbuf, Gdk
from . import SettingsWidgets
from .. import TorrentClient
import webbrowser

class PreferencesDialog(Gtk.Dialog):
    def __init__(self, application, window):
        Gtk.Dialog.__init__(self, _("Preferences"))
        
        self.set_default_size(application.configuration.getint("Display", "preferences_dialog_width"), application.configuration.getint("Display", "preferences_dialog_height"))
        
        self._application = application
        self._window = window
        
        self.set_transient_for(window)
        self.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        
        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_halign(Gtk.Align.CENTER)
        self.get_content_area().pack_start(stack_switcher, False, False, 0)
        stack = Gtk.Stack()
        self.get_content_area().pack_start(stack, True, True, 0)
        
        stack_switcher.set_stack(stack)
        
        self._add_section(stack, "general_options", _("General"), application.configuration.get_preferences_section("General"))
        
        scw = Gtk.ScrolledWindow()
        scw.set_border_width(5)
        scw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        stack.add_titled(scw, "search_plugins", _("Search plugins"))
        self._plugins_treeview = Gtk.TreeView()
        scw.add(self._plugins_treeview)
        self._plugins_model = Gtk.ListStore(object, str, str, bool)
        self._plugins_treeview.set_model(self._plugins_model)
        col = Gtk.TreeViewColumn(_("Plugin"))
        r = Gtk.CellRendererToggle()
        col.pack_start(r, False)
        col.add_attribute(r, "active", 3)
        r.set_property("activatable", True)
        r.connect("toggled", self._on_plugin_toggled)
        r = Gtk.CellRendererText()
        col.pack_start(r, True)
        col.add_attribute(r, "text", 2)
        self._plugins_treeview.append_column(col)
        col = Gtk.TreeViewColumn(_("URL"))
        r = Gtk.CellRendererText()
        col.pack_start(r, True)
        col.set_cell_data_func(r, self._url_data_func)
        self._plugins_treeview.append_column(col)
        
        self._add_section(stack, "advanced_options", _("Advanced"), application.configuration.get_preferences_section("Advanced"))
                
        self._plugins_treeview.connect('button-press-event', self._on_plugins_treeview_button_press_event)
        self._plugins_treeview.connect('motion-notify-event', self._on_plugins_treeview_motion_notify_event)
        
    def _on_plugins_treeview_motion_notify_event(self, widget, event):
        data = widget.get_path_at_pos(int(event.x), int(event.y))
        if data:
            path, column, x, y = data
            if column.get_property('title') == _("URL"):
                self._plugins_treeview.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.HAND2))
                return
        self._plugins_treeview.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.ARROW))
    
    def _on_plugins_treeview_button_press_event(self, widget, event):
        if event.button == 1:
            data = widget.get_path_at_pos(int(event.x), int(event.y))
            if data:
                path, column, x, y = data
                if column.get_property('title') == _("URL"):
                    row_iter = self._plugins_model.get_iter(path)
                    plugin = self._plugins_model.get_value(row_iter, 0)
                    webbrowser.open(plugin.URL)
                    return True
    
    def _url_data_func(self, column, cell, model, row_iter, data):
      plugin = model.get_value(row_iter, 0)
      cell.set_property('markup', "<span color='#0000FF'><u>%s</u></span>" % plugin.URL)
    
    def _on_plugin_toggled(self, renderer, path):
        self._plugins_model[path][3] = not self._plugins_model[path][3]
        
        disabled_plugins = []
        for i in self._plugins_model:
            if not i[3]:
                disabled_plugins.append(i[0].ID)
        self._application.configuration.set("Plugins", "disabled_plugins", ",".join(disabled_plugins))
        self._application.load_plugins()
    
    def _add_section(self, stack, stack_id, label, settings):
        vbox = Gtk.VBox()
        stack.add_titled(vbox, stack_id, label)
        
        for section in settings:
            frame = Gtk.Frame()
            l = Gtk.Label()
            l.set_markup("<b>%s</b>" % section["section_label"])
            frame.set_label_widget(l)
            frame.set_border_width(5)
            frame.set_shadow_type(Gtk.ShadowType.IN)
            
            vbox.pack_start(frame, False, False, 0)
            
            table = Gtk.Table()
            table.set_border_width(5)
            table.set_row_spacings(10)
            table.set_col_spacings(10)
            frame.add(table)
            
            for i in range(len(section["items"])):
                option = section["items"][i]
                label = Gtk.Label(option["label"])
                label.set_xalign(0)
                table.attach(label, 0, 1, i, i + 1, Gtk.AttachOptions.FILL, Gtk.AttachOptions.SHRINK)
                widget = option["widget_class"](self._application, option["section"], option["key"], True)
                table.attach(widget, 1, 2, i, i + 1, Gtk.AttachOptions.FILL | Gtk.AttachOptions.EXPAND, Gtk.AttachOptions.SHRINK)
    
    def run(self):
        self._plugins_model.clear()
        plugins = self._application.search_plugins
        plugins.sort(key = lambda a: a.NAME.lower())
        for plugin in plugins:
            self._plugins_model.append((plugin, plugin.ID, plugin.NAME, plugin.enabled))
        self.show_all()
        Gtk.Dialog.run(self)
        width, height = self.get_size()
        self._application.configuration.set("Display", "preferences_dialog_width", str(width))
        self._application.configuration.set("Display", "preferences_dialog_height", str(height))
        self.hide()
        self._window.focus_search_entry()
