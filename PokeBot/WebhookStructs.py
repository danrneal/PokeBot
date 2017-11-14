#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from .utils import (get_pokemon_size, get_pokemon_gender, get_gmaps_link,
                    get_applemaps_link, get_image_url)

log = logging.getLogger('WebhookStructs')


def check_for_none(type_, val, default):
    return type_(val) if val is not None else default


class Webhook:

    @staticmethod
    def make_object(data):
        try:
            if data.get('type') == 'pokemon':
                return Webhook.pokemon(data.get('message'))
            elif (data.get('type') == 'gym' or
                  data.get('type') == 'gym_details'):
                return Webhook.gym(data.get('message'))
            elif data.get('type') == 'raid':
                return Webhook.egg_or_raid(data.get('message'))
            else:
                pass
        except Exception as e:
            log.error((
                "Encountered error while processing webhook ({}: {})"
            ).format(type(e).__name__, e))
        return None

    @staticmethod
    def pokemon(data):
        quick_id = check_for_none(int, data.get('move_1'), '?')
        charge_id = check_for_none(int, data.get('move_2'), '?')
        lat, lng = data['latitude'], data['longitude']
        pkmn = {
            'type': "pokemon",
            'id': data['encounter_id'],
            'pkmn_id': int(data['pokemon_id']),
            'disappear_time': datetime.utcfromtimestamp(
                data['disappear_time']),
            'lat': float(data['latitude']),
            'lng': float(data['longitude']),
            'cp': check_for_none(int, data.get('cp'), '?'),
            'level': check_for_none(int, data.get('pokemon_level'), '?'),
            'iv': '?',
            'atk': check_for_none(int, data.get('individual_attack'), '?'),
            'def': check_for_none(int, data.get('individual_defense'), '?'),
            'sta': check_for_none(int, data.get('individual_stamina'), '?'),
            'quick_id': quick_id,
            'charge_id': charge_id,
            'height': check_for_none(float, data.get('height'), 'unkn'),
            'weight': check_for_none(float, data.get('weight'), 'unkn'),
            'gender': get_pokemon_gender(check_for_none(
                int, data.get('gender'), '?')),
            'form_id': check_for_none(int, data.get('form'), '?'),
            'size': 'unknown',
            'tiny_rat': '',
            'big_karp': '',
            'gmaps': get_gmaps_link(lat, lng),
            'applemaps': get_applemaps_link(lat, lng)
        }
        if pkmn['atk'] != '?' or pkmn['def'] != '?' or pkmn['sta'] != '?':
            pkmn['iv'] = float((
                (pkmn['atk'] + pkmn['def'] + pkmn['sta']) * 100) / float(45))
        else:
            pkmn['atk'], pkmn['def'], pkmn['sta'] = '?', '?', '?'
        if pkmn['height'] != 'unkn' or pkmn['weight'] != 'unkn':
            pkmn['size'] = get_pokemon_size(
                pkmn['pkmn_id'], pkmn['height'], pkmn['weight'])
            pkmn['height'] = "{:.2f}".format(pkmn['height'])
            pkmn['weight'] = "{:.2f}".format(pkmn['weight'])
        if pkmn['pkmn_id'] == 19 and pkmn['size'] == 'tiny':
            pkmn['tiny_rat'] = 'tiny'
        if pkmn['pkmn_id'] == 129 and pkmn['size'] == 'big':
            pkmn['big_karp'] = 'big'
        if pkmn['form_id'] == 0:
            pkmn['form_id'] = '?'
        return pkmn

    @staticmethod
    def gym(data):
        gym = {
            'type': "gym",
            'id': data.get('gym_id',  data.get('id')),
            'lat': float(data['latitude']),
            'lng': float(data['longitude']),
            'name': check_for_none(str, data.get('name'), 'unknown').strip(),
            'description': check_for_none(
                str, data.get('description'), 'unknown').strip(),
            'url': check_for_none(str, data.get('url'), 'unknown')
        }
        return gym

    @staticmethod
    def egg_or_raid(data):
        pkmn_id = check_for_none(int, data.get('pokemon_id'), 0)
        if pkmn_id == 0:
            return Webhook.egg(data)
        return Webhook.raid(data)

    @staticmethod
    def egg(data):
        raid_end = None
        raid_begin = None
        if 'raid_begin' in data:
            raid_begin = datetime.utcfromtimestamp(data['raid_begin'])
        elif 'battle' in data:
            raid_begin = datetime.utcfromtimestamp(data['battle'])
        elif 'start' in data:
            raid_begin = datetime.utcfromtimestamp(data['start'])
        if 'raid_end' in data:
            raid_end = datetime.utcfromtimestamp(data['raid_end'])
        egg = {
            'type': 'egg',
            'id': data.get('raid_seed'),
            'raid_level': check_for_none(int, data.get('level'), 0),
            'raid_end': raid_end,
            'raid_begin': raid_begin,
            'lat': float(data['latitude']),
            'lng': float(data['longitude']),
            'gym_name': check_for_none(str, data.get('gym_name'), 'unknown'),
            'gym_url': check_for_none(
                str, data.get('gym_url'),
                get_image_url("eggs/<raid_level>.png")),
            'team_id': check_for_none(int, data.get('team'), 0)
        }
        egg['gmaps'] = get_gmaps_link(egg['lat'], egg['lng'])
        egg['applemaps'] = get_applemaps_link(egg['lat'], egg['lng'])
        return egg

    @staticmethod
    def raid(data):
        quick_id = check_for_none(int, data.get('move_1'), '?')
        charge_id = check_for_none(int, data.get('move_2'), '?')
        raid_end = None
        raid_begin = None
        if 'raid_begin' in data:
            raid_begin = datetime.utcfromtimestamp(data['raid_begin'])
        elif 'battle' in data:
            raid_begin = datetime.utcfromtimestamp(data['battle'])
        elif 'start' in data:
            raid_begin = datetime.utcfromtimestamp(data['start'])
        if 'raid_end' in data:
            raid_end = datetime.utcfromtimestamp(data['raid_end'])
        raid = {
            'type': 'raid',
            'id': data.get('raid_seed'),
            'pkmn_id': check_for_none(int, data.get('pokemon_id'), 0),
            'cp': check_for_none(int, data.get('cp'), '?'),
            'quick_id': quick_id,
            'charge_id': charge_id,
            'raid_level': check_for_none(int, data.get('level'), 0),
            'raid_end': raid_end,
            'raid_begin': raid_begin,
            'lat': float(data['latitude']),
            'lng': float(data['longitude']),
            'gym_name': check_for_none(str, data.get('gym_name'), 'unknown'),
            'gym_url': check_for_none(
                str, data.get('gym_url'),
                get_image_url("monsters/<pkmn_id_3>_<form_id_or_empty>.png")),
            'team_id': check_for_none(int, data.get('team'), 0)
        }
        raid['gmaps'] = get_gmaps_link(raid['lat'], raid['lng'])
        raid['applemaps'] = get_applemaps_link(raid['lat'], raid['lng'])
        return raid
