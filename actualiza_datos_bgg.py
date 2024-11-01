#!/usr/bin/python
import sqlite3
import constantes
import urllib.request
import json
import time
import html
import re
from datetime import datetime

conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
conn.execute("PRAGMA journal_mode=WAL")
cursor = conn.cursor()

fecha = datetime.now()

cursor.execute('SELECT DISTINCT BGG_id, nombre FROM juegos ORDER BY nombre')
juegos_id = cursor.fetchall()

for j in juegos_id:
    BGG_id, nombre = j

    votos = {}
    BGG_id = j[0]
    url = f'https://api.geekdo.com/xmlapi2/thing?id={BGG_id}&stats=1'
    req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}) 
    data = urllib.request.urlopen(req).read()
    data = data.decode('utf-8')
    nombre = html.unescape(re.search('<name type=\"primary\" sortindex=\".*?\" value=\"(.*?)\"',data)[1])
    ranking = html.unescape(re.search('name=\"boardgame\".*?value=\"(.*?)\"',data)[1])

    votos_dep = float(re.search('poll name=\"language_dependence\".*?totalvotes=\"(.*?)\"',data)[1])
    if votos_dep >= 3:
        votos[1] = float(re.search('result level.*? value=\"No necessary in-game text\" numvotes=\"(.*?)\"',data)[1])
        votos[2] = float(re.search('result level.*? value=\"Some necessary text - easily memorized or small crib sheet\" numvotes=\"(.*?)\"',data)[1])
        votos[3] = float(re.search('result level.*? value=\"Moderate in-game text - needs crib sheet or paste ups\" numvotes=\"(.*?)\"',data)[1])
        votos[4] = float(re.search('result level.*? value=\"Extensive use of text - massive conversion needed to be playable\" numvotes=\"(.*?)\"',data)[1])
        votos[5] = float(re.search('result level.*? value=\"Unplayable in another language\" numvotes=\"(.*?)\"',data)[1])
        dependencia_leng = int(max(votos, key=votos.get))
    else:
        dependencia_leng = 0
    cursor.execute('UPDATE juegos SET nombre = ?, ranking = ?, dependencia_leng = ? WHERE BGG_id = ?',(nombre, ranking, dependencia_leng, BGG_id))
    conn.commit()
    time.sleep(1)

    url = f"https://api.geekdo.com/api/geekitem/linkeditems?ajax=1&linkdata_index=boardgameversion&nosession=1&objectid={BGG_id}&objecttype=thing&pageid=1&showcount=100&subtype=boardgameversion"
    req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}) 
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
    time.sleep(10)

