import logging
import json
import re
from glob import glob
from .GenUtils import get_path

log = logging.getLogger('GymUtils')


def get_team_id(team_name):
    try:
        name = str(team_name).lower()
        if not hasattr(get_team_id, 'ids'):
            get_team_id.ids = {}
            files = glob(get_path('locales/*.json'))

            for file_ in files:
                with open(file_, 'r') as f:
                    j = json.loads(f.read())
                    j = j['teams']
                    for id_ in j:
                        nm = j[id_].lower()
                        get_team_id.ids[nm] = int(id_)

        if name in get_team_id.ids:
            return get_team_id.ids[name]
        else:
            return int(name)
    except ValueError:
        raise ValueError((
            "Unable to interpret `{}` as a valid  team name or id."
        ).format(team_name))


def create_regex(pattern):
    return re.compile(str(pattern), re.I)


def match_regex_dict(reg_exs, name):
    name = str(name)
    for reg_ex in reg_exs:
        if reg_ex.search(name):
            return True
    return False
