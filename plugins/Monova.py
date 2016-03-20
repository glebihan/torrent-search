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

class MonovaPluginResult(BasePluginResult):
    def fetch_details(self):
        logging.debug("Loading details from : %s" % self["url"])
        
        response = self.http_get(self["url"], cookies = {'adult': 'true'})
        tree = HTMLNode(html.document_fromstring(response.text))
        
        self["date"] = self._plugin.parse_date(tree.find("h5", **{"class": "torrent_added"})[0].find("span")[0].getContent().decode("utf-8").strip().split(" by")[0].strip())
        
        infos_div = tree.find("div", **{"class": "col-md-7 general-info"})[0]
        for div in infos_div.find("div", maxdepth = 1):
            data = div.getContent().decode("utf-8").strip()
            if data.startswith("Hash:"):
                self["hash"] = data[5:].strip()
        
        magnet_link = tree.find("a", **{"id": "download-magnet"})
        if len(magnet_link) == 1 and magnet_link[0].prop("href").startswith("magnet:"):
            self["magnet_link"] = magnet_link[0].prop("href")
            
        file_link = tree.find("a", **{"id": "download-file"})
        if len(file_link) == 1 and file_link[0].prop("href").endswith(".torrent"):
            self["download_link"] = urllib.parse.urljoin(self["url"], file_link[0].prop("href"))

class MonovaPlugin(BasePlugin):
    def parse_date(self, date):
        monthday, year = date.split(", ")
        month, day = monthday.split(" ")
        month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(month.strip())+1
        year = int(year.strip())
        day = int(day.strip())
        return datetime.date(year, month, day)
    
    def parse_size(self, size):
        if size == "N/A":
            return None
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
            url = "http://monova.org/search?term=%s&method=" % urllib.parse.quote_plus(keyword)
            
        logging.debug("Searching from : %s" % url)
        
        response = self.http_get(url, cookies = {'adult': 'true'})
        tree = HTMLNode(html.document_fromstring(response.text))
        table = tree.find("table", **{"class": "table table-bordered main-table"})[0].find("tbody")[0]
        for tr in table.find("tr", maxdepth = 2):
            try:
                main_link = tr.find("td")[0].find("a")[0]
                title = main_link.getContent().strip().decode("utf-8")
                result_url = urllib.parse.urljoin(url, main_link.prop("href"))
                if not result_url.startswith("http://monova.org/torrent/"):
                    continue
                size = self.parse_size(tr.find("td")[4].getContent().strip().decode("utf-8").replace(",", ""))
                seeders = int(tr.find("td")[6].getContent().strip().decode("utf-8"))
                leechers = int(tr.find("td")[7].getContent().strip().decode("utf-8"))
                result = MonovaPluginResult(self, **{
                    "title": title,
                    "url": result_url,
                    "seeders": seeders,
                    "leechers": leechers,
                    "size": size
                })
                results.append(result)
            except:
                traceback.print_exc()
        
        continue_url = None
        pagination = tree.find("ul", **{"class": "pagination pagination-lg"})
        if len(pagination) > 0:
            current_page = pagination[0].find("li", **{"class": "active"})
            if len(current_page) == 1 and current_page[0].next is not None:
                continue_url = urllib.parse.urljoin(url, current_page[0].next.find("a")[0].prop("href"))
        if continue_url is None and not "cat=6" in url:
            continue_url = "http://monova.org/search?term=%s&method=&cat=6" % urllib.parse.quote_plus(keyword)
            
        return {
            "continue_url": continue_url,
            "results": results
        }
