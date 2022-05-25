#!/usr/bin/python
# -*- coding: utf-8 -*-
############################################################################################
# Este programa es llamado a correr cada n minutos por el sistema,
# y baja las páginas de cada juego, extrae el precio y el peso (si fuera necesario),
# calcula el precio final en Argentina, grafica y manda alarmas.
############################################################################################
# https://pypi.org/project/schedule/

import urllib.request
import re
from datetime import datetime
from urllib.error import URLError, HTTPError
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FormatStrFormatter
import constantes
import os.path
import path
from telegram.ext import (Updater)
import requests
import sys

prioridad = str(sys.argv[1])
os.chdir(path.actual)
bot_token = os.environ.get('bot_token')

updater = Updater(bot_token)

######### Baja una página cualquiera
def baja_pagina(url):
    req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}) 
    try:
        data = urllib.request.urlopen(req)
    except HTTPError as e:
        return "Error"
    except URLError as e:
        return "Error"

    if data.headers.get_content_charset() is None:
        encoding='utf-8'
    else:
        encoding = data.headers.get_content_charset()

    try: 
        pag = data.read().decode(encoding, errors='ignore')
    except:
        return "Error"
    return pag

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

    precio_ar = re.search("'ecomm_totalvalue' : '(.*?)'",text)
    if not precio_ar or float(precio_ar[1]) == 0:
        return None
    precio_ar = float(precio_ar[1]) + constantes.var['envio_BL']
    return precio_ar

######### Lee información de TMAM
def lee_pagina_tmam(ju_id):
    url = "https://tiendamia.com/ar/producto?amz="+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    peso = re.search('"weight":{"type":"normal","value":"(.*?) kg"',text)
    if not peso or peso[1] == "":
        return None
    peso = float(peso[1])
 
    precio_ar = re.search('<meta property="product:price:amount" content="(.*?)"',text)
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
    peso = re.search('Peso con empaque: <span>(.*?)kg</span>',text)
    if not peso or peso[1] == "":
        return None
    peso = float(peso[1])

    precio_ar = re.search('<span class="currency_price">AR\$ (.*)</span>',text)
    stock = 'Disponibilidad: <span>Fuera de stock</span>' in text
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
    stock = '<span id="stock_producto_ajax">Sin Stock</span>' in text
    if not precio_ar or stock == 1:
        return None
    precio_ar = float(re.sub("\.", "", precio_ar[1]))
    if precio_ar < 100:
        return None

    pr_tm = precio_tm(peso,precio_ar)
    return pr_tm

######### Lee información de TMMA
def lee_pagina_tmma(ju_id):
    url = "https://tiendamia.com/ar/product/mcy/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    peso = re.search('"weight":(\d*\.?\d*)',text)
    if not peso:
        return None
    peso = float(peso[1])

    precio_ar = re.search('"local":(.*?),"cur":"ARS"',text)
    stock = 'product\.setVariations.*?"available":false,' in text
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
    no_stock = re.search('<p class="red-text bold">Actualmente no disponible</p>',text)
    if no_stock:
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

    precio_lb = re.search('<span class=\"uk-text-large uk-text-primary\">&pound;(.*?)<',text)
    if not precio_lb:
        return None
    precio_pesos = (float(precio_lb[1]) + constantes.var['envio_365']) * constantes.var['libra'] 
    precio_dol = precio_pesos / constantes.var['dolar']

    imp_aduana = 0
    if precio_dol > 50:
        imp_aduana = (precio_dol - 50) * 0.5

    precio_final_ad = precio_pesos * constantes.var['impuesto_compras_exterior'] + imp_aduana * constantes.var['dolar'] + constantes.var['tasa_correo']

    return precio_final_ad

######### Lee información de shop4es
def lee_pagina_shop4es(ju_id):
    url = "https://www.shop4es.com/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_eu = re.search('<span class=\"uk-text-large uk-text-primary\">(.*?)&euro',text)
    if not precio_eu:
        return None
    precio_pesos = (float(re.sub("\,", ".", precio_eu[1])) + constantes.var['envio_shop4es']) * constantes.var['euro'] 
    precio_dol = precio_pesos / constantes.var['dolar']

    imp_aduana = 0
    if precio_dol > 50:
        imp_aduana = (precio_dol - 50) * 0.5

    precio_final_ad = precio_pesos * constantes.var['impuesto_compras_exterior'] + imp_aduana * constantes.var['dolar'] + constantes.var['tasa_correo']

    return precio_final_ad

######### Lee información de shop4world
def lee_pagina_shop4world(ju_id):
    url = "https://www.shop4world.com/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_lb = re.search('<span class=\"uk-text-large uk-text-primary\">&pound;(.*?)<',text)
    if not precio_lb:
        return None
    precio_pesos = (float(precio_lb[1]) + constantes.var['envio_shop4world']) * constantes.var['libra'] 
    precio_dol = precio_pesos / constantes.var['dolar']

    imp_aduana = 0
    if precio_dol > 50:
        imp_aduana = (precio_dol - 50) * 0.5

    precio_final_ad = precio_pesos * constantes.var['impuesto_compras_exterior'] + imp_aduana * constantes.var['dolar'] + constantes.var['tasa_correo']

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

    imp_aduana = 0
    if precio_dol > 50:
        imp_aduana = (precio_dol - 50) * 0.5

    precio_ar = precio_dol * constantes.var['dolar'] * constantes.var['impuesto_compras_exterior']
    precio_final_ad = precio_ar + imp_aduana * constantes.var['dolar'] + constantes.var['tasa_correo']

    return precio_final_ad

######### Lee información de grooves
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
    precio_pesos = precio_eur * constantes.var['euro'] 
    precio_dol = precio_pesos / constantes.var['dolar']

    imp_aduana = 0
    if precio_dol > 50:
        imp_aduana = (precio_dol - 50) * 0.5

    precio_final_ad = precio_pesos * constantes.var['impuesto_compras_exterior'] + imp_aduana * constantes.var['dolar'] + constantes.var['tasa_correo']

    return precio_final_ad

######### Lee información de planeton
def lee_pagina_planeton(ju_id, precio_envio):
    url = "https://www.planetongames.com/es/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_eur = re.search('<span itemprop="price" content="(.*?)">',text)
    stock = '<span id="availability_value" class="warning_inline">No Disponible </span>' in text
    if not precio_eur or stock == 1:
        return None

    precio_eur = float(precio_eur[1])
    if precio_eur > constantes.var['limite_descuento_planeton']:
        precio_eur -= constantes.var['descuento_montoalto_planeton']
    precio_eur /= constantes.var['descuento_iva_planeton']  
    precio_eur += precio_envio
    precio_pesos = precio_eur * constantes.var['euro'] 
    precio_dol = precio_pesos / constantes.var['dolar']

    imp_aduana = 0
    if precio_dol > 50:
        imp_aduana = (precio_dol - 50) * 0.5

    precio_final_ad = precio_pesos * constantes.var['impuesto_compras_exterior'] + imp_aduana * constantes.var['dolar'] + constantes.var['tasa_correo']

    return precio_final_ad

######### Lee información de Miniature Market
def lee_pagina_mm(ju_id, precio_envio):
    url = "https://www.miniaturemarket.com/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_dol = re.search("price: '(.*?)',",text)
    stock = '<div class="availability out-of-stock">Out of stock</div>' in text
    if not precio_dol or stock == 1:
        return None

    precio_dol = float(precio_dol[1])
    precio_dol += precio_envio
    precio_pesos = precio_dol * constantes.var['dolar'] 

    imp_aduana = 0
    if precio_dol > 50:
        imp_aduana = (precio_dol - 50) * 0.5

    precio_final_ad = precio_pesos * constantes.var['impuesto_compras_exterior'] + imp_aduana * constantes.var['dolar'] + constantes.var['tasa_correo']

    return precio_final_ad

######### Programa principal
def main():
    plt.ioff()
    conn = sqlite3.connect(constantes.db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT BGG_id, nombre FROM juegos WHERE prioridad = ? ORDER BY nombre',[prioridad])
    juegos_BGG = cursor.fetchall()
    for jb in juegos_BGG: # Cada juego diferente
        bgg_id, nombre = jb
        hacer_grafico = False
        cursor.execute('SELECT id_juego, sitio, sitio_ID, peso, precio_envio FROM juegos WHERE BGG_id = ? ORDER BY sitio', [bgg_id])
        juegos_id = cursor.fetchall()
        for j in juegos_id: # Cada repetición del mismo juego
            fecha = datetime.now()
            id_juego, sitio, sitio_ID, peso, precio_envio = j
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
            elif sitio == "TMMA":
                precio = lee_pagina_tmma(sitio_ID) 
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
            elif sitio == "planeton":
                precio = lee_pagina_planeton(sitio_ID, precio_envio)
            elif sitio == "MM":
                precio = lee_pagina_mm(sitio_ID, precio_envio)

            if precio != None:
                cursor.execute('INSERT INTO precios (id_juego, precio, fecha) VALUES (?,?,?)',[id_juego, precio, fecha]) 
                conn.commit()

            cursor.execute('SELECT precio, fecha as "[timestamp]" FROM precios WHERE id_juego = ? ORDER BY precio, fecha DESC LIMIT 1', [id_juego])
            mejor = cursor.fetchone()
            if mejor != None:
                precio_mejor, fecha_mejor = mejor
            else:
                precio_mejor = None
                fecha_mejor = None
            cursor.execute('UPDATE juegos SET precio_actual = ?, fecha_actual = ?, precio_mejor = ?, fecha_mejor = ? WHERE id_juego = ?',[precio, fecha, precio_mejor, fecha_mejor, id_juego])
            conn.commit()

            cursor.execute('SELECT precio, fecha as "[timestamp]" FROM precios WHERE id_juego = ?',[id_juego])
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
            plt.close('all')

        cursor.execute('SELECT id_persona, precio_alarma FROM alarmas WHERE BGG_id = ? and precio_alarma >= ?',(bgg_id, precio))
        alarmas = cursor.fetchall()
        for alarma in alarmas:
            id_persona, precio_al = alarma
            if str(precio_al) == "":
                continue
            arch = f"{bgg_id}.png"
            if not os.path.exists(f"graficos/{arch}"):
                arch = "0000.png"
            imagen = f'{constantes.sitio_URL["base"]}graficos/{arch}?f={datetime.now().isoformat()}' # Para evitar que una imagen quede en cache

            texto = f'\U000023F0\U000023F0\U000023F0\n[ ]({imagen})\n[{nombre}]({constantes.sitio_URL["BGG"]+str(bgg_id)}) está a *${precio:.0f}* en [{constantes.sitio_nom[sitio]}]({constantes.sitio_URL[sitio]+sitio_ID}) (tenés una alarma a los ${precio_al:.0f})\n\n\U000023F0\U000023F0\U000023F0'
            requests.get(f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={id_persona}&disable_web_page_preview=False&parse_mode=Markdown&text={texto}')

if __name__ == '__main__':
    main()
