import re
from requests import get
from urllib.error import URLError, HTTPError
import urllib.request

def baja_pagina(url):
    req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36'})

    try:
        data = urllib.request.urlopen(req)
    except urllib.error.HTTPError as err:
        print(f'A HTTPError was thrown: {err.code} {err.reason}')
        return("Error1")
    except URLError as e:
        return "Error2"

    if data.headers.get_content_charset() is None:
        encoding='utf-8'
    else:
        encoding = data.headers.get_content_charset()

    return data.read().decode(encoding, errors='ignore')

######### Lee información de BLIB
def lee_pagina_blib(ju_id):
    url = "https://www.buscalibre.com.ar/"+ju_id
    text = baja_pagina(url)
    print(text)
    if text == "Error":
        return None

    precio_ar = re.search("'ecomm_totalvalue' : '(.*?)'",text)
    if not precio_ar or float(precio_ar[1]) == 0:
        return None
    precio_ar = float(precio_ar[1]) + 2900
    return precio_ar

ju_id = "libro-undaunted-normandy/9781472834706/p/51957292"

print(lee_pagina_blib(ju_id))

