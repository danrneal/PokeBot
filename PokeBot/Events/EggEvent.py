from datetime import datetime
from .BaseEvent import BaseEvent
from .. import Unknown
from ..Utilities.GenUtils import (
    get_time_as_str, get_seconds_remaining, get_gmaps_link, get_applemaps_link,
    get_weather_emoji
)


class EggEvent(BaseEvent):

    def __init__(self, data):
        super(EggEvent, self).__init__('egg')
        check_for_none = BaseEvent.check_for_none
        self.gym_id = data.get('gym_id')
        self.hatch_time = datetime.utcfromtimestamp(
            data.get('start') or data.get('raid_begin'))
        self.time_left = get_seconds_remaining(self.hatch_time)
        self.raid_end = datetime.utcfromtimestamp(
            data.get('end') or data.get('raid_end'))
        self.lat = float(data['latitude'])
        self.lng = float(data['longitude'])
        self.weather_id = check_for_none(
            int, data.get('weather'), Unknown.TINY)
        self.egg_lvl = check_for_none(int, data.get('level'), 0)
        self.gym_name = check_for_none(
            str, data.get('name'), Unknown.REGULAR).strip()
        self.gym_image = check_for_none(str, data.get('url'), Unknown.REGULAR)
        self.gym_sponsor = check_for_none(
            int, data.get('sponsor'), Unknown.SMALL)
        self.gym_park = check_for_none(str, data.get('park'), Unknown.REGULAR)
        self.current_team_id = check_for_none(
            int, data.get('team'), Unknown.TINY)
        self.name = self.gym_id
        self.geofence = Unknown.REGULAR
        self.custom_dts = {}

    def generate_dts(self, locale):
        hatch_time = get_time_as_str(self.hatch_time, self.lat, self.lng)
        raid_end_time = get_time_as_str(self.raid_end, self.lat, self.lng)
        weather_name = locale.get_weather_name(self.weather_id)
        dts = self.custom_dts.copy()
        dts.update({
            'gym_id': self.gym_id,
            'hatch_time_left': hatch_time[0],
            '12h_hatch_time': hatch_time[1],
            '24h_hatch_time': hatch_time[2],
            'raid_time_left': raid_end_time[0],
            '12h_raid_end': raid_end_time[1],
            '24h_raid_end': raid_end_time[2],
            'lat': self.lat,
            'lng': self.lng,
            'lat_5': "{:.5f}".format(self.lat),
            'lng_5': "{:.5f}".format(self.lng),
            'gmaps': get_gmaps_link(self.lat, self.lng),
            'applemaps': get_applemaps_link(self.lat, self.lng),
            'geofence': self.geofence,
            'weather_id': self.weather_id,
            'weather': weather_name,
            'weather_or_empty': Unknown.or_empty(weather_name),
            'weather_emoji': get_weather_emoji(self.weather_id),
            'egg_lvl': self.egg_lvl,
            'gym_name': self.gym_name,
            'gym_image': self.gym_image,
            'gym_sponsor': self.gym_sponsor,
            'gym_park': self.gym_park,
            'team_id': self.current_team_id,
            'team_name': locale.get_team_name(self.current_team_id),
            'team_leader': locale.get_leader_name(self.current_team_id)
        })
        return dts
