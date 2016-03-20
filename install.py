#! /usr/bin/env python3
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import optparse
import subprocess
import os

if __name__ == "__main__":
    os.chdir(os.path.split(__file__)[0])
    
    optparser = optparse.OptionParser()
    optparser.add_option('--prefix', dest = "prefix", default = "/usr/local")
    cli_options, cli_args = optparser.parse_args()
    
    subprocess.call(["python3", "setup.py", "install", "--install-lib", os.path.join(cli_options.prefix, "share", "torrent-search"), "--install-scripts", os.path.join(cli_options.prefix, "share", "torrent-search"), "--prefix", cli_options.prefix])
    if not os.path.exists(os.path.join(cli_options.prefix, "bin", "torrent-search")):
        subprocess.call(["ln", "-s", os.path.join(cli_options.prefix, "share", "torrent-search", "torrent-search"), os.path.join(cli_options.prefix, "bin", "torrent-search")])
