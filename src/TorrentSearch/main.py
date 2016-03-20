# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib
from .ui.MainWindow import MainWindow
from .ui.PreferencesDialog import PreferencesDialog
from .ui.AboutDialog import AboutDialog
from .AppConfiguration import AppConfiguration
from .SearchProcess import SearchProcess
from .DownloadManager import DownloadManager
from .PluginsUpdater import PluginsUpdater
from .metadata import *
from . import TorrentClient
import logging
import os
import imp
import threading
import requests
import tempfile
import json
import gnupg
import platform
import urllib.request

logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.ERROR)

class Application(Gtk.Application):
    def __init__(self, cli_options):
        Gtk.Application.__init__(self, application_id = "org." + UNIX_APPNAME, register_session = True)
        
        self.cli_options = cli_options
        self.cli_options.plugins_dir = os.path.realpath(self.cli_options.plugins_dir)
        self.cli_options.data_dir = os.path.realpath(self.cli_options.data_dir)
        
        self.connect("activate", self.activate)
        self.connect("startup", self.startup)
        self.connect("shutdown", self.shutdown)
        
        self.configuration = AppConfiguration(self, self.cli_options.data_dir)
        self.download_manager = DownloadManager(self)
                
        self._search_id = 0
        self._search_process = None
        self._current_keyword = ""
        self.search_history = self.configuration.get("History", "search_history").split("\n")
        if len(self.search_history) == 1 and self.search_history[0] == "":
            self.search_history = []
    
    def startup(self, application):
        ACTIONS = {
            "quit": lambda a,e: self.quit(),
            "about": lambda a,e: self._about_dialog.run(),
            "preferences": lambda a,e: self._preferences_dialog.run()
        }
        for action_name in ACTIONS:
            action = Gio.SimpleAction(name = action_name)
            action.connect("activate", ACTIONS[action_name])        
            self.add_action(action)
        
        self.load_plugins()
            
    def load_plugins(self):
        self.search_plugins = []
        
        disabled_plugins = []
        for i in self.configuration.get("Plugins", "disabled_plugins").split(","):
            if i != "":
                disabled_plugins.append(i)
        
        if os.path.exists(self.cli_options.plugins_dir):
            for filename in os.listdir(self.cli_options.plugins_dir):
                if filename.endswith(".py"):
                    try:
                        plugin_id = filename[:-3]
                        metadata_file = os.path.join(self.cli_options.plugins_dir, filename[:-3] + ".json")
                        if os.path.exists(metadata_file):
                            f = open(metadata_file)
                            metadata = json.loads(f.read())
                            f.close()
                        else:
                            metadata = {}
                        full_filename = os.path.join(self.cli_options.plugins_dir, filename)
                        f = open(full_filename)
                        m = imp.load_module(plugin_id, f, full_filename, ('.py', 'r', imp.PY_SOURCE))
                        plugin_class = getattr(m, plugin_id + "Plugin")
                        plugin = plugin_class(self)
                        plugin.ID = plugin_id
                        plugin.NAME = metadata.setdefault("name", plugin_id)
                        plugin.URL = metadata.setdefault("url", "")
                        plugin.VERSION = metadata.setdefault("version", 1)
                        plugin.enabled = not (plugin_id in disabled_plugins)
                        self.search_plugins.append(plugin)
                    except:
                        logging.warn("Failed to load plugin from file : %s" % filename)
        else:
            logging.warn("Plugins folder \"%s\" does not exist" % self.cli_options.plugins_dir)
    
    def _get_enabled_search_plugins(self):
        return [p for p in self.search_plugins if p.enabled]
    enabled_search_plugins = property(_get_enabled_search_plugins)
    
    def activate(self, application):
        self.window = MainWindow(self)
        self.window.show_all()
        
        self._about_dialog = AboutDialog(self, self.window)
        self._preferences_dialog = PreferencesDialog(self, self.window)
        
        if self.configuration.getboolean("Network", "check_plugin_updates_on_startup"):
            PluginsUpdater(self, self.finalize_activate).run()
        else:
            self.finalize_activate()
    
    def finalize_activate(self):
        self.update_search_filters()
        
        if self.cli_options.search:
            self.window.run_search(self.cli_options.search)
        
    def shutdown(self, shutdown):
        if self._search_process:
            self._search_process.stop()
        os.kill(os.getpid(), 9)
    
    def run_search(self, keyword):
        if self._search_process:
            self._search_process.stop()
            self._search_process = None
            
        self.window.clear_results()
        
        while "  " in keyword:
            keyword = keyword.replace("  "," ")
        keyword = keyword.lower()
        
        if len(keyword) > 0:
            self._search_id += 1
            self._current_keyword = keyword
            self.update_search_filters()
            self._search_process = SearchProcess(self, self._search_id, keyword)
            self._search_process.start()
            if keyword.lower() in self.search_history:
                i = self.search_history.index(keyword.lower())
                del self.search_history[i]
            self.search_history.insert(0, keyword.lower())
            self.search_history = self.search_history[:100]
            self.configuration.set("History", "search_history", "\n".join(self.search_history))
    
    def display_result(self, search_id, plugin, result):
        if search_id == self._search_id:
            self.window.display_result(plugin, result)
    
    def get_selected_torrent_client(self):
        for i in TorrentClient.TorrentClient.get_list():
            if i.get_id() == self.configuration.get("Downloads", "torrent_client"):
                return i
        return TorrentClient.TorrentClient.get_default()
    
    def download_result(self, result):
        self.download_manager.append(result)
    
    def http_get(self, url, params = None, **kwargs):
        kwargs.setdefault("headers", {})["User-Agent"] = self.configuration.get("Network", "http_user_agent")
        return requests.get(url, params, **kwargs)
    
    def http_post(self, url, data = None, json = None, **kwargs):
        kwargs.setdefault("headers", {})["User-Agent"] = self.configuration.get("Network", "http_user_agent")
        return requests.post(url, data, json, **kwargs)
    
    def update_search_filters(self):
        self.window.update_search_filters(self._current_keyword)
    
    def format_size(self, value):
        if value is None:
            return "?"
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        ui = 0
        while value >= 1024 and ui < len(units) - 1:
            value = value / 1024
            ui += 1
        return "%.1f %s" % (value, units[ui])
    
    def format_date(self, date):
        return date.strftime(self.configuration.get("Display", "date_format"))
