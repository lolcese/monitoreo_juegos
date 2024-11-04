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
from telegram.ext import (Updater)
from decouple import config
import sys
import os
import constantes
import manda
import hace_grafico
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent
import socket
from datetime import date
import time

bot_token = config('bot_token')
id_aviso = config('id_aviso')

prioridad = str(sys.argv[1])

updater = Updater(bot_token)

######### Baja una página cualquiera
def baja_pagina(url):
    req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}) 
    try:
        data = urllib.request.urlopen(req, timeout = 60)
    except HTTPError as e:
        # print(f"**** HTTPError bajando {url}")
        return "Error"
    except socket.timeout:
        # print(f"**** Timeout bajando {url}")
        return "Error"
    except URLError as e:
        # print(f"**** URLError bajando {url}")
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

    stock = 'Disponibilidad: <span>En stock</span>' in text
 
    # precio_dol = re.search('"final_price":{"label":"","value":{"dollar_price":"U\$S (.*?)"',text)
    # if not precio_dol or not stock:
    #     return None
    # precio_dol = float(precio_dol[1])
    # if precio_dol < 1:
    #     return None

    precio_ar = re.search('"final_price":.*?"currency_price":"AR\$  (.*?)"',text)
    if not precio_ar or not stock:
        return None
    precio_ar = float(re.sub("\.", "", precio_ar[1]))
    if precio_ar < 1000:
        return None

    pr_tm = precio_tm(peso,precio_ar)
    return pr_tm

######### Lee información de TMWM
def lee_pagina_tmwm(ju_id):
    url = "https://tiendamia.com/ar/productow?wrt="+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    peso = re.search('Peso con empaque: <span>(.*?) kg<\/span>',text)
    if not peso or peso[1] == "":
        return None
    peso = float(peso[1])

    stock = '<span class="notranslate">Sin stock<\/span>' in text

    # precio_dol = re.search('"final_price":{"label":"","value":{"dollar_price":"U\$S (.*?)"',text)
    # if not precio_dol or stock:
    #     return None
    # precio_dol = float(precio_dol[1])
    # if precio_dol < 1:
    #     return None

    precio_ar = re.search('"localPrice":"AR\$  (.*?)"',text)
    if not precio_ar or stock:
        return None
    precio_ar = float(re.sub("\.", "", precio_ar[1]))
    if precio_ar < 1000:
        return None

    pr_tm = precio_tm(peso,precio_ar)
    return pr_tm

######### Calcula precio para TM
def precio_tm(peso,precio_ar):
# def precio_tm(peso,precio_dol):
    costo_peso = peso * constantes.var['precio_kg']
    if peso > 3:
        desc_3kg = 0.3 * (peso - 3) * constantes.var['precio_kg']
    else:
        desc_3kg = 0
    if peso > 5:
        desc_5kg = 0.5 * (peso - 5) * constantes.var['precio_kg']
    else:
        desc_5kg = 0
    # precio_dol = precio_dol * 1.1 + constantes.var['tasa_tm'] + costo_peso - desc_3kg - desc_5kg
    precio_ar = precio_ar * 1.1 + constantes.var['tasa_tm'] + costo_peso - desc_3kg - desc_5kg
    precio_dol = precio_ar / constantes.var['dolar_tm']

    imp = 0
    if precio_dol > 50:
        imp = (precio_dol - 50) * 0.5
    # precio_final_arg = (precio_dol + imp) * constantes.var['dolar'] * constantes.var['impuesto_compras_exterior'] + constantes.var['tasa_correo']
    precio_final_arg = precio_ar + imp * constantes.var['dolar'] + constantes.var['tasa_correo']
    return precio_final_arg

# ######### Lee información de BOOK
# def lee_pagina_book(ju_id):
#     url = "https://www.bookdepository.com/es/x/"+ju_id
#     text = baja_pagina(url)
#     if text == "Error":
#         return None

#     precio_ar = re.search('<span class=\"sale-price\">ARS\$(.*?)<\/span>',text)
#     if not precio_ar:
#         return None
#     no_stock = re.search('<p class="red-text bold">Actualmente no disponible<\/p>',text)
#     if no_stock:
#         return None
#     precio_ar = re.sub("\.", "", precio_ar[1])
#     precio_ar = float(re.sub(",", ".", precio_ar)) * constantes.var['impuesto_compras_exterior']

#     return precio_ar

# ######### Lee información de deepdiscount
# def lee_pagina_deep(ju_id, peso):
#     url = "https://www.deepdiscount.com/"+ju_id
#     text = baja_pagina(url)
#     if text == "Error":
#         return None

#     precio_dol = re.search('\"price\": \"(.*?)"',text)
#     if not precio_dol:
#         return None

#     if peso < 2:
#         costo_envio = constantes.var['envio_deepdiscount_0_2_lb']
#     elif peso < 3:
#         costo_envio = constantes.var['envio_deepdiscount_2_3_lb']
#     elif peso < 4:
#         costo_envio = constantes.var['envio_deepdiscount_3_4_lb']

#     precio_dol = float(precio_dol[1]) + costo_envio

#     imp_aduana = 0
#     if precio_dol > 50:
#         imp_aduana = (precio_dol - 50) * 0.5

#     precio_ar = precio_dol * constantes.var['dolar'] * constantes.var['impuesto_compras_exterior']
#     precio_final_ad = precio_ar + imp_aduana * constantes.var['dolar'] + constantes.var['tasa_correo']

#     return precio_final_ad

######### Lee información de grooves
def lee_pagina_grooves(ju_id):
    url = "https://www.grooves.land/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_eur = re.search('<div class=\"price\".*?[^s]>(\d.*?)&nbsp;EUR<\/big>',text)
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
    stock = '<span id="availability_value" class="warning_inline">No Disponible <\/span>' in text
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

# ######### Lee información de Miniature Market
# def lee_pagina_mm(ju_id, precio_envio):
#     url = "https://www.miniaturemarket.com/"+ju_id
#     text = baja_pagina(url)
#     if text == "Error":
#         return None

#     precio_dol = re.search("price: '(.*?)',",text)
#     stock = '<div class="availability out-of-stock">Out of stock<\/div>' in text
#     if not precio_dol or stock == 1:
#         return None

#     precio_dol = float(precio_dol[1])
#     precio_dol += precio_envio
#     precio_pesos = precio_dol * constantes.var['dolar'] 

#     imp_aduana = 0
#     if precio_dol > 50:
#         imp_aduana = (precio_dol - 50) * 0.5

#     precio_final_ad = precio_pesos * constantes.var['impuesto_compras_exterior'] + imp_aduana * constantes.var['dolar'] + constantes.var['tasa_correo']

#     return precio_final_ad

# ######### Lee información de Casa del Libro
# def lee_pagina_cdl(ju_id, precio_envio):
#     url = "https://www.casadellibro.com/"+ju_id
#     text = baja_pagina(url)
#     if text == "Error":
#         return None

#     precio_eur = re.search('\"Price\":\"(.*?)€?\"',text)
#     stock = '"availability":"OutOfStock"' in text
#     if not precio_eur or stock == 1:
#         return None

#     precio_eur = float(precio_eur[1])
#     precio_eur /= constantes.var['descuento_iva_CDL']
#     precio_eur += precio_envio
#     precio_pesos = precio_eur * constantes.var['euro'] * constantes.var['impuesto_CDL']
#     precio_final_ad = precio_pesos * constantes.var['impuesto_compras_exterior']

#     return precio_final_ad

# ######### Lee información de Magic Madhouse
# def lee_pagina_mmadhouse(ju_id):
#     url = "https://magicmadhouse.co.uk/"+ju_id
#     text = baja_pagina(url)
#     if text == "Error":
#         return None

#     precio_gbp = re.search('"itemSalePrice": "(.*?)",',text)
#     stock = '"stock":0,' in text
#     if not precio_gbp or stock == 1:
#         return None

#     precio_gbp = float(precio_gbp[1])
#     precio_gbp /= constantes.var['descuento_iva_MMadhouse']
#     precio_envio = constantes.var['envio_MMadhouse']
#     precio_imp = precio_gbp * constantes.var['fraccion_imp_MMadhouse'] + constantes.var['fijo_imp_MMadhouse']
#     precio_gbp += precio_envio + precio_imp
#     precio_pesos = precio_gbp * constantes.var['libra'] 
#     precio_final_ad = precio_pesos * constantes.var['impuesto_compras_exterior']

#     return precio_final_ad

######### Lee información de FNAC
# def lee_pagina_fnac(ju_id):
#     url = f"https://www.google.com/search?q=fnac+{ju_id}"

#     text = baja_pagina(url)
#     if text == "Error":
#         return None

#     precio_eur = re.search('<span>€(\d+\.\d+)<\/span>',text)
#     if not precio_eur:
#         precio_eur = re.search('>‏(\d.*) ‏€<\/span>',text)
#         if not precio_eur:
#             return None

#     precio_eur = float(precio_eur[1])
#     precio_envio = constantes.var['envio_FNAC']
#     precio_eur += precio_envio
#     precio_pesos = precio_eur * constantes.var['euro'] 
#     precio_final_ad = precio_pesos * constantes.var['impuesto_compras_exterior']

#     return precio_final_ad

######### Lee información de Philibert
def lee_pagina_phil(ju_id, precio_envio):
    url = "https://www.philibertnet.com/"+ju_id
    text = baja_pagina(url)
    if text == "Error":
        return None

    precio_eur = re.search('var gtmProductData .*"price":"(.*?)"',text)
    stock = 'This product is no longer in stock <' in text
    if not precio_eur or stock == 1:
        return None

    precio_eur = float(precio_eur[1]) / constantes.var['descuento_iva_Philibert']
    precio_eur += precio_envio

    precio_final_ad = precio_eur * constantes.var['euro'] * constantes.var['impuesto_compras_exterior'] + precio_eur * constantes.var['euro'] * constantes.var['impuesto_Philibert']

    return precio_final_ad

######### Programa principal
def main():
    conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT BGG_id, nombre FROM juegos WHERE prioridad = ? ORDER BY nombre',[prioridad])
    juegos_BGG = cursor.fetchall()
    for jb in juegos_BGG: # Cada juego diferente
        print (f"Procesando {jb[1]}")
        bgg_id, nombre = jb
        cursor.execute('SELECT id_juego, sitio, sitio_id, peso, precio_envio FROM juegos WHERE BGG_id = ? and sitio != "Usuario" ORDER BY sitio', [bgg_id])
        juegos_id = cursor.fetchall()
        for j in juegos_id: # Cada repetición del mismo juego
            print(f"Sitio: {j[1]}")
            fecha = datetime.now()
            id_juego, sitio, sitio_id, peso, precio_envio = j
            if sitio == "BLAM":
                precio = lee_pagina_blam(sitio_id)
            elif sitio == "BLIB":
                precio = lee_pagina_blib(sitio_id)
            elif sitio == "TMAM":
                precio = lee_pagina_tmam(sitio_id)
            elif sitio == "TMWM":
                precio = lee_pagina_tmwm(sitio_id) 
            # elif sitio == "deep":
            #     precio = lee_pagina_deep(sitio_id, peso)
            elif sitio == "grooves":
                precio = lee_pagina_grooves(sitio_id)
            elif sitio == "planeton":
                precio = lee_pagina_planeton(sitio_id, precio_envio)
            # elif sitio == "MM":
            #     precio = lee_pagina_mm(sitio_id, precio_envio)
            # elif sitio == "CDL":
            #     precio = lee_pagina_cdl(sitio_id, precio_envio)
            # elif sitio == "MMadhouse":
            #     precio = lee_pagina_mmadhouse(sitio_id)
            elif sitio == "PHIL":
                precio = lee_pagina_phil(sitio_id, precio_envio)

            cursor.execute('SELECT precio_prom, fecha_reposicion as "[timestamp]", fecha_oferta as "[timestamp]", fecha_agregado as "[timestamp]" FROM juegos WHERE id_juego = ?', [id_juego])
            prom = cursor.fetchone()
            precio_prom, fecha_reposicion, fecha_oferta, fecha_agregado = prom
            if precio is not None:
                precio = round(precio)
# Calcula el promedio y reposicion
                if precio_prom is None and (datetime.now() - fecha_agregado).days > 3:
                    fecha_reposicion = datetime.now()
# Dispara aviso reposiciones
                    if precio < constantes.var["precio_max_avisos"]:
                        if sitio == "BLIB" or sitio == "BLAM":
                            cursor.execute('SELECT id_usuario FROM alarmas_ofertas WHERE (tipo_alarma_reposicion = "BLP" OR tipo_alarma_reposicion = "Todo")')
                        else:
                            cursor.execute('SELECT id_usuario FROM alarmas_ofertas WHERE tipo_alarma_reposicion = "Todo"')
                        usuarios_ofertas = cursor.fetchall()
                        for u in usuarios_ofertas:
                            texto = f'\U00002757\U00002757\U00002757\n\n<b>Reposición</b>: <a href="{constantes.sitio_URL["BGG"]+str(bgg_id)}">{nombre}</a> está en stock en <a href="{constantes.sitio_URL[sitio]+sitio_id}">{constantes.sitio_nom[sitio]}</a> a ${precio:.0f} (y antes no lo estaba)\n\n\U00002757\U00002757\U00002757'
                            manda.send_message(u[0], texto)

                else:
# Dispara aviso ofertas
                    if precio_prom is not None and precio <= precio_prom * 0.9:
                        if precio < constantes.var["precio_max_avisos"]:
                            porc = (precio_prom - precio) / precio_prom * 100
                            if fecha_oferta is None or (datetime.now() - fecha_oferta).days > 7:
                                if sitio == "BLIB" or sitio =="BLAM":
                                    cursor.execute('SELECT id_usuario FROM alarmas_ofertas WHERE (tipo_alarma_oferta = "BLP" OR tipo_alarma_oferta = "Todo")')
                                else:
                                    cursor.execute('SELECT id_usuario FROM alarmas_ofertas WHERE tipo_alarma_oferta = "Todo"')
                                usuarios_ofertas = cursor.fetchall()
                                for u in usuarios_ofertas:
                                    texto = f'\U0001F381\U0001F381\U0001F381\n\n<b>Oferta</b>: <a href="{constantes.sitio_URL["BGG"]+str(bgg_id)}">{nombre}</a> está en <a href="{constantes.sitio_URL[sitio]+sitio_id}">{constantes.sitio_nom[sitio]}</a> a ${precio:.0f} y el promedio de 15 días es de ${precio_prom:.0f} ({porc:.0f}% menos)\n\n\U0001F381\U0001F381\U0001F381'
                                    manda.send_message(u[0], texto)
                        fecha_oferta = datetime.now()

# Guarda el precio en la tabla precios
                cursor.execute('INSERT INTO precios (id_juego, precio, fecha) VALUES (?,?,?)',[id_juego, precio, fecha]) 
                conn.commit()

# Guarda el precio, promedio y reposición en la tabla juegos
            cursor.execute('SELECT avg(precio) FROM precios WHERE id_juego = ?', [id_juego])
            precio_prom = cursor.fetchone()[0]
            if precio_prom is not None:
                precio_prom = round(precio_prom)

            cursor.execute('SELECT min(precio), fecha FROM precios WHERE id_juego = ?', [id_juego])
            juegos = cursor.fetchone()
            if juegos == None:
                precio_mejor = None
                fecha_mejor = None
            else:
                precio_mejor = juegos[0]
                fecha_mejor = juegos[1]

            cursor.execute('UPDATE juegos SET precio_actual = ?, fecha_actual = ?, precio_mejor = ?, fecha_mejor = ?, precio_prom = ?, fecha_reposicion = ?, fecha_oferta = ? WHERE id_juego = ?',[precio, fecha, precio_mejor, fecha_mejor, precio_prom, fecha_reposicion, fecha_oferta, id_juego])
            conn.commit()

# Manda alarmas
            cursor.execute('SELECT id_persona, precio_alarma FROM alarmas WHERE BGG_id = ? and precio_alarma >= ?',(bgg_id, precio))
            alarmas = cursor.fetchall()
            if len(alarmas) > 0:
                arch = hace_grafico.grafica(bgg_id, nombre, "actual")
                for alarma in alarmas:
                    id_persona, precio_al = alarma
                    texto = f'\U000023F0\U000023F0\U000023F0\n\n<a href="{constantes.sitio_URL["BGG"]+str(bgg_id)}">{nombre}</a> está a <b>${precio:.0f}</b> en <a href="{constantes.sitio_URL[sitio]+sitio_id}">{constantes.sitio_nom[sitio]}</a> (tenés una alarma a los ${precio_al:.0f}).\n\n\U000023F0\U000023F0\U000023F0'
                    manda.send_photo(id_persona, "", arch)
                    keyboard = [
                        [InlineKeyboardButton("Borrar alarma (después apretar START)", url=f"https://t.me/Monitor_Juegos_bot?start=borraalarma_{id_persona}_{bgg_id}")],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    manda.send_message_key(id_persona, texto, reply_markup)
                os.remove(arch)
    time.sleep(5)
    
if __name__ == '__main__':
    main()
