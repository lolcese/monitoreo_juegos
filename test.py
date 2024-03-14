import requests
from bs4 import BeautifulSoup
import re
from requests import get
from urllib.error import URLError, HTTPError
import urllib.request

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

url = "https://www.buscalibre.com.ar/despacho-ar_st.html"
response = baja_pagina(url)

datos1 = re.findall('const data.* = \[ \".*\", \".*\", \"(.*)\", \".*\", \".*\", \".*\", \".*\", \".*\" \];',response)


env_bl = float(datos1[-1])

print(env_bl)