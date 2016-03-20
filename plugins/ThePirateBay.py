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

class ThePirateBayPluginResult(BasePluginResult):
    pass
    
class ThePirateBayPlugin(BasePlugin):
    def parse_date(self, date):
        if date.startswith("Today"):
            return datetime.date.today()
        year = date[-4:]
        if ":" in year:
            year = time.strftime("%Y")
        month, day = date[:5].split("-")
        year = int(year)
        month = int(month)
        day = int(day)
        return datetime.date(year, month, day)
    
    def parse_size(self, size):
        units = ["KiB", "MiB", "GiB", "TiB"]
        value = size[:-4]
        unit = size[-4:]
        value = int(round(float(value.strip())))
        ui = units.index(unit.strip())
        while ui >= 0:
            value = 1024 * value
            ui -= 1
        return value
        
    def run_search(self, keyword, url = None):
        results = []
        if url == None:
            url = "https://thepiratebay.se/search/%s/0/99/0" % urllib.parse.quote(keyword)
            
        logging.debug("Searching from : %s" % url)
        
        response = self.http_get(url)
        tree = HTMLNode(html.document_fromstring(response.text))
        
        table = tree.find("table", **{"id": "searchResult"})[0]
        for tr in table.find("tr", maxdepth = 1):
            try:
                cat, name, seeders, leechers = tr.find("td", maxdepth = 1)
                main_link = name.find("a")[0]
                title = main_link.getContent().strip().decode("utf-8")
                result_url = urllib.parse.urljoin(url, main_link.prop("href"))
                seeders = int(seeders.getContent().strip().decode("utf-8"))
                leechers = int(leechers.getContent().strip().decode("utf-8"))
                detdesc = tr.find("font", **{"class": "detDesc"})[0]
                for val in detdesc.getContent().strip().decode("utf-8").split(","):
                    val = val.strip()
                    if val.startswith("Uploaded"):
                        date = self.parse_date(val[8:].strip())
                    if val.startswith("Size"):
                        size = self.parse_size(val[4:].strip())
                magnet_link = tr.find("a", title = "Download this torrent using magnet")[0].prop("href")
                result = ThePirateBayPluginResult(self, **{
                    "title": title,
                    "url": result_url,
                    "seeders": seeders,
                    "leechers": leechers,
                    "date": date,
                    "size": size,
                    "magnet_link": magnet_link,
                    "hash": magnet_link.split(":btih:")[1].split("&dn")[0]
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
