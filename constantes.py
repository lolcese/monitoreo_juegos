########################################################
##### Constantes
########################################################

import sqlite3
import os.path
import path

os.chdir(path.actual)

db_file = 'monitoreo_juegos.db'

conn = sqlite3.connect(db_file, timeout = 30, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
cursor = conn.cursor()

sitio_nom = {}
sitio_URL = {}
cursor.execute('SELECT sitio_ID, nombre_sitio, URL_base FROM sitios')
variables = cursor.fetchall()
for variable in variables:
    sitio_ID, nombre_sitio, URL_base = variable
    sitio_nom[sitio_ID] = nombre_sitio
    sitio_URL[sitio_ID] = URL_base

var = {}
cursor.execute('SELECT variable, valor, descripcion FROM variables')
variables = cursor.fetchall()
for variable in variables:
    nom_v, valor, desc = variable
    var[nom_v] = float(valor)
