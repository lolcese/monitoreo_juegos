import unicodedata
import sqlite3
import constantes

def strip_accents(s):
    print(s)
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
    print(id_juego, nombre,nom_n, "*")
    cursor.execute('UPDATE juegos SET nombre_noacentos = ? WHERE id_juego = ?', (nom_n, id_juego))
    
