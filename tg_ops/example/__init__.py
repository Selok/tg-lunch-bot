from telegram.update import Update
from telegram.ext import CallbackContext

from tg_ops.bot import Bot

def cmd(instance: Bot, update: Update, context: CallbackContext):
    update.message.reply_text(f"update: \r\n {update}")
    update.message.reply_text(f"context: \r\n {context}")
    instance.log.info(f"{update.message.chat_id}")

def msg(instance: Bot, update: Update, context: CallbackContext):
    # content = str(update.message.text)
    # print(context.)
    # exit()
    pass
