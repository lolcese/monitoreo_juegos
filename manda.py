from telegram.ext import (Updater)
from datetime import datetime
from decouple import config

bot_token = config('bot_token')
id_aviso = config('id_aviso')

def get_bot():
    updater = Updater(bot_token)
    return updater.bot

def send_message(chat_id, text):
    bot = get_bot()
    # try:
    bot.send_message(chat_id = chat_id, text = text, parse_mode = "HTML", disable_web_page_preview = True)
    # except:
    #     pass
        # print(f"{datetime.now()} - Error enviando mensaje a {chat_id}")

def send_photo(chat_id, caption, photo):
    bot = get_bot()
    # try:
    bot.send_photo(chat_id, photo = open(photo, 'rb'), caption = caption, parse_mode = "HTML")
    # except:
        # pass
        # print(f"{datetime.now()} - Error enviando imagen a {chat_id}")

def send_message_key(chat_id, text, reply_markup):
    bot = get_bot()
    # try:
    bot.send_message(chat_id = chat_id, text = text, parse_mode = "HTML", disable_web_page_preview = True, reply_markup = reply_markup)
    # except:
    #     pass
        # print(f"{datetime.now()} - Error enviando mensaje a {chat_id}")
