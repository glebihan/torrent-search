# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from gi.repository import Gtk, Gio

class MainMenuButton(Gtk.MenuButton):
    def __init__(self, application, window):
        Gtk.MenuButton.__init__(self)
        
        image = Gtk.Image()
        self.add(image)
        image.set_from_icon_name("open-menu-symbolic", Gtk.IconSize.MENU)
        
        self._menu = Gio.Menu()
        section = Gio.Menu()
        section.append(_("Preferences"), "app.preferences")
        section.append(_("About"), "app.about")
        self._menu.append_section(None, section)
        section = Gio.Menu()
        section.append(_("Quit"), "app.quit")
        self._menu.append_section(None, section)
        self.set_menu_model(self._menu)
