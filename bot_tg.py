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
import os.path
import path
from uuid import uuid4
import requests

os.chdir(path.actual)
bot_token = os.environ.get('bot_token')
id_aviso = os.environ.get('id_aviso')

PRINCIPAL, LISTA_JUEGOS, JUEGO_ELECCION, JUEGO, ALARMAS, ALARMAS_NUEVA_PRECIO, ALARMAS_CAMBIAR_PRECIO, COMENTARIOS, JUEGO_AGREGAR = range(9)

######### Conecta con la base de datos
def conecta_db():
    conn = sqlite3.connect(constantes.db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    return conn

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
    update.message.reply_text(f'Hola {usuario.first_name}, te doy la bienvenida al bot para monitorear precios de juegos. ¿Qué querés hacer?', parse_mode = "Markdown", reply_markup=reply_markup)
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
    query.edit_message_text(f'Hola {usuario.first_name}, te doy la bienvenida al bot para monitorear precios de juegos. ¿Qué querés hacer?', parse_mode = "Markdown", reply_markup=reply_markup)
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
    context.bot.send_message(chat_id=update.effective_chat.id, text = f'Hola {usuario.first_name}, te doy la bienvenida al bot para monitorear precios de juegos. ¿Qué querés hacer?', parse_mode = "Markdown", reply_markup=reply_markup)
    return PRINCIPAL

######### Menú principal
def menu():
    keyboard = [
        [InlineKeyboardButton("\U0001F4DA Lista de juegos monitoreados", callback_data='juegos_lista')],
        [InlineKeyboardButton("\U0001F4B2 30 juegos baratos", callback_data='juegos_baratos')],
        # [InlineKeyboardButton("\U0001F947 30 mejores juegos de BGG", callback_data='juegos_BGG')],
        [InlineKeyboardButton("\U0001F3B2 Ver un juego y poner alarmas", callback_data='juego_ver')],
        [InlineKeyboardButton("\U000023F0 Ver mis alarmas", callback_data='alarmas_muestra')],
        [InlineKeyboardButton("\U0001F381 Ofertas y juegos en reposición", callback_data='ofertas_restock')],
        [InlineKeyboardButton("\U0001F522 Estadística", callback_data='estadistica')],
        [InlineKeyboardButton("\U0000270F Sugerir juego a monitorear", callback_data='sugerir_juego_datos')],
        [InlineKeyboardButton("\U0001F4AC Comentarios y sugerencias", callback_data='comentarios_texto')],
        [InlineKeyboardButton("\U00002757 Novedades", callback_data='novedades')],
        [InlineKeyboardButton("\U00002753 Ayuda", callback_data='ayuda')]
    ]
    return keyboard

######### Listas de juegos 
def juegos_lista(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("\U0001F4DA Todos", callback_data='juegos_lista_TODO')],
        [InlineKeyboardButton("\U0001F4D5 Buscalibre", callback_data='juegos_lista_sitio_BLIB')],
        [InlineKeyboardButton("\U0001F4D5 Buscalibre Amazon", callback_data='juegos_lista_sitio_BLAM')],
        [InlineKeyboardButton("\U0001F4D8 Tiendamia Amazon", callback_data='juegos_lista_sitio_TMAM')],
        [InlineKeyboardButton("\U0001F4D8 Tiendamia Walmart", callback_data='juegos_lista_sitio_TMWM')],
        [InlineKeyboardButton("\U0001F4D8 Tiendamia EBAY", callback_data='juegos_lista_sitio_TMEB')],
        [InlineKeyboardButton("\U0001F4D9 Bookdepository", callback_data='juegos_lista_sitio_BOOK')],
        [InlineKeyboardButton("\U0001F4D2 365games", callback_data='juegos_lista_sitio_365')],
        [InlineKeyboardButton("\U0001F4D2 shop4es", callback_data='juegos_lista_sitio_shop4es')],
        [InlineKeyboardButton("\U0001F4D2 shop4world", callback_data='juegos_lista_sitio_shop4world')],
        [InlineKeyboardButton("\U0001F4D7 Deepdiscount", callback_data='juegos_lista_sitio_deep')],
        [InlineKeyboardButton("\U0001F5DE Últimos 30 agregados", callback_data='juegos_lista_ULT')],
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    id = query.edit_message_text(text = "Elegí los juegos a listar", reply_markup=reply_markup)
    context.chat_data["mensaje_id"] = id.message_id
    return LISTA_JUEGOS

######### Lista de todos los juegos
def juegos_lista_TODO(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id   
    texto = "*Todos los juegos monitoreados*\n\n"
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT nombre FROM juegos ORDER BY nombre')
    juegos = cursor.fetchall()
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    cont = 0
    for j in juegos:
        texto += f"\U000027A1 {j[0]}\n"
        if cont % 150 == 0 and cont != 0:
            context.bot.send_message(chat_id = usuario_id, text = texto, parse_mode = "Markdown")
            texto = ""
        cont += 1
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id = usuario_id, text = texto, parse_mode = "Markdown", reply_markup=reply_markup)
    return PRINCIPAL

######### Lista de juegos de un sitio
def juegos_lista_sitio(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id   
    sitio = query.data.split("_")[3]
    texto = f"*Juegos monitoreados en {constantes.sitio_nom[sitio]}*\n\n"
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, sitio_id FROM juegos WHERE sitio = ? ORDER BY nombre',[sitio])
    juegos = cursor.fetchall()
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    cont = 0
    for j in juegos:
        nombre, sitio_id = j
        texto += f"\U000027A1 [{nombre}]({constantes.sitio_URL[sitio]+str(sitio_id)})\n"
        if cont % 100 == 0 and cont != 0:
            context.bot.send_message(chat_id = usuario_id, text = texto, parse_mode = "Markdown")
            texto = ""
        cont += 1
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id = usuario_id, text = texto, parse_mode = "Markdown", reply_markup=reply_markup, disable_web_page_preview = True)
    return PRINCIPAL

######### Lista de los últimos juegos agregados
def juegos_lista_ULT(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id   
    texto = f"*Últimos 30 juegos agregados*\n\n"
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, sitio, sitio_id FROM juegos ORDER BY fecha_agregado DESC LIMIT 30')
    juegos = cursor.fetchall()
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    cont = 0
    for j in juegos:
        nombre, sitio, sitio_id = j
        texto += f"\U000027A1 [{nombre}]({constantes.sitio_URL[sitio]+str(sitio_id)})\n"
        if cont % 150 == 0 and cont != 0:
            context.bot.send_message(chat_id = usuario_id, text = texto, parse_mode = "Markdown")
            texto = ""
        cont += 1
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id = usuario_id, text = texto, parse_mode = "Markdown", reply_markup=reply_markup, disable_web_page_preview = True)
    return PRINCIPAL

######### Muestra todas las alarmas de un usuario
def alarmas_muestra(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    user = update.callback_query.from_user
    usuario_id = update.callback_query.from_user.id  
    query.answer()
    texto = ""
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT BGG_id, precio_alarma FROM alarmas WHERE id_persona = ?',[usuario_id])
    alarmas = cursor.fetchall()
    alar = []
    for a in alarmas:
        cursor.execute('SELECT DISTINCT nombre FROM juegos WHERE BGG_id = ?',[a[0]])
        juegos = cursor.fetchone()
        alar.append("\U000027A1 {0} (${1:.0f})\n".format(juegos[0],a[1]))
    alar.sort()
    cont = 0
    for a in alar:
        texto += a
        if cont % 100 == 0 and cont != 0:
            context.bot.send_message(chat_id = usuario_id, text = texto, parse_mode = "Markdown")
            texto = ""
        cont += 1
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = f"*Mis alarmas*\n\n{texto}", parse_mode = "Markdown", reply_markup=reply_markup)
    return PRINCIPAL

######### Juegos baratos
def juegos_baratos(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    conn = conecta_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id_juego, min(precio) FROM precios WHERE (precio NOT NULL AND fecha > datetime("now", "-1 days", "localtime")) group by id_juego ORDER BY min(precio) LIMIT 30')
    baratos = cursor.fetchall()
    barato = ""
    for b in baratos:
        id_juego, precio = b
        cursor.execute('SELECT nombre, sitio, sitio_id, bgg_id FROM juegos WHERE id_juego = ?',[id_juego])
        nombre, sitio, sitio_id, bgg_id = cursor.fetchone()
        barato += f"\U000027A1 [{nombre}]({constantes.sitio_URL['BGG']+str(bgg_id)}) está en [{constantes.sitio_nom[sitio]}]({constantes.sitio_URL[sitio]+sitio_id}) a ${precio:.0f}\n"
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = f"*Juegos más baratos en las últimas 24 horas*\n\n{barato}", parse_mode = "Markdown", reply_markup=reply_markup, disable_web_page_preview = True)
    return PRINCIPAL

######### Juegos de BGG
# def juegos_BGG(update: Update, context: CallbackContext) -> int:
#     query = update.callback_query
#     query.answer()

#     conn = conecta_db()
#     cursor = conn.cursor()

#     cursor.execute('SELECT id_juego FROM juegos ORDER BY ranking LIMIT 30')
#     ranking = cursor.fetchall()
#     rank = ""
#     for r in ranking:
#         id_juego = r
#         cursor.execute('SELECT nombre, sitio, sitio_id, BGG_id FROM juegos WHERE id_juego = ?',[id_juego])
#         nombre, sitio, sitio_id, BGG_id = cursor.fetchone()
#         rank += f"\U000027A1 [{nombre}]({constantes.sitio_URL['BGG']+str(BGG_id)}) está en [{constantes.sitio_nom[sitio]}]({constantes.sitio_URL[sitio]+sitio_id}) a ${precio:.0f}\n"
#     keyboard = [
#         [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     query.edit_message_text(text = f"*Juegos con mejor ranking en BGG*\n\n{rank}", parse_mode = "Markdown", reply_markup=reply_markup, disable_web_page_preview = True)
#     return PRINCIPAL

######### Pide que se escriba el nombre del juego
def juego_ver(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text(text = 'Para ver información de un juego, escribí al menos 3 letras del mismo.', parse_mode = "Markdown")
    return JUEGO_ELECCION

######### Muestra un menú con los juegos que coinciden con el texto
def juego_nom(update: Update, context: CallbackContext) -> int:
    nombre_juego = update.message.text
    if len(nombre_juego) < 3:
        update.message.reply_text("Escribí al menos 3 letras")    
        return JUEGO_ELECCION
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT nombre, BGG_id FROM juegos WHERE nombre LIKE ? ORDER BY nombre',['%'+nombre_juego+'%'])
    juegos = cursor.fetchall()
    if len(juegos) > 10:
        update.message.reply_text("Demasiados resultados, escribí más letras")    
        return JUEGO_ELECCION
    if len(juegos) == 0:
        update.message.reply_text("Ningún resultado, escribí otra cosa. Recordá que podés sugerir juegos a monitorear.")
        return JUEGO_ELECCION
    keyboard = []
    for j in juegos:
        keyboard.append([InlineKeyboardButton(f'\U000027A1 {j[0]}', callback_data='BGG_'+str(j[1]))])

    keyboard.append( [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    id = update.message.reply_text(text = "Elegí el juego", parse_mode = "Markdown", reply_markup=reply_markup)
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
            [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
        ]
    else:
        ala_fech = alarmas[1]
        texto += f"Tenés una alarma para cuando valga menos de ${alarmas[0]:.0f} desde el {ala_fech.day}/{ala_fech.month}/{ala_fech.year} a las {ala_fech.hour}:{ala_fech.minute:02d}.\n"
        keyboard = [
            [InlineKeyboardButton("\U00002716 Cambiar alarma", callback_data='alarmas_cambiar_precio')],
            [InlineKeyboardButton("\U00002796 Borrar alarma", callback_data='alarmas_borrar')],
            [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    arch = f"graficos/{BGG_id}.png"
    if not os.path.exists(arch):
        arch = "graficos/0000.png"
    arch += f"?f={datetime.now().isoformat()}" # Para evitar que una imagen quede en cache
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    id = context.bot.sendPhoto(chat_id=update.effective_chat.id, photo = constantes.sitio_URL["base"]+arch, caption=texto, parse_mode="Markdown", reply_markup=reply_markup)
    fecha = datetime.now()
    cursor.execute('INSERT INTO usuarios (nombre, id, fecha, accion) VALUES (?,?,?,?)',[update.callback_query.from_user.full_name,usuario_id,fecha,f"Ver juego {nombre}"])
    conn.commit()
    context.chat_data["mensaje_id"] = id.message_id
    context.chat_data["BGG_id"] = BGG_id
    context.chat_data["BGG_nombre"] = nombre
    return ALARMAS

######### Muestra toda la información del juego elegido
def texto_info_juego(BGG_id):
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id_juego, nombre, sitio, sitio_ID, ranking FROM juegos WHERE BGG_id = ?',[BGG_id])
    juegos = cursor.fetchall()
    nombre = juegos[0][1]
    ranking = juegos[0][4]
    link_BGG = constantes.sitio_URL["BGG"]+str(BGG_id)
    texto = f"*{nombre}*\n\n"
    texto += f"[Enlace BGG]({link_BGG}) - Ranking: {ranking}\n\n"
    texto += "Los precios indicados son *finales* (incluyen Aduana y correo).\n\n"
    texto_ju = []
    precio_ju = []
    ju = 0
    for j in juegos:
        nombre_sitio = constantes.sitio_nom[j[2]]
        url_sitio = constantes.sitio_URL[j[2]] + j[3]
        id_juego = j[0]
        if nombre_sitio == "deep":
            aclar = " El precio final no es exacto. Podría variar unos ± U$S 2."
        else:
            aclar = ""
        cursor.execute('SELECT precio FROM precios WHERE id_juego = ? ORDER BY fecha DESC LIMIT 1', [id_juego])
        ult_precio = cursor.fetchone()
        if ult_precio == None:
            precio_ju.append(999999)
            texto_ju.append(f"[{nombre_sitio}]({url_sitio}): Está en la base de datos del bot pero todavía no intenté buscar el precio, en los próximos 30 minutos debería aparecer.\n")
        else:
            ult_precio = ult_precio[0]
            if ult_precio == None:
                precio_ju.append(999999)
                texto_ju.append(f"[{nombre_sitio}]({url_sitio}): No está en stock actualmente, ")
                cursor.execute('SELECT precio, fecha as "[timestamp]" FROM precios WHERE id_juego = ? AND precio NOT NULL AND (fecha BETWEEN datetime("now", "-15 days", "localtime") AND datetime("now", "localtime")) ORDER BY fecha DESC LIMIT 1', [id_juego])
                ult_val = cursor.fetchone()
                if ult_val == None:
                    texto_ju[ju] += "y no lo estuvo en los últimos 15 días.\n"
                else:
                    ult_prec = ult_val[0]
                    ult_fech = ult_val[1]
                    texto_ju[ju] += f"pero el {ult_fech.day}/{ult_fech.month}/{ult_fech.year} tuvo un precio de ${ult_prec:.0f}.{aclar}\n"
            else:
                precio_ju.append(ult_precio)
                texto_ju.append(f"[{nombre_sitio}]({url_sitio}): *${ult_precio:.0f}* - ")
                cursor.execute('SELECT precio,fecha as "[timestamp]" FROM precios WHERE id_juego = ? AND precio NOT NULL AND (fecha BETWEEN datetime("now", "-15 days", "localtime") AND datetime("now", "localtime")) ORDER BY precio,fecha DESC LIMIT 1', [id_juego])
                min_reg = cursor.fetchone()
                min_precio = min_reg[0]
                if min_precio == ult_precio:
                    texto_ju[ju] += f"Es el precio más barato de los últimos 15 días.{aclar}\n"
                else:
                    min_fech = min_reg[1]
                    texto_ju[ju] += f"El mínimo para los últimos 15 días fue de ${min_precio:.0f} (el {min_fech.day}/{min_fech.month}/{min_fech.year}).{aclar}\n"    
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
    usuario_id = update.callback_query.from_user.id   
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    context.bot.send_message(chat_id=update.effective_chat.id, text = "Escribí el precio *final* (incluyendo Aduana y correo), para que si cuesta menos que eso *en cualquier sitio* te llegue la alarma.", parse_mode = "Markdown")
    return ALARMAS_NUEVA_PRECIO

######### Guarda la alarma agregada
def alarmas_agregar(update: Update, context: CallbackContext) -> int:
    precio = re.sub("\D", "", update.message.text)
    usuario_id = update.message.from_user.id
    BGG_id = context.chat_data["BGG_id"]
    nombre = context.chat_data["BGG_nombre"]
    conn = conecta_db()
    cursor = conn.cursor()
    fecha = datetime.now()
    cursor.execute('INSERT INTO alarmas (id_persona, BGG_id, precio_alarma, fecha, sitio) VALUES (?,?,?,?,?)',[usuario_id,BGG_id,precio,fecha,"TODO"])
    conn.commit()
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text = f'Agregaste una alarma para {nombre}. Si el precio es menor a ${precio}, te mando un mensaje.', parse_mode = "Markdown", reply_markup=reply_markup)
    return PRINCIPAL

######### Pide que se ingrese el precio de la alarma a cambiar
def alarmas_cambiar_precio(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id   
    context.bot.deleteMessage(chat_id = usuario_id, message_id = context.chat_data["mensaje_id"])
    context.bot.send_message(chat_id=update.effective_chat.id, text = "Escribí el precio *final* (incluyendo Aduana y correo), para que si cuesta menos que eso *en cualquier sitio* te llegue la alarma.", parse_mode = "Markdown")
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

    update.message.reply_text(text = f'Cambiaste la alarma para {nombre}. Ahora, si el precio es menor a ${precio}, te mando un mensaje.', parse_mode = "Markdown", reply_markup=reply_markup)
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
    context.bot.send_message(chat_id=update.effective_chat.id, text = f'Borraste la alarma para {nombre}.', parse_mode = "Markdown", reply_markup=reply_markup)
    return PRINCIPAL

######### Muestra ayuda
def ayuda(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    texto = '*Ayuda*\n\n' + \
    '@Monitor\_Juegos\_bot es un bot de telegram que monitorea precios de juegos desde diversos sitios  (por el momento Buscalibre, Tiendamia, Bookdepository, 365games, shop4es, shop4world y deepdiscount) con una frecuencia de 30 minutos. No es un buscador, no sirve para juegos que no estén siendo monitoreados.\n\n' + \
    'Ofrece la posibilidad de agregar alarmas para que te llegue una notificación cuando el precio *FINAL EN ARGENTINA* de un juego desede cualquier sitio (incluyendo 65% a compras en el exterior, tasa de Aduana y correo) sea menor al que le indicaste. Para borrar la alarma, andá al juego correspondiente.\n\n' + \
    'Para ver la información de un juego en particular, elegí la opción _Ver un juego_ y escribí parte de su nombre. Ahí mismo vas a poder agregar alarmas cuando llegue a un determinado precio.\n\n' + \
    'Si no está el juego que te interesa, o si encontraste otro lugar donde lo venden, elegí en el menú la opción _Sugerir juego a monitorear_. Este agregado *no* es automático.\n\n' + \
    'En _Ofertas y juegos en reposición_ vas a ver todos los juegos que han bajado de precio más del 10% respecto a su promedio de 15 días, y los juegos que ahora están disponibles pero no lo estuvieron por más de 15 días.\n\n' + \
    'Desde cualquier chat o grupo, escribí @Monitor\_Juegos\_bot y parte del nombre de un juego para ver la información sin salir del chat (sin el gráfico por el momento).\n\n' + \
    'Si un menú no responde, escribí nuevamente /start.\n\n' + \
    'Cualquier duda, mandame un mensaje a @Luis\_Olcese.'
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = texto, parse_mode = "Markdown", reply_markup=reply_markup)
    return PRINCIPAL

######### Muestra las novedades
def novedades(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    texto = '*Novedades*\n\n' + \
    '05/08/2021: Muestra los links al sitio de cada juego en los listados.\n\n' + \
    '04/08/2021: Muestra los links a BGG en los listados de ofertas.\n\n' + \
    '01/08/2021: Cuando se ve un juego, los precios salen ordenados.\n\n' + \
    '01/08/2021: La búsqueda inline muestra imágenes.\n\n' + \
    '31/07/2021: Se actualizan automáticamente las cotizaciones de las divisas.\n\n' + \
    '30/07/2021: Muestra ranking de BGG y los 30 juegos más baratos.\n\n'

    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = texto, parse_mode = "Markdown", reply_markup=reply_markup)
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
    texto = '*Estadística*\n\n' + \
    f'En las últimas 24 horas se conectaron {num_usu} personas al bot\n\n' + \
    f'Actualmente se están monitoreando los precios de {num_jue} juegos desde {num_jue_fu} sitios.\n\n' + \
    f'Hay {num_ala} alarmas de {pers_ala} personas distintas. El juego con más alarmas es {mas_ala}.\n\n' + \
    f'El juego monitoreado más caro en las últimas 24 horas fue {mas_caro} (${mas_caro_precio:.0f}) y el más barato {mas_barato} (${mas_barato_precio:.0f}).'

    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = texto, parse_mode = "Markdown", reply_markup=reply_markup)
    return PRINCIPAL

######### Muestra estadísticas de uso
def comentarios_texto(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text(text = 'Escribí el comentario o sugerencia que quieras hacer.', parse_mode = "Markdown")
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
    update.message.reply_text(text = 'Gracias por el comentario.', parse_mode = "Markdown", reply_markup=reply_markup)
    return PRINCIPAL

######### Pide que se ingrese el juego a monitorear
def sugerir_juego_datos(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text(text = 'Escribí la URL de BGG del juego (https://www.boardgamegeek.com/boardgame/XXXXXXX), una coma y el URL del juego en el sitio donde lo vendan (por el momento Buscalibre, Tiendamia, Bookdepository, 365games, shop4es, shop4world y deepdiscount).\n\nPor ejemplo https://www.boardgamegeek.com/boardgame/220/high-society , https://www.bookdepository.com/es/High-Society-Dr-Reiner-Knizia/9781472827777', parse_mode = "Markdown", disable_web_page_preview = True)
    return JUEGO_AGREGAR

######### Guarda el juego sugerido
def sugerir_juego(update: Update, context: CallbackContext) -> int:
    usuario_nom = update.message.from_user.full_name
    usuario_id = update.message.from_user.id
    dat = update.message.text.split(",")
    if len(dat) != 2:
        update.message.reply_text("Por favor, revisá lo que escribiste, tenés que poner el ID de BGG, el URL del juego.")    
        return JUEGO_AGREGAR
    BGG_URL = dat[0]
    url = dat[1]

    conn = conecta_db()
    cursor = conn.cursor()
    fecha = datetime.now()
    cursor.execute('INSERT INTO juegos_sugeridos (usuario_nom, usuario_id, BGG_URL, URL, fecha) VALUES (?,?,?,?,?)',[usuario_nom,usuario_id,BGG_URL,url,fecha])
    conn.commit()
    texto = f"{usuario_nom} sugirió el juego {url}"
    # update.bot.sendMessage(chat_id = id_aviso, text = texto, parse_mode = "Markdown")
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={id_aviso}&parse_mode=Markdown&text={texto}'
    response = requests.get(send_text)
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text = 'Gracias por la sugerencia. Va a ser revisada y vas a recibir un mensaje si es aprobada o rechazada.', parse_mode = "Markdown", reply_markup=reply_markup)
    return PRINCIPAL

######### Muestra los juegos en oferta y restock
def ofertas_restock(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id 

    conn = conecta_db()
    cursor = conn.cursor()

    texto_of = ""
    cursor.execute('SELECT id_juego,precio_prom,precio_actual FROM ofertas WHERE activa = "Sí"')
    ofertas = cursor.fetchall()
    for o in ofertas:
        cursor.execute('SELECT nombre, sitio, sitio_id, bgg_id FROM juegos WHERE id_juego = ?',[o[0]])
        nombre, sitio, sitio_id, bgg_id = cursor.fetchone()
        precio_prom = o[1]
        precio_actual = o[2]
        porc = (precio_prom - precio_actual) / precio_prom * 100
        texto_of += f"\U000027A1 [{nombre}]({constantes.sitio_URL['BGG']+str(bgg_id)}) está en [{constantes.sitio_nom[sitio]}]({constantes.sitio_URL[sitio]+sitio_id}) a ${precio_actual:.0f} y el promedio es de ${precio_prom:.0f} ({porc:.0f}% menos)\n"
    if texto_of == "":
        texto_of = "No hay ningún juego en oferta\n"

    texto_st = ""
    cursor.execute('SELECT id_juego FROM restock WHERE activa = "Sí"')
    restock = cursor.fetchall()
    for r in restock:
        id_juego = r[0]
        cursor.execute('SELECT nombre, sitio, sitio_id, bgg_id FROM juegos WHERE id_juego = ?',[id_juego])
        nombre, sitio, sitio_id, bgg_id = cursor.fetchone()
        cursor.execute('SELECT precio FROM precios WHERE id_juego = ? ORDER BY fecha DESC LIMIT 1', [id_juego])
        precio_actual = cursor.fetchone()[0]
        texto_st += f"\U000027A1 [{nombre}]({constantes.sitio_URL['BGG']+str(bgg_id)}) está en stock en [{constantes.sitio_nom[sitio]}]({constantes.sitio_URL[sitio]+sitio_id}) a ${precio_actual:.0f} (y antes no lo estaba)\n"
    if texto_st == "":
        texto_st = "No hay ningún juego en reposición\n"

    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    cursor.execute('SELECT id_usuario FROM alarmas_ofertas WHERE id_usuario = ?',[usuario_id])
    alarmas_ofertas = cursor.fetchone()
    if alarmas_ofertas == None:
        texto_al = "Cuando haya una oferta o reposición, te puedo mandar un mensaje (solo la primera vez que esté en ese estado).\n"
        keyboard = [
            [InlineKeyboardButton("\U00002795 Mandarme un mensaje", callback_data='mensaje_oferta_agregar')],
            [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
        ]
    else:
        texto_al = "Cuando haya una oferta o reposición, te voy a mandar un mensaje (solo la primera vez que esté en ese estado).\n"
        keyboard = [
            [InlineKeyboardButton("\U00002796 No mandarme más mensajes", callback_data='mensaje_oferta_borrar')],
            [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = f"*Juegos en oferta*\n\n{texto_of}\n*Juegos en reposición*\n\n{texto_st}\n{texto_al}", parse_mode = "Markdown", reply_markup=reply_markup, disable_web_page_preview = True)
    return PRINCIPAL

######### Agregar al aviso de ofertas
def mensaje_oferta_agregar(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id 
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO alarmas_ofertas (id_usuario) VALUES (?)',[usuario_id])
    conn.commit()
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = f"Vas a recibir mensajes cuando cualquier juego esté de oferta o reposición", parse_mode = "Markdown", reply_markup=reply_markup)
    return PRINCIPAL

######### Borrar el aviso de ofertas
def mensaje_oferta_borrar(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    usuario_id = update.callback_query.from_user.id 
    conn = conecta_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM alarmas_ofertas WHERE id_usuario = ?',[usuario_id])
    conn.commit()
    keyboard = [
        [InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text = f"No vas a recibir más mensajes cuando cualquier juego esté de oferta o reposición", parse_mode = "Markdown", reply_markup=reply_markup)
    return PRINCIPAL

######### Responde directamente a las consultas inline
def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    if query == "" or len(query) < 3:
        return

    conn = sqlite3.connect(constantes.db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT nombre, BGG_id FROM juegos WHERE nombre LIKE ? ORDER BY nombre',["%"+query+"%"])
    juegos = cursor.fetchall()
    results = []

    if len(juegos) <= 10:
        for j in juegos:
            BGG_id = j[1]
            nombre, texto = texto_info_juego(BGG_id)
            arch = f"{BGG_id}.png"
            if not os.path.exists(f"graficos/{arch}"):
                arch = "0000.png"
            imagen = f'{constantes.sitio_URL["base"]}graficos/{arch}?f={datetime.now().isoformat()}' # Para evitar que una imagen quede en cache

            results.append(
                    InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=nombre,
                    input_message_content = InputTextMessageContent(f"[ ]({imagen})\n{texto}\nPara más información y la posibilidad de poner alarmas, andá a @Monitor\_Juegos\_bot y escribí /start",
                                            parse_mode="Markdown",
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
                CallbackQueryHandler(juegos_lista,           pattern='^juegos_lista$'),
                CallbackQueryHandler(alarmas_muestra,        pattern='^alarmas_muestra$'),
                CallbackQueryHandler(juego_ver,              pattern='^juego_ver$'),
                CallbackQueryHandler(novedades,              pattern='^novedades$'),
                CallbackQueryHandler(juegos_baratos,         pattern='^juegos_baratos$'),
                # CallbackQueryHandler(juegos_BGG,             pattern='^juegos_BGG$'),
                CallbackQueryHandler(ofertas_restock,        pattern='^ofertas_restock$'),
                CallbackQueryHandler(sugerir_juego_datos,    pattern='^sugerir_juego_datos$'),
                CallbackQueryHandler(comentarios_texto,      pattern='^comentarios_texto$'),
                CallbackQueryHandler(ayuda,                  pattern='^ayuda$'),
                CallbackQueryHandler(inicio,                 pattern='^inicio$'),
                CallbackQueryHandler(estadistica,            pattern='^estadistica$'),
                CallbackQueryHandler(mensaje_oferta_agregar, pattern='^mensaje_oferta_agregar$'),
                CallbackQueryHandler(mensaje_oferta_borrar,  pattern='^mensaje_oferta_borrar$'),
            ],
            LISTA_JUEGOS: [
                CallbackQueryHandler(juegos_lista_TODO,    pattern='^juegos_lista_TODO$'),
                CallbackQueryHandler(juegos_lista_sitio,   pattern='^juegos_lista_sitio_'),
                CallbackQueryHandler(juegos_lista_ULT,     pattern='^juegos_lista_ULT$'),
                CallbackQueryHandler(inicio,               pattern='^inicio$'),
            ],
            JUEGO_ELECCION: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, juego_nom)
            ],
            JUEGO: [
                CallbackQueryHandler(juego_info,        pattern='^BGG_'),
                CallbackQueryHandler(inicio,            pattern='^inicio$'),
            ],
            ALARMAS_NUEVA_PRECIO: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, alarmas_agregar)
            ],
            ALARMAS_CAMBIAR_PRECIO: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, alarmas_cambiar)
            ],
            ALARMAS: [
                CallbackQueryHandler(alarmas_agregar_precio,   pattern='^alarmas_agregar_precio$'),
                CallbackQueryHandler(alarmas_cambiar_precio,   pattern='^alarmas_cambiar_precio$'),
                CallbackQueryHandler(alarmas_borrar,           pattern='^alarmas_borrar$'),
                CallbackQueryHandler(inicio_borrar,            pattern='^inicio$'),
            ],
            COMENTARIOS: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, comentarios_mandar)
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
