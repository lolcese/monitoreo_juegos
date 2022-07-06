#!/usr/bin/python
# -*- coding: utf-8 -*-
############################################################################################
# # Este bot de telegram es iniciado como un servicio y brinda la posibilidad
# de ver datos de juegos, fijar alarmas, sugerir nuevos juegos a monitorear, etc.
############################################################################################

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (Updater,InlineQueryHandler,CommandHandler,CallbackQueryHandler,ConversationHandler,CallbackContext,MessageHandler,Filters)
from datetime import datetime
import re
import sqlite3
import os
import constantes
from uuid import uuid4
import html
import manda
import hace_grafico
import urllib.request
from decouple import config

bot_token = config('bot_token')
id_aviso = config('id_aviso')

PRINCIPAL, LISTA_JUEGOS, JUEGO_ELECCION, JUEGO, ALARMAS, ALARMAS_NUEVA_PRECIO, ALARMAS_CAMBIAR_PRECIO, COMENTARIOS, OFERTAS, ADMIN = range(10)

######### Conecta con la base de datos
def conecta_db():
    conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

######### Divide texto largo en partes
def dividir_texto(texto, n):
    lineas = texto.split("\n")
    bloque = []
    for i in range(0, len(lineas), n):
        bloque.append("\n".join(lineas[i:i + n]))
    if bloque[-1] == "" or bloque[-1] == "\n":
        bloque.pop()
    return bloque

######### Cuando se elige la opción Inicio
def start(update: Update, context: CallbackContext) -> int:
    usuario = update.message.from_user
    nombre = usuario.full_name
    usuario_id = usuario.id
    fecha = datetime.now()
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO usuarios (nombre, id, fecha, accion) VALUES (?,?,?,?)',[nombre, usuario_id, fecha, "Inicio"])
    conn.commit()
    cursor.execute('SELECT monto, fecha from colaboradores WHERE id_persona = ?',[usuario_id])
    cola = cursor.fetchone()
    txt = ""
    if cola != None:
        txt = f"\U0000FE0F Gracias por colaborar con ${cola[0]} el {cola[1]} \U0000FE0F\n"
    keyboard = menu()
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text = f'Hola, te doy la bienvenida al bot para monitorear precios de juegos. Si apretás un botón y no responde, escribí /start.\n{txt}¿Qué querés hacer?', reply_markup=reply_markup)
    return PRINCIPAL

######### Cuando se elige la opción Inicio (es diferente al anterior porque viene de una query)
def inicio(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario = query.from_user
    nombre = usuario.full_name
    usuario_id = usuario.id
    fecha = datetime.now()
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO usuarios (nombre, id, fecha, accion) VALUES (?,?,?,?)',[nombre, usuario_id, fecha, "Inicio"])
    conn.commit()
    cursor.execute('SELECT monto, fecha from colaboradores WHERE id_persona = ?',[usuario_id])
    cola = cursor.fetchone()
    txt = ""
    if cola != None:
        txt = f"Gracias por colaborar con ${cola[0]} el {cola[1]}\n"
    keyboard = menu()
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = f'Hola, te doy la bienvenida al bot para monitorear precios de juegos. Si apretás un botón y no responde, escribí /start.\n{txt}¿Qué querés hacer?', reply_markup=reply_markup)
    return PRINCIPAL

######### Cuando se elige la opción Inicio (es diferente al anterior porque tiene que borrar el mensaje)
def inicio_borrar(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id
    keyboard = menu()
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    context.bot.send_message(chat_id = update.effective_chat.id, text = 'Hola, te doy la bienvenida al bot para monitorear precios de juegos. Si apretás un botón y no responde, escribí /start.\n¿Qué querés hacer?', reply_markup=reply_markup)
    return PRINCIPAL

######### Menú principal
def menu():
    keyboard = [
        [InlineKeyboardButton("\U0001F4DA Ver Listas de juegos \U0001F4DA", callback_data='juegos_lista_menu')],
        [InlineKeyboardButton("\U0001F3B2 Ver un juego y mis alarmas \U0001F3B2", callback_data='juego_ver')],
        [InlineKeyboardButton("\U00002753 Ayuda e información \U00002753", callback_data='ayuda_info')],
        [InlineKeyboardButton("\U0001F932 Colaborá con el server \U0001F932", callback_data='colaborar')]
    ]
    return keyboard

######### Menú de listas de juegos
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
        [InlineKeyboardButton("\U0001F381 Ofertas y juegos en reposición", callback_data='ofertas_restock')],
        [InlineKeyboardButton("\U0000270F Sugerir juego a monitorear", callback_data='sugerir_juego_datos')],
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        id = query.edit_message_text(text = "Elegí los juegos a listar", reply_markup=reply_markup)
    except:
        return LISTA_JUEGOS

    context.chat_data["mensaje_id"] = id.message_id
    return LISTA_JUEGOS

######### Link a la planilla con todos los juegos
def juegos_planilla(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    texto = """<b>Planilla con todos los juegos</b>
    
Si querés ver una planilla con todos los precios de los juegos, andá <a href="https://docs.google.com/spreadsheets/d/1eh5ckbIl5td0B8aRScxkIZU62MfeMplXxGdlsAWPoVA/edit?usp=sharing">acá</a>.
    
Tené en cuenta que, si bien se actualiza automáticamente, puede tener un desfasaje de 2-3 horas con los precios reales (y 1 hora con los precios que muestra el bot)."""
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
            InlineKeyboardButton("\U0001F4D3 Grooves.land", callback_data='juegos_todos_sitio_grooves')
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
            InlineKeyboardButton("\U0001FA90 Planeton", callback_data='juegos_todos_sitio_planeton'),
        ],
        [
            InlineKeyboardButton("\U000024C2 Miniature Market", callback_data='juegos_todos_sitio_MM'),
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
    texto_mensaje_div = dividir_texto(f"{texto}\n", 30)

    for t in texto_mensaje_div[0:-1]:
        context.bot.send_message(chat_id = usuario_id, text = t, parse_mode = "HTML", disable_web_page_preview = True)
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
            InlineKeyboardButton("\U0001F4D3 Grooves.land", callback_data='juegos_stockalfab_sitio_grooves')
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
            InlineKeyboardButton("\U0001FA90 Planeton", callback_data='juegos_stockalfab_sitio_planeton'),
        ],
        [
            InlineKeyboardButton("\U000024C2 Miniature Market", callback_data='juegos_stockalfab_sitio_MM'),
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
    texto_mensaje_div = dividir_texto(f"{texto}\n", 30)
    for t in texto_mensaje_div[0:-1]:
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
            InlineKeyboardButton("\U0001F4D3 Grooves.land", callback_data='juegos_stockprecio_sitio_grooves')
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
            InlineKeyboardButton("\U0001FA90 Planeton", callback_data='juegos_stockprecio_sitio_planeton'),
        ],
        [
            InlineKeyboardButton("\U000024C2 Miniature Market", callback_data='juegos_stockprecio_sitio_MM'),
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
    texto_mensaje_div = dividir_texto(f"{texto}\n", 30)
    for t in texto_mensaje_div[0:-1]:
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
            cursor.execute('SELECT nombre, precio_actual FROM juegos WHERE BGG_id = ? ORDER BY precio_actual NULLS LAST',[a[0]])
            juegos = cursor.fetchone()
            if juegos[1] == None:
                pre_act = "No disponible"
            else:
                pre_act = f"${juegos[1]:.0f}"
            alar.append(f"\U000027A1 {html.escape(juegos[0])}: ${a[1]:.0f} <i>({pre_act})</i> \n")
        alar.sort()
    texto = "<b>Mis alarmas - alarma (precio actual)</b>\n\n"+''.join(alar)
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    texto_mensaje_div = dividir_texto(f"{texto}\n", 30)
    for t in texto_mensaje_div[0:-1]:
        context.bot.send_message(chat_id = usuario_id, text = t, parse_mode = "HTML", disable_web_page_preview = True)
    context.bot.send_message(chat_id = usuario_id, text = texto_mensaje_div[-1], parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)

    return PRINCIPAL

######### Pide que se escriba el nombre del juego
def juego_ver(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("\U000023F0 Ver mis alarmas", callback_data='alarmas_muestra')],
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
    if len(juegos) > 15:
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
    arch = hace_grafico.grafica(BGG_id, nombre)
    
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    
    if arch != None:
        id = context.bot.sendPhoto(chat_id = update.effective_chat.id, photo = open(arch, "rb"))
        os.remove(arch)
    id = context.bot.send_message(chat_id = update.effective_chat.id, text = texto, parse_mode="HTML", disable_web_page_preview = True, reply_markup=reply_markup)

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
    texto += "Los precios indicados son <b>finales</b> (incluyen envío, aduana y correo).\n\n"
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
                texto_ju[ju] += "Es el precio más barato de los últimos 15 días.\n"
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
    if precio is None or int(precio) == 0:
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("El precio tiene que ser un número", reply_markup=reply_markup)        
        return ALARMAS_NUEVA_PRECIO
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

######### Muestra ayuda e información
def ayuda_info(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("\U00002753 Ayuda", callback_data='ayuda')],
        [InlineKeyboardButton("\U00002757 Novedades del bot", callback_data='novedades')],
        [InlineKeyboardButton("\U0001F4A1 Consejos para comprar", callback_data='consejos')],
        [InlineKeyboardButton("\U0001F4AC Enviar comentarios y sugerencias", callback_data='comentarios_texto')],
        [InlineKeyboardButton("\U0001F522 Estadística", callback_data='estadistica')],
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = "Elegí lo que quieras ver", parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return PRINCIPAL

######### Muestra ayuda
def ayuda(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    texto = """<b>Ayuda</b>
    
@Monitor_Juegos_bot es un bot de telegram que monitorea precios de juegos desde diversos sitios (Buscalibre, Tiendamia, Bookdepository, 365games, Shop4es, Shop4world, Deepdiscount, Grooves.land, Planeton y Miniaturemarket) con una frecuencia de entre 15 minutos y 2 horas, dependiendo del número de alarmas del juego. No es un buscador, no sirve para juegos que no estén siendo monitoreados.
    
Ofrece la posibilidad de agregar alarmas para que te llegue una notificación cuando el precio <b>FINAL EN ARGENTINA</b> de un juego desede cualquier sitio (incluyendo 65% a compras en el exterior, tasa de Aduana y correo) sea menor al que le indicaste. Para borrar la alarma, andá al juego correspondiente.
    
Para ver la información de un juego en particular, elegí la opción <i>Ver un juego y poner/sacar alarmas</i> y escribí parte de su nombre. Ahí mismo vas a poder agregar alarmas cuando llegue a un determinado precio, o borrarla si lo querés.
    
Si no está el juego que te interesa, o si encontraste otro lugar donde lo venden, elegí en el menú la opción <i>Sugerir juego a monitorear</i>. Este agregado <b>no</b> es automático.
    
En <i>Ofertas y juegos en reposición</i> vas a ver todos los juegos que han bajado de precio más del 10% respecto a su promedio de 15 días, y los juegos que ahora están disponibles pero no lo estuvieron por más de 15 días.

Desde cualquier chat o grupo, escribí @Monitor_Juegos_bot y parte del nombre de un juego para ver la información de ese juego sin salir del chat.

Si un menú no responde, escribí nuevamente /start.

<b>@matiliza armó un tutorial sobre todas las funciones del bot, miralo <a href='https://www.dropbox.com/s/15abm8a78x1jcwf/tuto-bot.mov?dl=0'>acá.</a></b>

Cualquier duda, mandame un mensaje a @Luis_Olcese."""
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return PRINCIPAL

######### Muestra consejos
def consejos(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    texto = """<b>Consejos</b>
    
Todos los precios que se muestran acá son finales, considerando los impuestos del 35%, 30% y aduana.
\U000027A1 <a href='https://www.buscalibre.com.ar/'>Buscalibre</a>: Los precios en la página son finales, y los juegos llegan directamente a tu casa sin trámite de aduana. Podés pagar en Ahora 3.
\U000027A1 <a href='https://www.tiendamia.com/'>Tiendamía</a>: Siempre hay cupones que se pueden usar para bajar el precio. Buscalos en los mensajes fijados de https://t.me/comprasjuegosexterior.
\U000027A1 <a href='https://www.bookdepository.com/'>Bookdepository</a>: Si sacás tarjeta de débito de Mercadopago y pagás con eso, no te cobra el 65% de impuestos.
\U000027A1 <a href='https://www.365games.co.uk/'>365games</a> / <a href='https://www.shop4es.com/'>shop4es</a> / <a href='https://www.shop4world.com/'>shop4world</a>: A algunos juegos los mandan por courier, por lo que tenés que pagar un extra al recibirlos.
\U000027A1 <a href='http://grooves.land/'>Grooves.land</a>: Cuidado, los juegos están en alemán. Se puede pagar un par de euros para tener tracking en el envío.
\U000027A1 <a href='http://www.planeton.com/'>Planeton</a>: Los juegos son en español, pero los precios son aproximados (por el envío). Conviene pedir de a varios juegos por vez, así el envío es proporcionalmente más barato.
\U000027A1 <a href='http://www.miniaturemarket.com/'>Miniature Market</a>: Se toma el envío más barato. Conviene pedir de a varios juegos por vez, así el envío es proporcionalmente más barato.
\U000027A1 <a href='https://www.deepdiscount.com/'>Deepdiscount</a>: El envío es caro, pero a veces aparecen ofertas."""

    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return PRINCIPAL

######### Muestra las novedades
def novedades(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    texto = """<b>Novedades</b>
    
03/07/2022: Cambio de server.
02/07/2022: Campaña para cambio de server.
21/05/2022: Agregado Miniature Market.
18/05/2022: Agregado Planeton.
18/05/2022: Agregado un tutorial por @matiliza.
18/05/2022: Muestra precios actuales en las alarmas.
18/05/2022: Resuelta la actualización automática de la planilla.
"""

    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup)
    return PRINCIPAL

######### Muestra |ísticas de uso
def estadistica(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT (DISTINCT nombre) FROM usuarios WHERE fecha > datetime("now", "-1 days")')
    num_usu_24h = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT (DISTINCT nombre) FROM usuarios WHERE fecha > datetime("now", "-30 days")')
    num_usu_30d = cursor.fetchone()[0]
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
    f'En las últimas 24 horas se conectaron {num_usu_24h} personas al bot, y {num_usu_30d} en el último mes.\n\n' + \
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
    texto = f"{usuario} dejó el comentario:\n{comentario}"
    manda.send_message(id_aviso, texto)

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
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    texto = """<b>Sugerir juego a monitorear</b>
    
<b>LEER, HAY CAMBIOS</b>

Escribí la URL de BGG del juego (es decir https://www.boardgamegeek.com/boardgame/XXXXXXX) y en el renglón siguiente el URL del juego en el sitio donde lo vendan (por el momento Buscalibre, Tiendamia, Bookdepository, 365games, Shop4es, Shop4world, Deepdiscount, Grooves.land, Planeton y Miniature Market).
En el caso que agregues un juego de deepdiscount, poné también el peso en libras que informa cuando lo agregás al carrito (o 0 si no lo informa).
<b>En el caso que agregues un juego de Planeton o Miniature Market, poné también el costo (en euros) del envío a Argentina que aparece cuando lo agregás al carrito.</b>

Ejemplos:
<i>Deepdiscount</i>
https://www.boardgamegeek.com/boardgame/293296/splendor-marvel
https://www.deepdiscount.com/splendor-marvel/3558380055334
2.43

<i>Planeton / Miniature Market</i>
https://boardgamegeek.com/boardgame/266192/wingspan
https://www.planetongames.com/es/wingspan-p-8175.html
34.85

<i>Otros</i>
https://www.boardgamegeek.com/boardgame/220/high-society
https://www.bookdepository.com/es/High-Society-Dr-Reiner-Knizia/9781472827777
"""

    query.edit_message_text(text = texto, parse_mode = "HTML", disable_web_page_preview = True, reply_markup=reply_markup)
    return LISTA_JUEGOS

######### Guarda el juego sugerido
def sugerir_juego(update: Update, context: CallbackContext) -> int:
    usuario_nom = update.message.from_user.full_name
    usuario_id = update.message.from_user.id
    dat = update.message.text.split("\n")

    if len(dat) < 2:
        update.message.reply_text("Por favor, revisá lo que escribiste, tenés que poner el URL de BGG y en el renglón siguiente el URL del juego.")
        return LISTA_JUEGOS

    bgg_url = dat[0]
    url = dat[1]

    busca_id = re.search('boardgamegeek\.com\/boardgame(expansion)?\/(.*?)($|\/)',bgg_url)
    if busca_id:
        bgg_id = busca_id.group(2)
    else:
        update.message.reply_text("Por favor, revisá lo que escribiste, tenés que poner el URL de la entrada del juego (no de la versión).")
        return LISTA_JUEGOS

    if not re.search("tiendamia|bookdepository|buscalibre|365games|shop4es|shop4world|deepdiscount|grooves|planeton|miniaturemarket", url):
        update.message.reply_text("Por favor, revisá lo que escribiste, el sitio tiene que ser Buscalibre, Tiendamia, Bookdepository, 365games, Shop4es, Shop4world, Deepdiscount, Grooves.land o Planeton")
        return LISTA_JUEGOS

    sitio_nom, sitio_id = extrae_sitio(url)
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute ('SELECT * FROM juegos WHERE sitio = ? AND sitio_ID = ?',[sitio_nom, sitio_id])
    moni = cursor.fetchall()
    if moni:
        keyboard = [
            [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text = f'Ese juego ya está siendo monitoreado desde {url}.', reply_markup=reply_markup, disable_web_page_preview = True)
        return PRINCIPAL

    if len(dat) == 2 and re.search("deepdiscount", url):
        update.message.reply_text("Cuando agregás un juego de deepdiscount, tenés que poner el peso.")
        return LISTA_JUEGOS

    if len(dat) == 2 and (re.search("planeton", url) or re.search("miniaturemarket", url)):
        update.message.reply_text("Cuando agregás un juego de Planeton, tenés que poner el monto del envío.")
        return LISTA_JUEGOS

    peso = None
    precio_envio = None

    if len(dat) > 2 and re.search("deepdiscount", url):
        peso = dat[2]
    if len(dat) > 2 and (re.search("planeton", url) or re.search("miniaturemarket", url)):
        precio_envio = dat[2]

    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO juegos_sugeridos (usuario_nom, bgg_id, usuario_id, sitio_nom, sitio_id, peso, precio_envio) VALUES (?,?,?,?,?,?,?)',[usuario_nom, bgg_id, usuario_id, sitio_nom, sitio_id, peso, precio_envio])
    conn.commit()
    texto = f"{usuario_nom} sugirió el juego {url}"
    manda.send_message(id_aviso, texto)
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text = 'Gracias por agregar el juego. Va a ser revisado y vas a recibir un mensaje si es aprobado o rechazado.', reply_markup=reply_markup)
    return PRINCIPAL

######### Extrae ID del sitio
def extrae_sitio(sitio_url):
    sitio_id = re.search('buscalibre\.com\.ar\/amazon\?url=.*?\/dp\/(.*?)\/',sitio_url)
    if sitio_id:
        sitio_nom = "BLAM"
        sitio_id = sitio_id[1]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('buscalibre\.com\.ar\/amazon\?url=(.*?)(\s|$|\/|\?|&)',sitio_url)
    if sitio_id:
        sitio_nom = "BLAM"
        sitio_id = sitio_id[1]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('buscalibre\.com\.ar\/(.*?)(\s|$|\?|&)',sitio_url)
    if sitio_id:
        sitio_nom = "BLIB"
        sitio_id = sitio_id[1]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('bookdepository.com\/..\/.*?\/(.*?)(\s|$|\/|\?|&)',sitio_url)
    if sitio_id:
        sitio_nom = "BOOK"
        sitio_id = sitio_id[1]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('tiendamia\.com(\/|.)ar\/producto\?amz=(.*?)(\s|$|\/|\?|&)',sitio_url)
    if sitio_id:
        sitio_nom = "TMAM"
        sitio_id = sitio_id[2]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('tiendamia\.com(\/|.)ar\/productow\?wrt=(.*?)(\s|$|\/|\?|&)',sitio_url)
    if sitio_id:
        sitio_nom = "TMWM"
        sitio_id = sitio_id[2]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('tiendamia\.com(\/|.)ar\/e-?producto?\?ebay=(.*?)(\s|$|\/|\?|&)',sitio_url)
    if sitio_id:
        sitio_nom = "TMEB"
        sitio_id = sitio_id[2]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('365games\.co\.uk\/(.*?)(\?|&|$)',sitio_url)
    if sitio_id:
        sitio_nom = "365"
        sitio_id = sitio_id[1]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('shop4es\.com\/(.*?)(\?|&|$)',sitio_url)
    if sitio_id:
        sitio_nom = "shop4es"
        sitio_id = sitio_id[1]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('shop4world\.com\/(.*?)(\?|&|$)',sitio_url)
    if sitio_id:
        sitio_nom = "shop4world"
        sitio_id = sitio_id[1]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('deepdiscount\.com\/(.*?)(\?|&|$)',sitio_url)
    if sitio_id:
        sitio_nom = "deep"
        sitio_id = sitio_id[1]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('grooves\.land\/(.*?html)',sitio_url)
    if sitio_id:
        sitio_nom = "grooves"
        sitio_id = sitio_id[1]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('planetongames\.com\/(es\/)?(.*?html)',sitio_url)
    if sitio_id:
        sitio_nom = "planeton"
        sitio_id = sitio_id[2]
        return [sitio_nom, sitio_id]

    sitio_id = re.search('miniaturemarket\.com\/(.*?html)',sitio_url)
    if sitio_id:
        sitio_nom = "MM"
        sitio_id = sitio_id[1]
        return [sitio_nom, sitio_id]

######### Muestra los juegos en oferta y restock
def ofertas_restock(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id

    conn = conecta_db()
    cursor = conn.cursor()

    ofertas_10 = []
    ofertas_15 = []
    ofertas_20 = []
    porc_10 = []
    porc_15 = []
    porc_20 = []
    texto_of = "<b>Juegos en oferta</b>\n\n"
    cursor.execute('SELECT nombre, sitio, sitio_id, bgg_id, precio_prom, precio_actual FROM juegos WHERE precio_actual < 0.9 * precio_prom')
    ofertas = cursor.fetchall()
    for o in ofertas:
        nombre, sitio, sitio_id, bgg_id, precio_prom, precio_actual = o
        porc = (precio_prom - precio_actual) / precio_prom * 100
        if porc >= 20:
            ofertas_20.append(f"\U0001F381 <a href='{constantes.sitio_URL['BGG']+str(bgg_id)}'>{html.escape(nombre)}</a> está en <a href='{constantes.sitio_URL[sitio]+sitio_id}'>{constantes.sitio_nom[sitio]}</a> a ${precio_actual:.0f} y el promedio es de ${precio_prom:.0f} ({porc:.0f}% menos)\n")
            porc_20.append(porc)
        elif porc >= 15:
            ofertas_15.append(f"\U000027A1 <a href='{constantes.sitio_URL['BGG']+str(bgg_id)}'>{html.escape(nombre)}</a> está en <a href='{constantes.sitio_URL[sitio]+sitio_id}'>{constantes.sitio_nom[sitio]}</a> a ${precio_actual:.0f} y el promedio es de ${precio_prom:.0f} ({porc:.0f}% menos)\n")
            porc_15.append(porc)
        elif porc >= 10:
            ofertas_10.append(f"\U000027A1 <a href='{constantes.sitio_URL['BGG']+str(bgg_id)}'>{html.escape(nombre)}</a> está en <a href='{constantes.sitio_URL[sitio]+sitio_id}'>{constantes.sitio_nom[sitio]}</a> a ${precio_actual:.0f} y el promedio es de ${precio_prom:.0f} ({porc:.0f}% menos)\n")
            porc_10.append(porc)

    if ofertas_20:
        texto_of += "<b>Juegos con descuento &gt; 20%</b>\n" + "".join([x for _, x in sorted(zip(porc_20,ofertas_20), reverse=True)])+"\n"
    if ofertas_15:
        texto_of += "<b>Juegos con descuento &gt; 15%</b>\n" + "".join([x for _, x in sorted(zip(porc_15,ofertas_15), reverse=True)])+"\n"
    if ofertas_10:
        texto_of += "<b>Juegos con descuento &gt; 10%</b>\n" + "".join([x for _, x in sorted(zip(porc_10,ofertas_10), reverse=True)])+"\n"

    if texto_of == "<b>Juegos en oferta</b>\n\n":
        texto_of += "No hay ningún juego en oferta\n"

    texto_st = "<b>Juegos en reposición</b>\n\n"
    cursor.execute('SELECT nombre, sitio, sitio_id, bgg_id, precio_actual FROM juegos WHERE reposicion = "Sí"')
    restock = cursor.fetchall()
    for r in restock:
        nombre, sitio, sitio_id, bgg_id, precio_actual = r
        if precio_actual != None:
            texto_st += f"\U000027A1 <a href='{constantes.sitio_URL['BGG']+str(bgg_id)}'>{html.escape(nombre)}</a> está en stock en <a href='{constantes.sitio_URL[sitio]+sitio_id}'>{constantes.sitio_nom[sitio]}</a> a ${precio_actual:.0f} (y antes no lo estaba)\n"
    if texto_st == "<b>Juegos en reposición</b>\n\n":
        texto_st = "No hay ningún juego en reposición\n"

    cursor.execute('SELECT tipo_alarma_oferta, tipo_alarma_reposicion FROM alarmas_ofertas WHERE id_usuario = ?',[usuario_id])
    alarmas_ofertas = cursor.fetchone()

    if alarmas_ofertas == None:
        texto_al = "Según tus preferencias actuales, no vas a recibir mensajes cuando haya una oferta, y no vas a recibir mensajes cuando haya reposiciones.\n"
    else:
        texto_al = "Según tus preferencias actuales, "
        tipo_alarma_oferta, tipo_alarma_reposicion = alarmas_ofertas[0]
        if tipo_alarma_oferta == "BLP":
            texto_al += "vas a recibir un mensaje cuando haya una oferta en Buscalibre, Buscalibre Amazon o Planeton, "
        elif tipo_alarma_oferta == "Todo":
            texto_al += "vas a recibir un mensaje cuando haya una oferta en cualquier sitio, "
        else:
            texto_al += "no vas a recibir mensajes cuando haya una oferta, "

        if tipo_alarma_reposicion == "BLP":
            texto_al += "y vas a recibir un mensaje cuando haya una reposición en Buscalibre, Buscalibre Amazon o Planeton."
        elif tipo_alarma_reposicion == "Todo":
            texto_al += "y vas a recibir un mensaje cuando haya una reposición en cualquier sitio."
        else:
            texto_al += "y no vas a recibir mensajes cuando haya reposiciones."

    keyboard = [
        [InlineKeyboardButton("\U0000267B Modificar los avisos", callback_data='modificar_avisos1')],
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    texto_mensaje_div = dividir_texto(f"{texto_of}\n{texto_st}\n", 25)
    for t in texto_mensaje_div:
        context.bot.send_message(chat_id = usuario_id, text = t, parse_mode = "HTML", disable_web_page_preview = True)
    context.bot.send_message(chat_id = usuario_id, text = f"{texto_al}", parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return OFERTAS

######### Paso 1 en la modificación de avisos de ofertas y reposiciones
def modificar_avisos1(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("\U0000267B Solo Buscalibre, Buscalibre Amazon y Planeton", callback_data='modificar_avisos2_BLP')],
        [InlineKeyboardButton("\U0000267B Para todos los sitios", callback_data='modificar_avisos2_Todo')],
        [InlineKeyboardButton("\U0000267B No quiero recibirlas", callback_data='modificar_avisos2_No')],
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = "¿Querés recibir alarmas cuando hay ofertas?", parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return OFERTAS

######### Paso 2 en la modificación de avisos de ofertas y reposiciones
def modificar_avisos2(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    context.chat_data["tipo_oferta"] = query.data.split("_")[2]
    keyboard = [
        [InlineKeyboardButton("\U0000267B Solo Buscalibre, Buscalibre Amazon y Planeton", callback_data='avisos_reposiciones_BLP')],
        [InlineKeyboardButton("\U0000267B Para todos los sitios", callback_data='avisos_reposiciones_Todo')],
        [InlineKeyboardButton("\U0000267B No quiero recibirlas", callback_data='avisos_reposiciones_No')],
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = "¿Querés recibir alarmas cuando haya reposiciones?", parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return OFERTAS

######### Cambiar al aviso de ofertas
def aceptar_ofe_repo(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    tipo_reposicion = query.data.split("_")[2]
    tipo_oferta = context.chat_data["tipo_oferta"]
    usuario_id = update.callback_query.from_user.id
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT tipo_alarma_oferta, tipo_alarma_reposicion FROM alarmas_ofertas WHERE id_usuario = ?',[usuario_id])
    alarmas_ofertas = cursor.fetchone()
    if alarmas_ofertas == None:
        cursor.execute('INSERT INTO alarmas_ofertas (id_usuario, tipo_alarma_oferta, tipo_alarma_reposicion) VALUES (?,?,?)',[usuario_id, tipo_oferta, tipo_reposicion])
        conn.commit()
    else:
        cursor.execute('UPDATE alarmas_ofertas SET tipo_alarma_oferta = ?, tipo_alarma_reposicion = ? WHERE id_usuario = ?',[tipo_oferta, tipo_reposicion, usuario_id])
        conn.commit()
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = "Tus preferencias se actualizaron", reply_markup=reply_markup)
    return PRINCIPAL

######### Colaborar
def colaborar(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM colaboradores')
    n_colaboradores = cursor.fetchone()[0]
    cursor.execute('SELECT usuario_tg, usuario FROM colaboradores WHERE mostrar = "Si" OR mostrar = "Sí"')
    colaboradores = cursor.fetchall()
    cola = []
    for col in colaboradores:
        cola.append(col[1]+" (@" + col[0]+")")

    texto = f"<b>Colaborar con el server</b>\n\nEl objetivo de este bot no es el de generar ganancia, sino de tener una herramienta para comparar precios para la Comunidad Boardgamera Argentina. Por razones de estabilidad se muda a un server pago, y es por eso que pedimos una colaboración para mantenerlo. El costo anual es de unos $6000, y es por eso que buscamos a 30 personas que aporten $200 anuales. Si te interesa, <a href='https://forms.gle/dV7MSopV1aVwG1kC9'>acá</a> están las instrucciones para colaborar.\n\nHay {n_colaboradores} colaboradores: {', '.join(sorted(cola))} y otros que prefieren no aparecer.\n\n<b>No hay absolutamente ninguna diferencia en las funciones, ni alarmas, ni nada para quienes hayan aportado y para los que no.</b>"
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
            nombre, texto = texto_info_juego(j[0])

            results.append(
                    InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=nombre,
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

######### Módulo de administración
def admin(update: Update, context: CallbackContext) -> None:
    usuario = update.message.from_user
    if usuario.id == int(id_aviso):
        texto = 'Hola Luis'
        keyboard = menu()
        reply_markup = InlineKeyboardMarkup(keyboard)
        keyboard = [
            [InlineKeyboardButton("\U00002753 Administrar juegos sugeridos", callback_data='admin_juegos_sugeridos')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup)
        return ADMIN
    else:
        texto = '\U0001F6AB\U0001F6AB No sos un usuario autorizado a administrar, fuera de aquí \U0001F6AB\U0001F6AB'
        keyboard = menu()
        reply_markup = InlineKeyboardMarkup(keyboard)
        keyboard = [
            [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup)
        return PRINCIPAL

######### Administrar juegos sugeridos
def admin_juegos_sugeridos(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id_juego_sugerido, usuario_nom, usuario_id, bgg_id, sitio_nom, sitio_id, peso, precio_envio FROM juegos_sugeridos')
    juegos = cursor.fetchone()
    if juegos is None:
        texto = "No hay juegos sugeridos"
        keyboard = [
            [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    else:
        id_juego_sugerido, usuario_nom, _, bgg_id, sitio_nom, sitio_id, peso, precio_envio = juegos
        texto = f"Usuario: {usuario_nom}\n"
        url = f'https://api.geekdo.com/xmlapi2/thing?id={bgg_id}&stats=1'
        req = urllib.request.Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}) 
        data = urllib.request.urlopen(req).read()
        data = data.decode('utf-8')
        votos = {}

        nombre = html.unescape(re.search('<name type=\"primary\" sortindex=\".*?\" value=\"(.*?)\"',data)[1])
        ranking = html.unescape(re.search('name=\"boardgame\".*?value=\"(.*?)\"',data)[1])

        votos_dep = float(re.search('poll name=\"language_dependence\".*?totalvotes=\"(.*?)\"',data)[1])
        if votos_dep >= 3:
            votos[1] = float(re.search('result level.*? value=\"No necessary in-game text\" numvotes=\"(.*?)\"',data)[1])
            votos[2] = float(re.search('result level.*? value=\"Some necessary text - easily memorized or small crib sheet\" numvotes=\"(.*?)\"',data)[1])
            votos[3] = float(re.search('result level.*? value=\"Moderate in-game text - needs crib sheet or paste ups\" numvotes=\"(.*?)\"',data)[1])
            votos[4] = float(re.search('result level.*? value=\"Extensive use of text - massive conversion needed to be playable\" numvotes=\"(.*?)\"',data)[1])
            votos[5] = float(re.search('result level.*? value=\"Unplayable in another language\" numvotes=\"(.*?)\"',data)[1])
            dependencia_leng = int(max(votos, key=votos.get))
        else:
            dependencia_leng = 0

        texto += f"Nombre: <a href='{constantes.sitio_URL['BGG']+str(bgg_id)}'>{html.escape(nombre)}</a>\n"
        if peso != None:
            texto += f"Peso: {peso}\n"

        if precio_envio != None:
            texto += f"Precio envío: {precio_envio}\n"

        cursor.execute ('SELECT sitio, sitio_ID FROM juegos WHERE BGG_id = ?',[int(bgg_id)])
        moni = cursor.fetchall()
        for m in moni:
            sitio_ya, sitio_id_ya = m
            texto += f"<b>Ya está siendo monitoreado desde <a href='{constantes.sitio_URL[sitio_ya]+str(sitio_id_ya)}'>{constantes.sitio_nom[sitio_ya]}</a></b>\n"
        texto += f"URL: {constantes.sitio_URL[sitio_nom]+sitio_id}"
        keyboard = [
            [InlineKeyboardButton("\U00002705 Aprobar", callback_data=f'admin_sugeridos_{id_juego_sugerido}_aprobar')],
            [InlineKeyboardButton("\U0000274C Rechazar no Argentina", callback_data=f'admin_sugeridos_{id_juego_sugerido}_rechazarnoARG')],
            [InlineKeyboardButton("\U0000274C Rechazar juego equivocado", callback_data=f'admin_sugeridos_{id_juego_sugerido}_rechazarequiv')],
            [InlineKeyboardButton("\U0000274C Rechazar otro", callback_data=f'admin_sugeridos_{id_juego_sugerido}_rechazarotro')],
            [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
        context.chat_data["nombre"] = nombre
        context.chat_data["ranking"] = ranking
        context.chat_data["dependencia_leng"] = dependencia_leng
        return ADMIN

######### Procesa sugeridos
def admin_sugeridos_r(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    sug_id = query.data.split("_")[2]
    estado = query.data.split("_")[3]
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id_juego_sugerido, usuario_nom, usuario_id, bgg_id, sitio_nom, sitio_id, peso, precio_envio FROM juegos_sugeridos WHERE id_juego_sugerido = ?', [sug_id])
    juegos = cursor.fetchone()
    _, _, usuario_id, bgg_id, sitio_nom, sitio_id, peso, precio_envio = juegos

    if estado == "rechazarnoARG":
        manda.send_message(usuario_id, f'Gracias por la sugerencia, pero {constantes.sitio_URL[sitio_nom]+sitio_id} no se envía a Argentina')
    elif estado == "rechazarequiv":
        manda.send_message(usuario_id, f'Gracias por la sugerencia, pero {constantes.sitio_URL[sitio_nom]+sitio_id} no corresponde a <a href="{constantes.sitio_URL["BGG"]+bgg_id}">{nombre}</a>')
    elif estado == "rechazarotro":
        manda.send_message(usuario_id, f'Gracias por la sugerencia, pero <a href="{constantes.sitio_URL["BGG"]+bgg_id}">{nombre}</a> desde {constantes.sitio_URL[sitio_nom]+sitio_id} no puede ser monitoreado')
    elif estado.startswith("aprobar"):
        nombre = context.chat_data["nombre"]
        ranking = context.chat_data["ranking"]
        dependencia_leng = context.chat_data["dependencia_leng"]
        fecha = datetime.now()
        conn.execute ('INSERT INTO juegos (BGG_id,nombre,sitio,sitio_ID,fecha_agregado,ranking, peso, dependencia_leng, prioridad, precio_envio) VALUES (?,?,?,?,?,?,?,?,?,?)',(int(bgg_id), nombre, sitio_nom, sitio_id, fecha, ranking, peso, dependencia_leng, "3", precio_envio))
        conn.commit()
        manda.send_message(usuario_id, f'Gracias por la sugerencia, <a href="{constantes.sitio_URL["BGG"]+bgg_id}">{nombre}</a> desde {constantes.sitio_URL[sitio_nom]+sitio_id} ha sido agregado al monitoreo')
    conn.execute ('DELETE FROM juegos_sugeridos WHERE id_juego_sugerido = ?',[sug_id])
    conn.commit()
    texto = "Juego procesado"
    keyboard = [
        [InlineKeyboardButton("\U00002753 Más juegos sugeridos", callback_data='admin_juegos_sugeridos')],
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = texto, parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
    return ADMIN

######### Handlers
def main() -> PRINCIPAL:
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_args=True),CommandHandler('admin', admin)],
        states={
            PRINCIPAL: [
                CallbackQueryHandler(juegos_lista_menu,        pattern='^juegos_lista_menu$'),
                CallbackQueryHandler(juego_ver,                pattern='^juego_ver$'),
                CallbackQueryHandler(sugerir_juego_datos,      pattern='^sugerir_juego_datos$'),
                CallbackQueryHandler(comentarios_texto,        pattern='^comentarios_texto$'),
                CallbackQueryHandler(ayuda_info,               pattern='^ayuda_info$'),
                CallbackQueryHandler(novedades,                pattern='^novedades$'),
                CallbackQueryHandler(estadistica,              pattern='^estadistica$'),
                CallbackQueryHandler(colaborar,                pattern='^colaborar$'),
                CallbackQueryHandler(ayuda,                    pattern='^ayuda$'),
                CallbackQueryHandler(consejos,                 pattern='^consejos$'),
                CallbackQueryHandler(inicio,                   pattern='^inicio$'),
            ],  
            LISTA_JUEGOS: [
                CallbackQueryHandler(ofertas_restock,          pattern='^ofertas_restock$'),
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
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, sugerir_juego)
            ],
            JUEGO_ELECCION: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, juego_nom),
                CallbackQueryHandler(alarmas_muestra,          pattern='^alarmas_muestra$'),
                CallbackQueryHandler(inicio,                   pattern='^inicio$'),
            ],
            JUEGO: [
                CallbackQueryHandler(juego_info,               pattern='^BGG_'),
                CallbackQueryHandler(inicio,                   pattern='^inicio$'),
            ],
            ALARMAS_NUEVA_PRECIO: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, alarmas_agregar),
                CallbackQueryHandler(inicio,                   pattern='^inicio$'),
            ],
            ALARMAS_CAMBIAR_PRECIO: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, alarmas_cambiar),
                CallbackQueryHandler(inicio,                   pattern='^inicio$'),
            ],
            ALARMAS: [
                CallbackQueryHandler(alarmas_agregar_precio,   pattern='^alarmas_agregar_precio$'),
                CallbackQueryHandler(alarmas_cambiar_precio,   pattern='^alarmas_cambiar_precio$'),
                CallbackQueryHandler(alarmas_borrar,           pattern='^alarmas_borrar$'),
                CallbackQueryHandler(inicio_borrar,            pattern='^inicio$'),
                CallbackQueryHandler(juego_nom_otra,           pattern='^juego_nom_otra$'),
            ],
            OFERTAS: [
                CallbackQueryHandler(modificar_avisos1,        pattern='^modificar_avisos1_'),
                CallbackQueryHandler(modificar_avisos2,        pattern='^modificar_avisos2_'),
                CallbackQueryHandler(aceptar_ofe_repo,         pattern='^aceptar_ofertas_reposiciones$'),
                CallbackQueryHandler(inicio,                   pattern='^inicio$'),
            ],
            COMENTARIOS: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, comentarios_mandar),
                CallbackQueryHandler(inicio,                   pattern='^inicio$'),
            ],
            ADMIN: [
                CallbackQueryHandler(admin_juegos_sugeridos,   pattern='^admin_juegos_sugeridos$'),
                CallbackQueryHandler(admin_sugeridos_r,        pattern='^admin_sugeridos_'),
                CallbackQueryHandler(inicio,                   pattern='^inicio$'),
            ],
        },
    fallbacks=[CommandHandler('start', start, pass_args=True),CommandHandler('admin', admin)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(InlineQueryHandler(inlinequery))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

#https://t.me/Monitor_Juegos_bot?start=test
#dispatcher.add_handler(CommandHandler('hello', SayHello, pass_args=True))