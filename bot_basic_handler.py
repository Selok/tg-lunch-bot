from datetime import datetime, time
from pytz import timezone
from setting import BotConfig, ChannelConfig, TimestampConfig, ReplyStrMap


def get_user_info(update):

    user = update.message.from_user
    # msg  = 'You talk with user {} and his user ID: {} '.format(user['username'], user['id'])
    user_id = user["id"]
    user_name = user["username"]
    first_name = user["first_name"]
    last_name = user["last_name"]
    print(f"User id : {user_id}")
    return user_id, first_name, last_name, user_name


def getDateTime():
    now = datetime.now()
    current_time = now.strftime("%Y/%m/%d %H:%M:%S")
    return current_time


def printT(msg):
    print(f"[{getDateTime()}] {msg}")


def get_hhmm():
    hhmm = datetime.now(timezone(TimestampConfig.time_zone)).strftime("%H:%M")
    printT("get_hhmm = " + str(hhmm))
    return hhmm


def check_within_weekdays():
    day_of_week = datetime.today().isoweekday()
    print("day_of_week " + str(day_of_week))
    return 1 <= day_of_week <= 5
