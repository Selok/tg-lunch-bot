import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from datetime import datetime, time
from pytz import timezone
from threading import Timer
import os, sys, inspect

import logging, logging.config

from telegram.update import Update
from telegram.ext import CallbackContext
from typing import Dict, Tuple

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

from decide_lunch import getLunchDecision, getTxt
from setting import BotConfig, ChannelConfig, TimestampConfig, ReplyStrMap
from bot_basic_handler import *

from tg_ops.bot import Bot

def test(bot: Bot, update: Update, context: CallbackContext):
    bot.log.info(f"{update}, {context}")

def start(update: Update, context: CallbackContext) -> None:
    """Inform user about what this bot can do"""
    update.message.reply_text(
        'Please select /poll to get a Poll, /quiz to get a Quiz or /preview'
        ' to generate a preview for your poll'
    )
    
def help_handler(update: Update, context: CallbackContext) -> None:
    """Display a help message"""
    update.message.reply_text("Use /quiz, /poll or /preview to test this bot.")

if __name__ == "__main__":
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    token = os.environ.get("TOKEN")
    bot = Bot(token)
    bot.addFunc('test', test, 't')
    bot.start()

