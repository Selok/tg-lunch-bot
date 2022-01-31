import os
import json

from tg_ops.bot import Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.update import Update
from telegram.ext import CallbackContext, ConversationHandler
from config import ENROLL_DIR


def add_me(instance: Bot, update: Update, context: CallbackContext):
    jsonFile = os.path.join(
        ENROLL_DIR,
        f"{update.message.chat_id}.json"
    )
    name = f"{update.message.from_user.full_name}"
    user_id = update.message.from_user.id

    enrolled = {}
    invited = set()
    if os.path.isfile(jsonFile):
        with open(jsonFile) as f:
            enrolled = json.load(f)
            if 'invited' in enrolled:
                invited = set(enrolled['invited'])

    # cache user info
    user_info = {}
    if 'user_info' in enrolled:
        user_info = enrolled['user_info']
    user_info[user_id] = {
        'name': name
    }
    enrolled['user_info'] = user_info

    # update invited list
    update_user = (user_id in invited)
    invited.add(user_id)
    enrolled['invited'] = list(invited)

    with open(jsonFile, "w") as f:
        f.write(json.dumps(enrolled))

    if update_user:
        update.message.reply_text(
            f"[{name}](tg://user?id={user_id}) already in the invite list\.", parse_mode='MarkdownV2')
    else:
        update.message.reply_text(
            f"[{name}](tg://user?id={user_id}) added to invite list\.", parse_mode='MarkdownV2')


def remove_me(instance: Bot, update: Update, context: CallbackContext):
    jsonFile = os.path.join(
        ENROLL_DIR,
        f"{update.message.chat_id}.json"
    )
    name = f"{update.message.from_user.full_name}"
    user_id = update.message.from_user.id

    enrolled = {}
    invited = set()
    if not os.path.isfile(jsonFile):
        return

    with open(jsonFile) as f:
        enrolled = json.load(f)
        if 'invited' in enrolled:
            invited = set(enrolled['invited'])

    # remove cached user info
    if 'user_info' in enrolled:
        user_info = enrolled['user_info']
        if user_id in user_info:
            del user_info[user_id]

    # update invited list
    update_user = (user_id in invited)
    invited.remove(user_id)
    enrolled['invited'] = list(invited)

    with open(jsonFile, "w") as f:
        f.write(json.dumps(enrolled))

    if update_user:
        update.message.reply_text(
            f"[{name}](tg://user?id={user_id}) removed from the invite list\.", parse_mode='MarkdownV2')
    else:
        update.message.reply_text(
            f"[{name}](tg://user?id={user_id}) is not in the invite list\.", parse_mode='MarkdownV2')


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
