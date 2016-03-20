# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from gi.repository import Gtk, GdkPixbuf

class ResultsPane(Gtk.TreeView):
    COLUMNS = [
        {"title": _("Title"), "key": "title", "type": str, "cmp_method": "_str_cmp"},
        {"title": _("Date"), "key": "date", "type": str},
        {"title": _("Size"), "key": "size", "type": str, "cmp_method": "_size_cmp"},
        {"title": _("Seeders"), "key": "seeders", "type": int},
        {"title": _("Leechers"), "key": "leechers", "type": int},
    ]
    DEFAULT_SORT = ("seeders", "DESCENDING")
    def __init__(self, application, window):
        Gtk.TreeView.__init__(self)
        
        self._application = application
        self._window = window
        
        self.set_headers_clickable(True)
        
        model_columns = (object,)
        
        i = 0
        for column in self.COLUMNS:
            col = Gtk.TreeViewColumn(column["title"])
            r = Gtk.CellRendererText()
            col.pack_start(r, False)
            col.set_resizable(True)
            col.add_attribute(r, "text", i + 1)
            model_columns += (column["type"],)
            self.append_column(col)
            col.set_sort_column_id(i + 1)
            i += 1
        
        self._filters = {}
        self._current_keyword = ""
        
        self._model = Gtk.ListStore(*model_columns)
        self._filtered_model = self._model.filter_new()
        self._filtered_model.set_visible_func(self._get_must_show)
        self._sorted_and_filtered_model = Gtk.TreeModelSort(self._filtered_model)
        self.set_model(self._sorted_and_filtered_model)
        
        for i in range(len(self.COLUMNS)):
            column = self.COLUMNS[i]
            if "cmp_method" in column:
                self._sorted_and_filtered_model.set_sort_func(i + 1, getattr(self, column["cmp_method"]), i + 1)
            if column["key"] == self.DEFAULT_SORT[0]:
                if self.DEFAULT_SORT[1] == "DESCENDING":
                    self._sorted_and_filtered_model.set_sort_column_id(i + 1, Gtk.SortType.DESCENDING)
                else:
                    self._sorted_and_filtered_model.set_sort_column_id(i + 1, Gtk.SortType.ASCENDING)
        
        self.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        
        self.connect('row-activated', self._on_row_activated)
        self.get_selection().connect('changed', self._on_selection_changed)
    
    def _on_selection_changed(self, selection):
        self._window.clear_torrent_details()
        
        model, paths = selection.get_selected_rows()
        if len(paths) == 1:
            result = model[paths[0]][0]
            self._window.display_torrent_details(result)
    
    def update_search_filters(self, keyword, filters):
        self._current_keyword = keyword
        self._filters = filters
        self._filtered_model.refilter()
    
    def _split_words(self, phrase):
        words = []
        sw = 0
        i = 0
        while i < len(phrase):
            if phrase[i].isalnum():
                i += 1
            else:
                words.append(phrase[sw:i])
                sw = i+1
                i += 1
        words.append(phrase[sw:])
        return words
    
    def _get_must_show(self, model, row_iter, data):
        result = model.get_value(row_iter, 0)
        if self._filters.setdefault("minimum_size", 0) > 0 and (result["size"] is None or result["size"] < self._filters["minimum_size"]):
            return False
        if self._filters.setdefault("maximum_size", 0) > 0 and result["size"] is not None and result["size"] > self._filters["maximum_size"]:
            return False
        if self._filters.setdefault("hide_torrents_with_no_seeders", False) and result["seeders"] == 0:
            return False
        if self._filters.setdefault("minimum_date", None) is not None and result["date"] < self._filters["minimum_date"]:
            return False
        if self._filters.setdefault("maximum_date", None) is not None and result["date"] > self._filters["maximum_date"]:
            return False
        if self._filters.setdefault("show_only_torrents_with_all_words_in_name", False):
            for word in self._split_words(self._current_keyword):
                if not word in result["title"].lower():
                    return False
        if self._filters.setdefault("show_only_torrents_with_exact_phrase_in_name", False) and not self._current_keyword in result["title"].lower():
            return False
        if self._filters.setdefault("name_contains", "") != "" and not self._filters["name_contains"].lower() in result["title"].lower():
            return False
        if self._filters.setdefault("name_does_not_contain", "") != "" and self._filters["name_does_not_contain"].lower() in result["title"].lower():
            return False
        return True
    
    def _str_cmp(self, model, iter1, iter2, cid):
        a = model.get(iter1, cid)[0]
        b = model.get(iter2, cid)[0]
        return (a.lower() > b.lower()) - (a.lower() < b.lower())
    
    def _size_cmp(self, model, iter1, iter2, cid):
        a = model.get(iter1, 0)[0]
        b = model.get(iter2, 0)[0]
        return (a["size"] > b["size"]) - (a["size"] < b["size"])
    
    def display_result(self, plugin, result):
        line = (result,)
        for column in self.COLUMNS:
            if column["key"] == "date":
                value = self._application.format_date(result["date"])
            elif column["key"] == "size":
                value = self._application.format_size(result["size"])
            elif column["key"] == "title":
                if len(result["title"]) > 80:
                    value = result["title"][:77] + "..."
                else:
                    value = result["title"]
            else:
                value = result[column["key"]]
            line += (value,)
        self._model.append(line)
    
    def clear_results(self):
        self._model.clear()
    
    def _on_row_activated(self, treeview, path, column):
        row_iter = self._sorted_and_filtered_model.get_iter(path)
        result = self._sorted_and_filtered_model.get_value(row_iter, 0)
        self._application.download_result(result)
