#!/usr/bin/python
import sqlite3
import re
import html
import urllib.request
import time
from datetime import datetime
from decouple import config
import json

BGG_id = 269207

url = f"https://api.geekdo.com/api/geekitem/linkeditems?ajax=1&linkdata_index=boardgameversion&nosession=1&objectid={BGG_id}&objecttype=thing&pageid=1&showcount=100&subtype=boardgameversion"
req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}) 
data = urllib.request.urlopen(req)
dato_bgg = json.loads(data.read())

for item in dato_bgg["items"]:
    linkedname = item["linkedname"]
    for lan in item["links"]["languages"]:
        if lan["name"] == "Spanish":
            print(linkedname)
            break