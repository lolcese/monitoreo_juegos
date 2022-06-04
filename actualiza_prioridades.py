#!/usr/bin/python
import os.path
import path
import constantes
import sqlite3

os.chdir(path.actual)
conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
conn.execute("PRAGMA journal_mode=WAL")
cursor = conn.cursor()
cursor.execute('UPDATE juegos SET prioridad = "3"')
conn.commit()
cursor.execute('SELECT BGG_id FROM alarmas GROUP BY BGG_id ORDER BY count() DESC LIMIT 70')
alarmas = cursor.fetchall()
num = 0
for a in alarmas:
    bgg_id = a[0]
    if num < 20:
        prioridad = "1"
    else:
        prioridad = "2"
    cursor.execute('UPDATE juegos SET prioridad = ? WHERE BGG_id = ?', (prioridad, bgg_id))
    conn.commit()
    num += 1

# cursor.execute('UPDATE juegos SET prioridad = 1 WHERE BGG_id = 250458 OR BGG_id = 251247')
conn.commit()
