from telegram.ext import (Updater)
from datetime import datetime
import sqlite3
import constantes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent
from decouple import config

bot_token = config('bot_token')
id_aviso = config('id_aviso')

def get_bot():
    updater = Updater(bot_token)
    return updater.bot

def send_message(chat_id, text):
    bot = get_bot()
    try:
        bot.send_message(chat_id = chat_id, text = text, parse_mode = "HTML", disable_web_page_preview = True)
    except:
        # conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
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
        # conn = sqlite3.connect(constantes.db_file, timeout=20, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # conn.execute("PRAGMA journal_mode=WAL")
        # cursor = conn.cursor()
        # cursor.execute('DELETE FROM alarmas WHERE id_persona = ?',[chat_id])
        # cursor.execute('DELETE FROM alarmas_ofertas WHERE id_usuario = ?',[chat_id])
        print(f"{datetime.now()} - Error enviando imagen a {chat_id} - Borrado")
        # conn.commit()