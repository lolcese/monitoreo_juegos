#!/usr/bin/python
import sqlite3
import urllib.request
import constantes
import json
import csv
import time
import os
import html

conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
conn.execute("PRAGMA journal_mode=WAL")
cursor = conn.cursor()

caza = open(constantes.exporta_cazagangas+".temp", mode='w', newline='', encoding="UTF-8")
cazagangas_exporta = csv.writer(caza, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

data = []

cursor.execute('SELECT DISTINCT BGG_id, nombre, dependencia_leng, ranking FROM juegos WHERE precio_actual NOT NULL ORDER BY nombre')
juegos_id = cursor.fetchall()
for j in juegos_id:
    BGG_id, nombre, dependencia_leng, ranking = j
    if ranking == "Not Ranked":
        ranking = ""
    url = f"https://www.cazagangas.com.ar/api/id/{BGG_id}"
    req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}) 
    data = urllib.request.urlopen(req)
    cazagangas = json.loads(data.read())
    if cazagangas["disponible"] == True:
        cazagangas_exporta.writerow([f"{constantes.sitio_URL['BGG']+str(BGG_id)}++{nombre}", f"{cazagangas['url']}++Cazagangas", "ar", f"${cazagangas['precio']:.0f}", "", "", "-", constantes.dependencia_len[dependencia_leng], ranking])

        data.append([f"<a href=\'{constantes.sitio_URL['BGG']+str(BGG_id)}\'>{html.escape(nombre)}</a>", \
        f"<a href=\'{cazagangas['url']}\'>Cazagangas</a>", \
        f"<img src='https://flagcdn.com/24x18/ar.png' alt='Bandera ar'>", \
        f"{cazagangas['precio']:.0f}", \
        f"", \
        f"", \
        f"-", \
        f"{constantes.dependencia_len[dependencia_leng]}", \
        f"{ranking}" ])

    time.sleep(1)

tabla = open(constantes.exporta_cazagangas_json, 'w', encoding='utf-8')
json.dump(data, tabla, ensure_ascii=False, indent=4)

os.remove(constantes.exporta_cazagangas)
os.rename(constantes.exporta_cazagangas+".temp",constantes.exporta_cazagangas)