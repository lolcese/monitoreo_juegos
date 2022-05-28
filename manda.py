from telegram.ext import (Updater)
import os.path

bot_token = os.environ.get('bot_token')

def get_bot():
    updater = Updater(bot_token)
    return updater.bot

def send_message(chat_id, text):
    bot = get_bot()
    bot.send_message(chat_id = chat_id, text = text, parse_mode = "HTML")

def send_photo(chat_id, caption, photo):
    bot = get_bot()
    bot.send_photo(chat_id, photo, caption, parse_mode = "HTML")