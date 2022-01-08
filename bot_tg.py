#!/usr/bin/python
# -*- coding: utf-8 -*-
############################################################################################
# # Este bot de telegram es iniciado como un servicio y brinda la posibilidad
# de ver datos de juegos, fijar alarmas, sugerir nuevos juegos a monitorear, etc.
############################################################################################

from ntpath import join
from sqlite3.dbapi2 import version
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (Updater,InlineQueryHandler,CommandHandler,CallbackQueryHandler,ConversationHandler,CallbackContext,MessageHandler,Filters)
from datetime import datetime
import re
import sqlite3
import os
import constantes
import os.path
import path
from uuid import uuid4
import requests
import html

os.chdir(path.actual)
bot_token = os.environ.get('bot_token')
id_aviso = os.environ.get('id_aviso')

PRINCIPAL, LISTA_JUEGOS, JUEGO_ELECCION, JUEGO, ALARMAS, ALARMAS_NUEVA_PRECIO, ALARMAS_CAMBIAR_PRECIO, COMENTARIOS, JUEGO_AGREGAR = range(9)

######### Conecta con la base de datos
def conecta_db():
    conn = sqlite3.connect(constantes.db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

######### Divide texto largo en partes
def dividir_texto(texto, n):
    lineas = texto.split("\n")
    bloque = []
    for i in range(0, len(lineas), n):
        bloque.append("\n".join(lineas[i:i + n]))
    return bloque

######### Cuando se elige la opción Inicio
def start(update: Update, context: CallbackContext) -> int:
    usuario = update.message.from_user
    fecha = datetime.now()
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO usuarios (nombre, id, fecha, accion) VALUES (?,?,?,?)',[usuario.full_name,usuario.id,fecha,"Inicio"])
    conn.commit()
    keyboard = menu()
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text = f'Hola, te doy la bienvenida al bot para monitorear precios de juegos. Si apretás un botón y no responde, escribí /start.\n¿Qué querés hacer?', reply_markup=reply_markup)
    return PRINCIPAL

######### Cuando se elige la opción Inicio (es diferente al anterior porque viene de una query)
def inicio(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario = query.from_user
    fecha = datetime.now()
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO usuarios (nombre, id, fecha, accion) VALUES (?,?,?,?)',[usuario.full_name,usuario.id,fecha,"Inicio secundario"])
    conn.commit()
    keyboard = menu()
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = f'Hola, te doy la bienvenida al bot para monitorear precios de juegos. Si apretás un botón y no responde, escribí /start.\n¿Qué querés hacer?', reply_markup=reply_markup)
    return PRINCIPAL

######### Cuando se elige la opción Inicio (es diferente al anterior porque tiene que borrar el mensaje)
def inicio_borrar(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario = query.from_user
    usuario_id = update.callback_query.from_user.id
    keyboard = menu()
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    context.bot.send_message(chat_id = update.effective_chat.id, text = f'Hola, te doy la bienvenida al bot para monitorear precios de juegos. Si apretás un botón y no responde, escribí /start.\n¿Qué querés hacer?', reply_markup=reply_markup)
    return PRINCIPAL

######### Menú principal
def menu():
    keyboard = [
        [InlineKeyboardButton("\U0001F4DA Listas de juegos monitoreados", callback_data='juegos_lista_menu')],
        [InlineKeyboardButton("\U0001F381 Ofertas y juegos en reposición", callback_data='ofertas_restock')],
        [InlineKeyboardButton("\U0001F3B2 Ver un juego y poner/borrar alarmas", callback_data='juego_ver')],
        [InlineKeyboardButton("\U0000270F Sugerir juego a monitorear", callback_data='sugerir_juego_datos')],
        [InlineKeyboardButton("\U000023F0 Ver mis alarmas", callback_data='alarmas_muestra')],
        [InlineKeyboardButton("\U0001F4AC Enviar comentarios y sugerencias", callback_data='comentarios_texto')],
        [InlineKeyboardButton("\U00002757 Novedades", callback_data='novedades')],
        [InlineKeyboardButton("\U0001F522 Estadística", callback_data='estadistica')],
        [InlineKeyboardButton("\U00002615 Invitame a un cafecito", callback_data='cafecito')],
        [InlineKeyboardButton("\U00002753 Ayuda", callback_data='ayuda')]
    ]
    return keyboard

######### Manú de listas de juegos
def juegos_lista_menu(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("\U0001F4DC Planilla con todos los juegos", callback_data='juegos_planilla')],
        [InlineKeyboardButton("\U0001F4D4 Todos los juegos", callback_data='juegos_todos')],
        [InlineKeyboardButton("\U0001F520 Juegos disp. (alfabéticamente)", callback_data='juegos_stockalfab')],
        [InlineKeyboardButton("\U0001F522 Juegos disp. (por precio)", callback_data='juegos_stockprecio')],
        [InlineKeyboardButton("\U0001F5DE Últimos 30 agregados", callback_data='juegos_lista_ULT')],
        [InlineKeyboardButton("\U0001F4B2 30 juegos baratos", callback_data='juegos_baratos_0')],
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    id = query.edit_message_text(text = "Elegí los juegos a listar", reply_markup=reply_markup)
    context.chat_data["mensaje_id"] = id.message_id
    return LISTA_JUEGOS

######### Link a la planilla con todos los juegos
def juegos_planilla(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    texto = '<b>Planilla con todos los juegos</b>\n\n' + \
    'Si querés ver una planilla con todos los precios de los juegos, andá ' + \
    '<a href="https://docs.google.com/spreadsheets/d/1eh5ckbIl5td0B8aRScxkIZU62MfeMplXxGdlsAWPoVA/edit?usp=sharing">acá</a>.\n' + \
    'Tené en cuenta que, si bien se actualiza automáticamente, puede tener un desfasaje de 2-3 horas con los precios reales (y 1 hora con los precios que muestra el bot).'
    keyboard = [
        [
            InlineKeyboardButton("\U00002B05 Anterior", callback_data='juegos_lista_menu'),
            InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return PRINCIPAL

######### Listas de todos los juegos en sitios en orden alfabético
def juegos_todos(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("\U0001F4D5 Buscalibre", callback_data='juegos_todos_sitio_BLIB'),
            InlineKeyboardButton("\U0001F4D5 Buscalibre Amazon", callback_data='juegos_todos_sitio_BLAM')
        ],
        [
            InlineKeyboardButton("\U0001F4D8 Tiendamia Amazon", callback_data='juegos_todos_sitio_TMAM'),
            InlineKeyboardButton("\U0001F4D8 Tiendamia Walmart", callback_data='juegos_todos_sitio_TMWM')
        ],
        [
            InlineKeyboardButton("\U0001F4D8 Tiendamia EBAY", callback_data='juegos_todos_sitio_TMEB'),
            InlineKeyboardButton("\U0001F4D8 Tiendamia Macys", callback_data='juegos_todos_sitio_TMMA')
        ],
        [
            InlineKeyboardButton("\U0001F4D9 Bookdepository", callback_data='juegos_todos_sitio_BOOK'),
            InlineKeyboardButton("\U0001F4D2 365games", callback_data='juegos_todos_sitio_365')
        ],
        [
            InlineKeyboardButton("\U0001F4D2 shop4es", callback_data='juegos_todos_sitio_shop4es'),
            InlineKeyboardButton("\U0001F4D2 shop4world", callback_data='juegos_todos_sitio_shop4world')
        ],
        [
            InlineKeyboardButton("\U0001F4D7 Deepdiscount", callback_data='juegos_todos_sitio_deep'),
            InlineKeyboardButton("\U0001F4D3 Grooves.land", callback_data='juegos_todos_sitio_grooves')
        ],
        [
            InlineKeyboardButton("\U00002B05 Anterior", callback_data='juegos_lista_menu'),
            InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    id = query.edit_message_text(text = "Elegí los juegos a listar", reply_markup=reply_markup)
    context.chat_data["mensaje_id"] = id.message_id
    return LISTA_JUEGOS
   
######### Lista de todos los juegos de un sitio en orden alfabético
def juegos_todos_sitio(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id
    sitio = query.data.split("_")[3]
    texto = f"<b>Juegos en {constantes.sitio_nom[sitio]}</b>\n\n"
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, sitio_id, precio_actual FROM juegos WHERE sitio = ? ORDER BY nombre',[sitio])
    juegos = cursor.fetchall()
    for j in juegos:
        nombre, sitio_id, precio_actual = j
        if precio_actual == None:
            texto += f"\U000027A1 <a href='{constantes.sitio_URL[sitio]+str(sitio_id)}'>{html.escape(nombre)}</a> (No disponible)\n"
        else:
            texto += f"\U000027A1 <a href='{constantes.sitio_URL[sitio]+str(sitio_id)}'>{html.escape(nombre)}</a> (${precio_actual:.0f})\n"
    keyboard = [
        [
            InlineKeyboardButton("\U00002B05 Anterior", callback_data='juegos_todos'),
            InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    texto_mensaje_div = dividir_texto(f"{texto}\n", 50)
    for t in range(0, len(texto_mensaje_div-2)):
        context.bot.send_message(chat_id = usuario_id, text = texto_mensaje_div[t], parse_mode = "HTML", disable_web_page_preview = True)
    context.bot.send_message(chat_id = usuario_id, text = texto_mensaje_div[-1], parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return LISTA_JUEGOS

######### Listas de juegos disponibles en sitios en orden alfabético
def juegos_stockalfab(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("\U0001F4D5 Buscalibre", callback_data='juegos_stockalfab_sitio_BLIB'),
            InlineKeyboardButton("\U0001F4D5 Buscalibre Amazon", callback_data='juegos_stockalfab_sitio_BLAM')
        ],
        [
            InlineKeyboardButton("\U0001F4D8 Tiendamia Amazon", callback_data='juegos_stockalfab_sitio_TMAM'),
            InlineKeyboardButton("\U0001F4D8 Tiendamia Walmart", callback_data='juegos_stockalfab_sitio_TMWM')
        ],
        [
            InlineKeyboardButton("\U0001F4D8 Tiendamia EBAY", callback_data='juegos_stockalfab_sitio_TMEB'),
            InlineKeyboardButton("\U0001F4D8 Tiendamia Macys", callback_data='juegos_stockalfab_sitio_TMMA')
        ],
        [
            InlineKeyboardButton("\U0001F4D9 Bookdepository", callback_data='juegos_stockalfab_sitio_BOOK'),
            InlineKeyboardButton("\U0001F4D2 365games", callback_data='juegos_stockalfab_sitio_365')
        ],
        [
            InlineKeyboardButton("\U0001F4D2 shop4es", callback_data='juegos_stockalfab_sitio_shop4es'),
            InlineKeyboardButton("\U0001F4D2 shop4world", callback_data='juegos_stockalfab_sitio_shop4world')
        ],
        [
            InlineKeyboardButton("\U0001F4D7 Deepdiscount", callback_data='juegos_stockalfab_sitio_deep'),
            InlineKeyboardButton("\U0001F4D3 Grooves.land", callback_data='juegos_stockalfab_sitio_grooves')
        ],
        [
            InlineKeyboardButton("\U00002B05 Anterior", callback_data='juegos_lista_menu'),
            InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    id = query.edit_message_text(text = "Elegí los juegos a listar", reply_markup=reply_markup)
    context.chat_data["mensaje_id"] = id.message_id
    return LISTA_JUEGOS
   
######### Lista de juegos disponibles de un sitio en orden alfabético
def juegos_stockalfab_sitio(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id
    sitio = query.data.split("_")[3]
    texto = f"<b>Juegos disponibles en {constantes.sitio_nom[sitio]}</b>\n\n"
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, sitio_id, precio_actual FROM juegos WHERE sitio = ? AND precio_actual NOT NULL ORDER BY nombre',[sitio])
    juegos = cursor.fetchall()
    for j in juegos:
        nombre, sitio_id, precio_actual = j
        texto += f"\U000027A1 <a href='{constantes.sitio_URL[sitio]+str(sitio_id)}'>{html.escape(nombre)}</a> (${precio_actual:.0f})\n"
    keyboard = [
        [
            InlineKeyboardButton("\U00002B05 Anterior", callback_data='juegos_stockalfab'),
            InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    texto_mensaje_div = dividir_texto(f"{texto}\n", 50)
    for t in texto_mensaje_div[0:-2]:
        context.bot.send_message(chat_id = usuario_id, text = t, parse_mode = "HTML", disable_web_page_preview = True)
    context.bot.send_message(chat_id = usuario_id, text = texto_mensaje_div[-1], parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return LISTA_JUEGOS

######### Listas de juegos disponibles en sitios en orden de precios
def juegos_stockprecio(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("\U0001F4D5 Buscalibre", callback_data='juegos_stockprecio_sitio_BLIB'),
            InlineKeyboardButton("\U0001F4D5 Buscalibre Amazon", callback_data='juegos_stockprecio_sitio_BLAM')
        ],
        [
            InlineKeyboardButton("\U0001F4D8 Tiendamia Amazon", callback_data='juegos_stockprecio_sitio_TMAM'),
            InlineKeyboardButton("\U0001F4D8 Tiendamia Walmart", callback_data='juegos_stockprecio_sitio_TMWM')
        ],
        [
            InlineKeyboardButton("\U0001F4D8 Tiendamia EBAY", callback_data='juegos_stockprecio_sitio_TMEB'),
            InlineKeyboardButton("\U0001F4D8 Tiendamia Macys", callback_data='juegos_stockprecio_sitio_TMMA')
        ],
        [
            InlineKeyboardButton("\U0001F4D9 Bookdepository", callback_data='juegos_stockprecio_sitio_BOOK'),
            InlineKeyboardButton("\U0001F4D2 365games", callback_data='juegos_stockprecio_sitio_365')
        ],
        [
            InlineKeyboardButton("\U0001F4D2 shop4es", callback_data='juegos_stockprecio_sitio_shop4es'),
            InlineKeyboardButton("\U0001F4D2 shop4world", callback_data='juegos_stockprecio_sitio_shop4world')
        ],
        [
            InlineKeyboardButton("\U0001F4D7 Deepdiscount", callback_data='juegos_stockprecio_sitio_deep'),
            InlineKeyboardButton("\U0001F4D3 Grooves.land", callback_data='juegos_stockprecio_sitio_grooves')
        ],
        [
            InlineKeyboardButton("\U00002B05 Anterior", callback_data='juegos_lista_menu'),
            InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    id = query.edit_message_text(text = "Elegí los juegos a listar", reply_markup=reply_markup)
    context.chat_data["mensaje_id"] = id.message_id
    return LISTA_JUEGOS
   
######### Lista de juegos disponibles de un sitio en orden de precios
def juegos_stockprecio_sitio(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id
    sitio = query.data.split("_")[3]
    texto = f"<b>Juegos disponibles en {constantes.sitio_nom[sitio]}</b>\n\n"
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, sitio_id, precio_actual FROM juegos WHERE sitio = ? AND precio_actual NOT NULL ORDER BY precio_actual',[sitio])
    juegos = cursor.fetchall()
    for j in juegos:
        nombre, sitio_id, precio_actual = j
        texto += f"\U000027A1 <a href='{constantes.sitio_URL[sitio]+str(sitio_id)}'>{html.escape(nombre)}</a> (${precio_actual:.0f})\n"
    keyboard = [
        [
            InlineKeyboardButton("\U00002B05 Anterior", callback_data='juegos_stockprecio'),
            InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    texto_mensaje_div = dividir_texto(f"{texto}\n", 50)
    for t in texto_mensaje_div[0:-2]:
        context.bot.send_message(chat_id = usuario_id, text = t, parse_mode = "HTML", disable_web_page_preview = True)
    context.bot.send_message(chat_id = usuario_id, text = texto_mensaje_div[-1], parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return LISTA_JUEGOS

######### Lista de los últimos juegos agregados
def juegos_lista_ULT(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id
    texto = "<b>Últimos 30 juegos agregados</b>\n\n"
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, sitio, sitio_id, precio_actual FROM juegos ORDER BY fecha_agregado DESC LIMIT 30')
    juegos = cursor.fetchall()
    for j in juegos:
        nombre, sitio, sitio_id, precio_actual = j
        if precio_actual == None:
            texto += f"\U000027A1 <a href='{constantes.sitio_URL[sitio]+str(sitio_id)}'>{html.escape(nombre)}</a> (No disponible)\n"
        else:
            texto += f"\U000027A1 <a href='{constantes.sitio_URL[sitio]+str(sitio_id)}'>{html.escape(nombre)}</a> (${precio_actual:.0f})\n"
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id = usuario_id, text = texto, parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return PRINCIPAL

######### Juegos baratos
def juegos_baratos(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    num = int(query.data.split("_")[2])

    conn = conecta_db()
    cursor = conn.cursor()

    cursor.execute('SELECT nombre, sitio, sitio_id, bgg_id, precio_actual FROM juegos WHERE precio_actual NOT NULL ORDER BY precio_actual LIMIT 30 OFFSET ?',[num])
    baratos = cursor.fetchall()
    barato = ""
    for b in baratos:
        nombre, sitio, sitio_id, bgg_id, precio = b
        barato += f"\U000027A1 <a href='{constantes.sitio_URL['BGG']+str(bgg_id)}'>{html.escape(nombre)}</a> está en <a href='{constantes.sitio_URL[sitio]+sitio_id}'>{constantes.sitio_nom[sitio]}</a> a ${precio:.0f}\n"
    keyboard = [
        [
            InlineKeyboardButton("\U00002795 Siguientes 30 juegos", callback_data='juegos_baratos_'+str(num+30)),
            InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = f"<b>Juegos más baratos en las últimas 24 horas</b>\n\n{barato}", parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return LISTA_JUEGOS

######### Muestra todas las alarmas de un usuario
def alarmas_muestra(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    user = update.callback_query.from_user
    usuario_id = update.callback_query.from_user.id
    query.answer()
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT BGG_id, precio_alarma FROM alarmas WHERE id_persona = ?',[usuario_id])
    alarmas = cursor.fetchall()
    if alarmas == None:
        alar = "No tenés alarmas"
    else:
        alar = []
        for a in alarmas:
            cursor.execute('SELECT DISTINCT nombre FROM juegos WHERE BGG_id = ?',[a[0]])
            juegos = cursor.fetchone()
            alar.append(f"\U000027A1 {html.escape(juegos[0])} (${a[1]:.0f})\n")
        alar.sort()
    texto = "<b>Mis alarmas</b>\n\n"+''.join(alar)
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    texto_mensaje_div = dividir_texto(f"{texto}\n", 50)
    for t in texto_mensaje_div[0:-1]:
        context.bot.send_message(chat_id = usuario_id, text = t, parse_mode = "HTML", disable_web_page_preview = True)
    context.bot.send_message(chat_id = usuario_id, text = texto_mensaje_div[-1], parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)

    return PRINCIPAL

######### Pide que se escriba el nombre del juego
def juego_ver(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = 'Para ver información de un juego, escribí parte del nombre.', reply_markup=reply_markup)
    return JUEGO_ELECCION

######### Muestra un menú con los juegos que coinciden con el texto
def juego_nom(update: Update, context: CallbackContext) -> int:
    nombre_juego = update.message.text
    context.chat_data["nombre_juego"] = nombre_juego
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT nombre, BGG_id FROM juegos WHERE nombre LIKE ? ORDER BY nombre',['%'+nombre_juego+'%'])
    juegos = cursor.fetchall()
    keyboard = []
    if len(juegos) > 10:
        keyboard.append( [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Demasiados resultados, escribí más letras", reply_markup=reply_markup)
        return JUEGO_ELECCION
    if len(juegos) == 0:
        keyboard.append( [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Ningún resultado, escribí otra cosa. Recordá que podés sugerir juegos a monitorear", reply_markup=reply_markup)
        return JUEGO_ELECCION
    
    for j in juegos:
        keyboard.append([InlineKeyboardButton(f'\U000027A1 {j[0]}', callback_data='BGG_'+str(j[1]))])
    keyboard.append( [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    id = update.message.reply_text(text = "Elegí el juego", reply_markup=reply_markup)
    context.chat_data["mensaje_id"] = id.message_id
    return JUEGO

######### Muestra un menú con los juegos que coinciden con el texto cuando viene de otra consulta
def juego_nom_otra(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id
    nombre_juego = context.chat_data["nombre_juego"]
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT nombre, BGG_id FROM juegos WHERE nombre LIKE ? ORDER BY nombre',['%'+nombre_juego+'%'])
    juegos = cursor.fetchall()
    keyboard = []
    for j in juegos:
        keyboard.append([InlineKeyboardButton(f'\U000027A1 {j[0]}', callback_data='BGG_'+str(j[1]))])
    keyboard.append( [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    id = context.bot.send_message(chat_id = usuario_id, text = "Elegí el juego", reply_markup=reply_markup)
    context.chat_data["mensaje_id"] = id.message_id
    return JUEGO

######### Muestra toda la información del juego elegido
def juego_info(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id
    BGG_id = query.data.split("_")[1]
    conn = conecta_db()
    cursor = conn.cursor()
    nombre, texto = texto_info_juego(BGG_id)
    texto += "\n"
    cursor.execute('SELECT precio_alarma, fecha as "[timestamp]" FROM alarmas WHERE BGG_id = ? AND id_persona = ?', [BGG_id,usuario_id])
    alarmas = cursor.fetchone()
    if alarmas == None:
        texto += "No tenés alarmas para este juego.\n"
        keyboard = [
            [InlineKeyboardButton("\U00002795 Agregar alarma", callback_data='alarmas_agregar_precio')],
            [
                InlineKeyboardButton("\U00002B05 Volver al listado", callback_data='juego_nom_otra'),
                InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')
            ]
        ]
    else:
        ala_fech = alarmas[1]
        texto += f"Tenés una alarma para cuando valga menos de ${alarmas[0]:.0f} desde el {ala_fech.day}/{ala_fech.month}/{ala_fech.year} a las {ala_fech.hour}:{ala_fech.minute:02d}.\n"
        keyboard = [
            [
                InlineKeyboardButton("\U00002716 Cambiar alarma", callback_data='alarmas_cambiar_precio'),
                InlineKeyboardButton("\U00002796 Borrar alarma", callback_data='alarmas_borrar')
            ],
            [
                InlineKeyboardButton("\U00002B05 Volver al listado", callback_data='juego_nom_otra'),
                InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')
            ]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    arch = f"graficos/{BGG_id}.png"
    if not os.path.exists(arch):
        arch = "graficos/0000.png"
    arch += f"?f={datetime.now().isoformat()}" # Para evitar que una imagen quede en cache
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    id = context.bot.sendPhoto(chat_id=update.effective_chat.id, photo = constantes.sitio_URL["base"]+arch)
    context.bot.send_message(chat_id = update.effective_chat.id, text = texto, parse_mode="HTML", disable_web_page_preview = False, reply_markup=reply_markup)

    fecha = datetime.now()
    cursor.execute('INSERT INTO usuarios (nombre, id, fecha, accion) VALUES (?,?,?,?)',[update.callback_query.from_user.full_name,usuario_id,fecha,f"Ver juego {nombre}"])
    conn.commit()
    context.chat_data["mensaje_id"] = id.message_id
    context.chat_data["BGG_id"] = BGG_id
    context.chat_data["BGG_nombre"] = nombre
    return ALARMAS

######### Recopila la información del juego elegido
def texto_info_juego(BGG_id):
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id_juego, nombre, sitio, sitio_ID, ranking, dependencia_leng, precio_actual, precio_mejor, fecha_mejor as "[timestamp]" FROM juegos WHERE BGG_id = ?',[BGG_id])
    juegos = cursor.fetchall()
    nombre = juegos[0][1]
    ranking = juegos[0][4]
    dependencia_leng = constantes.dependencia_len[juegos[0][5]]
    link_BGG = constantes.sitio_URL["BGG"]+str(BGG_id)
    texto = f"<b>{html.escape(nombre)}</b>\n\n"
    texto += f"<a href= '{link_BGG}'>Enlace BGG</a> - Ranking: {ranking}\n"
    texto += f"Dependencia del idioma: {dependencia_leng}\n\n"
    texto += "Los precios indicados son <b>finales</b> (incluyen Aduana y correo).\n\n"
    texto_ju = []
    precio_ju = []
    ju = 0
    for j in juegos:
        nombre_sitio = constantes.sitio_nom[j[2]]
        url_sitio = constantes.sitio_URL[j[2]] + j[3]
        precio_actual = j[6]
        precio_mejor = j[7]
        fecha_mejor = j[8]

        if precio_actual == None:
            precio_ju.append(999999)
            texto_ju.append(f"<a href='{url_sitio}'>{nombre_sitio}</a>: No está en stock actualmente, ")
            if precio_mejor == None:
                texto_ju[ju] += "y no lo estuvo en los últimos 15 días.\n"
            else:
                texto_ju[ju] += f"pero el {fecha_mejor.day}/{fecha_mejor.month}/{fecha_mejor.year} tuvo un precio de ${precio_mejor:.0f}.\n"
        else:
            precio_ju.append(precio_actual)
            texto_ju.append(f"<a href='{url_sitio}'>{nombre_sitio}</a>: <b>${precio_actual:.0f}</b> - ")
            if precio_mejor == precio_actual:
                texto_ju[ju] += f"Es el precio más barato de los últimos 15 días.\n"
            else:
                texto_ju[ju] += f"El mínimo para los últimos 15 días fue de ${precio_mejor:.0f} (el {fecha_mejor.day}/{fecha_mejor.month}/{fecha_mejor.year}).\n"
        ju += 1
    if min(precio_ju) != 999999:
        ini = "\U0001F449 "
    else:
        ini = "\U000027A1 "
    texto += ini + '\U000027A1 '.join([x for _, x in sorted(zip(precio_ju,texto_ju))])

    return [nombre, texto]

######### Pide que se ingrese el precio de la alarma
def alarmas_agregar_precio(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    usuario_id = update.callback_query.from_user.id
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    context.bot.send_message(chat_id=update.effective_chat.id, text = "Escribí el precio <b>final</b> (incluyendo Aduana y correo), para que si cuesta menos que eso <b>en cualquier sitio</b>, te llegue la alarma.", parse_mode = "HTML", reply_markup=reply_markup)
    return ALARMAS_NUEVA_PRECIO

######### Guarda la alarma agregada
def alarmas_agregar(update: Update, context: CallbackContext) -> int:
    precio = re.sub("\D", "", update.message.text)
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    usuario_id = update.message.from_user.id
    BGG_id = context.chat_data["BGG_id"]
    nombre = context.chat_data["BGG_nombre"]
    conn = conecta_db()
    cursor = conn.cursor()
    fecha = datetime.now()
    cursor.execute('INSERT INTO alarmas (id_persona, BGG_id, precio_alarma, fecha, sitio) VALUES (?,?,?,?,?)',[usuario_id,BGG_id,precio,fecha,"TODO"])
    conn.commit()
    update.message.reply_text(text = f'Agregaste una alarma para {nombre}. Si el precio es menor a ${precio}, te voy a mandar un mensaje.', reply_markup=reply_markup)
    return PRINCIPAL

######### Pide que se ingrese el precio de la alarma a cambiar
def alarmas_cambiar_precio(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    context.bot.send_message(chat_id=update.effective_chat.id, text = "Escribí el precio <b>final</b> (incluyendo Aduana y correo), para que si cuesta menos que eso <b>en cualquier sitio</b> te llegue la alarma.", parse_mode = "HTML", reply_markup=reply_markup)
    return ALARMAS_CAMBIAR_PRECIO

######### Cambia una alarma
def alarmas_cambiar(update: Update, context: CallbackContext) -> int:
    precio = re.sub("\D", "", update.message.text)
    usuario_id = update.message.from_user.id
    BGG_id = context.chat_data["BGG_id"]
    nombre = context.chat_data["BGG_nombre"]
    conn = conecta_db()
    cursor = conn.cursor()
    fecha = datetime.now()
    cursor.execute('UPDATE alarmas SET precio_alarma = ?, fecha = ? WHERE id_persona = ? AND BGG_id = ?',[precio, fecha, usuario_id, BGG_id])
    conn.commit()

    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(text = f'Cambiaste la alarma para {nombre}. Ahora, si el precio es menor a ${precio}, te mando un mensaje.', reply_markup=reply_markup)
    return PRINCIPAL

######### Borra una alarma
def alarmas_borrar(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id
    BGG_id = context.chat_data["BGG_id"]
    nombre = context.chat_data["BGG_nombre"]
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM alarmas WHERE id_persona = ? AND BGG_id = ?',[usuario_id,BGG_id])
    conn.commit()

    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    context.bot.send_message(chat_id=update.effective_chat.id, text = f'Borraste la alarma para {nombre}.', reply_markup=reply_markup)
    return PRINCIPAL

######### Muestra ayuda
def ayuda(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    texto = '<b>Ayuda</b>\n\n' + \
    '@Monitor_Juegos_bot es un bot de telegram que monitorea precios de juegos desde diversos sitios (Buscalibre, Tiendamia, Bookdepository, 365games, Shop4es, Shop4world, Deepdiscount y Grooves.land) con una frecuencia de entre 15 minutos y 2 horas, dependiendo del número de alarmas del juego. No es un buscador, no sirve para juegos que no estén siendo monitoreados.\n\n' + \
    'Ofrece la posibilidad de agregar alarmas para que te llegue una notificación cuando el precio <b>FINAL EN ARGENTINA</b> de un juego desede cualquier sitio (incluyendo 65% a compras en el exterior, tasa de Aduana y correo) sea menor al que le indicaste. Para borrar la alarma, andá al juego correspondiente.\n\n' + \
    'Para ver la información de un juego en particular, elegí la opción <i>Ver un juego y poner/sacar alarmas</i> y escribí parte de su nombre. Ahí mismo vas a poder agregar alarmas cuando llegue a un determinado precio, o borrarla si lo querés.\n\n' + \
    'Si no está el juego que te interesa, o si encontraste otro lugar donde lo venden, elegí en el menú la opción <i>Sugerir juego a monitorear</i>. Este agregado <b>no</b> es automático.\n\n' + \
    'En <i>Ofertas y juegos en reposición</i> vas a ver todos los juegos que han bajado de precio más del 10% respecto a su promedio de 15 días, y los juegos que ahora están disponibles pero no lo estuvieron por más de 15 días.\n\n' + \
    'Desde cualquier chat o grupo, escribí @Monitor_Juegos_bot y parte del nombre de un juego para ver la información sin salir del chat.\n\n' + \
    'Si un menú no responde, escribí nuevamente /start.\n\n' + \
    'Cualquier duda, mandame un mensaje a @Luis_Olcese.'
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup)
    return PRINCIPAL

######### Muestra las novedades
def novedades(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    texto = '<b>Novedades</b>\n\n' + \
    '08/01/2022: La búsqueda online funciona correctamente.\n\n' + \
    '08/01/2022: Reorganización en los menúes.\n\n' + \
    '08/01/2022: Muestra precios en los listados.\n\n' + \
    '08/01/2022: Cambio en la base de datos que debería acelerar todo.\n\n' + \
    '05/12/2021: Automatizada la descarga de todos los costos de Tiendamia.\n\n' + \
    '23/11/2021: Corrección de error grave en precios que no son originalmente en pesos.\n\n'

    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup)
    return PRINCIPAL

######### Muestra estadísticas de uso
def estadistica(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT (DISTINCT nombre) FROM usuarios WHERE fecha > datetime("now", "-1 days")')
    num_usu = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT (DISTINCT BGG_id) FROM juegos')
    num_jue = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT () FROM juegos')
    num_jue_fu = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT () FROM alarmas')
    num_ala = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT (DISTINCT id_persona) FROM alarmas')
    pers_ala = cursor.fetchone()[0]
    cursor.execute('SELECT BGG_id,COUNT(BGG_id) AS freq FROM alarmas GROUP BY BGG_id ORDER by freq DESC LIMIT 1')
    jue_mas_ala = int(cursor.fetchone()[0])
    cursor.execute('SELECT nombre FROM juegos WHERE BGG_id = ?',[jue_mas_ala])
    mas_ala = cursor.fetchone()[0]
    cursor.execute('SELECT id_juego,MAX(precio) FROM precios WHERE fecha > datetime("now", "-1 days")')
    juego_mas_pr, mas_caro_precio = cursor.fetchone()
    cursor.execute('SELECT nombre FROM juegos WHERE id_juego = ?',[juego_mas_pr])
    mas_caro = cursor.fetchone()[0]
    cursor.execute('SELECT id_juego,MIN(precio) FROM precios WHERE fecha > datetime("now", "-1 days")')
    juego_menos_pr, mas_barato_precio = cursor.fetchone()
    cursor.execute('SELECT nombre FROM juegos WHERE id_juego = ?',[juego_menos_pr])
    mas_barato = cursor.fetchone()[0]
    texto = '<b>Estadística</b>\n\n' + \
    f'En las últimas 24 horas se conectaron {num_usu} personas al bot\n\n' + \
    f'Actualmente se están monitoreando los precios de {num_jue} juegos desde {num_jue_fu} sitios.\n\n' + \
    f'Hay {num_ala} alarmas de {pers_ala} personas distintas. El juego con más alarmas es {html.escape(mas_ala)}.\n\n' + \
    f'El juego monitoreado más caro en las últimas 24 horas fue {html.escape(mas_caro)} (${mas_caro_precio:.0f}) y el más barato {html.escape(mas_barato)} (${mas_barato_precio:.0f}).'

    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup)
    return PRINCIPAL

######### Pide que se escriba un comentario
def comentarios_texto(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text = 'Escribí el comentario o sugerencia que quieras hacer.', reply_markup=reply_markup)
    return COMENTARIOS

######### Manda comentarios
def comentarios_mandar(update: Update, context: CallbackContext) -> int:
    usuario = update.message.from_user.full_name
    comentario = update.message.text
    conn = conecta_db()
    cursor = conn.cursor()
    fecha = datetime.now()
    cursor.execute('INSERT INTO comentarios (usuario, comentario,fecha) VALUES (?,?,?)',[usuario,comentario,fecha])
    conn.commit()

    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text = 'Gracias por el comentario.', reply_markup=reply_markup)
    return PRINCIPAL

######### Pide que se ingrese el juego a monitorear
def sugerir_juego_datos(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text(text = '<b>LEER, HAY CAMBIOS</b>\nEscribí la URL de BGG del juego (es decir https://www.boardgamegeek.com/boardgame/XXXXXXX) y en el renglón siguiente el URL del juego en el sitio donde lo vendan (por el momento Buscalibre, Tiendamia, Bookdepository, 365games, Shop4es, Shop4world, Deepdiscount y Grooves.land).\nEn el caso que agregues un juego de deepdiscount, poné también el peso en libras que informa cuando lo agregás al carrito (o 0 si no lo informa).\n\nEjemplos:\n\nhttps://www.boardgamegeek.com/boardgame/220/high-society\nhttps://www.bookdepository.com/es/High-Society-Dr-Reiner-Knizia/9781472827777\n\nhttps://www.boardgamegeek.com/boardgame/293296/splendor-marvel\nhttps://www.deepdiscount.com/splendor-marvel/3558380055334\n2.43', parse_mode = "HTML", disable_web_page_preview = True)
    return JUEGO_AGREGAR

######### Guarda el juego sugerido
def sugerir_juego(update: Update, context: CallbackContext) -> int:
    usuario_nom = update.message.from_user.full_name
    usuario_id = update.message.from_user.id
    dat = update.message.text.split("\n")

    if len(dat) < 2:
        update.message.reply_text("Por favor, revisá lo que escribiste, tenés que poner el ID de BGG, el URL del juego.")
        return JUEGO_AGREGAR

    url = dat[1]

    if not re.search("tiendamia|bookdepository|buscalibre|365games|shop4es|shop4world|deepdiscount|grooves", url):
        update.message.reply_text("Por favor, revisá lo que escribiste, el sitio tiene que ser Buscalibre, Tiendamia, Bookdepository, 365games, Shop4es, Shop4world, Deepdiscount o Grooves.land")
        return JUEGO_AGREGAR

    if len(dat) == 2 and re.search("deepdiscount", url):
        update.message.reply_text("Cuando agregás un juego de deepdiscount, tenés que poner el peso.")
        return JUEGO_AGREGAR

    if len(dat) == 2:
        peso = None
    BGG_URL = dat[0]
    if len(dat) > 2:
        peso = dat[2]

    conn = conecta_db()
    cursor = conn.cursor()
    fecha = datetime.now()
    cursor.execute('INSERT INTO juegos_sugeridos (usuario_nom, usuario_id, BGG_URL, URL, peso, fecha) VALUES (?,?,?,?,?,?)',[usuario_nom, usuario_id, BGG_URL, url, peso, fecha])
    conn.commit()
    texto = f"{usuario_nom} sugirió el juego {url}"
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={id_aviso}text={texto}'
    response = requests.get(send_text)
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text = 'Gracias por agregar el juego. Va a ser revisado y vas a recibir un mensaje si es aprobado o rechazado.', reply_markup=reply_markup)
    return PRINCIPAL

######### Muestra los juegos en oferta y restock
def ofertas_restock(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id

    conn = conecta_db()
    cursor = conn.cursor()

    texto_of = "<b>Juegos en oferta</b>\n\n"
    cursor.execute('SELECT id_juego,precio_prom,precio_actual FROM ofertas WHERE activa = "Sí"')
    ofertas = cursor.fetchall()
    ofertas_10 = []
    ofertas_15 = []
    ofertas_20 = []
    porc_10 = []
    porc_15 = []
    porc_20 = []
    for o in ofertas:
        cursor.execute('SELECT nombre, sitio, sitio_id, bgg_id FROM juegos WHERE id_juego = ?',[o[0]])
        nombre, sitio, sitio_id, bgg_id = cursor.fetchone()
        precio_prom = o[1]
        precio_actual = o[2]
        porc = (precio_prom - precio_actual) / precio_prom * 100
        if porc >= 20:
            ofertas_20.append(f"\U0001F381 <a href='{constantes.sitio_URL['BGG']+str(bgg_id)}'>{nombre}</a> está en <a href='{constantes.sitio_URL[sitio]+sitio_id}'{constantes.sitio_nom[sitio]}</a> a ${precio_actual:.0f} y el promedio es de ${precio_prom:.0f} ({porc:.0f}% menos)\n")
            porc_20.append(porc)
        elif porc >= 15:
            ofertas_15.append(f"\U000027A1 <a href='{constantes.sitio_URL['BGG']+str(bgg_id)}'>{nombre}</a> está en <a href='{constantes.sitio_URL[sitio]+sitio_id}'{constantes.sitio_nom[sitio]}</a> a ${precio_actual:.0f} y el promedio es de ${precio_prom:.0f} ({porc:.0f}% menos)\n")
            porc_15.append(porc)
        elif porc >= 10:
            ofertas_10.append(f"\U000027A1 <a href='{constantes.sitio_URL['BGG']+str(bgg_id)}'>{nombre}</a> está en <a href='{constantes.sitio_URL[sitio]+sitio_id}'{constantes.sitio_nom[sitio]}</a> a ${precio_actual:.0f} y el promedio es de ${precio_prom:.0f} ({porc:.0f}% menos)\n")
            porc_10.append(porc)

    if ofertas_20:
        texto_of += "<b>Juegos con descuento >20%</b>\n" + "".join([x for _, x in sorted(zip(porc_20,ofertas_20), reverse=True)])+"\n"
    if ofertas_15:
        texto_of += "<b>Juegos con descuento >15%</b>\n" + "".join([x for _, x in sorted(zip(porc_15,ofertas_15), reverse=True)])+"\n"
    if ofertas_10:
        texto_of += "<b>Juegos con descuento >10%</b>\n" + "".join([x for _, x in sorted(zip(porc_10,ofertas_10), reverse=True)])+"\n"

    if texto_of == "<b>Juegos en oferta</b>\n\n":
        texto_of += "No hay ningún juego en oferta\n"

    texto_st = "*Juegos en reposición*\n\n"
    cursor.execute('SELECT id_juego FROM restock WHERE activa = "Sí"')
    restock = cursor.fetchall()
    for r in restock:
        id_juego = r[0]
        cursor.execute('SELECT nombre, sitio, sitio_id, bgg_id, precio_actual FROM juegos WHERE id_juego = ?',[id_juego])
        nombre, sitio, sitio_id, bgg_id, precio_actual = cursor.fetchone()
        texto_st += f"\U000027A1 <a href='{constantes.sitio_URL['BGG']+str(bgg_id)}'>{nombre}</a> está en stock en <a href='{constantes.sitio_URL[sitio]+sitio_id}'{constantes.sitio_nom[sitio]}</a> a ${precio_actual:.0f} (y antes no lo estaba)\n"
    if texto_st == "<b>Juegos en reposición</b>\n\n":
        texto_st = "No hay ningún juego en reposición\n"

    cursor.execute('SELECT id_usuario, tipo_alarma FROM alarmas_ofertas WHERE id_usuario = ?',[usuario_id])
    alarmas_ofertas = cursor.fetchone()
    if alarmas_ofertas == None:
        texto_al = "Cuando haya una oferta o reposición, te puedo mandar un mensaje (solo la primera vez que esté en ese estado).\n"
        keyboard = [
            [
                InlineKeyboardButton("\U00002795 Ofertas", callback_data='mensaje_oferta_1'),
                InlineKeyboardButton("\U00002795 Reposiciones", callback_data='mensaje_oferta_2'),
                InlineKeyboardButton("\U00002795 Ambas", callback_data='mensaje_oferta_3')
            ],
            [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
        ]
    elif (alarmas_ofertas[1] == 3):
        texto_al = "Cuando haya una oferta o reposición, te voy a mandar un mensaje (solo la primera vez que esté en ese estado).\n"
        keyboard = [
            [
                InlineKeyboardButton("\U00002796 Ofertas", callback_data='mensaje_oferta_2'),
                InlineKeyboardButton("\U00002796 Reposiciones", callback_data='mensaje_oferta_1'),
                InlineKeyboardButton("\U00002796 Ninguna", callback_data='mensaje_oferta_0')
            ],
            [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
        ]
    elif (alarmas_ofertas[1] == 1):
        texto_al = "Cuando haya una oferta, te voy a mandar un mensaje (solo la primera vez que esté en ese estado).\n"
        keyboard = [
            [
                InlineKeyboardButton("\U00002796 Ofertas", callback_data='mensaje_oferta_0'),
                InlineKeyboardButton("\U00002795 Reposiciones", callback_data='mensaje_oferta_3')
            ],
            [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
        ]
    elif (alarmas_ofertas[1] == 2):
        texto_al = "Cuando haya una reposición, te voy a mandar un mensaje (solo la primera vez que esté en ese estado).\n"
        keyboard = [
            [
                InlineKeyboardButton("\U00002795 Ofertas", callback_data='mensaje_oferta_3'),
                InlineKeyboardButton("\U00002796 Reposiciones", callback_data='mensaje_oferta_0')
            ],
            [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    texto_mensaje_div = dividir_texto(f"{texto_of}\n{texto_st}\n", 25)
    for t in texto_mensaje_div:
        context.bot.send_message(chat_id = usuario_id, text = t, parse_mode = "HTML", disable_web_page_preview = True)
    context.bot.send_message(chat_id = usuario_id, text = f"{texto_al}", parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return PRINCIPAL

######### Cambiar al aviso de ofertas
def mensaje_oferta(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    tipo_of = int(query.data.split("_")[2])
    usuario_id = update.callback_query.from_user.id

    if (tipo_of == 0):
        conn = conecta_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM alarmas_ofertas WHERE id_usuario = ?',[usuario_id])
        conn.commit()
    else:
        conn = conecta_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id_usuario, tipo_alarma FROM alarmas_ofertas WHERE id_usuario = ?',[usuario_id])
        alarmas_ofertas = cursor.fetchone()
        if alarmas_ofertas == None:
            cursor.execute('INSERT INTO alarmas_ofertas (tipo_alarma, id_usuario) VALUES (?,?)',[tipo_of, usuario_id])
            conn.commit()
        else:
            cursor.execute('UPDATE alarmas_ofertas SET tipo_alarma = ? WHERE id_usuario = ?',[tipo_of, usuario_id])
            conn.commit()
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = f"Tus preferencias se actualizaron", reply_markup=reply_markup)
    return PRINCIPAL

######### Invitame a un cafecito
def cafecito(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    texto = "<b>Invitame a un cafecito</b>\n\nEl objetivo de este bot no es el de generar ganancia, sino de tener una herramienta para comparar precios para la Comunidad Boardgamera Argentina. De todos modos, hay costos de electricidad para mantenerlo funcionando y muchas horas de trabajo encima, así que dejo abierta la posibilidad de quien quiera y pueda haga un aporte monetario.\n\n<b>No hay absolutamente ninguna diferencia en las funciones, ni alarmas, ni nada para quienes hayan aportado y para los que no.</b>\n\n\U00002615 <a href='https://cafecito.app/lolcese'>Invitame a un cafecito</a> \U00002615"
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return PRINCIPAL

######### Responde directamente a las consultas inline
def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    if query == "" or len(query) < 3:
        return

    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT BGG_id FROM juegos WHERE nombre LIKE ? ORDER BY nombre',["%"+query+"%"])
    juegos = cursor.fetchall()
    results = []

    if len(juegos) <= 10:
        for j in juegos:
            BGG_id = j[0]
            nombre, texto = texto_info_juego(j[0])
            arch = f"{BGG_id}.png"
            if not os.path.exists(f"graficos/{arch}"):
                arch = "0000.png"
            imagen = f'{constantes.sitio_URL["base"]}graficos/{arch}?f={datetime.now().isoformat()}' # Para evitar que una imagen quede en cache

            results.append(
                    InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=nombre,
                    # input_message_content = InputTextMessageContent(f"<a href={imagen}>{texto}\n</a>\nPara más información y la posibilidad de poner alarmas, andá a @Monitor_Juegos_bot y escribí /start",
                    input_message_content = InputTextMessageContent(
                                            message_text = f"{texto}\n\nPara más información y la posibilidad de poner alarmas, andá a @Monitor_Juegos_bot y escribí /start",
                                            parse_mode="HTML",
                                            disable_web_page_preview = False)
                    )
            )
        update.inline_query.answer(results)
        fecha = datetime.now()
        cursor.execute('INSERT INTO usuarios (nombre, id, fecha, accion) VALUES (?,?,?,?)',["-",0,fecha,"Inline "+query])
        conn.commit()

######### Handlers
def main() -> PRINCIPAL:
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PRINCIPAL: [
                CallbackQueryHandler(juegos_lista_menu,      pattern='^juegos_lista_menu$'),
                CallbackQueryHandler(ofertas_restock,        pattern='^ofertas_restock$'),
                CallbackQueryHandler(juego_ver,              pattern='^juego_ver$'),
                CallbackQueryHandler(sugerir_juego_datos,    pattern='^sugerir_juego_datos$'),
                CallbackQueryHandler(alarmas_muestra,        pattern='^alarmas_muestra$'),
                CallbackQueryHandler(comentarios_texto,      pattern='^comentarios_texto$'),
                CallbackQueryHandler(novedades,              pattern='^novedades$'),
                CallbackQueryHandler(estadistica,            pattern='^estadistica$'),
                CallbackQueryHandler(cafecito,               pattern='^cafecito$'),
                CallbackQueryHandler(ayuda,                  pattern='^ayuda$'),
                CallbackQueryHandler(inicio,                 pattern='^inicio$'),
                CallbackQueryHandler(mensaje_oferta,         pattern='^mensaje_oferta_'),
            ],
            LISTA_JUEGOS: [
                CallbackQueryHandler(juegos_lista_menu,        pattern='^juegos_lista_menu$'),
                CallbackQueryHandler(juegos_planilla,          pattern='^juegos_planilla$'),
                CallbackQueryHandler(juegos_todos,             pattern='^juegos_todos$'),
                CallbackQueryHandler(juegos_todos_sitio,       pattern='^juegos_todos_sitio_'),
                CallbackQueryHandler(juegos_stockalfab,        pattern='^juegos_stockalfab$'),
                CallbackQueryHandler(juegos_stockalfab_sitio,  pattern='^juegos_stockalfab_sitio_'),
                CallbackQueryHandler(juegos_stockprecio,       pattern='^juegos_stockprecio$'),
                CallbackQueryHandler(juegos_stockprecio_sitio, pattern='^juegos_stockprecio_sitio_'),
                CallbackQueryHandler(juegos_lista_ULT,         pattern='^juegos_lista_ULT$'),
                CallbackQueryHandler(juegos_baratos,           pattern='^juegos_baratos_'),
                CallbackQueryHandler(inicio,                   pattern='^inicio$'),
            ],
            JUEGO_ELECCION: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, juego_nom),
                CallbackQueryHandler(inicio,               pattern='^inicio$'),
            ],
            JUEGO: [
                CallbackQueryHandler(juego_info,        pattern='^BGG_'),
                CallbackQueryHandler(inicio,            pattern='^inicio$'),
            ],
            ALARMAS_NUEVA_PRECIO: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, alarmas_agregar),
                CallbackQueryHandler(inicio,               pattern='^inicio$'),
            ],
            ALARMAS_CAMBIAR_PRECIO: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, alarmas_cambiar),
                CallbackQueryHandler(inicio,               pattern='^inicio$'),
            ],
            ALARMAS: [
                CallbackQueryHandler(alarmas_agregar_precio,   pattern='^alarmas_agregar_precio$'),
                CallbackQueryHandler(alarmas_cambiar_precio,   pattern='^alarmas_cambiar_precio$'),
                CallbackQueryHandler(alarmas_borrar,           pattern='^alarmas_borrar$'),
                CallbackQueryHandler(inicio_borrar,            pattern='^inicio$'),
                CallbackQueryHandler(juego_nom_otra,           pattern='^juego_nom_otra$'),
            ],
            COMENTARIOS: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, comentarios_mandar),
                CallbackQueryHandler(inicio,                   pattern='^inicio$'),
            ],
            JUEGO_AGREGAR: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, sugerir_juego)
            ],

},
    fallbacks=[CommandHandler('start', start)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(InlineQueryHandler(inlinequery))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
