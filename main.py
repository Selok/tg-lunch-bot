import os
from telegram.update import Update
from telegram.ext import CallbackContext
from telegram.ext.filters import Filters

from config import setup
from tg_ops.bot import Bot
from tg_ops.example import cmd, msg
from decide_lunch.servant import Servant, add_me, remove_me
from decide_lunch.scheduler import Scheduler
from message.simple import SimpleMessager

from telegram.ext import ConversationHandler

from poll_test import setup as setup_poll
from edit_reply_test import setup as setup_reply
from reply_keyboard_test import setup as setup_reply_keyboard

def start(instance: Bot, update: Update, context: CallbackContext):
    ''' Replies to start command '''
    update.message.reply_text('Hi! I am alive')

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
EXPECT_NAME, EXPECT_BUTTON_CLICK = range(2)

def set_name_handler(instance: Bot, update: Update, context: CallbackContext):
    ''' Entry point of conversation  this gives  buttons to user'''

    print('set_name_handler')

    button = [[InlineKeyboardButton("name", callback_data='name')]]
    markup = InlineKeyboardMarkup(button)

    # you can add more buttons here

    #  learn more about inline keyboard
    # https://github.com/python-telegram-bot/python-telegram-bot/wiki/InlineKeyboard-Example

    update.message.reply_text('Name button', reply_markup=markup)

    return EXPECT_BUTTON_CLICK


def button_click_handler(instance: Bot, update: Update, context: CallbackContext):
    ''' This gets executed on button click '''
    query = update.callback_query
    # shows a small notification inside chat
    query.answer(f'button click {query.data} recieved')

    if query.data == 'name':
        query.edit_message_text(f'You clicked on "name"')
        # asks for name, and prompts user to reply to it
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Send your name', reply_markup=ForceReply())
        # learn more about forced reply
        # https://python-telegram-bot.readthedocs.io/en/stable/telegram.forcereply.html
        return EXPECT_NAME


def name_input_by_user(instance: Bot, update: Update, context: CallbackContext):
    ''' The user's reply to the name prompt comes here  '''
    name = update.message.text

    # saves the name
    context.user_data['name'] = name
    update.message.reply_text(f'Your name is saved as {name[:100]}')

    # ends this particular conversation flow
    return ConversationHandler.END


def cancel(instance: Bot, update: Update, context: CallbackContext):
    update.message.reply_text(
        'Name Conversation cancelled by user. Bye. Send /set_name to start again')
    return ConversationHandler.END


def get_name(instance: Bot, update: Update, context: CallbackContext):
    ''' Handle the get_name command. Replies the name of user if found. '''
    value = context.user_data.get(
        'name', 'Not found. Set your name using /set_name command')
    update.message.reply_text(value)

import asyncio
async def timer_alert(instance: Bot, update: Update, context: CallbackContext):
    ''' Entry point of conversation  this gives  buttons to user'''

    print('set_name_handler')

    button = [[InlineKeyboardButton("join", callback_data='join'), InlineKeyboardButton("pass", callback_data='pass')]]
    markup = InlineKeyboardMarkup(button)

    # you can add more buttons here

    #  learn more about inline keyboard
    # https://github.com/python-telegram-bot/python-telegram-bot/wiki/InlineKeyboard-Example

    update.message.reply_text('Name button', reply_markup=markup)

    await asyncio.sleep(10)

    return EXPECT_BUTTON_CLICK

if __name__ == "__main__":
    setup()

    token = os.environ.get("TOKEN")
    bot = Bot(token)
    # bot.addCmd('test', ['t', 'test'], cmd, 'test message')
    # bot.addMsg('msg', msg, Filters.text)
    
    # bot.addConversation(
    #     'conversation', 
    #     'set_name', 
    #     set_name_handler, 
    #     {EXPECT_BUTTON_CLICK: button_click_handler},
    #     {EXPECT_NAME: (Filters.text, name_input_by_user)},
    #     ('cancel', cancel),
    #     'conversation test'
    # )
    # bot.addCmd('conversation_result', ['get_name'], get_name, 'conversation test result')

    # setup_reply_keyboard(bot._updater.dispatcher)

    messager = SimpleMessager()
    scheduler = Scheduler([-687899940], messager)
    servant = Servant(messager, bot)
    
    loop = asyncio.get_event_loop()
    tasks = [
        asyncio.ensure_future(bot.start(), loop=loop),
        asyncio.ensure_future(servant.start(), loop=loop),
        asyncio.ensure_future(messager.start(), loop=loop),
        asyncio.ensure_future(scheduler.start(), loop=loop)
    ]

    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
