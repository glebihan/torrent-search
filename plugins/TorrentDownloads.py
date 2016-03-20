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

class TorrentDownloadsPluginResult(BasePluginResult):
    def fetch_details(self):
        logging.debug("Loading details from : %s" % self["url"])
        
        response = self.http_get(self["url"])
        tree = HTMLNode(html.document_fromstring(response.text))
        
        for prop in [div for div in tree.find("div") if div.prop("class") is not None and"grey_bar1" in div.prop("class")]:
            value = prop.getContent().decode("utf-8").strip()
            if value.startswith("Torrent added: "):
                self["date"] = self._plugin.parse_date(value[15:].strip().split(" ")[0].strip())
        
        self["download_link"] = tree.find("img", src = "/templates/new/images/download_button1.jpg")[0].parent.prop("href")
        self["magnet_link"] = [a for a in tree.find("a") if a.prop("href") is not None and a.prop("href").startswith("magnet:")][0].prop("href")
        self["hash"] = self["magnet_link"].split(":btih:")[1].split("&dn")[0]
        
        self["files"] = []
        for f in tree.find("p", **{"class": "sub_file"}):
            try:
                self["files"].append(ResultFile(**{
                    "filename": f.getContent().decode("utf-8").strip(),
                    "size": self._plugin.parse_size(f.next.getContent().decode("utf-8").strip())
                }))
            except:
                pass

class TorrentDownloadsPlugin(BasePlugin):
    def parse_date(self, date):
        year, month, day = date.split("-")
        year = int(year)
        month = int(month)
        day = int(day)
        return datetime.date(year, month, day)
    
    def parse_size(self, size):
        units = ["KB", "MB", "GB", "TB"]
        value = size[:-3].strip()
        unit = size[-2:].strip()
        value = int(round(float(value)))
        ui = units.index(unit)
        while ui >= 0:
            value = 1024 * value
            ui -= 1
        return value
    
    def run_search(self, keyword, url = None):
        results = []
        if url == None:
            url = "http://www.torrentdownloads.me/search/?search=%s" % urllib.parse.quote_plus(keyword)
            
        logging.debug("Searching from : %s" % url)
        
        response = self.http_get(url)
        tree = HTMLNode(html.document_fromstring(response.text))
        lines = [a.parent.parent for a in tree.find("a") if a.prop("href") is not None and a.prop("href").startswith("/torrent/") and a.prop("title") is not None]
        for line in lines:
            try:
                main_link = line.find("a")[0]
                title = main_link.getContent().strip().decode("utf-8")
                result_url = urllib.parse.urljoin(url, main_link.prop("href"))
                health, leechers, seeders, size, check = line.find("span")
                leechers = int(leechers.getContent().decode("utf-8").strip())
                seeders = int(seeders.getContent().decode("utf-8").strip())
                size = self.parse_size(size.getContent().decode("utf-8").strip())
                result = TorrentDownloadsPluginResult(self, **{
                    "title": title,
                    "url": result_url,
                    "seeders": seeders,
                    "leechers": leechers,
                    "size": size,
                })
                results.append(result)
            except:
                traceback.print_exc()
        
        continue_url = None
        pager = tree.find("div", **{"class": "pagination_box"})
        if len(pager) == 1:
            links = [a for a in pager[0].find("a") if a.getContent().decode("utf-8") == ">>"]
            if len(links) == 1:
                continue_url = urllib.parse.urljoin(url, links[0].prop("href"))
            
        return {
            "continue_url": continue_url,
            "results": results
        }
