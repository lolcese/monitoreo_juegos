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

datos_cazagangas = []

cursor.execute('SELECT DISTINCT BGG_id, nombre, dependencia_leng, ranking, nom_alt_1, nom_alt_2, nom_alt_3, nom_alt_4, nom_alt_5, nom_alt_6, nom_alt_7, nom_alt_8 FROM juegos WHERE precio_actual NOT NULL ORDER BY nombre')
juegos_id = cursor.fetchall()
for j in juegos_id:
    BGG_id, nombre, dependencia_leng, ranking, nom_alt_1, nom_alt_2, nom_alt_3, nom_alt_4, nom_alt_5, nom_alt_6, nom_alt_7, nom_alt_8 = j
    if ranking == "Not Ranked":
        ranking = "Sin datos"
    url = f"https://www.cazagangas.com.ar/api/id/{BGG_id}"
    req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}) 
    data = urllib.request.urlopen(req)
    cazagangas = json.loads(data.read())
    if cazagangas["disponible"] == True:
        cazagangas_exporta.writerow([f"{constantes.sitio_URL['BGG']+str(BGG_id)}++{nombre}", f"{cazagangas['url']}++Cazagangas", "ar", f"${cazagangas['precio']:.0f}", "", "", "-", constantes.dependencia_len[dependencia_leng], ranking])

        nom_alt = " / ".join(filter(None,[nom_alt_1, nom_alt_2, nom_alt_3, nom_alt_4, nom_alt_5, nom_alt_6, nom_alt_7, nom_alt_8]))
        datos_cazagangas.append([f"'nombre': '<a href=\'{constantes.sitio_URL['BGG']+str(BGG_id)}\'>{html.escape(nombre)}</a> ({nom_alt}), Ranking BGG: {ranking}, Dependencia idioma: {constantes.dependencia_len[dependencia_leng]}'", \
            f"'sitio': '<a href=\'{cazagangas['url']}\'>Cazagangas</a>'", \
            f"'pais': '<img src='https://flagcdn.com/24x18/ar.png' alt='Bandera ar'>'", \
            f"'precio_actual': '${cazagangas['precio']:.0f}'", \
            f"'minimo_15': ''", \
            f"'promedio_15': ''", \
            f"'notas': '-'" ])

    time.sleep(1)

tabla = open(constantes.exporta_cazagangas_json, 'w', encoding='utf-8')
json.dump(datos_cazagangas, tabla, ensure_ascii=False, indent=4)

os.remove(constantes.exporta_cazagangas)
os.rename(constantes.exporta_cazagangas+".temp",constantes.exporta_cazagangas)