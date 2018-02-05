import logging
from .MonEvent import MonEvent
from .EggEvent import EggEvent
from .RaidEvent import RaidEvent

log = logging.getLogger('Events')


def event_factory(data):
    try:
        kind = data['type']
        message = data['message']
        if kind == 'pokemon':
            return MonEvent(message)
        elif kind == 'raid' and not message.get('pokemon_id'):
            return EggEvent(message)
        elif kind == 'raid' and message.get('pokemon_id'):
            return RaidEvent(message)
    except Exception as e:
        log.error((
            "Encountered error while converting webhook data ({}: {})"
        ).format(type(e).__name__, e))
