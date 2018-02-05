import logging
import time


class BaseEvent(object):

    def __init__(self, kind):
        self._log = logging.getLogger(kind)
        self.id = time.time()

    @classmethod
    def check_for_none(cls, cast, val, default):
        return cast(val) if val is not None else default
