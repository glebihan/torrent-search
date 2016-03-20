# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from gi.repository import Gtk, GdkPixbuf
from .. import DownloadManager

STATUS_PIXBUFS = {
    DownloadManager.DOWNLOAD_STATUS_WAITING: Gtk.IconTheme.get_default().choose_icon(["network-idle"], Gtk.IconSize.lookup(Gtk.IconSize.BUTTON)[1], 0).load_icon(),
    DownloadManager.DOWNLOAD_STATUS_DOWNLOADING: Gtk.IconTheme.get_default().choose_icon(["network-receive"], Gtk.IconSize.lookup(Gtk.IconSize.BUTTON)[1], 0).load_icon(),
    DownloadManager.DOWNLOAD_STATUS_FAILED: Gtk.IconTheme.get_default().choose_icon(["gtk-no"], Gtk.IconSize.lookup(Gtk.IconSize.BUTTON)[1], 0).load_icon(),
    DownloadManager.DOWNLOAD_STATUS_DONE: Gtk.IconTheme.get_default().choose_icon(["gtk-yes"], Gtk.IconSize.lookup(Gtk.IconSize.BUTTON)[1], 0).load_icon(),
}

class DownloadsView(Gtk.Frame):
    def __init__(self, application):
        Gtk.Frame.__init__(self)
        
        self._application = application
        
        l = Gtk.Label()
        l.set_markup("<big><b>%s</b></big>" % _("Downloads"))
        self.set_label_widget(l)
        self.set_shadow_type(Gtk.ShadowType.NONE)
        scw = Gtk.ScrolledWindow()
        scw.set_border_width(5)
        scw.set_min_content_height(250)
        scw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.add(scw)
        self._downloads_treeview = Gtk.TreeView()
        self._downloads_treeview.set_headers_visible(False)
        scw.add(self._downloads_treeview)
        self._downloads_model = Gtk.ListStore(object, GdkPixbuf.Pixbuf, str)
        self._downloads_treeview.set_model(self._downloads_model)
        col = Gtk.TreeViewColumn()
        r = Gtk.CellRendererPixbuf()
        col.pack_start(r, False)
        col.add_attribute(r, "pixbuf", 1)
        r = Gtk.CellRendererText()
        col.pack_start(r, True)
        col.add_attribute(r, "text", 2)
        self._downloads_treeview.append_column(col)
        
        application.download_manager.set_view(self)
    
    def update(self):
        self._downloads_model.clear()
        self._application.download_manager.acquire_lock()
        for i in self._application.download_manager.queue:
            self._downloads_model.insert(0, (i, STATUS_PIXBUFS[i.status], i.title))
        self._application.download_manager.release_lock()
