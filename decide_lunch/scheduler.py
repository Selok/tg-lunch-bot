import asyncio
import aiofile as aiof
import json
from typing import List
from datetime import datetime


from utils.base import LoggingBase
from message.base import Messager
from enum import Enum


class Action(Enum):
    Setup: 1
    Modify: 2
    Skip: 3
    Cancel: 4
    List: 5


class ScheduleType(Enum):
    Weekday: 1
    OneTime: 2


class Scheduler(LoggingBase):
    """Scheduler instance

    Args:
        enabledChats (List[int]): Chat that allowed to use scheduler.
        messager (Messager): Messager instance to communicate with bot.

    Returns:
        Bot: bot instance
    """
    __slots__ = [
        '_messager',
        '_enabledChats',
        '_running'
    ]

    def __init__(self, enabledChats: List[int], messager: Messager):
        self._messager = messager
        self._enabledChats = enabledChats
        super(Scheduler, self).__init__()

    def setup(self):
        """initial object
        """
        self._running = False

    def cleanup(self):
        return super().cleanup()

    async def parseSchedule(self, msg: str):
        try:
            action: Action
            with json.loads(msg) as j:
                if 'type' not in j or j['type'] != 'schedule':
                    return
                action = Action(int(j['action']))
                chatId = j['chatId']
                if action == Action.Setup:
                    self.setupLunch(
                        chatId,
                        j['title'],
                        ScheduleType(int(j['schType'])),
                        datetime.strptime(j['datetime'], '%Y%m%d%H%M')
                    )
                elif action == Action.Modify:
                    self.modifyLunch(
                        chatId,
                        j['lunch_id'],
                        j['title'],
                        ScheduleType(int(j['schType'])),
                        datetime.strptime(j['datetime'], '%Y%m%d%H%M')
                    )
                elif action == Action.Skip:
                    self.skipLunch(chatId, j['lunch_id'])
                elif action == Action.Cancel:
                    self.cancelLunch(chatId, j['lunch_id'])
                elif action == Action.List:
                    self.listLunch(chatId)
        except:
            self.log.warning("Invalid message")

    async def setupLunch(self, chatId: str, title: str, schType: ScheduleType, datetime: datetime):
        pass

    async def modifyLunch(self, chatId: str, lunch_id: str, title: str, schType: ScheduleType, datetime: datetime):
        pass

    async def skipLunch(self, chatId: str, lunch_id: str):
        pass

    async def cancelLunch(self, chatId: str, lunch_id: str):
        pass

    async def listLunch(self, chatId: str):
        pass

    async def notifyLunch(self, chatId: str):
        pass

    async def start(self):
        self._running = True
        while self._running:
            await asyncio.sleep(1)
            for chatId in self._enabledChats:
                await self.notifyLunch(chatId)

    def stop(self):
        self._running = False
