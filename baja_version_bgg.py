#!/usr/bin/python
import sqlite3
import constantes
import urllib.request
import json
import time

conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
conn.execute("PRAGMA journal_mode=WAL")
cursor = conn.cursor()

cursor.execute('SELECT DISTINCT BGG_id, nombre FROM juegos ORDER BY nombre')
juegos_id = cursor.fetchall()
for j in juegos_id:
    BGG_id, nombre = j

    url = f"https://api.geekdo.com/api/geekitem/linkeditems?ajax=1&linkdata_index=boardgameversion&nosession=1&objectid={BGG_id}&objecttype=thing&pageid=1&showcount=100&subtype=boardgameversion"
    req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}) 
    data = urllib.request.urlopen(req)
    dato_bgg = json.loads(data.read())

    lis = []
    uni = []
    for item in dato_bgg["items"]:
        linkedname = item["linkedname"]
        for lan in item["links"]["languages"]:
            if lan["name"] == "Spanish" and linkedname != nombre:
                lis.append(linkedname)
                break

    for x in lis:
        if x not in uni:
            uni.append(x)

    for i in range(8):
        cursor.execute(f'UPDATE juegos SET nom_alt_{i+1} = ? WHERE BGG_id = ?',(None,BGG_id))
        conn.commit()
    if len(uni) > 0:
        for i in range(min(len(uni), 8)):
            cursor.execute(f'UPDATE juegos SET nom_alt_{i+1} = ? WHERE BGG_id = ?',(uni[i],BGG_id))
            conn.commit()

    time.sleep(1)

