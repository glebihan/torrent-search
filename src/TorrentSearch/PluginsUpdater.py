# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import threading
import tempfile
import gnupg
import os
import json
import base64
import logging
import subprocess
import traceback
from gi.repository import GLib
from .metadata import *
from .ui.PluginsUpdateDialog import PluginsUpdateDialog
from . import fstools

class PluginsUpdater(object):
    def __init__(self, application, callback):
        self._application = application
        self._callback = callback
        
        self._dialog = PluginsUpdateDialog(self._application.window, self)
    
    def _download(self, url):
        res = self._application.http_get(url)
        f = tempfile.NamedTemporaryFile(delete = False)
        f.write(res.content)
        f.close()
        return f.name
    
    def _download_and_verify(self, url):
        filename = self._download(url)
        gpg = gnupg.GPG(keyring = os.path.join(self._application.cli_options.data_dir, "keyring.gpg"))
        g = open(filename, "rb")
        verified = gpg.verify_file(g)
        g.close()
        if verified:
            f = tempfile.NamedTemporaryFile(delete = False)
            f.close()
            g = open(filename, "rb")
            gpg.decrypt_file(g, output = f.name)
            g.close()
            return f.name
        else:
            logging.error("Could not verify download : %s" % url)
            os.unlink(filename)
            return None
    
    def _do_run(self):
        try:
            if not os.path.exists(self._application.cli_options.plugins_dir):
                fstools.rec_mkdir(self._application.cli_options.plugins_dir)
            
            current_plugin_versions = {}
            for plugin in self._application.search_plugins:
                current_plugin_versions[plugin.ID] = plugin.VERSION
            url = "%splugins.json?appversion=%s&state=%s" % (WEBSITE, VERSION, base64.b64encode(json.dumps(current_plugin_versions).encode("utf-8")).decode("utf-8"))
                
            json_filename = self._download(url)
            f = open(json_filename)
            plugin_updates = json.loads(f.read())
            f.close()
            updates = plugin_updates.setdefault("updates", [])
            if len(updates) > 0:
                i = 0
                for update in updates:
                    plugin_filename = self._download_and_verify(update["url"])
                    if plugin_filename is not None:
                        subprocess.call(["tar", "--overwrite", "-C", self._application.cli_options.plugins_dir, "-xvvf", plugin_filename], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
                    i += 1
                    self._dialog.set_fraction(i / len(updates))
        except:
            traceback.print_exc()
            
        GLib.idle_add(self._on_run_complete)
    
    def _on_run_complete(self):
        self._dialog.hide()
        self._application.load_plugins()
        self._callback()
    
    def run(self):
        self._dialog.show_all()
        threading.Thread(target = self._do_run).start()
