# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from gi.repository import Gtk
from ..metadata import *

class AboutDialog(Gtk.AboutDialog):
    def __init__(self, application, window):
        Gtk.AboutDialog.__init__(self)
        
        self.set_transient_for(window)
        
        self.set_program_name(APPNAME)
        self.set_version(VERSION)
        self.set_authors(AUTHORS)
        #~ self.set_documenters(DOCUMENTERS)
        #~ self.set_translator_credits(TRANSLATOR_CREDITS)
        self.set_website(WEBSITE)
        self.set_copyright(COPYRIGHT)
        self.set_license(LICENSE)
        #~ self.set_artists(ARTISTS)
        self.set_logo_icon_name(UNIX_APPNAME)
    
    def run(self):
        self.show_all()
        Gtk.AboutDialog.run(self)
        self.hide()
