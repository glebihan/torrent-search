# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import requests
import logging
import traceback
import datetime
import time
import urllib.parse
from TorrentSearch.HTMLNode import HTMLNode
from TorrentSearch.BasePlugin import BasePlugin
from TorrentSearch.BasePluginResult import BasePluginResult
from TorrentSearch.ResultFile import ResultFile
from lxml import html
from io import StringIO

class RarbgPluginResult(BasePluginResult):
    def fetch_details(self):
        logging.debug("Loading details from : %s" % self["url"])
        
        response = self.http_get(self["url"])
        tree = HTMLNode(html.document_fromstring(response.text))
        
        print ([a for a in tree.find("a") if a.prop("href") is not None and a.prop("href").startswith("magnet:")])

class RarbgPlugin(BasePlugin):
    def parse_size(self, size):
        units = ["KB", "MB", "GB", "TB"]
        value, unit = size.split(" ")
        value = int(round(float(value.strip())))
        ui = units.index(unit.strip())
        while ui >= 0:
            value = 1024 * value
            ui -= 1
        return value
    
    def run_search(self, keyword, url = None):
        results = []
        if url == None:
            url = "https://rarbg.to/torrents.php?search=%s" % urllib.parse.quote_plus(keyword)
            
        logging.debug("Searching from : %s" % url)
        
        response = self.http_get(url)
        print(response.text)
        tree = HTMLNode(html.document_fromstring(response.text))
        table = tree.find("table", **{"class": "lista2t"})[0]
        for tr in table.find("tr", maxdepth = 2)[1:]:
            try:
                main_link = tr.find("td", maxdepth = 1)[1].find("a")[0]
                title = main_link.getContent().strip().decode("utf-8")
                result_url = urllib.parse.urljoin(url, main_link.prop("href"))
                date = tr.find("td", maxdepth = 1)[2].getContent().decode("utf-8").strip()
                date = time.strptime(date.split(" ")[0], "%Y-%m-%d")
                date = datetime.date(date.tm_year, date.tm_mon, date.tm_mday)
                size = self.parse_size(tr.find("td", maxdepth = 1)[3].getContent().decode("utf-8").strip())
                seeders = int(tr.find("td", maxdepth = 1)[4].getContent().decode("utf-8").strip())
                leechers = int(tr.find("td", maxdepth = 1)[5].getContent().decode("utf-8").strip())
                result = RarbgPluginResult(self, **{
                    "title": title,
                    "url": result_url,
                    "seeders": seeders,
                    "leechers": leechers,
                    "date": date,
                    "size": size
                })
                results.append(result)
            except:
                traceback.print_exc()
        
        continue_url = None
        #~ next_page_links = [a for a in tree.find("a", **{"class": "pager_link"}) if a.getContent().decode("utf-8").strip() == ">"]
        #~ if len(next_page_links) > 0:
            #~ continue_url = urllib.parse.urljoin(url, next_page_links[0].prop("href"))
            
        return {
            "continue_url": continue_url,
            "results": results
        }
