from telegram.ext import (Updater)
import os.path
import path
from datetime import datetime
import sqlite3
import constantes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent

os.chdir(path.actual)

bot_token = os.environ.get('bot_token')

def get_bot():
    updater = Updater(bot_token)
    return updater.bot

def send_message(chat_id, text):
    bot = get_bot()
    try:
        bot.send_message(chat_id = chat_id, text = text, parse_mode = "HTML", disable_web_page_preview = True)
    except:
        # conn = sqlite3.connect(constantes.db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # conn.execute("PRAGMA journal_mode=WAL")
        # cursor = conn.cursor()
        # cursor.execute('DELETE FROM alarmas WHERE id_persona = ?',[chat_id])
        # cursor.execute('DELETE FROM alarmas_ofertas WHERE id_usuario = ?',[chat_id])
        print(f"{datetime.now()} - Error enviando mensaje a {chat_id}")
        # conn.commit()

def send_photo(chat_id, caption, photo):
    bot = get_bot()
    try:
        bot.send_photo(chat_id, photo = open(photo, 'rb'), caption = caption, parse_mode = "HTML")
    except:
        # conn = sqlite3.connect(constantes.db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # conn.execute("PRAGMA journal_mode=WAL")
        # cursor = conn.cursor()
        # cursor.execute('DELETE FROM alarmas WHERE id_persona = ?',[chat_id])
        # cursor.execute('DELETE FROM alarmas_ofertas WHERE id_usuario = ?',[chat_id])
        print(f"{datetime.now()} - Error enviando imagen a {chat_id} - Borrado")
        # conn.commit()

def send_button(chat_id, texto):
    bot = get_bot()
    keyboard = [
        [
            InlineKeyboardButton("\U00002B06 Inicio", callback_data='inicio')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(chat_id, text = texto, parse_mode = "HTML", reply_markup=reply_markup, disable_web_page_preview = True)
