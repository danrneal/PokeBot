import os
import logging
import pickle
import portalocker
from ..utils import get_path
from .Cache import Cache

log = logging.getLogger('FileCache')


class FileCache(Cache):

    def __init__(self, name):
        super(FileCache, self).__init__()
        self._name = name
        self._file = get_path(os.path.join("cache", "{}.cache".format(name)))
        if os.path.isfile(self._file):
            self._load()
        else:
            with portalocker.Lock(self._file, mode="wb+") as f:
                pickle.dump({}, f, protocol=pickle.HIGHEST_PROTOCOL)

    def _load(self):
        with portalocker.Lock(self._file, mode="rb") as f:
            data = pickle.load(f)
            self._pokemon_hist = data.get('pokemon_hist', {})
            self._egg_hist = data.get('egg_hist', {})
            self._raid_hist = data.get('raid_hist', {})

    def _save(self):
        data = {
            'pokemon_hist': self._pokemon_hist,
            'egg_hist': self._egg_hist,
            'raid_hist': self._raid_hist
        }
        try:
            with portalocker.Lock(self._file, timeout=5, mode="wb+") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            log.error("Encountered error while saving cache: {}: {}".format(
                type(e).__name__, e))
