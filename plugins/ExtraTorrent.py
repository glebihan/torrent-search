# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import requests
import logging
import traceback
import datetime
import urllib.parse
from TorrentSearch.HTMLNode import HTMLNode
from TorrentSearch.BasePlugin import BasePlugin
from TorrentSearch.BasePluginResult import BasePluginResult
from TorrentSearch.ResultFile import ResultFile
from lxml import html
from io import StringIO

class ExtraTorrentPluginResult(BasePluginResult):
    def fetch_details(self):
        logging.debug("Loading details from : %s" % self["url"])
        
        response = self.http_get(self["url"])
        tree = HTMLNode(html.document_fromstring(response.text))
        
        data = {}
        for label_cell in tree.find("td", **{"class": "tabledata1"}):
            label = label_cell.getContent().decode("utf-8").strip()
            data[label] = label_cell.parent.find("td")[1].getContent().decode("utf-8").strip()
        
        if "Info hash:" in data:
            self["hash"] = data["Info hash:"]
        if "Torrent added:" in data:
            self["date"] = self._parse_date(data["Torrent added:"])
        
        self["magnet_link"] = tree.find("a", title = "Magnet link")[0].prop("href")
        
        torrent_files_link = [a for a in tree.find("a") if a.prop("href") is not None and a.prop("href").startswith("/torrent_files/")]
        if len(torrent_files_link) > 0:
            self["torrent_files_page"] = urllib.parse.urljoin(self["url"], torrent_files_link[0].prop("href"))
    
    def _do_fetch_all(self):
        logging.debug("Fetching all data from : %s" % self["url"])
        
        if "torrent_files_page" in self:
            self["files"] = []
            response = self.http_get(self["torrent_files_page"])
            tree = HTMLNode(html.document_fromstring(response.text))
            for td in tree.find("td", colspan = "99"):
                filedata = td.getContent().decode("utf-8").strip()
                try:
                    self["files"].append(ResultFile(**{
                        "filename":  ("(".join(filedata.split("(")[:-1])).strip(),
                        "size": self._plugin.parse_size(filedata.split("(")[-1].split(")")[0].strip())
                    }))
                except:
                    pass
        
        if "download_link_page" in self:
            response = self.http_get(self["download_link_page"])
            tree = HTMLNode(html.document_fromstring(response.text))
            download_links = [a for a in tree.find("a") if a.prop("href") is not None and a.prop("href").startswith("/download/")]
            if len(download_links) == 1:
                self["download_link"] = urllib.parse.urljoin(self["download_link_page"], download_links[0].prop("href"))
    
    def _parse_date(self, value):
        year, month, day = value.split(" ")[0].split("-")
        year = int(year)
        month = int(month)
        day = int(day)
        return datetime.date(year, month, day)

class ExtraTorrentPlugin(BasePlugin):
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
        #~ return
        results = []
        if url == None:
            url = "http://extratorrent.cc/search/?search=%s&new=1&x=0&y=0" % urllib.parse.quote_plus(keyword)
            
        logging.debug("Searching from : %s" % url)
        
        response = self.http_get(url)
        tree = HTMLNode(html.document_fromstring(response.text))
        for tr in tree.find("table", **{"class": "tl"})[0].find("tr", maxdepth = 1):
            try:
                title = tr.find("td", **{"class": "tli"})[0].find("a", maxdepth = 1)[0].getContent().strip().decode("utf-8")
                result_url = urllib.parse.urljoin(url, tr.find("td", **{"class": "tli"})[0].find("a", maxdepth = 1)[0].prop("href"))
                size = self.parse_size(tr.find("td")[3].getContent().decode("utf-8").strip())
                try:
                    seeders = int(tr.find("td", **{"class": "sy"})[0].getContent().decode("utf-8").strip())
                except:
                    seeders = 0
                try:
                    leechers = int(tr.find("td", **{"class": "ly"})[0].getContent().decode("utf-8").strip())
                except:
                    leechers = 0
                download_link = urllib.parse.urljoin(url, tr.find("td")[0].find("a")[0].prop("href"))
                result = ExtraTorrentPluginResult(self, **{
                    "title": title,
                    "url": result_url,
                    "seeders": seeders,
                    "leechers": leechers,
                    "size": size,
                    "download_link_page": download_link
                })
                results.append(result)
            except:
                traceback.print_exc()
        
        continue_url = None
        next_page_links = [a for a in tree.find("a", **{"class": "pager_link"}) if a.getContent().decode("utf-8").strip() == ">"]
        if len(next_page_links) > 0:
            continue_url = urllib.parse.urljoin(url, next_page_links[0].prop("href"))
            
        return {
            "continue_url": continue_url,
            "results": results
        }
