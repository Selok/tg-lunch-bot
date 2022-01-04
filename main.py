import os
from telegram.update import Update
from telegram.ext import CallbackContext
from telegram.ext.filters import Filters

from config import setup
from tg_ops.bot import Bot
from decide_lunch.enrollment import add_me, remove_me

def test(instance: Bot, update: Update, context: CallbackContext):
    update.message.reply_text(f"{update}, {context}")
    instance.log.info(f"{update}, {context}")

def tag_all(update: Update, context: CallbackContext):
    content = str(update.message.text)
    print(content)

if __name__ == "__main__":
    setup()

    token = os.environ.get("TOKEN")
    bot = Bot(token)
    bot.addCommand('test', test, 't', 'test message')
    bot.addCommand('add_me', add_me, 'add_me', 'Add to lunch name list')
    bot.addCommand('remove_me', remove_me, 'remove_me', 'Remove from lunch name list')
    bot.addMessageHandler('tag_all', tag_all, Filters.text)
    bot.start()
