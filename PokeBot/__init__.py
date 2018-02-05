import os
import binascii

config = {
    'ROOT_PATH': os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
}
not_so_secret_url = binascii.unhexlify(
    '68747470733a2f2f6d6f6e73746572696d616765732e746b2f76312e342f'
).decode("utf-8")


class Unknown:
    TINY = '?'
    SMALL = '???'
    REGULAR = 'unknown'
    EMPTY = ''
    __unknown_set = {TINY, SMALL, REGULAR}

    @classmethod
    def is_(cls, *args):
        for arg in args:
            if arg in cls.__unknown_set:
                return True
        return False

    @classmethod
    def is_not(cls, *args):
        for arg in args:
            if arg in cls.__unknown_set:
                return False
        return True

    @classmethod
    def or_empty(cls, val, default=EMPTY):
        return val if val not in cls.__unknown_set else default
