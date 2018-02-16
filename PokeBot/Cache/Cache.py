import logging
from datetime import datetime

log = logging.getLogger('Cache')


class Cache(object):

    def __init__(self):
        self._mon_hist = {}
        self._egg_hist = {}
        self._raid_hist = {}

    def monster_expiration(self, mon_id, expiration=None):
        if expiration is not None:
            self._mon_hist[mon_id] = expiration
        return self._mon_hist.get(mon_id)

    def egg_expiration(self, egg_id, expiration=None):
        if expiration is not None:
            self._egg_hist[egg_id] = expiration
        return self._egg_hist.get(egg_id)

    def raid_expiration(self, raid_id, expiration=None):
        if expiration is not None:
            self._raid_hist[raid_id] = expiration
        return self._raid_hist.get(raid_id)

    def clean_and_save(self):
        self._clean_hist()

    def _clean_hist(self):
        for hist in (self._mon_hist, self._egg_hist, self._raid_hist):
            old = []
            now = datetime.utcnow()
            for key, expiration in hist.items():
                if expiration < now:
                    old.append(key)
            for key in old:
                del hist[key]
