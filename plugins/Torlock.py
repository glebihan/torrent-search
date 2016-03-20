# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

from TorrentSearch.BasePlugin import BasePlugin
from TorrentSearch.BasePluginResult import BasePluginResult
from TorrentSearch.ResultFile import ResultFile
import urllib.parse
import logging
import traceback
import datetime
from lxml import html
from TorrentSearch.HTMLNode import HTMLNode

class TorlockPluginResult(BasePluginResult):
    def fetch_details(self):
        logging.debug("Loading details from : %s" % self["url"])
        
        response = self.http_get(self["url"], cookies = {'adult': 'true'})
        tree = HTMLNode(html.document_fromstring(response.text))
        
        magnet_links = [a for a in tree.find("a") if a.prop("href") is not None and a.prop("href").startswith("magnet:")]
        if len(magnet_links) > 0:
            self["magnet_link"] = magnet_links[0].prop("href")
            self["hash"] = self["magnet_link"].split(":btih:")[1].split("&dn")[0]
        download_links = [a for a in tree.find("a") if a.prop("href") is not None and a.prop("href").startswith("/tor/") and a.prop("href").endswith(".torrent")]
        if len(download_links) > 0:
            self["download_link"] = urllib.parse.urljoin(self["url"], download_links[0].prop("href"))
        
        self["files"] = []
        tecnical_div = tree.find("div", **{"id": "tecnical"})
        if len(tecnical_div) == 1:
            table = tecnical_div[0].find("table")[1]
            for tr in table.find("tr"):
                try:
                    icon, filename, size = tr.find("td", maxdepth = 1)
                    self["files"].append(ResultFile(**{
                        "filename": filename.getContent().decode("utf-8").strip(),
                        "size": self._plugin.parse_size(size.getContent().decode("utf-8").strip())
                    }))
                except:
                    pass
    
class TorlockPlugin(BasePlugin):
    def parse_date(self, date):
        if date.startswith("Today"):
            return datetime.date.today()
        month, day, year = date.split("/")
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
            url = "https://www.torlock.com/?q=%s" % urllib.parse.quote_plus(keyword)
            
        logging.debug("Searching from : %s" % url)
        
        response = self.http_get(url)
        tree = HTMLNode(html.document_fromstring(response.text))
        
        table = tree.find("article")[0].find("div", **{"class": "panel panel-default"}, maxdepth = 1)[0].find("table")[0]
        for tr in table.find("tr", maxdepth = 1):
            try:
                main_link = tr.find("a")[0]
                title = main_link.getContent().strip().decode("utf-8")
                result_url = urllib.parse.urljoin(url, main_link.prop("href"))
                date = self.parse_date(tr.find("td", **{"class": "td"})[0].getContent().decode("utf-8").strip())
                size = self.parse_size(tr.find("td", **{"class": "ts"})[0].getContent().decode("utf-8").strip())
                seeders = int(tr.find("td", **{"class": "tul"})[0].getContent().decode("utf-8").strip())
                leechers = int(tr.find("td", **{"class": "tdl"})[0].getContent().decode("utf-8").strip())
                result = TorlockPluginResult(self, **{
                    "title": title,
                    "url": result_url,
                    "seeders": seeders,
                    "leechers": leechers,
                    "date": date,
                    "size": size,
                })
                results.append(result)
            except:
                traceback.print_exc()
        
        continue_url = None
        pager = tree.find("ul", **{"class": "pagination"})
        if len(pager) == 1:
            links = pager[0].find("a", **{"aria-label": "Next"})
            if len(links) == 1:
                continue_url = urllib.parse.urljoin(url, links[0].prop("href"))            
            
        return {
            "continue_url": continue_url,
            "results": results
        }
