import os


class BotConfig:
    token = os.environ.get("TOKEN")


class ChannelConfig:
    controller_id = os.environ.get("CONTROLLER_ID")
    chat_id = os.environ.get("CHAT_ID")


class TimestampConfig:
    time_zone = os.environ.get("TIME_ZONE", "Asia/Hong_Kong")
    time_lunch = os.environ.get("LUNCH_TIME", "11:30")
    time_traffic = str(
        os.environ.get("TRAFFIC_TIME", ["07:00", "12:00", "16:30"])
    ).split(",")


class ReplyStrMap:
    please_reroll = os.environ.get("please_reroll", "")
    too_noisy = os.environ.get("too_noisy", "")
    foul_1 = os.environ.get("foul_1", "")
