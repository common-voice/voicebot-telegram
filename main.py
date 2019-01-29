#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple Bot to reply to Telegram messages.
This program is dedicated to the public domain under the CC0 license.
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, RegexHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ReplyKeyboardMarkup
import logging
import urllib2
import json
from io import BytesIO

import os
import sys
from threading import Thread

from functools import wraps
from telegram import ChatAction

#base_url = "https://voice.allizom.org/api/v1/"
base_url = "http://10.238.31.20:9000/api/v1/"

def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(*args, **kwargs):
            bot, update = args
            bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(bot, update, **kwargs)
        return command_func

    return decorator
#import magic

#import requests

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

send_typing_action = send_action(ChatAction.TYPING)

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    button_list = [
        InlineKeyboardButton("Record a sentence", callback_data="start_speaking"),
        InlineKeyboardButton("Validate (not working)", callback_data="validate")
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    #custom_keyboard = [['Speak!', 'Validate (not working yet)']]
    #reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text('Hi there! What would you like to do?', reply_markup=reply_markup)

def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

@send_typing_action
def get_voice(bot, update, chat_data=None):
    """Echo the user message."""
    # TODO: check a sane lenght of a message
    logger.warning(chat_data)
    update.message.reply_text("Processing your new audio...")
    file_path = update.message.voice.get_file().download_as_bytearray()

    headers_dict = {
        'Content-Type': "application/octet-stream",
        'sentence': urllib2.quote(chat_data["sentence_text"].encode("utf-8")),
        'sentence_id': chat_data["sentence_id"],
        'client_id': 'telegram_v1_' + "%i" %(update.message.from_user.id)
      }

    logger.warning(headers_dict)
    req = urllib2.Request(base_url + 'en/clips', file_path, headers=headers_dict)
    res = urllib2.urlopen(req)
    logger.warning(res.getcode())
    update.message.reply_text("Audio uploaded! Thank you. For a new recording press /speak")

    #update.message.reply_text(update.message.voice.file_id)

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

def get_snippet():
    print("''")

@send_typing_action
def speak(bot, update, chat_data=None, user_data=None):

    chat_id = ""
    #logger.warning(update.callback_query.message)
    if (update.callback_query != None):
        chat_id = update.callback_query.message.chat.id
    else:
        chat_id = update.message.chat_id


    if (update.callback_query != None):
        callback_action = update.callback_query.data
        if (callback_action != "start_speaking") and (callback_action != "skip"):
            bot.send_message(chat_id, update.callback_query.data)
            bot.send_message(chat_id, "Not implemented yet")
            # start(bot, update)
            return

    button_list = [
        #InlineKeyboardButton("End Session", callback_data="end_session"),
        InlineKeyboardButton("Skip", callback_data="skip")
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    data = json.load(urllib2.urlopen(base_url + 'en/sentences/'))

    bot.send_message(chat_id,
                    "<i>Please send me a voice note with the following sentence:</i>",
                        parse_mode=ParseMode.HTML)
    bot.send_message(chat_id, "🎤 -- "+ data[0]["text"].encode('utf-8'), reply_markup=reply_markup)
    chat_data["sentence_id"] = data[0]["id"]
    chat_data["sentence_text"] = data[0]["text"]

def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(os.getenv("MOZ_VOICE_TELEGRAM"))

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("speak", speak, pass_chat_data=True))

    dp.add_handler(CallbackQueryHandler(speak, pass_chat_data=True, pass_user_data=True))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.voice, get_voice, pass_chat_data=True))

    # log all errors
    dp.add_error_handler(error)

    def stop_and_restart():
        """Gracefully stop the Updater and replace the current process with a new one"""
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(bot, update):
        update.message.reply_text('Bot is restarting...')
        Thread(target=stop_and_restart).start()
        update.message.reply_text('Here!')

    dp.add_handler(CommandHandler('r', restart, filters=Filters.user(username='@ruphy')))
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
