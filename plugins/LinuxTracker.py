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

class LinuxTrackerPluginResult(BasePluginResult):
    def _do_fetch_all(self):
        logging.debug("Fetching all data from : %s" % self["url"])
        
        response = self.http_get(self["url"])
        tree = HTMLNode(html.document_fromstring(response.text))
        
        self["files"] = []
        files_div = tree.find("div", **{"id": "files"})
        if len(files_div) == 1:
            files_table = files_div[0].find("table")
            if len(files_table) == 1:
                for tr in files_table[0].find("tr")[1:]:
                    filename, size = tr.find("td")
                    self["files"].append(ResultFile(**{
                        "filename": filename.getContent().decode("utf-8").strip(),
                        "size": self._plugin.parse_size(size.getContent().decode("utf-8").replace(",", "").strip())
                    }))
        
        logging.debug("Fetching all data from : %s" % self["download_link_page"])
        
        response = self.http_get(self["download_link_page"])
        tree = HTMLNode(html.document_fromstring(response.text))
        
        download_link =[a for a in tree.find("a") if a.prop("href") is not None and a.prop("href").startswith("download.php")][0]
        self["download_link"] = urllib.parse.urljoin(self["download_link_page"], download_link.prop("href"))

class LinuxTrackerPlugin(BasePlugin):
    def _parse_date(self, date):
        day, month, year = date.split("/")
        year = int(year)
        month = int(month)
        day = int(day)
        return datetime.date(year, month, day)
    
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
            url = "http://linuxtracker.org/index.php?page=torrents&search=%s&category=0&active=1" % urllib.parse.quote_plus(keyword)
            
        logging.debug("Searching from : %s" % url)
        
        response = self.http_get(url)
        tree = HTMLNode(html.document_fromstring(response.text))
        table = tree.find("form", **{"name": "deltorrent"})[0].find("table", **{"class": "lista"})[0]
        for tr in table.find("tr", maxdepth = 2)[1:]:
            try:
                main_cell = tr.find("td", maxdepth = 1)[1]
                main_link = main_cell.find("a")[0]
                title = main_link.getContent().strip().decode("utf-8")
                if title.endswith("("):
                    title = title[:-1].strip()
                result_url = urllib.parse.urljoin(url, main_link.prop("href"))
                data_table = main_cell.find("table")[0]
                for data_tr in data_table.find("tr"):
                    line = data_tr.getContent().decode("utf-8").strip()
                    if line.startswith("Added On: "):
                        date = self._parse_date(line[10:].strip())
                    elif line.startswith("Size: "):
                        size = self.parse_size(line[6:].replace(",", "").strip())
                    elif line.startswith("Seeds "):
                        seeders = int(line[6:].strip())
                    elif line.startswith("Leechers "):
                        leechers = int(line[9:].strip())
                magnet_links = [a for a in tr.find("a") if a.prop("href") is not None and a.prop("href").startswith("magnet:")]
                download_link_page = urllib.parse.urljoin(url, magnet_links[0].next.prop("href"))
                result = LinuxTrackerPluginResult(self, **{
                    "title": title,
                    "url": result_url,
                    "seeders": seeders,
                    "leechers": leechers,
                    "date": date,
                    "size": size,
                    "hash": result_url.split("id=")[1].split("&")[0],
                    "magnet_link": magnet_links[0].prop("href"),
                    "download_link_page": download_link_page
                })
                results.append(result)
            except:
                traceback.print_exc()
        
        continue_url = None
        pagercurrent = tree.find("span", **{"class": "pagercurrent"})
        if len(pagercurrent) > 0 and pagercurrent[0].next is not None:
            continue_url = urllib.parse.urljoin(url, pagercurrent[0].next.find("a")[0].prop("href"))
            
        return {
            "continue_url": continue_url,
            "results": results
        }
