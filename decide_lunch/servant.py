from ast import arguments
import asyncio
import os
import json
from types import MethodType
from typing import List
from message.base import Messager

from tg_ops.bot import Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.update import Update
from telegram.ext import CallbackContext, ConversationHandler

from config import ENROLL_DIR
from utils.base import LoggingBase
from decide_lunch.schedule import Schedule, parseActionFeedback, Action, ActionContext, parseActionMsg


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


def enroll_button():
    button = [[
        InlineKeyboardButton("join", callback_data='join_event'),
        InlineKeyboardButton("pass", callback_data='pass_event')]]
    return InlineKeyboardMarkup(button, one_time_keyboard=True)


def enroll(instance: Bot, update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == "join_event":
        join_event(update, context)
    elif query.data == "pass_event":
        pass_event(update, context)


def join_event(update: Update, context: CallbackContext):
    name = f"{update.effective_user.full_name}"
    user_id = update.effective_user.id
    update.effective_message.reply_text(
        f"[{name}](tg://user?id={user_id}) don't stand us up\!\.",
        parse_mode='MarkdownV2'
    )
    return ConversationHandler.END


def pass_event(update: Update, context: CallbackContext):
    name = f"{update.effective_user.full_name}"
    user_id = update.effective_user.id
    update.effective_message.reply_text(
        f"May be next time, [{name}](tg://user?id={user_id})\. T^T\.",
        parse_mode='MarkdownV2'
    )
    return ConversationHandler.END


EXPECT_NAME, EXPECT_BUTTON_CLICK = range(2)


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


def cmd(instance: Bot, update: Update, context: CallbackContext):
    update.message.reply_text(f"update: \r\n {update}")
    update.message.reply_text(f"context: \r\n {context}")
    instance.log.info(f"{update.message.chat_id}")


class Servant(LoggingBase):
    """Enrollment servant instance

    Args:
        messager (Messager): Messager instance to communicate with bot.
        bot (Bot): Telegram bot instance.

    Returns:
        Servant: Enrollment servant instance
    """
    __slots__ = [
        '_messager',
        '_bot',
        '_running'
    ]

    def __init__(self, messager: Messager, bot: Bot):
        self._messager = messager
        self._bot = bot
        super(Servant, self).__init__()

    def setup(self):
        """initial object
        """
        self._running = False

        self._bot.addCmd('add_me', 'add_me', add_me, 'Add to lunch name list')
        self._bot.addCmd('remove_me', 'remove_me', remove_me,
                         'Remove from lunch name list')
        self._bot.addCmd('test', ['t', 'test'], cmd, 'test message')

        self._bot.addCmd(
            'list_event',
            'list', self.list_event,
            'List upcoming event'
        )

        self._bot.addCallback('enroll', enroll)

        self._messager.addConsumer(self.parseMsg)

    def list_event(self, bot: Bot, update: Update, context: CallbackContext):
        asyncio.run(self._actual_list_event(bot, update, context))

    # list
    async def _actual_list_event(self, bot: Bot, update: Update, context: CallbackContext):
        context = ActionContext(Action.List, update.message.chat_id, None)
        await self._messager.send(
            context.toJson()
        )

    def cleanup(self):
        return super().cleanup()

    async def parseMsg(self, msg: str):
        try:
            feedback = parseActionFeedback(msg)
        except Exception as e:
            self.log.warning("Invalid message", e)
            return
            
        try:
            if not feedback:
                pass
            elif feedback.action == Action.Notify and feedback.schedules:
                self.sendNotify(feedback.chat_id, feedback.schedules[0])
            elif feedback.action == Action.List:
                self.sendList(feedback.chat_id, feedback.schedules)
        except:
            self.log.exception("unknown error")

    def sendNotify(self, chatId: int, schedule: Schedule):
        self._bot.sendmsg(
            chatId,
            f"{schedule.title} is about to begin",
            enroll_button()
        )

        return EXPECT_BUTTON_CLICK

    def sendList(self, chatId: int, schedules: List[Schedule]):
        msg = ""
        for sch in schedules:
            msg += f"{sch.title} "
        self._bot.sendmsg(
            chatId,
            msg
        )

        return EXPECT_BUTTON_CLICK

    async def start(self):
        self._loop = asyncio.get_event_loop()
        self._running = True
        while self._running:
            await asyncio.sleep(1)

    def stop(self):
        self._running = False
