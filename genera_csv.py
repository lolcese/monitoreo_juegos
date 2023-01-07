#!/usr/bin/python
# -*- coding: utf-8 -*-
############################################################################################
# Este programa es llamado a correr cada n minutos por el sistema,
# y baja las páginas de cada juego, extrae el precio y el peso (si fuera necesario),
# calcula el precio final en Argentina, grafica y manda alarmas.
############################################################################################

import sqlite3
import constantes
import csv
import urllib.request
import json

######### Programa principal
def main():
    conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    # Exporta el archivo
    ju = open(constantes.exporta_file, mode='w', newline='', encoding="UTF-8")
    juegos_exporta = csv.writer(ju, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    ju2 = open(constantes.exporta_file2, mode='w', newline='', encoding="UTF-8")
    juegos_exporta2 = csv.writer(ju2, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    juegos_exporta2.writerow(["Nombre","Sitio","País","Precio actual","Mínimo 15 días","Notas","Dependencia idioma","Ranking BGG"])

    # cursor.execute('SELECT nombre, BGG_id, sitio, sitio_ID, dependencia_leng, precio_actual, fecha_actual, precio_mejor, ranking FROM juegos WHERE sitio != "Usuario" ORDER BY nombre')
    cursor.execute('SELECT nombre, BGG_id, sitio, sitio_ID, dependencia_leng, precio_actual, fecha_actual, precio_mejor, ranking FROM juegos  ORDER BY nombre')
    juegos_id = cursor.fetchall()
    for j in juegos_id:
        nombre, BGG_id, sitio, sitio_ID, dependencia_leng, precio_actual, fecha_actual, precio_min, ranking = j
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

        if sitio != "Usuario":
            juegos_exporta.writerow([nombre,constantes.sitio_URL['BGG']+str(BGG_id),constantes.sitio_nom[sitio],constantes.sitio_URL[sitio]+sitio_ID, precio, fecha_actual, min_precio, constantes.dependencia_len[dependencia_leng], ranking])

        if sitio == "Usuario":
            cursor.execute('SELECT username, precio, estado, ciudad FROM ventas WHERE id_venta = ?', [sitio_ID])
            juego_venta = cursor.fetchone()
            username, precio, estado, ciudad = juego_venta
            sitio_v = f"https://t.me/{username}++Vendido por @{username}"
            precio = f"${precio}"
            notas = f"{ciudad} - {estado}"
            band = "AR"
        else:
            sitio_v = f"{constantes.sitio_URL[sitio]+sitio_ID}++{constantes.sitio_nom[sitio]}"
            notas = "-"
            band = constantes.sitio_pais[sitio]

        if precio == "-":
            continue

        juegos_exporta2.writerow([f"{constantes.sitio_URL['BGG']+str(BGG_id)}++{nombre}", sitio_v, {band.lower()}, precio, min_precio, notas, constantes.dependencia_len[dependencia_leng], ranking])

        # url = f"https://www.cazagangas.com.ar/api/id/{BGG_id}"
        # req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}) 
        # data = urllib.request.urlopen(req)
        # cazagangas = json.loads(data.read())
        # if cazagangas["disponible"] == True:
        #     juegos_exporta2.writerow([f"{constantes.sitio_URL['BGG']+str(BGG_id)}++{nombre}", f"{cazagangas['url']}++Cazagangas 🇦🇷", precio, "-", notas, constantes.dependencia_len[dependencia_leng], ranking])

    ju.close()

if __name__ == '__main__':
    main()
