from telegram.ext import (Updater)
import os.path
import path
from datetime import datetime

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
        print(f"{datetime.now()} - Error enviando mensaje a {chat_id}")

def send_photo(chat_id, caption, photo):
    bot = get_bot()
    try:
        bot.send_photo(chat_id, photo = open(photo, 'rb'), caption = caption, parse_mode = "HTML", disable_web_page_preview = True)
    except:
        print(f"{datetime.now()} - Error enviando imagen a {chat_id}")