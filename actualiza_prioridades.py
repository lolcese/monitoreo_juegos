#!/usr/bin/python
import os.path
import path
import constantes
import sqlite3

os.chdir(path.actual)
conn = sqlite3.connect(constantes.db_file, timeout = 30, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
cursor = conn.cursor()
cursor.execute('UPDATE juegos SET prioridad = "3"')
conn.commit()
cursor.execute('SELECT BGG_id FROM alarmas GROUP BY BGG_id ORDER BY count() DESC LIMIT 50')
alarmas = cursor.fetchall()
num = 0
for a in alarmas:
    bgg_id = a[0]
    if num < 20:
        prioridad = "1"
    elif num < 50:
        prioridad = "2"
    print (prioridad, bgg_id)  
    cursor.execute('UPDATE juegos SET prioridad = ? WHERE BGG_id = ?', (prioridad, bgg_id))
    conn.commit()
    num += 1

cursor.execute('UPDATE juegos SET prioridad = 1 WHERE BGG_id = 250458')
conn.commit()