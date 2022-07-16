########################################################
##### Constantes
########################################################

import sqlite3

db_file = 'db/monitoreo_juegos.db'
db_file_histo = 'db/monitoreo_juegos_todo.db'
exporta_file = 'exporta/precios_exporta.csv'

conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
conn.execute("PRAGMA journal_mode=WAL")
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

dependencia_len = {}
dependencia_len[0] = "No hay datos"
dependencia_len[1] = "Sin texto"
dependencia_len[2] = "Poco texto"
dependencia_len[3] = "Cantidad de texto moderada"
dependencia_len[4] = "Alta dependencia"
dependencia_len[5] = "Injugable en otro idioma"
