from typing import List, Tuple, Callable
from types import MethodType

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
        '_updater'
    ]

    def __init__(self, token: str):
        super(Bot, self).__init__(token)

    def setup(self, token: str):
        """initial object
        """
        print(f"updater: {token}")
        self._updater = Updater(token, use_context=True)

    def cleanup(self):
        if self._updater:
            self._updater.stop()
        return super().cleanup()

    def addFunc(self, method_name: str, func: Callable, commands: SLT[str]):
        """[summary]

        Args:
            method_name (str): Function name, use for debug
            func (Callable): [description]
            commands (SLT[str]): [description]
        """
        setattr(self, method_name, MethodType(func, self))
        print(f"addFunc: /{commands} - {getattr(self, method_name)}")
        self._updater.dispatcher.add_handler(CommandHandler(commands, getattr(self, method_name)))

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
