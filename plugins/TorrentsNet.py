# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from TorrentSearch.BasePlugin import BasePlugin
from TorrentSearch.BasePluginResult import BasePluginResult
from TorrentSearch.ResultFile import ResultFile
import urllib.parse
import logging
import traceback
import datetime
import time
from lxml import html
from TorrentSearch.HTMLNode import HTMLNode

class TorrentsNetPluginResult(BasePluginResult):
    def fetch_details(self):
        logging.debug("Loading details from : %s" % self["url"])
        
        response = self.http_get(self["url"])
        tree = HTMLNode(html.document_fromstring(response.text))
        
        for dl in tree.find("div", **{"class": "info-table"})[0].find("dl"):
            key = dl.find("dt")[0].getContent().decode("utf-8").strip()
            value = dl.find("dd")[0].getContent().decode("utf-8").strip()
            if key == "Added":
                self["date"] = self._plugin.parse_date(value)
            if key == "Hash":
                self["hash"] = value
        
        self["magnet_link"] = tree.find("a", **{"class": "btn2-download"})[0].prop("href")
        
        self["files"] = []
        for li in tree.find("div", **{"class": "files-table"})[0].find("ul")[0].find("li"):
            try:
                self["files"].append(ResultFile(**{
                    "filename": li.find("span", **{"class": "name"})[0].getContent().decode("utf-8").strip(),
                    "size": self._plugin.parse_size(li.find("span", **{"class": "size"})[0].getContent().decode("utf-8").strip())
                }))
            except:
                pass
    
class TorrentsNetPlugin(BasePlugin):
    def parse_date(self, date):
        day, month, year = date.split("-")
        year = int(year)
        month = int(month)
        day = int(day)
        return datetime.date(year, month, day)
    
    def parse_size(self, size):
        units = ["B", "KB", "MB", "GB", "TB"]
        value, unit = size.split(" ")
        value = int(round(float(value.strip())))
        ui = units.index(unit.strip().upper())
        while ui > 0:
            value = 1024 * value
            ui -= 1
        return value
        
    def run_search(self, keyword, url = None):
        results = []
        if url == None:
            url = "http://www.torrents.net/find/%s/" % urllib.parse.quote_plus(keyword)
            
        logging.debug("Searching from : %s" % url)
        
        response = self.http_get(url)
        tree = HTMLNode(html.document_fromstring(response.text))
        
        ul = tree.find("ul", **{"class": "table-list newly"})[0]
        for li in ul.find("li", maxdepth = 1):
            try:
                title = li.find("div", **{"class": "name"})[0].find("span")[0].getContent().decode("utf-8").strip()
                result_url = urllib.parse.urljoin(url, "/" + li.find("div", **{"class": "name"})[0].find("span")[0].find("a")[0].prop("href"))
                size = self.parse_size(li.find("span", **{"class": "size"})[0].getContent().decode("utf-8").strip())
                seeders = int(li.find("span", **{"class": "s"})[0].getContent().decode("utf-8").strip())
                leechers = int(li.find("span", **{"class": "l"})[0].getContent().decode("utf-8").strip())
                result = TorrentsNetPluginResult(self, **{
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
        next_page_links = tree.find("img", src = "//thepiratebay.se/static/img/next.gif")
        if len(next_page_links) == 1:
            continue_url = urllib.parse.urljoin(url, next_page_links[0].parent.prop("href"))
            
        return {
            "continue_url": continue_url,
            "results": results
        }
