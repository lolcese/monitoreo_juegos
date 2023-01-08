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

######### Programa principal
def main():
    conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    # Exporta el archivo
    ju = open(constantes.exporta_file, mode='w', newline='', encoding="UTF-8")
    juegos_exporta = csv.writer(ju, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    juegos_exporta.writerow(["Nombre","Sitio","País","Precio actual","Mínimo 15 días","Promedio 15 días","Notas","Dependencia idioma","Ranking BGG"])

    cursor.execute('SELECT nombre, BGG_id, sitio, sitio_ID, dependencia_leng, precio_actual, fecha_actual, precio_mejor, precio_prom, ranking FROM juegos ORDER BY nombre')
    juegos_id = cursor.fetchall()
    for j in juegos_id:
        nombre, BGG_id, sitio, sitio_ID, dependencia_leng, precio_actual, fecha_actual, precio_min, precio_prom, ranking = j
        if precio_actual == None:
            precio_p = "-"
        else:
            precio_p = f"${precio_actual:.0f}"
        if precio_min == None:
            min_precio = "-"
        else:
            min_precio = f"${precio_min:.0f}"
        if precio_prom == None:
            prom_precio = "-"
        else:
            prom_precio = f"${precio_prom:.0f}"

        if fecha_actual == None:
            fecha_actual = "-"

        if precio_p == "-" and sitio != "Usuario":
            continue

        if sitio == "Usuario":
            cursor.execute('SELECT username, precio, estado, ciudad FROM ventas WHERE id_venta = ?', [sitio_ID])
            juego_venta = cursor.fetchone()
            username, precio, estado, ciudad = juego_venta
            sitio_v = f"https://t.me/{username}++Vendido por @{username}"
            precio_p = f"${precio}"
            notas = f"{ciudad} - {estado}"
            band = "AR"
        else:
            sitio_v = f"{constantes.sitio_URL[sitio]+sitio_ID}++{constantes.sitio_nom[sitio]}"
            notas = "-"
            band = constantes.sitio_pais[sitio]
            if precio_actual <= precio_prom * 0.9:
                notas = f"Oferta ({int((precio_prom - precio_actual) / precio_prom * 100)}% menos) "

        band = band.lower()
        if band == "uk":
            band = "gb"

        if ranking == "Not Ranked":
            ranking = ""
        
        if min_precio == "-":
            min_precio = ""

        if prom_precio == "-":
            prom_precio = ""

        juegos_exporta.writerow([f"{constantes.sitio_URL['BGG']+str(BGG_id)}++{nombre}", sitio_v, band, precio_p, min_precio, prom_precio, notas, constantes.dependencia_len[dependencia_leng], ranking])

    ju.close()

    filenames = [constantes.exporta_file, constantes.exporta_cazagangas]
    with open(constantes.exporta_tabla, 'w') as outfile:
        for fname in filenames:
            with open(fname) as infile:
                outfile.write(infile.read())

if __name__ == '__main__':
    main()
