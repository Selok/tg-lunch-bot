import os
import asyncio
from typing import List, Dict, Callable, Optional, Any, Tuple
from types import MethodType
from telegram.ext.callbackcontext import CallbackContext

from telegram.update import Update
from telegram.ext import Updater
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler
from telegram.ext import Filters
from telegram.utils.types import SLT

from utils.base import LoggingBase


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
        print(f"updater: {token}")
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

    def addCmd(self, method_name: str, commands: SLT[str], func: Callable[['Bot', Update, CallbackContext], Any], helpMsg: Optional[str] = None):
        """Add command handler to bot

        Args:
            method_name (str): Function name, use for debug
            commands (SLT[str]): Command and its alias
            func (Callable[['Bot', Update, CallbackContext], Any]): Actual Handler 
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

    def addMsg(self, method_name: str, func: Callable[['Bot', Update, CallbackContext], Any], filters: Filters):
        """Add message handler to bot

        Args:
            method_name (str): Function name, use for debug
            func (Callable[['Bot', Update, CallbackContext], Any]): Actual Handler 
            filters (Filters): Message filter
        """
        setattr(self, method_name, MethodType(func, self))
        self._updater.dispatcher.add_handler(
            MessageHandler(
                filters, getattr(self, method_name),
                run_async=True
            )
        )

    def addConversation(
        self,
        method_name: str,
        commands: SLT[str],
        entry_point: Callable[['Bot', Update, CallbackContext], object],
        callback_states: Optional[Dict[
            object,
            Callable[['Bot', Update, CallbackContext], Any]
        ]] = {},
        msg_state: Optional[Dict[
            object,
            Tuple[
                Filters, Callable[['Bot', Update, CallbackContext], Any]
            ]
        ]] = {},
        fallback: Optional[
            Tuple[
                SLT[str],
                Callable[['Bot', Update, CallbackContext], Any]
            ]
        ] = None,
        helpMsg: Optional[str] = None
    ):
        """Add conversation handler to bot

        Args:
            method_name (str): Function name, use for debug
            commands (SLT[str]): Command and its alias
            entry_point (Callable[['Bot', Update, CallbackContext], Any]): Actual Handler,
            callback_states (Optional[Dict[object, Callable[['Bot', Update, CallbackContext], Any]]]): Command handler trigger by user feedback,
            msg_state (Optional[Dict[object, Tuple[Callable[['Bot', Update, CallbackContext], Any]], Filters]]): Message handler trigger by user feedback,
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

    async def start(self):
        print('start')
        if self._updater:
            self._running = True
            print('start_polling')
            self._updater.start_polling()
            print('idle')
            while self._running:
                await asyncio.sleep(10)
            # self._updater.idle()

    def stop(self):
        if self._updater:
            self._running = False
            self._updater.stop()

