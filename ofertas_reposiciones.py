#!/usr/bin/python

import constantes
import sqlite3
from datetime import datetime
import manda

conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
conn.execute("PRAGMA journal_mode=WAL")
cursor = conn.cursor()
cursor.execute('SELECT id_juego, avg(precio) FROM precios GROUP BY id_juego HAVING avg(precio) NOT NULL')
prom = cursor.fetchall()
texto_of = ""
texto_of_me = ""
cursor.execute('DELETE FROM ofertas WHERE fecha_inicial < datetime("now", "-15 days", "localtime")')
conn.commit()
cursor.execute('UPDATE ofertas SET activa = "No"')
conn.commit()
for p in prom:
    id_juego, precio_prom = p
    cursor.execute('SELECT precio FROM precios WHERE id_juego = ? ORDER BY fecha DESC LIMIT 1', [id_juego])
    precio_actual = cursor.fetchone()[0]
    if precio_actual is not None and precio_actual <= 0.9 * precio_prom:
        cursor.execute('SELECT nombre, sitio, sitio_id,BGG_id FROM juegos WHERE id_juego = ?', [id_juego])
        nombre, sitio, sitio_id, bgg_id = cursor.fetchone()
        porc = (precio_prom - precio_actual) / precio_prom * 100
        fecha = datetime.now()
        cursor.execute('SELECT fecha_inicial as "[timestamp]" FROM ofertas WHERE id_juego = ?',[id_juego])
        ofertas_act = cursor.fetchone()
        tx_al = f'\U000027A1 <a href="{constantes.sitio_URL["BGG"]+str(bgg_id)}">{nombre}</a> está en <a href="{constantes.sitio_URL[sitio]+sitio_id}">{constantes.sitio_nom[sitio]}</a> a ${precio_actual:.0f} y el promedio de 15 días es de ${precio_prom:.0f} ({porc:.0f}% menos)\n'
        if ofertas_act == None: # Si no está en el listado de ofertas actuales
            cursor.execute('INSERT INTO ofertas (id_juego,precio_prom,precio_actual,fecha_inicial,activa) VALUES (?,?,?,?,?)',(id_juego,precio_prom,precio_actual,fecha,"Sí"))
            conn.commit()
            texto_of_me += tx_al
            texto_of += tx_al
        else:
            cursor.execute('UPDATE ofertas SET precio_prom = ?, precio_actual = ?, activa = "Sí" WHERE id_juego = ?',(precio_prom,precio_actual,id_juego))
            conn.commit()
            texto_of += tx_al
            
cursor.execute('SELECT precios.* FROM precios INNER JOIN (SELECT id_juego, MAX(fecha) AS ultima_fecha FROM precios GROUP BY id_juego) AS precios_ultima_fecha ON precios_ultima_fecha.ultima_fecha = precios.fecha AND precios_ultima_fecha.id_juego = precios.id_juego INNER JOIN (SELECT id_juego, MAX(fecha) AS ultima_fecha_con_stock FROM precios WHERE precio IS NOT NULL GROUP BY id_juego) AS precios_ultima_fecha_con_stock ON precios_ultima_fecha_con_stock.ultima_fecha_con_stock = precios_ultima_fecha.ultima_fecha AND precios_ultima_fecha_con_stock.id_juego = precios_ultima_fecha.id_juego WHERE precios.id_juego NOT IN (SELECT id_juego FROM precios WHERE precio IS NOT NULL AND fecha BETWEEN datetime("now", "-30 days", "localtime") AND datetime("now", "-2 days", "localtime") GROUP BY id_juego)') # Gracias a Juan Leal
stock = cursor.fetchall()
texto_st = ""
texto_st_me = ""
cursor.execute('DELETE FROM restock WHERE fecha_inicial < datetime("now", "-3 days", "localtime")')
conn.commit()
cursor.execute('UPDATE restock SET activa = "No"')
conn.commit()
for s in stock:
    id_juego = s[1]
    cursor.execute('SELECT nombre, BGG_id, sitio, sitio_id, fecha_agregado as "[timestamp]" FROM juegos WHERE id_juego = ?',[id_juego])
    nombre, bgg_id, sitio, sitio_id, fecha_ag = cursor.fetchone()
    cursor.execute('SELECT precio FROM precios WHERE id_juego = ? ORDER BY fecha DESC LIMIT 1', [id_juego])
    precio_actual = cursor.fetchall()[0][0]
    if (precio_actual > 0):
        fecha = datetime.now()
        tx_of = f'\U000027A1 <a href="{constantes.sitio_URL["BGG"]+str(bgg_id)}">{nombre}</a> está en stock en <a href="{constantes.sitio_URL[sitio]+sitio_id}">{constantes.sitio_nom[sitio]}</a> a ${precio_actual:.0f} (y antes no lo estaba)\n'
        if (fecha - fecha_ag).days >= 7:
            cursor.execute('SELECT * FROM restock WHERE id_juego = ?',[id_juego])
            restock_act = cursor.fetchone()
            if restock_act == None: # Si no está en el listado de restock actuales
                cursor.execute('INSERT INTO restock (id_juego, fecha_inicial, activa) VALUES (?,?,?)',(id_juego, fecha, "Sí"))
                conn.commit()
                texto_st_me += tx_of
                texto_st += tx_of
            else:
                cursor.execute('UPDATE restock SET activa = "Sí" WHERE id_juego = ?',[id_juego])
                conn.commit()
                texto_st += tx_of

if texto_of_me != "":
    texto_of_me = f"\U0001F381\U0001F381\U0001F381\n\n<b>Juegos en oferta</b>\n\n{texto_of_me}\n\U0001F381\U0001F381\U0001F381"
if texto_st_me != "":
    texto_st_me = f"\U0001F381\U0001F381\U0001F381\n\n<b>Juegos en reposición</b>\n\n{texto_st_me}\n\U0001F381\U0001F381\U0001F381"
if texto_of_me != "" or texto_st_me != "":
    cursor.execute('SELECT id_usuario,tipo_alarma FROM alarmas_ofertas')
    mensa = cursor.fetchall()
    for m in mensa:
        id_usuario = m[0]
        tipo_alarma = m[1]
        if (tipo_alarma == 1 or tipo_alarma == 3) and texto_of_me != "":
            manda.send_message(id_usuario, texto_of_me)
        if (tipo_alarma == 2 or tipo_alarma == 3) and texto_st_me != "":
            manda.send_message(id_usuario, texto_st_me)
