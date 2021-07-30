#!/usr/bin/python
import sqlite3
import re
import html
import urllib.request
import os
import constantes
import path
import time

os.chdir(path.actual)

conn = sqlite3.connect(constantes.db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT BGG_id FROM juegos')
juegos_BGG = cursor.fetchall()
for j in juegos_BGG:
    BGG_id = j[0]
    url = f'https://api.geekdo.com/xmlapi2/thing?id={BGG_id}&stats=1'
    req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}) 
    data = urllib.request.urlopen(req).read()
    data = data.decode('utf-8')
    ranking = html.unescape(re.search('name=\"boardgame\".*?value=\"(.*?)\"',data)[1])
    cursor.execute('UPDATE juegos SET ranking = ? WHERE BGG_id = ?',(ranking, BGG_id))
    conn.commit()
    time.sleep(3)
cursor.close()
