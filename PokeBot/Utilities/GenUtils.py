import logging
import os
import sys
import pytz
import json
from random import randint
from datetime import datetime, timedelta
from collections import OrderedDict
from timezonefinder import TimezoneFinder
from .. import config, not_so_secret_url

log = logging.getLogger('GenUtils')

tf = TimezoneFinder()


def get_path(path):
    if not os.path.isabs(path):
        path = os.path.join(config['ROOT_PATH'], path)
    return path


def parse_bool(value):
    try:
        b = str(value).lower()
        if b in {'t', 'true', 'y', 'yes'}:
            return True
        elif b in {'f', 'false', 'n', 'no'}:
            return False
    except Exception:
        pass
    raise ValueError('Not a valid boolean')


def reject_leftover_parameters(dict_, location):
    if len(dict_) > 0:
        log.error("Unknown parameters at {}: ".format(location))
        log.error(dict_.keys())
        log.error("Please consult the PokeBot wiki for accepted parameters.")
        sys.exit(1)


def get_weather_emoji(weather_id):
    return {
        1: "<:weather_clear:409041567534415873>",
        2: "<:weather_rain:409041567412912130>",
        3: "<:weather_partly_cloudy:409041567790268428>",
        4: "<:weather_cloudy:409041567517769728>",
        5: "<:weather_windy:409041567593136128>",
        6: "<:weather_snow:409041567551062016>",
        7: "<:weather_foggy:409041567358386177>"
    }.get(weather_id, '')


def get_gmaps_link(lat, lng):
    latlng = '{},{}'.format(repr(lat), repr(lng))
    return 'http://maps.google.com/maps?q={}'.format(latlng)


def get_applemaps_link(lat, lng):
    latlon = '{},{}'.format(repr(lat), repr(lng))
    return 'http://maps.apple.com/maps?daddr={}&z=10&t=s&dirflg=w'.format(
        latlon)


def get_static_map_url(settings, api_key=None):
    if not parse_bool(settings.get('enabled', 'True')):
        return None
    width = settings.get('width', '250')
    height = settings.get('height', '125')
    maptype = settings.get('maptype', 'roadmap')
    zoom = settings.get('zoom', '15')
    center = '{},{}'.format('<lat>', '<lng>')
    query_center = 'center={}'.format(center)
    query_markers = 'markers=color:red%7C{}'.format(center)
    query_size = 'size={}x{}'.format(width, height)
    query_zoom = 'zoom={}'.format(zoom)
    query_maptype = 'maptype={}'.format(maptype)
    map_ = (
        'https://maps.googleapis.com/maps/api/staticmap?' +
        query_center + '&' + query_markers + '&' +
        query_maptype + '&' + query_size + '&' + query_zoom
    )

    if api_key is not None:
        gmaps_key = api_key[randint(0, len(api_key) - 1)]
        map_ += '&key={}'.format(gmaps_key)

    return map_


def get_time_as_str(t, lat, lng):
    timezone = tf.timezone_at(lng=lng, lat=lat)
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
    time_12 = (
        disappear_time.strftime("%I:%M:%S") +
        disappear_time.strftime("%p").lower()
    )
    time_24 = disappear_time.strftime("%H:%M:%S")
    return time_left, time_12, time_24


def get_seconds_remaining(t):
    seconds = (t - datetime.utcnow()).total_seconds()
    return seconds


def get_image_url(suffix):
    return not_so_secret_url + suffix


def msg_split(msg):
    msg_split1 = msg[:len(msg[:1999].rsplit('\n', 1)[0])]
    msg_split2 = msg[len(msg[:1999].rsplit('\n', 1)[0]):]
    if msg_split1.count('```') % 2 != 0:
        msg_split1 += '\n```'
        msg_split2 = '\n```' + msg_split2
    return [msg_split1, msg_split2]


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def update_filters(user_filters, filter_file, f):
    for user_id in user_filters:
        for section in user_filters[user_id]:
            user_filters[user_id][section]['filters'] = OrderedDict(sorted(
                user_filters[user_id][section]['filters'].items(),
                key=lambda t: t[0]
            ))
            for filt_name in user_filters[user_id][section]['filters']:
                user_filters[user_id][section]['filters'][
                    filt_name] = OrderedDict(sorted(
                        user_filters[user_id][section]['filters'][
                            filt_name].items(),
                        key=lambda t: t[0]
                    ))
    f.seek(0)
    json.dump(user_filters, f, indent=4)
    f.truncate()
    try:
        mod = datetime.utcfromtimestamp(os.path.getmtime(
            get_path(filter_file + '.hr_backup')))
    except OSError:
        mod = datetime.utcnow() - timedelta(minutes=60)
    if datetime.utcnow() - mod >= timedelta(minutes=60):
        with open(get_path(
            filter_file + '.hr_backup'), 'w+',
            encoding="utf-8"
        ) as hr:
            json.dump(user_filters, hr, indent=4)
    try:
        mod = datetime.utcfromtimestamp(os.path.getmtime(
            get_path(filter_file + '.day_backup')))
    except OSError:
        mod = datetime.utcnow() - timedelta(hours=24)
    if datetime.utcnow() - mod >= timedelta(hours=24):
        with open(get_path(
            filter_file + '.day_backup'), 'w+',
            encoding="utf-8"
        ) as day:
            json.dump(user_filters, day, indent=4)


class LoggerWriter:

    def __init__(self, level):
        self.level = level
        self.linebuf = ''

    def write(self, message):
        for line in message.rstrip().splitlines():
            self.level(line.rstrip())

    def flush(self):
        self.level(sys.stderr)
