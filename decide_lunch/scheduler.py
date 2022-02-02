import os
from turtle import up
import uuid
import asyncio
import json
from typing import Any, Dict, Set, List, NamedTuple
from datetime import datetime, timedelta

import aiofile as aiof

from config import ENROLL_DIR
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
    Daily: 3


class Schedule(NamedTuple):
    chat_id: int
    lunch_id: str
    title: str
    time: datetime
    type: ScheduleType


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
        '_running',
        '_notified'
    ]

    def __init__(self, enabledChats: List[int], messager: Messager):
        self._messager = messager
        self._enabledChats: Dict[int, List[Schedule]] = {
            chat_id: [] for chat_id in enabledChats}
        self._notified: Dict[int, Set[str]] = {
            chat_id: [] for chat_id in enabledChats}
        super(Scheduler, self).__init__()

    def setup(self):
        """initial object
        """
        self._running = False
        for chat_id in self._enabledChats:
            json_path = os.path.join(
                ENROLL_DIR,
                f"{chat_id}.json"
            )
            with open(json_path) as f:
                self._enabledChats[chat_id] = self._parseSchedule(json.load(f))

        self._messager.addConsumer(self.parseMsg)

    def cleanup(self):
        return super().cleanup()

    def _parseSchedule(self, jsons: Any) -> List[Schedule]:
        try:
            schedules = []

            chat_id = jsons['chat_id']
            for sch in jsons['schedules']:
                lunch_id = sch['lunch_id']
                title = sch['title']
                time = datetime.strptime(sch['time'], '%Y%m%d%H%M')
                schType = ScheduleType(int(sch['schType']))
                schedules.append(Schedule(
                    chat_id, lunch_id, title,
                    time, schType
                ))

            return schedules
        except:
            self.log.error("Invalid json file")

    async def _updateJson(self, chatId: str):
        json_path = os.path.join(
            ENROLL_DIR,
            f"{chatId}.json"
        )
        json_str = json.dump(self._enabledChats[chatId])
        async with aiof.async_open(json_path, 'w') as afp:
            await afp.write(json_str)

    async def parseMsg(self, msg: str):
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

    async def setupLunch(self, chatId: str, title: str, schType: ScheduleType, time: datetime):
        try:
            sch = Schedule(
                chatId, str(uuid.uuid4()), title,
                time, schType
            )
            self._enabledChats[chatId].append(sch)
            await self._updateJson(chatId)
            feedback = {
                'chatId': chatId,
                'action': int(Action.Setup),
                'success': True,
                'lunch_id': sch.lunch_id,
                'title': sch.title
            }
        except:
            self.log.error("Setup lunch fail")
            feedback = {
                'chatId': chatId,
                'action': int(Action.Setup),
                'success': False
            }

        await self._messager.send(json.dump(feedback))

    async def modifyLunch(self, chatId: str, lunch_id: str, title: str, schType: ScheduleType, time: datetime):
        success = False
        try:
            for sch in self._enabledChats[chatId]:
                if sch.lunch_id == lunch_id:
                    sch.title = title
                    sch.type = schType
                    sch.time = time
                    await self._updateJson(chatId)
                    success = True
                    break
        except:
            self.log.error("Modify lunch fail")

        feedback = {
            'chatId': chatId,
            'action': int(Action.Modify),
            'success': success,
            'lunch_id': lunch_id,
            'title': title
        }

        await self._messager.send(json.dump(feedback))

    async def skipLunch(self, chatId: str, lunch_id: str):
        success = False
        try:
            self._notified[chatId].add(lunch_id)
            success = True
        except:
            self.log.error("Modify lunch fail")

        feedback = {
            'chatId': chatId,
            'action': int(Action.Skip),
            'success': success,
            'lunch_id': lunch_id
        }
        await self._messager.send(json.dump(feedback))

    async def cancelLunch(self, chatId: str, lunch_id: str):
        success = False
        try:
            for i, sch in enumerate(self._enabledChats[chatId]):
                if sch.lunch_id == lunch_id:
                    del self._enabledChats[chatId][i]
                    await self._updateJson(chatId)
                    success = True
                    break
        except:
            self.log.error("Cancel lunch fail")

        feedback = {
            'chatId': chatId,
            'action': int(Action.Cancel),
            'success': success,
            'lunch_id': lunch_id
        }

        await self._messager.send(json.dump(feedback))

    async def listLunch(self, chatId: str):
        feedback = {
            'chatId': chatId,
            'action': int(Action.List),
            'schedules': self._enabledChats[chatId]
        }

        await self._messager.send(json.dump(feedback))

    async def notifyLunch(self):
        now = datetime.now()

        for chatId in self._enabledChats:
            schedules = self._enabledChats[chatId]
            notified = self._notified[chatId]
            need_cleanup = []

            for sch in schedules:
                if sch.type in [ScheduleType.Daily, ScheduleType.Weekday]:
                    sch_time = sch.time.replace(
                        year=now.year, month=now.month, day=now.day
                    )
                else:
                    sch_time = sch.time
                if sch.lunch_id in self._notified[chatId] and now > sch_time:
                    notified.remove(sch.lunch_id)
                elif now < sch_time and sch_time - now < timedelta(minutes=30):
                    feedback = {
                        'chatId': chatId,
                        'schedule': sch
                    }
                    await self._messager.send(json.dump(feedback))

                    if sch.type == ScheduleType.OneTime:
                        need_cleanup.append(sch)

            for sch in need_cleanup:
                schedules.remove(sch)

            if len(need_cleanup) > 0:
                await self._updateJson(chatId)

    async def start(self):
        self._running = True
        while self._running:
            await self.notifyLunch()
            await asyncio.sleep(1)

    def stop(self):
        self._running = False
