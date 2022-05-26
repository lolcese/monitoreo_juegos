#!/usr/bin/python
# -*- coding: utf-8 -*-
############################################################################################
# Este programa es llamado a correr cada n minutos por el sistema,
# y baja las páginas de cada juego, extrae el precio y el peso (si fuera necesario),
# calcula el precio final en Argentina, grafica y manda alarmas.
############################################################################################

import sqlite3
import constantes
import os.path
import path
import csv

os.chdir(path.actual)

######### Programa principal
def main():
    conn = sqlite3.connect(constantes.db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    # Exporta el archivo
    ju = open(constantes.exporta_file, mode='w', newline='', encoding="UTF-8")
    juegos_exporta = csv.writer(ju, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    cursor.execute('SELECT nombre, BGG_id, sitio, sitio_ID, dependencia_leng, precio_actual, fecha_actual, precio_mejor FROM juegos ORDER BY nombre')
    juegos_id = cursor.fetchall()
    for j in juegos_id:
        nombre, BGG_id, sitio, sitio_ID, dependencia_leng, precio_actual, fecha_actual, precio_min = j
        if precio_actual == None:
            precio = "-"
        else:
            precio = f"${precio_actual:.0f}"
        if precio_min == None:
            min_precio = "-"
        else:
            min_precio = f"${precio_min:.0f}"
        if fecha_actual == None:
            fecha_actual = "-"
        juegos_exporta.writerow([nombre,constantes.sitio_URL['BGG']+str(BGG_id),constantes.sitio_nom[sitio],constantes.sitio_URL[sitio]+sitio_ID, precio, fecha_actual, min_precio, constantes.dependencia_len[dependencia_leng]])
    
    ju.close()
    if os.path.exists(f'graficos/{constantes.exporta_file}'):
        os.remove(f'graficos/{constantes.exporta_file}')
    os.rename(constantes.exporta_file,f'graficos/{constantes.exporta_file}')

if __name__ == '__main__':
    main()
