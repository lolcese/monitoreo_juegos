import sqlite3
import constantes

conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
conn.execute("PRAGMA journal_mode=WAL")
cursor = conn.cursor()

cursor.execute('SELECT id_juego FROM juegos')
juegos = cursor.fetchall()
for j in juegos:
    id_juego = j[0]
    cursor.execute('SELECT min(precio), fecha FROM precios WHERE id_juego = ?', [id_juego])
    juegos = cursor.fetchone()
    if juegos == None:
        mejor = None
        fecha = None
    else:
        mejor = juegos[0]
        fecha = juegos[1]
    
    cursor.execute('UPDATE juegos SET precio_mejor = ?, fecha_mejor = ? WHERE id_juego = ?', (mejor, fecha, id_juego))
    conn.commit()
