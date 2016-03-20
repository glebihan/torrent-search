# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import requests
import logging
import traceback
import datetime
import sys
import urllib.parse
from TorrentSearch.HTMLNode import HTMLNode
from TorrentSearch.BasePlugin import BasePlugin
from TorrentSearch.BasePluginResult import BasePluginResult
from TorrentSearch.ResultFile import ResultFile
from lxml import html
from io import StringIO

class KickassTorrentsPluginResult(BasePluginResult):
    def _do_fetch_all(self):
        logging.debug("Fetching all data from : %s" % self["url"])
        
        response = self.http_get(self["url"])
        tree = HTMLNode(html.document_fromstring(response.text))
        
        self["files"] = []
        filestable = tree.find("table", **{"class": "torrentFileList"})
        if len(filestable) == 1:
            for tr in filestable[0].find("tr"):
                try:
                    self["files"].append(ResultFile(**{
                        "filename": tr.find("td", **{"class": "torFileName"})[0].getContent().decode("utf-8").strip(),
                        "size": self._plugin.parse_size(tr.find("td", **{"class": "torFileSize"})[0].getContent().decode("utf-8").strip())
                    }))
                except:
                    pass

class KickassTorrentsPlugin(BasePlugin):
    def parse_size(self, size):
        units = ["KB", "MB", "GB", "TB"]
        value, unit = size.split(" ")
        value = int(round(float(value.strip())))
        ui = units.index(unit.strip())
        while ui >= 0:
            value = 1024 * value
            ui -= 1
        return value
    
    def _parse_date(self, value):
        day, month, year = value.split(" ")
        year = int(year)
        day = int(day)
        month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].index(month)+1
        return datetime.date(year, month, day)
    
    def run_search(self, keyword, url = None):
        #~ return
        results = []
        if url == None:
            url = "https://kat.cr/usearch/%s/" % urllib.parse.quote(keyword)
            
        logging.debug("Searching from : %s" % url)
        
        response = self.http_get(url)
        tree = HTMLNode(html.document_fromstring(response.text))
        for tr in tree.find("table", **{"class": "data"})[0].find("tr")[1:]:
            try:
                title = tr.find("a", **{'class': 'cellMainLink'})[0].getContent().strip().decode("utf-8")
                result_url = urllib.parse.urljoin(url, tr.find("a", **{'class': 'cellMainLink'})[0].prop("href"))
                magnet_link = tr.find("a", title = "Torrent magnet link")[0].prop("href")
                download_link = urllib.parse.urljoin(url, tr.find("a", title = "Download torrent file")[0].prop("href"))
                info_hash = magnet_link.split("btih:")[1].split("&dn=")[0].lower()
                seeders = int(tr.find("td", **{"class": "green center"})[0].getContent().decode("utf-8").strip())
                leechers = int(tr.find("td", **{"class": "red lasttd center"})[0].getContent().decode("utf-8").strip())
                size = self.parse_size(tr.find("td", **{"class": "nobr center"})[0].getContent().decode("utf-8").strip())
                try:
                    torrent_date = self._parse_date(tr.find("td", **{"class": "center"})[1].prop("title").strip().split(",")[0])
                except:
                    torrent_date = None
                results.append(KickassTorrentsPluginResult(self, **{
                    "title": title,
                    "url": result_url,
                    "magnet_link": magnet_link,
                    "download_link": download_link,
                    "hash": info_hash,
                    "seeders": seeders,
                    "leechers": leechers,
                    "size": size,
                    "date": torrent_date
                }))
            except:
                traceback.print_exc()
        
        continue_url = None
        pager_cur_page = tree.find("a", **{"class": "turnoverButton siteButton bigButton active"})
        if len(pager_cur_page) > 0:
            pager_links = pager_cur_page[0].parent.find("a")
            while len(pager_links) > 0 and not "active" in pager_links[0].prop("class"):
                del pager_links[0]
            if len(pager_links) > 0:
                del pager_links[0]
            if len(pager_links) > 0:
                continue_url = urllib.parse.urljoin(url, pager_links[0].prop("href"))
        
        return {
            "continue_url": continue_url,
            "results": results
        }
