#!/usr/bin/python
import sqlite3
import re
import html
import urllib.request
import os
import constantes
import path
from datetime import datetime
import requests

os.chdir(path.actual)
bot_token = os.environ.get('bot_token')
id_aviso = os.environ.get('id_aviso')

fecha = datetime.now()

conn = sqlite3.connect(constantes.db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
conn.execute("PRAGMA journal_mode=WAL")
cursor = conn.cursor()

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

# req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'},ssl_verify=True) 
# data = urllib.request.urlopen(req).read()
# data = data.decode('utf-8')

# datos1 = re.search('el shipping internacional tiene un costo de <span class="price dollar_price">\nU\$S (.*?) .*?\n.*?\nAR\$ (.*?) ',data)
# env_int_dol = datos1[1]
# env_int_int = datos1[2]

# cursor.execute('UPDATE variables SET valor = ?, fecha = ? WHERE variable = "env_int_dol"',(env_int_dol, fecha))
# cursor.execute('UPDATE variables SET valor = ?, fecha = ? WHERE variable = "tasa_tm"',(env_int_int, fecha))
# conn.commit()

# datos2 = re.search('<td class="indent">0.1</td>\n.*?\n.*?\n.*?\n.*?\n.*?\nAR\$ (.*?) ',data)
# tasa_kg = datos2[1]
# tasa_kg = float(re.sub("\.", "", tasa_kg))

# cursor.execute('UPDATE variables SET valor = ?, fecha = ? WHERE variable = "precio_kg"',(dolar, fecha))
# conn.commit()

cursor.close()
