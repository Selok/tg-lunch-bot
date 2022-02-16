import os
import uuid
import asyncio
import json
from typing import Any, Dict, Set, List, NamedTuple
from datetime import datetime, timedelta

import aiofile as aiof

from config import ENROLL_DIR
from decide_lunch.schedule import parseActionMsg, Action, Schedule, ScheduleType, FeedbackContext
from utils.base import LoggingBase
from message.base import Messager


class Scheduler(LoggingBase):
    """Scheduler instance

    Args:
        enabledChats (List[int]): Chat that allowed to use scheduler.
        messager (Messager): Messager instance to communicate with bot.

    Returns:
        Scheduler: Scheduler instance
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
            chat_id: set() for chat_id in enabledChats}
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

        self._messager.addConsumer(self.processMsg)

    def cleanup(self):
        return super().cleanup()

    def _parseSchedule(self, jsons: Any) -> List[Schedule]:
        try:
            schedules = []

            for sch in jsons['schedules']:
                lunch_id = sch['lunch_id']
                owner_id = sch['owner_id']
                title = sch['title']
                time = datetime.strptime(sch['time'], '%Y%m%d%H%M')
                schType = ScheduleType(int(sch['schType']))
                schedules.append(Schedule(
                    lunch_id, owner_id, title,
                    time, schType
                ))

            return schedules
        except Exception as e:
            self.log.error("Invalid json file", e)

    async def _updateJson(self, chatId: int):
        json_path = os.path.join(
            ENROLL_DIR,
            f"{chatId}.json"
        )
        json_str = json.dump(self._enabledChats[chatId])
        async with aiof.async_open(json_path, 'w') as afp:
            await afp.write(json_str)

    async def processMsg(self, msg: str):
        try:
            context = parseActionMsg(msg)
            if not context:
                # non schedule action
                return
        except Exception as e:
            self.log.warning("Invalid message", e)
            return

        try:
            schedule = context.schedule
            chat_id = context.chat_id
            if context.action == Action.Setup:
                await self.setupLunch(
                    chat_id,
                    schedule.owner_id,
                    schedule.title,
                    schedule.type,
                    schedule.time
                )
            elif context.action == Action.Modify:
                await self.modifyLunch(
                    chat_id,
                    schedule.lunch_id,
                    schedule.title,
                    schedule.type,
                    schedule.time
                )
            elif context.action == Action.Skip:
                await self.skipLunch(chat_id, schedule.lunch_id)
            elif context.action == Action.Cancel:
                await self.cancelLunch(chat_id, schedule.lunch_id)
            elif context.action == Action.List:
                await self.listLunch(chat_id)
        except:
            self.log.exception("unknown error")

    async def setupLunch(self, chatId: int, ownerId: str, title: str, schType: ScheduleType, time: datetime):
        try:
            sch = Schedule(
                str(uuid.uuid4()), ownerId, title, 
                time, schType
            )
            self._enabledChats[chatId].append(sch)
            await self._updateJson(chatId)
            feedback = FeedbackContext(Action.Setup, chatId, [sch], True)
        except Exception as e:
            self.log.error("Setup lunch fail", e)
            feedback = FeedbackContext(Action.Setup, chatId, [], False)

        await self._messager.send(feedback.toJson())

    async def modifyLunch(self, chatId: int, lunchId: str, title: str, schType: ScheduleType, time: datetime):
        success = False
        schedules = []
        try:
            for sch in self._enabledChats[chatId]:
                if sch.lunch_id == lunchId:
                    sch.title = title
                    sch.type = schType
                    sch.time = time
                    await self._updateJson(chatId)
                    success = True
                    schedules.append(sch)
                    break
        except Exception as e:
            self.log.error("Modify lunch fail", e)

        feedback = FeedbackContext(Action.Modify, chatId, schedules, success)

        await self._messager.send(feedback.toJson())

    async def skipLunch(self, chatId: int, lunchId: str):
        success = False
        try:
            self._notified[chatId].add(lunchId)
            success = True
        except Exception as e:
            self.log.error("Modify lunch fail", e)

        feedback = FeedbackContext(Action.Skip, chatId, [], success)
        
        await self._messager.send(feedback.toJson())

    async def cancelLunch(self, chatId: int, lunchId: str):
        success = False
        schedules = []
        try:
            for i, sch in enumerate(self._enabledChats[chatId]):
                if sch.lunch_id == lunchId:
                    del self._enabledChats[chatId][i]
                    await self._updateJson(chatId)
                    success = True
                    schedules.append(sch)
                    break
        except Exception as e:
            self.log.error("Cancel lunch fail", e)

        feedback = FeedbackContext(Action.Cancel, chatId, schedules, success)

        await self._messager.send(feedback.toJson())

    async def listLunch(self, chatId: int):
        feedback = FeedbackContext(Action.List, chatId, self._enabledChats[chatId], True)
        msg = feedback.toJson()

        await self._messager.send(msg)

    async def notifyLunch(self):
        now = datetime.utcnow()

        try:
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
                    if sch.lunch_id in notified:
                        if now > sch_time:
                            notified.remove(sch.lunch_id)
                    elif now < sch_time and sch_time - now < timedelta(minutes=30):
                        feedback = FeedbackContext(
                            Action.Notify,
                            [sch],
                            True
                        )
                        json_feedback = feedback.toJson()
                        await self._messager.send(json_feedback)
                        notified.add(sch.lunch_id)
                        if sch.type == ScheduleType.OneTime:
                            need_cleanup.append(sch)

                for sch in need_cleanup:
                    schedules.remove(sch)

                if len(need_cleanup) > 0:
                    await self._updateJson(chatId)
        except Exception as e:
            self.log.error("Notify lunch error", e)

    async def start(self):
        self._running = True
        while self._running:
            await self.notifyLunch()
            await asyncio.sleep(1)

    def stop(self):
        self._running = False
