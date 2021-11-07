#!/usr/bin/python

import constantes
import os.path
import path
import sqlite3
import csv

os.chdir(path.actual)
conn = sqlite3.connect(constantes.db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
conn.execute("PRAGMA journal_mode=WAL")
cursor = conn.cursor()
csv_lineas = []
cursor.execute('SELECT nombre, BGG_id, id_juego, sitio, sitio_ID, dependencia_leng FROM juegos ORDER BY nombre')
juegos_id = cursor.fetchall()
for j in juegos_id:
    nombre, BGG_id, id_juego, sitio, sitio_ID, dependencia_leng = j
    cursor.execute('SELECT precio, fecha FROM precios WHERE id_juego = ? ORDER BY fecha DESC LIMIT 1', [id_juego])
    dat = cursor.fetchone()
    if dat:
        precio_actual, fecha = dat
        if precio_actual == None:
            precio = "-"
        else:
            precio = f"${precio_actual:.0f}"
        cursor.execute('SELECT precio FROM precios WHERE id_juego = ? AND precio NOT NULL AND (fecha BETWEEN datetime("now", "-15 days", "localtime") AND datetime("now", "localtime")) ORDER BY precio ASC LIMIT 1', [id_juego])
        min_precio = cursor.fetchone()
        if min_precio:
            min_precio = f"${min_precio[0]:.0f}"
        else:
            min_precio = "-"
        csv_lineas.append([nombre, constantes.sitio_URL['BGG']+str(BGG_id), constantes.sitio_nom[sitio], constantes.sitio_URL[sitio]+sitio_ID, precio, fecha, min_precio, constantes.dependencia_len[dependencia_leng]])

cursor.close()
ju = open(constantes.exporta_file, mode='w', newline='', encoding="UTF-8")
juegos_exporta = csv.writer(ju, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
for c in csv_lineas:
    juegos_exporta.writerow(c)
ju.close()
if os.path.exists(f'graficos/{constantes.exporta_file}'):
    os.remove(f'graficos/{constantes.exporta_file}')
os.rename(constantes.exporta_file,f'graficos/{constantes.exporta_file}')
