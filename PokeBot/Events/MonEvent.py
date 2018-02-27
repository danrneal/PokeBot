from datetime import datetime
from .BaseEvent import BaseEvent
from .. import Unknown
from ..Utilities.MonUtils import (
    get_pokemon_size, get_base_types, get_type_emoji, get_gender_sym,
    get_move_type, get_move_damage, get_move_dps, get_move_duration,
    get_move_energy
)
from ..Utilities.GenUtils import (
    get_gmaps_link, get_applemaps_link, get_time_as_str, get_seconds_remaining,
    get_weather_emoji
)


class MonEvent(BaseEvent):

    def __init__(self, data):
        super(MonEvent, self).__init__('monster')
        check_for_none = BaseEvent.check_for_none
        self.enc_id = data['encounter_id']
        self.monster_id = int(data['pokemon_id'])
        self.disappear_time = datetime.utcfromtimestamp(data['disappear_time'])
        self.time_left = get_seconds_remaining(self.disappear_time)
        self.spawn_start = check_for_none(
            int, data.get('spawn_start'), Unknown.REGULAR)
        self.spawn_end = check_for_none(
            int, data.get('spawn_end'), Unknown.REGULAR)
        self.spawn_verified = check_for_none(bool, data.get('verified'), False)
        self.lat = float(data['latitude'])
        self.lng = float(data['longitude'])
        self.weather_id = check_for_none(
            int, data.get('weather'), Unknown.TINY)
        self.boosted_weather_id = check_for_none(
            int, data.get('boosted_weather'), 0)
        self.mon_lvl = check_for_none(
            int, data.get('pokemon_level'), Unknown.TINY)
        self.cp = check_for_none(int, data.get('cp'), Unknown.TINY)
        self.atk_iv = check_for_none(
            int, data.get('individual_attack'), Unknown.TINY)
        self.def_iv = check_for_none(
            int, data.get('individual_defense'), Unknown.TINY)
        self.sta_iv = check_for_none(
            int, data.get('individual_stamina'), Unknown.TINY)
        if Unknown.is_not(self.atk_iv, self.def_iv, self.sta_iv):
            self.iv = (
                100 * (self.atk_iv + self.def_iv + self.sta_iv) / float(45)
            )
        else:
            self.iv = Unknown.SMALL
        self.form_id = check_for_none(int, data.get('form'), 0)
        self.quick_id = check_for_none(int, data.get('move_1'), Unknown.TINY)
        self.quick_type = get_move_type(self.quick_id)
        self.quick_damage = get_move_damage(self.quick_id)
        self.quick_dps = get_move_dps(self.quick_id)
        self.quick_duration = get_move_duration(self.quick_id)
        self.quick_energy = get_move_energy(self.quick_id)
        self.charge_id = check_for_none(int, data.get('move_2'), Unknown.TINY)
        self.charge_type = get_move_type(self.charge_id)
        self.charge_damage = get_move_damage(self.charge_id)
        self.charge_dps = get_move_dps(self.charge_id)
        self.charge_duration = get_move_duration(self.charge_id)
        self.charge_energy = get_move_energy(self.charge_id)
        self.gender = get_gender_sym(check_for_none(
            int, data.get('gender'), Unknown.TINY))
        self.height = check_for_none(float, data.get('height'), Unknown.SMALL)
        self.weight = check_for_none(float, data.get('weight'), Unknown.SMALL)
        if Unknown.is_not(self.height, self.weight):
            self.size_id = get_pokemon_size(
                self.monster_id, self.height, self.weight)
        else:
            self.size_id = Unknown.SMALL
        self.types = get_base_types(self.monster_id)
        self.name = self.monster_id
        self.geofence = Unknown.REGULAR
        self.custom_dts = {}

    def generate_dts(self, locale):
        time = get_time_as_str(self.disappear_time, self.lat, self.lng)
        form_name = locale.get_form_name(self.monster_id, self.form_id)
        weather_name = locale.get_weather_name(self.weather_id)
        boosted_weather_name = locale.get_weather_name(self.boosted_weather_id)
        type1 = locale.get_type_name(self.types[0])
        type2 = locale.get_type_name(self.types[1])
        dts = self.custom_dts.copy()
        dts.update({
            'encounter_id': self.enc_id,
            'mon_name': locale.get_pokemon_name(self.monster_id),
            'mon_id': self.monster_id,
            'mon_id_3': "{:03}".format(self.monster_id),
            'time_left': time[0],
            '12h_time': time[1],
            '24h_time': time[2],
            'spawn_start': self.spawn_start,
            'spawn_end': self.spawn_end,
            'spawn_verified': self.spawn_verified,
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
            'boosted_weather_id': self.boosted_weather_id,
            'boosted_weather': boosted_weather_name,
            'boosted_weather_or_empty': (
                '' if self.boosted_weather_id == 0
                else Unknown.or_empty(boosted_weather_name)),
            'boosted_weather_emoji':
                get_weather_emoji(self.boosted_weather_id),
            'boosted_or_empty': locale.get_boosted_text() if (
                Unknown.is_not(self.boosted_weather_id) and
                self.boosted_weather_id != 0) else '',
            'mon_lvl': self.mon_lvl,
            'cp': self.cp,
            'iv_0': (
                "{:.0f}".format(self.iv) if Unknown.is_not(self.iv)
                else Unknown.TINY
            ),
            'iv': (
                "{:.1f}".format(self.iv) if Unknown.is_not(self.iv)
                else Unknown.SMALL
            ),
            'iv_2': (
                "{:.2f}".format(self.iv) if Unknown.is_not(self.iv)
                else Unknown.SMALL
            ),
            'atk': self.atk_iv,
            'def': self.def_iv,
            'sta': self.sta_iv,
            'type1': type1,
            'type1_or_empty': Unknown.or_empty(type1),
            'type1_emoji': Unknown.or_empty(get_type_emoji(self.types[0])),
            'type2': type2,
            'type2_or_empty': Unknown.or_empty(type2),
            'type2_emoji': Unknown.or_empty(get_type_emoji(self.types[1])),
            'types': (
                "{}/{}".format(type1, type2)
                if Unknown.is_not(type2) else type1),
            'types_emoji': (
                "{}{}".format(
                    get_type_emoji(self.types[0]),
                    get_type_emoji(self.types[1]))
                if Unknown.is_not(type2) else get_type_emoji(self.types[0])),
            'form': form_name,
            'form_or_empty': Unknown.or_empty(form_name),
            'form_id': self.form_id,
            'form_id_3': "{:03d}".format(self.form_id),
            'quick_move': locale.get_move_name(self.quick_id),
            'quick_id': self.quick_id,
            'quick_type_id': self.quick_type,
            'quick_type': locale.get_type_name(self.quick_type),
            'quick_type_emoji': get_type_emoji(self.quick_type),
            'quick_damage': self.quick_damage,
            'quick_dps': self.quick_dps,
            'quick_duration': self.quick_duration,
            'quick_energy': self.quick_energy,
            'charge_move': locale.get_move_name(self.charge_id),
            'charge_id': self.charge_id,
            'charge_type_id': self.charge_type,
            'charge_type': locale.get_type_name(self.charge_type),
            'charge_type_emoji': get_type_emoji(self.charge_type),
            'charge_damage': self.charge_damage,
            'charge_dps': self.charge_dps,
            'charge_duration': self.charge_duration,
            'charge_energy': self.charge_energy,
            'gender': self.gender,
            'height': self.height,
            'height_2': (
                "{:.2f}".format(self.height) if Unknown.is_not(self.height)
                else Unknown.SMALL
            ),
            'weight': self.weight,
            'weight_2': (
                "{:.2f}".format(self.weight) if Unknown.is_not(self.height)
                else Unknown.SMALL
            ),
            'size': locale.get_size_name(self.size_id),
            'big_karp': (
                'big' if self.monster_id == 129 and Unknown.is_not(self.weight)
                and self.weight >= 13.13 else ''),
            'tiny_rat': (
                'tiny' if self.monster_id == 19 and Unknown.is_not(self.weight)
                and self.weight <= 2.41 else '')
        })
        return dts
