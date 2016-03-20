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

class IsohuntPluginResult(BasePluginResult):
    def fetch_details(self):
        logging.debug("Loading details from : %s" % self["url"])
        
        response = self.http_get(self["url"])
        tree = HTMLNode(html.document_fromstring(response.text))
        
        self["date"] = self._plugin.parse_date(tree.find("p", **{"class": "text-lg mb2"})[0].getContent().decode("utf-8").split(" Added")[1].split(" ")[0].strip())
        self["seeders"] = int(tree.find("span", **{"class": "seeds"})[0].getContent().decode("utf-8").split(" ")[0].strip())
        self["leechers"] = int(tree.find("span", **{"class": "leechs"})[0].getContent().decode("utf-8").split(" ")[0].strip())
        self["download_link"] = urllib.parse.urljoin(self["url"], tree.find("a", title = "You need BitTorrent software for this P2P download link to work")[0].prop("href"))
        self["magnet_link"] = tree.find("a", title = "Download Magnet link")[0].prop("href")
        self["hash"] = self["magnet_link"].split(":btih:")[1].split("&dn")[0]
        
        self["files"] = []
        files_table = tree.find("div", **{"id": "torrent_files"})[0].find("table")[0]
        for tr in files_table.find("tr"):
            try:
                filename, size = tr.find("td")
                self["files"].append(ResultFile(**{
                    "filename":  filename.getContent().decode("utf-8").strip(),
                    "size": self._plugin.parse_size(size.getContent().decode("utf-8").strip())
                }))
            except:
                pass
    
class IsohuntPlugin(BasePlugin):
    def parse_date(self, date):
        year, month, day = date.split("-")
        year = int(year)
        month = int(month)
        day = int(day)
        return datetime.date(year, month, day)
    
    def parse_size(self, size):
        units = ["KB", "MB", "GB", "TB"]
        value, unit = size.split(" ")
        value = int(round(float(value.strip())))
        if unit.strip().upper() in units:
            ui = units.index(unit.strip().upper())
            while ui >= 0:
                value = 1024 * value
                ui -= 1
        return value
        
    def run_search(self, keyword, url = None):
        results = []
        if url == None:
            url = "https://isohunt.to/torrents/?ihq=%s" % urllib.parse.quote_plus(keyword)
            
        logging.debug("Searching from : %s" % url)
        
        response = self.http_get(url)
        tree = HTMLNode(html.document_fromstring(response.text))
        
        table = tree.find("div", **{"id": "serps"})[0].find("table")[0]
        for tr in table.find("tr", maxdepth = 2)[1:]:
            try:
                category, title_cell, verify, comments, date, size, sn, rating = tr.find("td", maxdepth = 1)
                if len(title_cell.find("a")) > 0:
                    title = title_cell.find("a")[0].getContent().decode("utf-8").strip()
                    result_url = urllib.parse.urljoin(url, title_cell.find("a")[0].prop("href"))
                    size = self.parse_size(size.getContent().decode("utf-8").strip())
                    result = IsohuntPluginResult(self, **{
                        "title": title,
                        "url": result_url,
                        "size": size,
                    })
                    results.append(result)
            except:
                traceback.print_exc()
        
        continue_url = None
        ul = tree.find("ul", **{'class': 'pagination'})
        if len(ul) == 1:
            li = ul[0].find("li", **{'class': 'next'})
            if len(li) == 1:
                a = li[0].find("a")
                if len(a) == 1:
                    continue_url = urllib.parse.urljoin(url, a[0].prop("href"))
            
        return {
            "continue_url": continue_url,
            "results": results
        }
