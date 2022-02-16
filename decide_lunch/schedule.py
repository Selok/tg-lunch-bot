from datetime import date, datetime
from enum import Enum
import json
from typing import List, NamedTuple, Union


class Action(Enum):
    Notify = 0
    Setup = 1
    Modify = 2
    Skip = 3
    Cancel = 4
    List = 5


class ScheduleType(Enum):
    Weekday = 1
    OneTime = 2
    Daily = 3


class Schedule(NamedTuple):
    lunch_id: str
    owner_id: str
    title: str
    time: datetime
    type: ScheduleType


def __json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.strftime('%Y%m%d%H%M')
    elif isinstance(obj, Enum):
        return str(obj.value)
    elif isinstance(obj, list):
        return [__json_serial(o) for o in obj]
    elif isinstance(obj, Schedule) or isinstance(obj, FeedbackContext):
        d = obj._asdict()
        return {k: __json_serial(d[k]) for k in d}
    else:
        return obj


def _toJson(t: tuple) -> str:
    kvPairs = {}
    d = t._asdict()
    for k in d:
        kvPairs[k] = __json_serial(d[k])

    return json.dumps(kvPairs, default=__json_serial)


class ActionContext(NamedTuple):
    action: Action
    chat_id: int
    schedule: Schedule

    def toJson(self) -> str:
        return _toJson(self)


class FeedbackContext(NamedTuple):
    action: Action
    chat_id: int
    schedules: List[Schedule]
    success: bool

    def toJson(self) -> str:
        return _toJson(self)


def parseActionMsg(msg: str) -> ActionContext:
    j = json.loads(msg)
    if 'action' not in j or 'schedule' not in j:
        return None

    action_type = Action(int(j['action']))
    chat_id = int(j['chat_id'])
    if action_type == Action.List:
        return ActionContext(
            Action(int(j['action'])),
            chat_id,
            None
        )

    sch_json = j['schedule']
    return ActionContext(
        Action(int(j['action'])),
        chat_id,
        Schedule(
            sch_json['lunch_id'],
            sch_json['owner_id'],
            sch_json['title'],
            datetime.strptime(sch_json['time'], '%Y%m%d%H%M'),
            ScheduleType(int(sch_json['type']))
        )
    )


def parseActionFeedback(msg: str) -> FeedbackContext:
    j = json.loads(msg)
    if 'action' not in j or 'schedules' not in j or 'success' not in j:
        return None

    sch_json = j['schedules']
    schedules = []
    for sch_json in j['schedules']:
        schedules.append(
            Schedule(
                sch_json['lunch_id'],
                sch_json['owner_id'],
                sch_json['title'],
                datetime.strptime(sch_json['time'], '%Y%m%d%H%M'),
                ScheduleType(int(sch_json['type']))
            )
        )
    return FeedbackContext(
        Action(int(j['action'])),
        int(j['chat_id']),
        schedules,
        j['success']
    )
