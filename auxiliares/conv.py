import unicodedata
import sqlite3
import constantes
import re

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
conn.execute("PRAGMA journal_mode=WAL")
cursor = conn.cursor()

cursor.execute('SELECT id_juego, nombre FROM juegos')
juegos = cursor.fetchall()
for j in juegos:
    id_juego, nombre = j
    nom_n = strip_accents(nombre)
    nom_n = re.sub(r'[^\w\s]','',nom_n)
    nom_n = re.sub(r'\s+',' ',nom_n)

    cursor.execute('SELECT avg(precio) FROM precios WHERE id_juego = ?', [id_juego])
    prom = cursor.fetchone()[0]
    
    cursor.execute('UPDATE juegos SET nombre_noacentos = ?, precio_prom = ? WHERE id_juego = ?', (nom_n, prom, id_juego))
    conn.commit()
