from .DiscordAlarm import DiscordAlarm
from .UserAlarm import UserAlarm


def alarm_factory(settings, max_attempts, api_key, kind):
    if kind == 'discord':
        return DiscordAlarm(settings, max_attempts, api_key)
    elif kind == 'user':
        return UserAlarm(settings, api_key)
    else:
        raise ValueError("{} is not a valid alarm type!".format(kind))
