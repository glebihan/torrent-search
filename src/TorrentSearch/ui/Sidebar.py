# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from gi.repository import Gtk, Gdk, GLib
import webbrowser
from .DownloadsView import DownloadsView

class Sidebar(Gtk.VBox):
    TORRENT_PROPERTIES = [
        {"key": "title", "label": _("Title")},
        {"key": "size", "label": _("Size")},
        {"key": "date", "label": _("Date")},
        {"key": "seeders", "label": _("Seeders")},
        {"key": "leechers", "label": _("Leechers")},
        {"key": "url", "label": _("URL")},
    ]
    def __init__(self, application, window):
        Gtk.VBox.__init__(self)
        
        self._application = application
        
        self.set_border_width(5)
        self.set_spacing(10)
        
        frame = Gtk.Frame()
        self.pack_start(frame, False, False, 0)
        l = Gtk.Label()
        l.set_markup("<big><b>%s</b></big>" % _("Torrent info"))
        frame.set_label_widget(l)
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.set_border_width(5)
        self._properties_table = Gtk.Table()
        self._properties_table.set_border_width(5)
        self._properties_table.set_row_spacings(5)
        self._properties_table.set_col_spacings(10)
        list_box = Gtk.ListBox()
        frame.add(list_box)
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        row = Gtk.ListBoxRow()
        row.add(self._properties_table)
        list_box.add(row)
        
        self._files_frame = Gtk.Frame()
        self.pack_start(self._files_frame, False, False, 0)
        l = Gtk.Label()
        l.set_markup("<big><b>%s</b></big>" % _("Files list"))
        self._files_frame.set_label_widget(l)
        self._files_frame.set_shadow_type(Gtk.ShadowType.NONE)
        scw = Gtk.ScrolledWindow()
        scw.set_border_width(5)
        scw.set_min_content_height(150)
        scw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._files_frame.add(scw)
        self._fileslist_treeview = Gtk.TreeView()
        scw.add(self._fileslist_treeview)
        self._fileslist_model = Gtk.ListStore(str, str)
        self._fileslist_treeview.set_model(self._fileslist_model)
        col = Gtk.TreeViewColumn(_("Filename"))
        r = Gtk.CellRendererText()
        col.pack_start(r, False)
        col.add_attribute(r, "text", 0)
        self._fileslist_treeview.append_column(col)
        col = Gtk.TreeViewColumn(_("Size"))
        r = Gtk.CellRendererText()
        col.pack_start(r, False)
        col.add_attribute(r, "text", 1)
        self._fileslist_treeview.append_column(col)
        
        sep = Gtk.HSeparator()
        self.pack_start(sep, False, False, 0)
        
        downloads_view = DownloadsView(application)
        self.pack_end(downloads_view, False, False, 0)
        
        self._current_result = None
    
    def _on_properties_treeview_button_press_event(self, widget, event):
        if event.button == 1:
            data=widget.get_path_at_pos(int(event.x), int(event.y))
            if data:
                path, column, x, y = data
                if column.get_property('title') == _("Value"):
                    row_iter = self._properties_model.get_iter(path)
                    if self._properties_model.get_value(row_iter, 0) == "url":
                        url = self._properties_model.get_value(row_iter, 2)
                        if url != "":
                            webbrowser.open(url)
                            return True
    
    def clear_torrent_details(self):
        self._current_result = None
        for i in self._properties_table.get_children():
            i.destroy()
        self._fileslist_model.clear()
    
    def display_torrent_details(self, result):
        self._current_result = result
        self._do_display_torrent_details(result)
        result.fetch_all(self._do_display_torrent_details, result)
    
    def _do_display_torrent_details(self, result):
        url_ev = None
        first = True
        if result == self._current_result:
            for i in self._properties_table.get_children():
                i.destroy()
            i = -1
            for prop in self.TORRENT_PROPERTIES:
                prop = self.TORRENT_PROPERTIES[i]
                if prop["key"] in result:
                    i += 1
                    if first:
                        first = False
                    else:
                        self._properties_table.attach(Gtk.HSeparator(), 0, 2, 2 * i - 1, 2 * i, Gtk.AttachOptions.FILL, Gtk.AttachOptions.SHRINK)
                    value = result[prop["key"]]
                    if prop["key"] == "size":
                        value = self._application.format_size(value)
                    elif prop["key"] in ["seeders", "leechers"]:
                        value = str(value)
                    elif prop["key"] == "date":
                        value = self._application.format_date(value)
                    label = Gtk.Label()
                    label.set_markup("<b>%s</b>" % prop["label"])
                    label.set_xalign(0)
                    label.set_yalign(0)
                    self._properties_table.attach(label, 0, 1, 2 * i, 2 * i +1, Gtk.AttachOptions.FILL, Gtk.AttachOptions.FILL)
                    value_label = Gtk.Label()
                    value_label.set_xalign(0)
                    value_label.set_yalign(0)
                    value_label.set_line_wrap(True)
                    value_label.set_width_chars(50) # Hack to get the label to have a proper height despite using wrapping
                    if prop["key"] == "url":
                        value_label.set_markup("<span color='#0000FF'><u>%s</u></span>" % value)
                    else:
                        value_label.set_text(value)
                    if prop["key"] == "url":
                        url_ev = Gtk.EventBox()
                        url_ev.add(value_label)
                        value_label = url_ev
                    self._properties_table.attach(value_label, 1, 2, 2 * i, 2 * i +1, Gtk.AttachOptions.FILL | Gtk.AttachOptions.EXPAND, Gtk.AttachOptions.FILL)
            self._properties_table.show_all()
            if url_ev is not None:
                url_ev.show_all()
                url_ev.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.HAND2))
                url_ev.connect("button-press-event", lambda w, e: webbrowser.open(result["url"]))
            
            self._fileslist_model.clear()
            if "files" in result:
                for f in result["files"]:
                    self._fileslist_model.append((f.filename, self._application.format_size(f.size)))
            else:
                self._fileslist_model.append((_("Loading..."), ""))
