#!/usr/bin/python
import sqlite3
import re
import html
import urllib.request
import os
import constantes
import path
import time
from datetime import datetime

os.chdir(path.actual)
fecha = datetime.now()

conn = sqlite3.connect(constantes.db_file, timeout = 10, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
cursor = conn.cursor()

######### Baja ranking de BGG
cursor.execute('SELECT DISTINCT BGG_id FROM juegos')
juegos_BGG = cursor.fetchall()
for j in juegos_BGG:
    votos = {}
    BGG_id = j[0]
    url = f'https://api.geekdo.com/xmlapi2/thing?id={BGG_id}&stats=1'
    req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}) 
    data = urllib.request.urlopen(req).read()
    data = data.decode('utf-8')
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
    cursor.execute('UPDATE juegos SET ranking = ?, dependencia_leng = ? WHERE BGG_id = ?',(ranking, dependencia_leng, BGG_id))
    conn.commit()
    time.sleep(3)

cursor.close()
