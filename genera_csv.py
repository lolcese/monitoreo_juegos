#!/usr/bin/python
# -*- coding: utf-8 -*-
############################################################################################
# Este programa es llamado a correr cada n minutos por el sistema,
# y baja las páginas de cada juego, extrae el precio y el peso (si fuera necesario),
# calcula el precio final en Argentina, grafica y manda alarmas.
############################################################################################

import urllib.request
import re
from datetime import datetime
from urllib.error import URLError, HTTPError
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FormatStrFormatter
import constantes
import os.path
import path
from telegram.ext import (Updater)
import requests
import csv

os.chdir(path.actual)
bot_token = os.environ.get('bot_token')
updater = Updater(bot_token)

######### Programa principal
def main():
    conn = sqlite3.connect(constantes.db_file, timeout = 30, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = conn.cursor()

    # Exporta el archivo
    ju = open(constantes.exporta_file, mode='w', newline='', encoding="UTF-8")
    juegos_exporta = csv.writer(ju, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

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
            print(nombre,constantes.sitio_URL['BGG']+str(BGG_id),constantes.sitio_nom[sitio],constantes.sitio_URL[sitio]+sitio_ID, precio, fecha, min_precio, constantes.dependencia_len[dependencia_leng])
            juegos_exporta.writerow([nombre,constantes.sitio_URL['BGG']+str(BGG_id),constantes.sitio_nom[sitio],constantes.sitio_URL[sitio]+sitio_ID, precio, fecha, min_precio, constantes.dependencia_len[dependencia_leng]])
    
    ju.close()
    if os.path.exists(f'graficos/{constantes.exporta_file}'):
        os.remove(f'graficos/{constantes.exporta_file}')
    os.rename(constantes.exporta_file,f'graficos/{constantes.exporta_file}')

if __name__ == '__main__':
    main()
