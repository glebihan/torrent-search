# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import threading
import configparser
import os
import json
import platform
from .metadata import *
from . import TorrentClient
from .ui import SettingsWidgets

class AppConfiguration(configparser.ConfigParser):
    _SPECIAL_DEFAULTS = {
        "default_torrent_client_id": TorrentClient.TorrentClient.get_default().get_id()
    }
    def __init__(self, application, data_dir):
        configparser.ConfigParser.__init__(self)
        
        self._application = application
        self._data_dir = data_dir
        
        self._lock = threading.Lock()
        
        self._load()
    
    def get_preferences_section(self, section):
        return self._preferences_sections.setdefault(section, [])
    
    def get_filters_options(self):
        return self._filters_options
    
    def _get_filename(self):
        if platform.system() == "Windows":
            return os.path.join(os.getenv("APPDATA"), APPNAME, UNIX_APPNAME + ".cfg")
        else:
            return os.path.join(os.getenv("HOME"), ".config", UNIX_APPNAME, UNIX_APPNAME + ".cfg")
    filename = property(_get_filename)
            
    def _load(self):
        settings_json_file = os.path.join(self._data_dir, "settings.json")
        
        f = open(settings_json_file)
        data = json.loads(f.read())
        f.close()
        
        self._default_values = {}
        self._preferences_sections = {}
        self._filters_options = {}
        for section in data["settings"]:
            self._default_values[section] = {}
            for option in data["settings"][section]:
                if option["type"] == "bool":
                    option["default"] = str(option["default"])
                elif "default" in option and type(option["default"]) == str and option["default"].startswith("special::"):
                    option["default"] = self._SPECIAL_DEFAULTS.setdefault(option["default"][9:], "")
                self._default_values[section][option["key"]] = option["default"]
                
                if "widget" in option:
                    option["widget_class"] = getattr(SettingsWidgets, option["widget"])
                
                option["section"] = section
                
                if "preferences_section" in option:
                    self._preferences_sections.setdefault(option["preferences_section"], {}).setdefault(option["preferences_subsection"], []).append(option)
                
                if "filters_section" in option:
                    self._filters_options.setdefault(option["filters_section"], []).append(option)
        
        for section in self._preferences_sections:
            self._preferences_sections[section] = [
                {
                    "section": subsection,
                    "section_label": _(subsection),
                    "items": [
                        {
                            "label": _(option["label"]),
                            "widget_class": option["widget_class"],
                            "section": option["section"],
                            "key": option["key"]
                        }
                        for option in self._preferences_sections[section][subsection]
                    ]
                }
                for subsection in self._preferences_sections[section]
            ]
            self._preferences_sections[section].sort(key = lambda a: data["preferences_sections_order"][section].index(a["section"]))
        
        self._filters_options = [
            {
                "section": section,
                "section_label": _(section),
                "items": [
                    {
                        "label": _(option["label"]),
                        "widget_class": option["widget_class"],
                        "key": option["key"],
                        "save": option["save"]
                    }
                    for option in self._filters_options[section]
                ]
            }
            for section in self._filters_options
        ]
        self._filters_options.sort(key = lambda a: data["filters_sections_order"].index(a["section"]))
            
        self.read([self.filename])
    
    def _save(self):
        if not os.path.exists(os.path.split(self.filename)[0]):
            os.mkdir(os.path.split(self.filename)[0])
        f = open(self.filename, "w")
        self.write(f)
        f.close()
    
    def set(self, section, key, value):
        if not self.has_section(section):
            self.add_section(section)
        configparser.ConfigParser.set(self, section, key, value)
        self._save()
    
    def get(self, section, option, raw = False, vars = None, fallback = None):
        if fallback is None:
            fallback = self._default_values.setdefault(section, {}).setdefault(option, None)
        return configparser.ConfigParser.get(self, section, option, raw = raw, vars = vars, fallback = fallback)
        
    def getint(self, section, option, raw = False, vars = None, fallback = None):
        if fallback is None:
            fallback = self._default_values.setdefault(section, {}).setdefault(option, None)
        return configparser.ConfigParser.getint(self, section, option, raw = raw, vars = vars, fallback = fallback)
        
    def getfloat(self, section, option, raw = False, vars = None, fallback = None):
        if fallback is None:
            fallback = self._default_values.setdefault(section, {}).setdefault(option, None)
        return configparser.ConfigParser.getfloat(self, section, option, raw = raw, vars = vars, fallback = fallback)
        
    def getboolean(self, section, option, raw = False, vars = None, fallback = None):
        if fallback is None:
            fallback = self._default_values.setdefault(section, {}).setdefault(option, None)
        return configparser.ConfigParser.getboolean(self, section, option, raw = raw, vars = vars, fallback = fallback)
