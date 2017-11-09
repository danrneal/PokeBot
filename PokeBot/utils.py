#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os
import sys
import configargparse
import pytz
import json
from glob import glob
from datetime import datetime, timedelta
from .Geofence import load_geofence_file

log = logging.getLogger('utils')


def get_path(path):
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), path)
    return path


def get_args():
    if '-cf' not in sys.argv and '--config' not in sys.argv:
        config_files = [get_path('../config/config.ini')]
    parser = configargparse.ArgParser(default_config_files=config_files)
    parser.add_argument(
        '-cf', '--config',
        is_config_file=True,
        help='Configuration file'
    )
    parser.add_argument(
        '-m', '--manager_count',
        type=int,
        default=1,
        help='Number of managers to start.'
    )
    parser.add_argument(
        '-M', '--manager_name',
        type=str,
        action='append',
        default=[],
        help='Names of Manager processes to start.'
    )
    parser.add_argument(
        '-a', '--alarms',
        type=str,
        action='append',
        default=[],
        help='Alarms configuration file. default: alarms.json'
    )
    parser.add_argument(
        '-f', '--filters',
        type=str,
        action='append',
        default=[],
        help='Filters configuration file. default: filters.json'
    )
    parser.add_argument(
        '-gf', '--geofences',
        type=str,
        action='append',
        default=[],
        help='Geofence configuration file. default: None'
    )
    parser.add_argument(
        '-L', '--locale',
        type=str,
        default='en',
        choices=['de', 'en', 'es', 'fr', 'it', 'ko', 'zh_hk'],
        help=(
            'Locale for Pokemon and Move names: default en, check locale ' +
            'folder for more options'
        )
    )
    parser.add_argument(
        '-ma', '--max_attempts',
        type=int,
        default=3,
        help=('Maximum number of attempts an alarm makes to send a ' +
              'notification.')
    )
    parser.add_argument(
        '-port', '--port',
        type=int,
        help='Port for webhook',
        default=4000
    )
    parser.add_argument(
        '-token', '--tokens',
        type=str,
        action='append',
        default=[],
        help='List of tokens for Discord bots',
        required=True
    )
    parser.add_argument(
        '-bcid', '--bot_client_ids',
        type=int,
        action='append',
        default=[],
        help='List of client ids for Discord Bots',
        required=True
    )
    parser.add_argument(
        '-com', '--command_channels',
        type=int,
        action='append',
        default=[],
        help='Channel ID that users input commands',
        required=True
    )
    parser.add_argument(
        '-alert', '--alert_role',
        type=str.lower,
        default='@everyone',
        help='Role for users that can use the bot'
    )
    parser.add_argument(
        '-muted', '--muted_role',
        type=str.lower,
        default=None,
        help='Role for muted users'
    )
    parser.add_argument(
        '-gmaps', '--gmaps_keys',
        type=str,
        action='append',
        default=[],
        help='Specify a Google API key or list of keys to use'
    )
    parser.add_argument(
        '-aa', '--all_areas',
        action='store_true',
        help=(
            'default to sub to all areas when true otherwise, default is ' +
            'no areas'
        ),
        default=False
    )

    args = parser.parse_args()

    files = glob(get_path('../alarms/*.json'))
    for file_ in files:
        args.alarms.append(file_)

    files = glob(get_path('../filters/*.json'))
    for file_ in files:
        args.filters.append(file_)

    files = glob(get_path('../geofences/*.txt'))
    for file_ in files:
        args.geofences.append(file_)
    if len(args.geofences) == 0:
        args.geofences = [None]

    if len(args.tokens) != len(args.bot_client_ids):
        log.critical("Token - Client ID mismatch")
        sys.exit(1)

    args.alarms = sorted(args.alarms)
    args.filters = sorted(args.filters)
    args.geofences = sorted(args.geofences)

    for list_ in [args.filters, args.alarms, args.geofences]:
        if len(list_) != 1 and len(list_) != args.manager_count:
            log.critical(
                "Number of arguments must be either 1 for all managers " +
                "or {} equal to Manager Count. Please provided the " +
                "correct number of arguments.".format(args.manager_count)
            )
            log.critical('Manager Count: {}'.format(args.manager_count))
            log.critical('Filters Count: {}'.format(len(args.filters)))
            log.critical('Alarms Count: {}'.format(len(args.alarms)))
            log.critical('Geofence Count: {}'.format(len(args.geofences)))
            sys.exit(1)

    for i in range(len(args.alarms)):
        if args.alarms[i].split('/')[-1].replace(
            'alarms_', '').replace('.json', '') == args.filters[i].split('/')[
                -1].replace('filters_', '').replace('.json', ''):
            args.manager_name.append(args.alarms[i].split('/')[-1].replace(
                'alarms_', '').replace('.json', ''))
        else:
            break

    args.master_geofences = {}
    args.geofence_names = []
    for geofence_file in args.geofences:
        geofences = load_geofence_file(geofence_file)
        names = []
        for geofence in geofences:
            name = geofence.get_name()
            names.append(name)
            if name not in args.master_geofences:
                args.master_geofences[name] = geofence
        args.geofence_names.append(names)
    if len(args.geofence_names) == 0:
        args.geofence_names = [None]

    return args


class Dicts(object):
    managers = {}
    bots = []
    loc_service = None
    locale = None
    geofences = []
    roles = {}
    hr_backup = 0
    day_backup = 0
    female_only = [29, 30, 31, 113, 115, 124, 238, 241, 242]
    male_only = [32, 33, 34, 106, 107, 128, 236, 237]
    genderless = [81, 82, 100, 101, 120, 121, 137, 201, 233]
    type_col = {
        'bug': 0xA8B820,
        'dark': 0x705848,
        'dragon': 0x7038F8,
        'electric': 0xF8D030,
        'fairy': 0xEE99AC,
        'fighting': 0xC03028,
        'fire': 0xF08030,
        'flying': 0xA890F0,
        'ghost': 0x705898,
        'grass': 0x78C850,
        'ground': 0xE0C068,
        'ice': 0x98D8D8,
        'normal': 0xA8A878,
        'poison': 0xA040A0,
        'psychic': 0xF85888,
        'rock': 0xB8A038,
        'steel': 0xB8B8D0,
        'water': 0x6890F0
    }
    info_msg = (
        "Hello there!\n\n" +
        "`!set [pokemon/default/all] [IV] CP[CP] L[level] [gender]` to add " +
        "an alert for a given pokemon based on it's characteristics, any of " +
        "the characteristics can be left blank,\n\n" +
        "`!delete [pokemon/default/all]` to remove an alert for a given " +
        "pokemon\n\n" +
        "`!reset [pokemon/all]` to reset an alert for a given pokemon to " +
        "your default alert characteristics\n\n" +
        "`!pause` or `!p` to pause all notifcations,\n\n" +
        "`!resume` or `!r` to resume all alerts,\n\n" +
        "`!activate [area/all]` to resume a given area,\n\n" +
        "`!deactivate [area/all]` to pause a given area,\n\n" +
        "`!areas` to see what areas area available to pause or resume,\n\n" +
        "`!alerts` to see your alert settings,\n\n"
        "`!dex [pokemon]` to get pokedex information for a given " +
        "pokemon,\n\n" +
        "`!status` to see which bots are currently online,\n\n" +
        "`!help` or `!commands` to see this message,\n\n" +
        "`!donate` to see donation information for this project.\n\n" +
        "It is possible to add or delete multiple pokemon or areas by " +
        "putting pokemon on seperate lines or separating them with commas.\n" +
        "Commands should be in the #custom_filters channel.\n\n"
    )


def update_dicts():
    master = {}
    for bot in Dicts.bots:
        master.update(bot['filters'])
    if Dicts.hr_backup == 0:
        Dicts.hr_backup = datetime.utcnow()
    elif datetime.utcnow() - Dicts.hr_backup > timedelta(minutes=60):
        with open(get_path('../user_dicts/user_filters.json')) as f:
            filters = json.load(f)
        with open(get_path(
                '../user_dicts/user_filters_hr_backup.json'), 'w') as f:
            json.dump(filters, f, indent=4)
        Dicts.hr_backup = datetime.utcnow()
    if Dicts.day_backup == 0:
        Dicts.day_backup = datetime.utcnow()
    elif datetime.utcnow() - Dicts.day_backup > timedelta(hours=24):
        with open(get_path('../user_dicts/user_filters.json')) as f:
            filters = json.load(f)
        with open(get_path(
                '../user_dicts/user_filters_day_backup.json'), 'w') as f:
            json.dump(filters, f, indent=4)
        Dicts.day_backup = datetime.utcnow()
    with open(get_path('../user_dicts/user_filters.json'), 'w') as f:
        json.dump(master, f, indent=4)


def contains_arg(line, args):
    for word in args:
        if ('<{}>'.format(word)) in line:
            return True
    return False


def parse_boolean(val):
    b = str(val).lower()
    if b in {'t', 'true', 'y', 'yes'}:
        return True
    if b in ('f', 'false', 'n', 'no'):
        return False
    return None


def reject_leftover_parameters(dict_, location):
    if len(dict_) > 0:
        log.critical("Unknown parameters at {}: ".format(location))
        log.critical(dict_.keys())
        log.critical(
            "Please consult the documentation for accepted parameters."
        )
        sys.exit(1)


def require_and_remove_key(key, _dict, location):
    if key in _dict:
        return _dict.pop(key)
    else:
        log.critical(
            "The parameter '{}' is required for {}. Please check " +
            "documentation for correct formatting.".format(key, location))
        sys.exit(1)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def truncate(msg):
    msg_split1 = msg[:len(msg[:1999].rsplit('\n', 1)[0])]
    msg_split2 = msg[len(msg[:1999].rsplit('\n', 1)[0]):]
    if msg_split1.count('```') % 2 != 0:
        msg_split1 += '\n```'
        msg_split2 = '\n```' + msg_split2
    return [msg_split1, msg_split2]


def get_pkmn_id(pokemon_name):
    name = pokemon_name.lower()
    if not hasattr(get_pkmn_id, 'ids'):
        get_pkmn_id.ids = {}
        files = glob(get_path('../locales/*.json'))
        for file_ in files:
            with open(file_, 'r', encoding="utf-8") as f:
                j = json.loads(f.read())
                j = j['pokemon']
                for id_ in j:
                    nm = j[id_].lower()
                    get_pkmn_id.ids[nm] = int(id_)
    return get_pkmn_id.ids.get(name)


def get_base_height(pokemon_id):
    if not hasattr(get_base_height, 'info'):
        get_base_height.info = {}
        file_ = get_path('../data/base_stats.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
        for id_ in j:
            get_base_height.info[int(id_)] = j[id_].get('height')
    return get_base_height.info.get(pokemon_id)


def get_base_weight(pokemon_id):
    if not hasattr(get_base_weight, 'info'):
        get_base_weight.info = {}
        file_ = get_path('../data/base_stats.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
        for id_ in j:
            get_base_weight.info[int(id_)] = j[id_].get('weight')
    return get_base_weight.info.get(pokemon_id)


def size_ratio(pokemon_id, height, weight):
    height_ratio = height / get_base_height(pokemon_id)
    weight_ratio = weight / get_base_weight(pokemon_id)
    return height_ratio + weight_ratio


def get_pokemon_size(pokemon_id, height, weight):
    size = size_ratio(pokemon_id, height, weight)
    if size < 1.5:
        return 'tiny'
    elif size <= 1.75:
        return 'small'
    elif size < 2.25:
        return 'normal'
    elif size <= 2.5:
        return 'large'
    else:
        return 'big'


def get_pokemon_gender(gender):
    if gender == 1:
        return u'\u2642'
    elif gender == 2:
        return u'\u2640'
    elif gender == 3:
        return u'\u26b2'
    return '?'


def get_color(color_id):
    try:
        if float(color_id) == 1:
            return 0xffb3d9
        elif float(color_id) == 2:
            return 0xff3377
        elif float(color_id) == 3:
            return 0xffcc99
        elif float(color_id) == 4:
            return 0xffcc33
        elif float(color_id) == 5:
            return 0x660066
        elif float(color_id) < 25:
            return 0x9d9d9d
        elif float(color_id) < 50:
            return 0xffffff
        elif float(color_id) < 82:
            return 0x1eff00
        elif float(color_id) < 90:
            return 0x0070dd
        elif float(color_id) < 100:
            return 0xa335ee
        elif float(color_id) == 100:
            return 0xff8000
    except ValueError:
        return 0x4F545C


def get_gmaps_link(lat, lng):
    latlng = '{},{}'.format(repr(lat), repr(lng))
    return 'http://maps.google.com/maps?q={}'.format(latlng)


def get_applemaps_link(lat, lng):
    latlng = '{},{}'.format(repr(lat), repr(lng))
    return 'http://maps.apple.com/maps?daddr={}&z=10&t=s&dirflg=w'.format(
        latlng)


def get_static_map_url(settings, api_key=None):
    if not parse_boolean(settings.get('enabled', 'True')):
        return None
    width = settings.get('width', '250')
    height = settings.get('height', '125')
    maptype = settings.get('maptype', 'roadmap')
    zoom = settings.get('zoom', '12')
    center = '{},{}'.format('<lat>', '<lng>')
    query_center = 'center={}'.format(center)
    query_markers = 'markers=color:red%7C{}'.format(center)
    query_size = 'size={}x{}'.format(width, height)
    query_zoom = 'zoom={}'.format(zoom)
    query_maptype = 'maptype={}'.format(maptype)
    map_ = ('https://maps.googleapis.com/maps/api/staticmap?' +
            query_center + '&' + query_markers + '&' +
            query_maptype + '&' + query_size + '&' + query_zoom)
    if api_key is not None:
        map_ += ('&key=%s' % api_key)
    return map_


def get_time_as_str(t, timezone=None):
    try:
        timezone = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        log.error("Invalid timezone")
        timezone = None
    s = (t - datetime.utcnow()).total_seconds()
    (m, s) = divmod(s, 60)
    (h, m) = divmod(m, 60)
    d = timedelta(hours=h, minutes=m, seconds=s)
    if timezone is not None:
        disappear_time = datetime.now(tz=timezone) + d
    else:
        disappear_time = datetime.now() + d
    time_left = "%dm %ds" % (m, s) if h == 0 else "%dh %dm" % (h, m)
    time_12 = (disappear_time.strftime("%I:%M:%S") +
               disappear_time.strftime("%p").lower())
    time_24 = disappear_time.strftime("%H:%M:%S")
    return time_left, time_12, time_24
