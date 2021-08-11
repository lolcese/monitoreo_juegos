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

######### Baja una página cualquiera
def baja_pagina(url):
    req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}) 
    try:
        data = urllib.request.urlopen(req).read()
    except HTTPError as e:
        return "Error"
    except URLError as e:
        return "Error"
    return data.decode('unicode_escape', errors = 'ignore')

######### Lee información de BLAM
def lee_pagina_blam(ju_id):
    url = f"https://www.buscalibre.com.ar/boton-prueba-gp?t=tetraemosv3&envio-avion=1&codigo={ju_id}&sitio=amazon&version=2&condition=new"
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_ar = re.search('<input data-total="\$ (.*?)"',text)
    if not precio_ar:
       return None
    precio_ar = float(re.sub("\.", "", precio_ar[1])) + constantes.var['envio_BL']

    return precio_ar

######### Lee información de BLIB
def lee_pagina_blib(ju_id):
    url = "https://www.buscalibre.com.ar/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_ar = re.search('<p class="precioAhora margin-0 font-weight-strong"><span>\$ (.*?)</span>',text)
    if not precio_ar:
        return None
    precio_ar = float(re.sub("\.", "", precio_ar[1])) + constantes.var['envio_BL']

    return precio_ar

######### Lee información de TMAM
def lee_pagina_tmam(ju_id):
    url = "https://tiendamia.com/ar/producto?amz="+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    peso = re.search('data-weight="(.*?)"',text)
    if not peso or peso[1] == "":
        return None
    peso = float(peso[1])
 
    precio_ar = re.search('ecomm_totalvalue: (.*?),',text)
    if not precio_ar:
        return None
    precio_ar = float(re.sub("\.", "", precio_ar[1]))
    if precio_ar < 100:
        return None

    pr_tm = precio_tm(peso,precio_ar)
    return pr_tm

######### Lee información de TMWM
def lee_pagina_tmwm(ju_id):
    url = "https://tiendamia.com/ar/productow?wrt="+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    peso = re.search('<span id="weight_producto_ajax">(.*?)</span>',text)
    if not peso or peso[1] == "":
        return None
    peso = float(peso[1])

    precio_ar = re.search('<span id="finalpricecountry_producto_ajax">AR\$ (.*)</span>',text)
    stock = '"availability": "https://schema.org/OutOfStock"' in text
    if not precio_ar or stock == 1:
        return None
    precio_ar = float(re.sub("\.", "", precio_ar[1]))
    if precio_ar < 100:
        return None

    pr_tm = precio_tm(peso,precio_ar)
    return pr_tm

######### Lee información de TMEB
def lee_pagina_tmeb(ju_id):
    url = "https://tiendamia.com/ar/e-product?ebay="+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    peso = re.search('<span id="weight_producto_ajax">(.*?)</span>',text)
    if not peso:
        return None
    peso = float(peso[1])

    precio_ar = re.search('<span id="finalpricecountry_producto_ajax" class="notranslate">AR\$ (.*)</span>',text)
    stock = '"availability": "https://schema.org/OutOfStock"' in text
    if not precio_ar or stock == 1:
        return None
    precio_ar = float(re.sub("\.", "", precio_ar[1]))
    if precio_ar < 100:
        return None

    pr_tm = precio_tm(peso,precio_ar)
    return pr_tm

######### Calcula precio para TM
def precio_tm(peso,precio_ar):
    costo_peso = peso * constantes.var['precio_kg']
    if peso > 3:
        desc_3kg = 0.3 * (peso - 3) * constantes.var['precio_kg']
    else:
        desc_3kg = 0
    if peso > 5:
        desc_5kg = 0.5 * (peso - 5) * constantes.var['precio_kg']
    else:
        desc_5kg = 0
    precio_final = precio_ar * 1.1 + costo_peso + constantes.var['tasa_tm'] - desc_3kg - desc_5kg
    precio_dol = precio_ar / constantes.var['dolar_tm'] + constantes.var['envio_dol']
    imp = 0
    if precio_dol > 50:
        imp = (precio_dol - 50) * 0.5
    precio_final_ad = precio_final + imp * constantes.var['dolar'] + constantes.var['tasa_correo']
    return precio_final_ad

######### Lee información de BOOK
def lee_pagina_book(ju_id):
    url = "https://www.bookdepository.com/es/x/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_ar = re.search('<span class=\"sale-price\">ARS\$(.*?)</span>',text)
    if not precio_ar:
        return None
    precio_ar = re.sub("\.", "", precio_ar[1])
    precio_ar = float(re.sub(",", ".", precio_ar)) * constantes.var['impuesto_compras_exterior']

    return precio_ar

######### Lee información de 365
def lee_pagina_365(ju_id):
    url = "https://www.365games.co.uk/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_lb = re.search('\"price\": \"(.*?)"',text)
    if not precio_lb:
        return None
    precio_ar = (float(precio_lb[1]) + constantes.var['envio_365']) * constantes.var['libra'] * constantes.var['impuesto_compras_exterior']

    precio_dol = precio_ar / constantes.var['dolar']
    imp = 0
    if precio_dol > 50:
        imp = (precio_dol - 50) * 0.5
    precio_final_ad = precio_ar + imp * constantes.var['dolar'] + constantes.var['tasa_correo']

    return precio_final_ad

######### Lee información de shop4es
def lee_pagina_shop4es(ju_id):
    url = "https://www.shop4es.com/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_eu = re.search('\"price\": \"(.*?)"',text)
    if not precio_eu:
        return None
    precio_ar = (float(re.sub("\,", ".", precio_eu[1])) + constantes.var['envio_shop4es']) * constantes.var['euro'] * constantes.var['impuesto_compras_exterior']

    precio_dol = precio_ar / constantes.var['dolar']
    imp = 0
    if precio_dol > 50:
        imp = (precio_dol - 50) * 0.5
    precio_final_ad = precio_ar + imp * constantes.var['dolar'] + constantes.var['tasa_correo']

    return precio_final_ad

######### Lee información de shop4world
def lee_pagina_shop4world(ju_id):
    url = "https://www.shop4world.com/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_lb = re.search('\"price\": \"(.*?)"',text)
    if not precio_lb:
        return None
    precio_ar = (float(precio_lb[1]) + constantes.var['envio_shop4world']) * constantes.var['libra'] * constantes.var['impuesto_compras_exterior']

    precio_dol = precio_ar / constantes.var['dolar']
    imp = 0
    if precio_dol > 50:
        imp = (precio_dol - 50) * 0.5
    precio_final_ad = precio_ar + imp * constantes.var['dolar'] + constantes.var['tasa_correo']

    return precio_final_ad

######### Lee información de deepdiscount
def lee_pagina_deep(ju_id, peso):
    url = "https://www.deepdiscount.com/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_dol = re.search('\"price\": \"(.*?)"',text)
    if not precio_dol:
        return None

    if peso < 2:
        costo_envio = constantes.var['envio_deepdiscount_0_2_lb']
    elif peso < 3:
        costo_envio = constantes.var['envio_deepdiscount_2_3_lb']
    elif peso < 4:
        costo_envio = constantes.var['envio_deepdiscount_3_4_lb']

    precio_dol = float(precio_dol[1]) + costo_envio

    if precio_dol > 50:
        imp = (precio_dol - 50) * 0.5
    else:
        imp = 0

    precio_ar = precio_dol * constantes.var['dolar'] * constantes.var['impuesto_compras_exterior']
    precio_final_ad = precio_ar + imp * constantes.var['dolar'] + constantes.var['tasa_correo']

    return precio_final_ad

######### Lee información de deepdiscount
def lee_pagina_grooves(ju_id):
    url = "https://www.grooves.land/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_eur = re.search('<div class=\"price\".*?[^s]>(\d.*?)&nbsp;EUR</big>',text)
    if not precio_eur:
        return None

    precio_eur = float(re.sub(",", ".", precio_eur[1]))
    if precio_eur < constantes.var['limite_envio_gratis_grooves']:
        precio_eur += constantes.var['envio_grooves']
    precio_dol = precio_eur * constantes.var['euro'] / constantes.var['dolar']
    precio_ar = precio_dol * constantes.var['dolar'] * constantes.var['impuesto_compras_exterior']

    if precio_dol > 50:
        imp = (precio_dol - 50) * 0.5
    else:
        imp = 0

    precio_final_ad = precio_ar + imp * constantes.var['dolar'] + constantes.var['tasa_correo']

    return precio_final_ad

######### Programa principal
def main():
    conn = sqlite3.connect(constantes.db_file, timeout = 30, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT BGG_id, nombre FROM juegos ORDER BY nombre')
    juegos_BGG = cursor.fetchall()
    for jb in juegos_BGG: # Cada juego diferente
        bgg_id, nombre = jb
        hacer_grafico = False
        cursor.execute('SELECT id_juego, sitio, sitio_ID, peso FROM juegos WHERE BGG_id = ? ORDER BY sitio', [bgg_id])
        juegos_id = cursor.fetchall()
        for j in juegos_id: # Cada repetición del mismo juego
            fecha = datetime.now()
            id_juego, sitio, sitio_ID, peso = j
            if   sitio == "BLAM":
                precio = lee_pagina_blam(sitio_ID)
            elif sitio == "BLIB":
                precio = lee_pagina_blib(sitio_ID)
            elif sitio == "TMAM":
                precio = lee_pagina_tmam(sitio_ID)
            elif sitio == "TMWM":
                precio = lee_pagina_tmwm(sitio_ID) 
            elif sitio == "TMEB":
                precio = lee_pagina_tmeb(sitio_ID) 
            elif sitio == "BOOK":
                precio = lee_pagina_book(sitio_ID)
            elif sitio == "365":
                precio = lee_pagina_365(sitio_ID)
            elif sitio == "shop4es":
                precio = lee_pagina_shop4es(sitio_ID)
            elif sitio == "shop4world":
                precio = lee_pagina_shop4world(sitio_ID)
            elif sitio == "deep":
                precio = lee_pagina_deep(sitio_ID, peso)
            elif sitio == "grooves":
                precio = lee_pagina_grooves(sitio_ID)

            cursor.execute('INSERT INTO precios (id_juego, precio, fecha) VALUES (?,?,?)',(id_juego, precio, fecha)) 
            conn.commit()

            cursor.execute('SELECT precio, fecha as "[timestamp]" FROM precios WHERE id_juego = ? AND fecha > datetime("now", "-15 days", "localtime")',[id_juego])
            datos = cursor.fetchall()
            precio_hi = [sub[0] for sub in datos]
            fecha_hi = [sub[1] for sub in datos]
            if any(precio_hi): # Si hay algún dato válido
                if hacer_grafico == False:
                    leyenda = []
                    plt.rc('xtick', labelsize=8)
                    fig, ax1 = plt.subplots()
                    ax1.set_xlabel('Fecha')
                    ax1.set_ylabel('Precio $')
                    ax1.ticklabel_format(useOffset=False)
                    ax1.tick_params(axis='y')
                    plt.grid()
                    fig.suptitle(nombre)
                    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
                    ax1.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
                    ax1.tick_params(axis='x', labelrotation= 45)
                    hacer_grafico = True
                ax1.plot(fecha_hi, precio_hi, marker='o', linestyle='dashed', markersize=5)
                leyenda.append(constantes.sitio_nom[j[1]])

        arch = f"graficos/{bgg_id}.png"
        if os.path.exists(arch):
            os.remove(arch)
        if hacer_grafico == True: # Una vez que se bajaron todas las páginas que monitorean un juego
            fig.tight_layout(rect=[0, 0.01, 1, 0.97])
            plt.legend(leyenda)
            plt.savefig(arch,dpi=100)
            # ida = updater.bot.sendPhoto(chat_id = token_bot.id_grupo_fotos, photo = open(arch, "rb"))
            # id_gr = ida['photo'][0]['file_id']
            plt.close()
        # else:
            # id_gr = 0
        # cursor.execute('UPDATE juegos SET id_grafico = ? WHERE BGG_id = ?',(id_gr, BGG_id))
        # conn.commit()

        cursor.execute('SELECT id_persona, precio_alarma FROM alarmas WHERE BGG_id = ? and precio_alarma >= ?',(bgg_id, precio))
        alarmas = cursor.fetchall()
        for alarma in alarmas:
            id_persona, precio_al = alarma
            arch = f"{bgg_id}.png"
            if not os.path.exists(f"graficos/{arch}"):
                arch = "0000.png"
            imagen = f'{constantes.sitio_URL["base"]}graficos/{arch}?f={datetime.now().isoformat()}' # Para evitar que una imagen quede en cache

            texto = f'\U000023F0\U000023F0\U000023F0\n[ ]({imagen})\n[{nombre}]({constantes.sitio_URL["BGG"]+str(bgg_id)}) está a *${precio:.0f}* en [{constantes.sitio_nom[sitio]}]({constantes.sitio_URL[sitio]+sitio_ID}) (tenés una alarma a los ${precio_al:.0f})\n\n\U000023F0\U000023F0\U000023F0'
            # updater.bot.sendMessage(chat_id = id_persona, text = texto, parse_mode = "Markdown", disable_web_page_preview = True)
            requests.get(f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={id_persona}&disable_web_page_preview=False&parse_mode=Markdown&text={texto}')

    # Ofertas y reposiciones
    cursor.execute('SELECT id_juego, avg(precio) FROM precios WHERE fecha > datetime("now", "-15 days", "localtime") GROUP BY id_juego HAVING avg(precio) NOT NULL')
    prom = cursor.fetchall()
    texto_of = ""
    texto_of_me = ""
    cursor.execute('DELETE FROM ofertas WHERE fecha_inicial < datetime("now", "-15 days", "localtime")')
    conn.commit()
    cursor.execute('UPDATE ofertas SET activa = "No"')
    conn.commit()
    for p in prom:
        id_juego, precio_prom = p
        cursor.execute('SELECT precio FROM precios WHERE id_juego = ? ORDER BY fecha DESC LIMIT 1', [id_juego])
        precio_actual = cursor.fetchone()[0]
        if precio_actual != None and precio_actual <= 0.9 * precio_prom:
            cursor.execute('SELECT nombre, sitio, sitio_id,BGG_id FROM juegos WHERE id_juego = ?', [id_juego])
            nombre, sitio, sitio_id, bgg_id = cursor.fetchone()
            porc = (precio_prom - precio_actual) / precio_prom * 100
            fecha = datetime.now()
            cursor.execute('SELECT fecha_inicial as "[timestamp]" FROM ofertas WHERE id_juego = ?',[id_juego])
            ofertas_act = cursor.fetchone()
            tx_al = f"\U000027A1 [{nombre}]({constantes.sitio_URL['BGG']+str(bgg_id)}) está en [{constantes.sitio_nom[sitio]}]({constantes.sitio_URL[sitio]+sitio_id}) a ${precio_actual:.0f} y el promedio de 15 días es de ${precio_prom:.0f} ({porc:.0f}% menos)\n"
            if ofertas_act == None: # Si no está en el listado de ofertas actuales
                cursor.execute('INSERT INTO ofertas (id_juego,precio_prom,precio_actual,fecha_inicial,activa) VALUES (?,?,?,?,?)',(id_juego,precio_prom,precio_actual,fecha,"Sí"))
                conn.commit()
                texto_of_me += tx_al
                texto_of += tx_al
            else:
                cursor.execute('UPDATE ofertas SET precio_prom = ?, precio_actual = ?, activa = "Sí" WHERE id_juego = ?',(precio_prom,precio_actual,id_juego))
                conn.commit()
                texto_of += tx_al
                
    cursor.execute('SELECT precios.* FROM precios INNER JOIN (SELECT id_juego, MAX(fecha) AS ultima_fecha FROM precios GROUP BY id_juego) AS precios_ultima_fecha ON precios_ultima_fecha.ultima_fecha = precios.fecha AND precios_ultima_fecha.id_juego = precios.id_juego INNER JOIN (SELECT id_juego, MAX(fecha) AS ultima_fecha_con_stock FROM precios WHERE precio IS NOT NULL GROUP BY id_juego) AS precios_ultima_fecha_con_stock ON precios_ultima_fecha_con_stock.ultima_fecha_con_stock = precios_ultima_fecha.ultima_fecha AND precios_ultima_fecha_con_stock.id_juego = precios_ultima_fecha.id_juego WHERE precios.id_juego NOT IN (SELECT id_juego FROM precios WHERE precio IS NOT NULL AND fecha BETWEEN datetime("now", "-30 days", "localtime") AND datetime("now", "-2 days", "localtime") GROUP BY id_juego)') # Gracias a Juan Leal
    stock = cursor.fetchall()
    texto_st = ""
    texto_st_me = ""
    cursor.execute('DELETE FROM restock WHERE fecha_inicial < datetime("now", "-3 days", "localtime")')
    conn.commit()
    cursor.execute('UPDATE restock SET activa = "No"')
    conn.commit()
    for s in stock:
        id_juego = s[1]
        cursor.execute('SELECT nombre, BGG_id, sitio, sitio_id, fecha_agregado as "[timestamp]" FROM juegos WHERE id_juego = ?',[id_juego])
        nombre, bgg_id, sitio, sitio_id, fecha_ag = cursor.fetchone()
        cursor.execute('SELECT precio FROM precios WHERE id_juego = ? ORDER BY fecha DESC LIMIT 1', [id_juego])
        precio_actual = cursor.fetchall()[0][0]
        fecha = datetime.now()
        tx_of = f"\U000027A1 [{nombre}]({constantes.sitio_URL['BGG']+str(bgg_id)}) está en stock en [{constantes.sitio_nom[sitio]}]({constantes.sitio_URL[sitio]+sitio_id}) a ${precio_actual:.0f} (y antes no lo estaba)\n"
        if (fecha - fecha_ag).days >= 7:
            cursor.execute('SELECT * FROM restock WHERE id_juego = ?',[id_juego])
            restock_act = cursor.fetchone()
            if restock_act == None: # Si no está en el listado de restock actuales
                cursor.execute('INSERT INTO restock (id_juego, fecha_inicial, activa) VALUES (?,?,?)',(id_juego, fecha, "Sí"))
                conn.commit()
                texto_st_me += tx_of
                texto_st += tx_of
            else:
                cursor.execute('UPDATE restock SET activa = "Sí" WHERE id_juego = ?',[id_juego])
                conn.commit()
                texto_st += tx_of

    if texto_of_me != "":
        texto_of_me = "*Juegos en oferta*\n\n" + texto_of_me
    if texto_st_me != "":
        texto_st_me = "*Juegos en reposición*\n\n" + texto_st_me
    if texto_of_me != "" or texto_st_me != "":
        cursor.execute('SELECT id_usuario FROM alarmas_ofertas')
        mensa = cursor.fetchall()
        texto = f"\U0001F381\U0001F381\U0001F381\n\n{texto_of_me}{texto_st_me}\n\U0001F381\U0001F381\U0001F381"
        for m in mensa:
            id_usuario = m[0]
            requests.get(f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={id_usuario}&disable_web_page_preview=True&parse_mode=Markdown&text={texto}')

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
            juegos_exporta.writerow([nombre,constantes.sitio_URL['BGG']+str(BGG_id),constantes.sitio_nom[sitio],constantes.sitio_URL[sitio]+sitio_ID, precio, fecha, min_precio, constantes.dependencia_len[dependencia_leng]])
    
    ju.close()
    if os.path.exists(f'graficos/{constantes.exporta_file}'):
        os.remove(f'graficos/{constantes.exporta_file}')
    os.rename(constantes.exporta_file,f'graficos/{constantes.exporta_file}')

if __name__ == '__main__':
    main()
