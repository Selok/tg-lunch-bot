import os
import asyncio
from typing import List, Dict, Callable, Optional, Any, Tuple
from types import MethodType
from telegram import InlineKeyboardMarkup
from telegram.ext.callbackcontext import CallbackContext

from telegram.update import Update
from telegram.ext import Updater
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler
from telegram.ext import Filters
from telegram.utils.types import SLT

from utils.base import LoggingBase

BotCallback = Callable[['Bot', Update, CallbackContext], Any]
EntryPoint = Callable[['Bot', Update, CallbackContext], object]
ConversationCallbackMap = Dict[object, BotCallback]
ConversationMessageMap = Dict[object, Tuple[Filters, BotCallback]]
Fallback = Tuple[SLT[str], BotCallback]


class Bot(LoggingBase):
    """Telegram bot instance

    Args:
        token (str): The bot's token given by the @BotFather.

    Returns:
        Bot: bot instance
    """
    __slots__ = [
        '_running',
        '_updater',
        '_helpMsg'
    ]

    def __init__(self, token: str, help_commands: SLT[str] = ['help', 'h']):
        self._helpMsg = ''
        super(Bot, self).__init__(token, help_commands)

    def setup(self, token: str, help_commands: SLT[str]):
        """initial object
        """
        self._updater = Updater(token, use_context=True)
        self._updater.dispatcher.add_handler(
            CommandHandler(help_commands, self.help))

    def cleanup(self):
        if self._updater:
            self._updater.stop()
        return super().cleanup()

    def help(self, update: Update, context: CallbackContext) -> None:
        """Display a help message"""
        update.message.reply_text(f"{self._helpMsg}")

    def addCmd(self, method_name: str, commands: SLT[str], func: BotCallback, helpMsg: Optional[str] = None):
        """Add command handler to bot

        Args:
            method_name (str): Function name, use for debug
            commands (SLT[str]): Command and its alias
            func (BotCallback): Actual Handler 
            helpMsg (Optional[str]): Help message
        """
        self._updateHelpMsg(commands, helpMsg)

        setattr(self, method_name, MethodType(func, self))
        self._updater.dispatcher.add_handler(
            CommandHandler(
                commands, getattr(self, method_name),
                run_async=True
            )
        )

    def addMsg(self, method_name: str, func: BotCallback, filters: Filters):
        """Add message handler to bot

        Args:
            method_name (str): Function name, use for debug
            func (BotCallback): Actual Handler 
            filters (Filters): Message filter
        """
        setattr(self, method_name, MethodType(func, self))
        self._updater.dispatcher.add_handler(
            MessageHandler(
                filters, getattr(self, method_name),
                run_async=True
            )
        )

    def addCallback(self, method_name: str, func: BotCallback):
        """Add command handler to bot

        Args:
            method_name (str): Function name, use for debug
            func (BotCallback): Actual Handler
        """
        setattr(self, method_name, MethodType(func, self))
        self._updater.dispatcher.add_handler(
            CallbackQueryHandler(getattr(self, method_name), run_async=True)
        )

    def addConversation(
        self,
        method_name: str,
        commands: SLT[str],
        entry_point: EntryPoint,
        callback_states: Optional[ConversationCallbackMap] = {},
        msg_state: Optional[ConversationMessageMap] = {},
        fallback: Optional[Fallback] = None,
        helpMsg: Optional[str] = None
    ):
        """Add conversation handler to bot

        Args:
            method_name (str): Function name, use for debug
            commands (SLT[str]): Command and its alias
            entry_point (EntryPoint): Actual Handler,
            callback_states (Optional[ConversationCallbackMap]): Command handler trigger by user feedback,
            msg_state (Optional[ConversationMessageMap]): Message handler trigger by user feedback,
            fallback (Optional[Fallback]): Command handlers trigger if all handlers return false,
            helpMsg (Optional[str]): Help message
        """
        self._updateHelpMsg(commands, helpMsg)

        setattr(self, method_name, MethodType(entry_point, self))
        entry_points = [CommandHandler(commands, getattr(self, method_name))]

        states = {}
        # callback query handler
        for action in callback_states:
            cb = callback_states[action]
            cb_name = f"{method_name}_{action}"
            setattr(self, cb_name, MethodType(cb, self))
            states[action] = [CallbackQueryHandler(getattr(self, cb_name))]
        # message handler
        for action in msg_state:
            filters, msg = msg_state[action]
            msg_name = f"{method_name}_{action}"
            setattr(self, msg_name, MethodType(msg, self))
            states[action] = [MessageHandler(filters, getattr(self, msg_name))]
        # fallback
        fallbacks = []
        if fallback:
            fb_cmds, fb_fn = fallback
            fb_name = f"{method_name}_fallback_{fb_fn.__name__}"
            setattr(self, fb_name, MethodType(fb_fn, self))
            fallbacks = [CommandHandler(fb_cmds, getattr(self, fb_name))]

        self._updater.dispatcher.add_handler(
            ConversationHandler(
                entry_points=entry_points,
                states=states,
                fallbacks=fallbacks,
                run_async=True
            )
        )

    def _updateHelpMsg(self, commands: SLT[str], helpMsg: Optional[str]):
        if helpMsg:
            command_str = f"/{commands}" if type(commands) is str else ' '.join(
                [f"/{c}" for c in commands]
            )
            self._helpMsg += f"{command_str} - {helpMsg}{os.linesep}"

    def sendmsg(self, chat_id: int, message: str, markup: Optional[InlineKeyboardMarkup] = None):
        """send message to chat

        Args:
            chat_id (int): chat id
            message (str): message body
            markup (Optional[InlineKeyboardMarkup]): inline keyboard
        """
        self._updater.bot.send_message(chat_id, message, reply_markup=markup)

    async def start(self):
        if self._updater:
            self._running = True
            self._updater.start_polling()
            while self._running:
                await asyncio.sleep(10)
            # self._updater.idle()

    def stop(self):
        if self._updater:
            self._running = False
            self._updater.stop()
