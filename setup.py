#! /usr/bin/env python3
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import sys
import os
import subprocess
import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

base_path = os.path.split(__file__)[0]

sys.path.insert(0, os.path.join(base_path, "src"))
from TorrentSearch.metadata import *
from distutils.core import setup

data_files = []
data_files.append(("share/" + UNIX_APPNAME, ["data/settings.json", "data/keyring.gpg"]))
for filename in subprocess.check_output(["find", os.path.join(base_path, "l10n"), "-name", "*.mo"]).splitlines():
    filename = filename.decode("utf-8")
    data_files.append(("share/locale/%s/LC_MESSAGES" % os.path.split(os.path.split(filename)[0])[1], [filename]))
data_files.append(("share/applications", ["data/%s.desktop" % UNIX_APPNAME]))
data_files.append(("share/icons/hicolor/scalable/apps", ["data/%s.svg" % UNIX_APPNAME]))

if not os.path.exists(os.path.join(base_path, "data", "icons")):
    os.mkdir(os.path.join(base_path, "data", "icons"))
for size in [16, 22, 24, 32, 48, 64, 72, 128]:
    if not os.path.exists(os.path.join(base_path, "data", "icons", "%dx%d" % (size, size))):
        os.mkdir(os.path.join(base_path, "data", "icons", "%dx%d" % (size, size)))
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(os.path.join(base_path, "data", "%s.svg" % UNIX_APPNAME), size, size)
    pixbuf.savev(os.path.join(base_path, "data", "icons", "%dx%d" % (size, size), "%s.png" % UNIX_APPNAME), "png", [None], [None])
    data_files.append(("share/icons/hicolor/%dx%d/apps" % (size, size), ["data/icons/%dx%d/%s.png" % (size, size, UNIX_APPNAME)]))

setup(
    name = UNIX_APPNAME,
    version = VERSION,
    author = 'Gwendal Le Bihan',
    author_email = 'gwendal.lebihan.dev@gmail.com',
    maintainer = 'Gwendal Le Bihan',
    maintainer_email = 'gwendal.lebihan.dev@gmail.com',
    description = 'Search for torrents on different websites',
    scripts = ["src/torrent-search"],
    packages = ["TorrentSearch", "TorrentSearch.ui"],
    package_dir = {
        'TorrentSearch':  'src/TorrentSearch'
    },
    data_files = data_files,
    url = WEBSITE,
    download_url = WEBSITE + "download.html",
)
