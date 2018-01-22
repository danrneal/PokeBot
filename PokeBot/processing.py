#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from datetime import datetime, timedelta
from .utils import get_args, Dicts

log = logging.getLogger('processing')
args = get_args()


async def in_q(client, bot_number):
    while True:
        obj = Dicts.bots[bot_number]['in_queue'].get()
        try:
            if obj['type'] == "pokemon":
                process_pokemon(client, bot_number, obj)
            elif obj['type'] == 'egg':
                process_egg(client, bot_number, obj)
            elif obj['type'] == "raid":
                process_raid(client, bot_number, obj)
            else:
                pass
        except Exception as e:
            log.error((
                "Encountered error during DM processing: {}: {}"
            ).format(type(e).__name__, e))


def check_pokemon_filter(filters, pkmn):
    passed = False
    cp = pkmn['cp']
    level = pkmn['level']
    iv = pkmn['iv']
    size = pkmn['size']
    gender = pkmn['gender']
    for filt_ct in range(len(filters)):
        filt = filters[filt_ct]
        if cp != '?':
            if not filt.check_cp(cp):
                continue
        else:
            if filt.ignore_missing is True:
                continue
        if level != '?':
            if not filt.check_level(level):
                continue
        else:
            if filt.ignore_missing is True:
                continue
        if iv != '?':
            if not filt.check_iv(float(iv)):
                continue
        else:
            if filt.ignore_missing is True:
                continue
        if size != 'unknown':
            if not filt.check_size(size):
                continue
        else:
            if filt.ignore_missing is True:
                continue
        if gender != 'unknown':
            if not filt.check_gender(gender):
                continue
        else:
            if filt.ignore_missing is True:
                continue
        passed = True
        break
    return passed


def check_egg_filter(settings, egg):
    level = egg['raid_level']
    if level < settings['min_level']:
        return False
    if level > settings['max_level']:
        return False
    return True


async def process_pokemon(client, bot_number, pkmn):
    user_ids = []
    pkmn_id = pkmn['pkmn_id']
    lat, lng = pkmn['lat'], pkmn['lng']
    name = pkmn['pkmn']
    for user_id in Dicts.bots[bot_number]['filters']:
        user_dict = Dicts.bots[bot_number]['filters'][user_id]
        user_filter_dict = Dicts.bots[bot_number]['pokemon_settings'][user_id]
        if (user_dict['paused'] is True or
            user_filter_dict['enabled'] is False or
                pkmn_id not in user_filter_dict['filters']):
            continue
        filters = user_filter_dict['filters'][pkmn_id]
        passed = check_pokemon_filter(filters, pkmn)
        if not passed:
            continue
        if (len(Dicts.geofences) > 0 and
                pkmn['geofence'].lower() not in user_dict['areas']):
            continue
        user_ids.append(user_id)
    if len(user_ids) > 0:
        if Dicts.loc_service and 'street_num' not in pkmn:
            Dicts.loc_service.add_optional_arguments([lat, lng], pkmn)
        log.info("{} DM notification has been triggered!".format(name))
        await Dicts.bots[bot_number]['alarm'].pokemon_alert(
            client, bot_number, pkmn, user_ids)


async def process_egg(client, bot_number, egg):
    user_ids = []
    lat, lng = egg['lat'], egg['lng']
    gym_id = egg['id']
    for user_id in Dicts.bots[bot_number]['filters']:
        user_dict = Dicts.bots[bot_number]['filters'][user_id]
        user_filter_dict = Dicts.bots[bot_number]['egg_settings'][user_id]
        if (user_dict['paused'] is True or
                user_filter_dict['enabled'] is False):
            continue
        passed = check_egg_filter(user_filter_dict, egg)
        if not passed:
            continue
        if (len(Dicts.geofences) > 0 and
                egg['geofence'].lower() not in user_dict['areas']):
            continue
        user_ids.append(user_id)
    if len(user_ids) > 0:
        if Dicts.loc_service and 'street_num' not in egg:
            Dicts.loc_service.add_optional_arguments([lat, lng], egg)
        log.info("Egg ({}) notification has been triggered!".format(gym_id))
        await Dicts.bots[bot_number]['alarm'].raid_egg_alert(
            client, bot_number, egg, user_ids)


async def process_raid(client, bot_number, raid):
    user_ids = []
    pkmn_id = raid['pkmn_id']
    lat, lng = raid['lat'], raid['lng']
    gym_id = raid['id']
    for user_id in Dicts.bots[bot_number]['filters']:
        user_dict = Dicts.bots[bot_number]['filters'][user_id]
        user_filter_dict = Dicts.bots[bot_number]['raid_settings'][user_id]
        if (user_dict['paused'] is True or
            user_filter_dict['enabled'] is False or
                pkmn_id not in user_filter_dict['filters']):
            continue
        if (len(Dicts.geofences) > 0 and
                raid['geofence'].lower() not in user_dict['areas']):
            continue
        user_ids.append(user_id)
    if len(user_ids) > 0:
        if Dicts.loc_service and 'street_num' not in raid:
            Dicts.loc_service.add_optional_arguments([lat, lng], raid)
        log.info("Raid ({}) notification has been triggered!".format(gym_id))
        await Dicts.bots[bot_number]['alarm'].raid_alert(
            client, bot_number, raid, user_ids)


async def out_q(bot_number):
    while True:
        while len(Dicts.bots[bot_number]['timestamps']) >= 120:
            if datetime.utcnow() - Dicts.bots[bot_number]['timestamps'][
                    0] > timedelta(minutes=1):
                Dicts.bots[bot_number]['timestamps'].pop(0)
        msg_params = Dicts.bots[bot_number]['out_queue'].get()
        if datetime.utcnow() - msg_params[2]['timestamp'] > timedelta(
                minutes=1):
            log.warning((
                "Bot queue is {} seconds behind..., consider adding more bots."
            ).format((datetime.utcnow() - msg_params[2][
                'timestamp']).total_seconds()))
        try:
            await msg_params[2]['destination'].send(
                msg_params[2].get('msg'),
                embed=msg_params[2].get('embed')
            )
            log.info('Sent msg to {}'.format(
                msg_params[2]['destination'].name))
            Dicts.bots[bot_number]['timestamps'].append(datetime.utcnow())
            if Dicts.bots[bot_number]['out_queue'].empty():
                Dicts.bots[bot_number]['count'] = 0
        except Exception as e:
            log.error((
                "Encountered error during DM processing: {}: {}"
            ).format(type(e).__name__, e))
