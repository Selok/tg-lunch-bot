import os
from typing import List, Tuple, Callable
from types import MethodType
from telegram.ext.callbackcontext import CallbackContext

from telegram.update import Update
from telegram.ext import Updater
from telegram.ext import CommandHandler, MessageHandler
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
        '_updater',
        '_helpMsg'
    ]

    def __init__(self, token: str):
        self._helpMsg = ''
        super(Bot, self).__init__(token)

    def setup(self, token: str):
        """initial object
        """
        print(f"updater: {token}")
        self._updater = Updater(token, use_context=True)
        self._updater.dispatcher.add_handler(CommandHandler(['help', 'h'], self.help))

    def cleanup(self):
        if self._updater:
            self._updater.stop()
        return super().cleanup()

    def help(self, update: Update, context: CallbackContext) -> None:
        """Display a help message"""
        update.message.reply_text(f"{self._helpMsg}")

    def addCommand(self, method_name: str, func: Callable, commands: SLT[str], helpMsg: str):
        """Add command handler to bot

        Args:
            method_name (str): Function name, use for debug
            func (Callable): Actual Handler 
            commands (SLT[str]): Command and its alias
        """
        setattr(self, method_name, MethodType(func, self))
        if helpMsg:
            command_str = f"/{commands}" if type(commands) is str else ''.join([f"/{c}" for c in commands])
            self._helpMsg += f"{command_str} - {helpMsg}{os.linesep}"
        print(f"addCommand: /{commands} - {getattr(self, method_name)}")
        self._updater.dispatcher.add_handler(CommandHandler(commands, getattr(self, method_name)))

    def addMessageHandler(self, method_name: str, func: Callable, filters: Filters):
        """Add message handler to bot

        Args:
            method_name (str): Function name, use for debug
            func (Callable): Actual Handler 
            filters (Filters): Message filter
        """
        setattr(self, method_name, MethodType(func, self))
        print(f"addMessageHandler: {getattr(self, method_name)}")
        self._updater.dispatcher.add_handler(MessageHandler(filters, getattr(self, method_name)))

    def start(self):
        print('start')
        if self._updater:
            print('start_polling')
            self._updater.start_polling()
            print('idle')
            self._updater.idle()
    
    def stop(self):
        if self._updater:
            self._updater.stop()
