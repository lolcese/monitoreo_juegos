#!/usr/bin/python
import sqlite3
import re
import html
import urllib.request
import constantes
from datetime import datetime
import requests
from requests import get
from urllib.error import URLError, HTTPError
from decouple import config

bot_token = config('bot_token')
id_aviso = config('id_aviso')

fecha = datetime.now()

conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
conn.execute("PRAGMA journal_mode=WAL")
cursor = conn.cursor()

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

    return data.read().decode(encoding, errors='ignore')

######### Baja cotización de monedas de BNA
url = 'https://www.bna.com.ar/Personas'
req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}) 
data = urllib.request.urlopen(req).read()
data = data.decode('utf-8')

dolar = html.unescape(re.search('<td class=\"tit\">Dolar U\.S\.A</td>\s+<td>.*?</td>\s+<td>(\d+\.\d+)</td>',data)[1])
dolar = float(re.sub("\,", ".", dolar))
cursor.execute('SELECT valor FROM variables WHERE variable = "dolar"')
dolar_viejo = float(cursor.fetchone()[0])
if abs(dolar - dolar_viejo) / dolar_viejo > 0.05:
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={id_aviso}&parse_mode=Markdown&text=El nuevo precio del dólar es ${dolar}, revisar'
    response = requests.get(send_text)
else:
    cursor.execute('UPDATE variables SET valor = ?, fecha = ? WHERE variable = "dolar"',(dolar, fecha))
    conn.commit()

libra = html.unescape(re.search('<td class=\"tit\">Libra Esterlina</td>\s+<td>.*?</td>\s+<td>(\d+\.\d+)</td>',data)[1])
libra = float(re.sub("\,", ".", libra))
cursor.execute('SELECT valor FROM variables WHERE variable = "libra"')
libra_viejo = float(cursor.fetchone()[0])
if abs(libra - libra_viejo) / libra_viejo > 0.05:
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={id_aviso}&parse_mode=Markdown&text=El nuevo precio de la libra es ${libra}, revisar'
    response = requests.get(send_text)
else:
    cursor.execute('UPDATE variables SET valor = ?, fecha = ? WHERE variable = "libra"',(libra, fecha))
    conn.commit()

euro = html.unescape(re.search('<td class=\"tit\">Euro</td>\s+<td>.*?</td>\s+<td>(\d+\.\d+)</td>',data)[1])
euro = float(re.sub("\,", ".", euro))
cursor.execute('SELECT valor FROM variables WHERE variable = "euro"')
euro_viejo = float(cursor.fetchone()[0])
if abs(euro - euro_viejo) / euro_viejo > 0.05:
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={id_aviso}&parse_mode=Markdown&text=El nuevo precio del euro es ${euro}, revisar'
    response = requests.get(send_text)
else:
    cursor.execute('UPDATE variables SET valor = ?, fecha = ? WHERE variable = "euro"',(euro, fecha))
    conn.commit()

######### Baja datos de costos de TM
url = 'https://tiendamia.com/ar/tarifas'
response = get(url)
data = response.content.decode('utf-8', errors='ignore')

datos1 = re.search('el shipping internacional tiene un costo de <span class="price dollar_price">\nU\$S (.*?) ',data)
env_int_dol = datos1[1]

cursor.execute('UPDATE variables SET valor = ?, fecha = ? WHERE variable = "tasa_tm"',(env_int_dol, fecha))
conn.commit()

datos2 = re.search('<td class="indent">0.1</td>\n.*?\n.*?\n.*?\n.*?\nU\$S (.*?) ',data)
tasa_kg = datos2[1]

cursor.execute('UPDATE variables SET valor = ?, fecha = ? WHERE variable = "precio_kg"',(tasa_kg, fecha))
conn.commit()

######### Baja dólar TM
id_prod_ref = "B000FZX93K"
url = "https://tiendamia.com/ar/producto?amz="+id_prod_ref
response = get(url)
text = response.content.decode('utf-8', errors='ignore')
precios = re.search('"currencies":{\n\s+"ARS":(.*?),\n\s+"USD":(.*?),',text)
precio_ar = float(precios[1])
precio_us = float(precios[2])
dolar_tm = precio_ar / precio_us

cursor.execute('UPDATE variables SET valor = ?, fecha = ? WHERE variable = "dolar_tm"',(dolar_tm, fecha))
conn.commit()

######### Baja envío BL
url = "https://www.buscalibre.com.ar/despacho-ar_st.html"
response = get(url)
text = response.content.decode('utf-8', errors='ignore')
datos1 = re.search('<span class="region">CABA</span><span class="valor">.*?</span><span class="despacho">.*?</span></li><li><span class="region">PROVINCIA DE BUENOS AIRES </span><span class="valor">\$ (.*?)</span>',text)
env_bl = float(datos1[1])

cursor.execute('UPDATE variables SET valor = ?, fecha = ? WHERE variable = "envio_BL"',(env_bl, fecha))
conn.commit()

cursor.close()
