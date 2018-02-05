import logging
from datetime import datetime
from ..Utilities.GenUtils import get_image_url

log = logging.getLogger('Cache')


class Cache(object):

    def __init__(self):
        self._pokemon_hist = {}
        self._egg_hist = {}
        self._raid_hist = {}

    def get_pokemon_expiration(self, pkmn_id):
        return self._pokemon_hist.get(pkmn_id)

    def update_pokemon_expiration(self, pkmn_id, expiration):
        self._pokemon_hist[pkmn_id] = expiration

    def get_egg_expiration(self, gym_id):
        return self._egg_hist.get(gym_id)

    def update_egg_expiration(self, gym_id, expiration):
        self._egg_hist[gym_id] = expiration

    def get_raid_expiration(self, gym_id):
        return self._raid_hist.get(gym_id)

    def update_raid_expiration(self, gym_id, expiration):
        self._raid_hist[gym_id] = expiration

    def clean_and_save(self):
        self._clean_hist()

    def _clean_hist(self):
        for hist in (self._pokemon_hist, self._egg_hist, self._raid_hist):
            old = []
            now = datetime.utcnow()
            for key, expiration in hist.items():
                if expiration < now:
                    old.append(key)
            for key in old:
                del hist[key]
