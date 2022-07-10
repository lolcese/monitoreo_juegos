import sqlite3
import constantes

conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
conn.execute("PRAGMA journal_mode=WAL")
cursor = conn.cursor()

cursor.execute('SELECT id_juego FROM juegos WHERE sitio = "TMAM" OR sitio = "TMWM" OR sitio = "TMEB"')
juegos = cursor.fetchall()
for j in juegos:
    id_juego = j[0]
    cursor.execute('DELETE FROM precios WHERE id_juego = ? and fecha BETWEEN datetime("2022-07-05") AND datetime("2022-07-08")', (id_juego))
    conn.commit()
