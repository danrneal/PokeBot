import os
import logging
import pickle
import portalocker
from ..Utilities.GenUtils import get_path
from . import Cache

log = logging.getLogger('FileCache')


class FileCache(Cache):

    def __init__(self, name):
        super(FileCache, self).__init__()
        self._name = name
        self._file = get_path(os.path.join("cache", "{}.cache".format(name)))
        cache_folder = get_path("cache")
        if not os.path.exists(cache_folder):
            os.makedirs(cache_folder)
        if os.path.isfile(self._file):
            self._load()
        else:
            self._save()

    def _load(self):
        try:
            with portalocker.Lock(self._file, mode="rb") as f:
                data = pickle.load(f)
                self._mon_hist = data.get('mon_hist', {})
                self._egg_hist = data.get('egg_hist', {})
                self._raid_hist = data.get('raid_hist', {})
        except Exception as e:
            log.error(
                "There was an error attempting to load the cache. The old " +
                "cache will be overwritten."
            )
            log.error("{}: {}".format(type(e).__name__, e))

    def _save(self):
        data = {
            'mon_hist': self._mon_hist,
            'egg_hist': self._egg_hist,
            'raid_hist': self._raid_hist
        }
        try:
            temp = self._file + ".new"
            with portalocker.Lock(self._file + ".lock", timeout=5, mode="wb+"):
                with portalocker.Lock(temp, timeout=5, mode="wb+") as f:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
                    if os.path.exists(self._file):
                        os.remove(self._file)
                    os.rename(temp, self._file)
        except Exception as e:
            log.error((
                "Encountered error while saving cache: {}: {}"
            ).format(type(e).__name__, e))
