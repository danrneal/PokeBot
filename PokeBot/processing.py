#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from datetime import datetime
from .utils import get_args, Dicts

log = logging.getLogger('processing')
args = get_args()


async def in_q(client, bot_number):
    while True:
        if not Dicts.bots[bot_number]['in_queue'].empty():
            if Dicts.bots[bot_number]['in_queue'].qsize() > 300:
                log.warning((
                    "Bot queue length is at {}... this may be causing a " +
                    "delay in notifications, consider adding more bots."
                ).format(Dicts.bots[bot_number]['in_queue'].qsize()))
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
        await out_q(bot_number)


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


def process_pokemon(client, bot_number, pkmn):
    user_ids = []
    pkmn_id = pkmn['pkmn_id']
    lat, lng = pkmn['lat'], pkmn['lng']
    name = pkmn['pkmn']
    for user_id in Dicts.bots[bot_number]['filters']:
        if (Dicts.bots[bot_number]['filters'][user_id]['paused'] is True or
            Dicts.bots[bot_number]['pokemon_setttings'][user_id][
                'enabled'] is False or
            pkmn_id not in Dicts.bots[bot_number]['pokemon_setttings'][
                user_id]['filters']):
            continue
        filters = Dicts.bots[bot_number]['pokemon_setttings']['filters'][
            pkmn_id]
        passed = check_pokemon_filter(filters, pkmn)
        if not passed:
            continue
        if (len(Dicts.bots[bot_number]['filters'][user_id]['areas']) > 0 and
            pkmn['geofence'] not in Dicts.bots[bot_number]['filters'][user_id][
                'areas']):
            continue
        user_ids.append(user_id)
    if len(user_ids) > 0:
        if Dicts.bots[bot_number]['loc_service']:
            Dicts.bots[bot_number]['loc_service'].add_optional_arguments(
                [lat, lng], pkmn)
        log.info("{} DM notification has been triggered!".format(name))
        Dicts.bots[bot_number]['alarm'].pokemon_alert(
            client, bot_number, pkmn, user_ids)


def process_egg(client, bot_number, egg):
    user_ids = []
    lat, lng = egg['lat'], egg['lng']
    gym_id = egg['id']
    for user_id in Dicts.bots[bot_number]['filters']:
        if (Dicts.bots[bot_number]['filters'][user_id]['paused'] is True or
            Dicts.bots[bot_number]['egg_settings'][user_id][
                'enabled'] is False):
            continue
        passed = check_egg_filter(
            Dicts.bots[bot_number]['egg_settings'][user_id], egg)
        if not passed:
            continue
        if (len(Dicts.bots[bot_number]['filters'][user_id]['areas']) > 0 and
            egg['geofence'] not in Dicts.bots[bot_number]['filters'][user_id][
                'areas']):
            continue
        user_ids.append(user_id)
    if len(user_ids) > 0:
        if Dicts.bots[bot_number]['loc_service']:
            Dicts.bots[bot_number]['loc_service'].add_optional_arguments(
                [lat, lng], egg)
        log.info("Egg ({}) notification has been triggered!".format(gym_id))
        Dicts.bots[bot_number]['alarm'].raid_egg_alert(
            client, bot_number, egg, user_ids)


def process_raid(client, bot_number, raid):
    user_ids = []
    pkmn_id = raid['pkmn_id']
    lat, lng = raid['lat'], raid['lng']
    gym_id = raid['id']
    for user_id in Dicts.bots[bot_number]['filters']:
        if (Dicts.bots[bot_number]['filters'][user_id]['paused'] is True or
            Dicts.bots[bot_number]['raid_setttings'][user_id][
                'enabled'] is False or
            pkmn_id not in Dicts.bots[bot_number]['raid_setttings'][user_id][
                'filters']):
            continue
        if (len(Dicts.bots[bot_number]['filters'][user_id]['areas']) > 0 and
            egg['geofence'] not in Dicts.bots[bot_number]['filters'][user_id][
                'areas']):
            continue
        user_ids.append(user_id)
    if len(user_ids) > 0:
        if Dicts.bots[bot_number]['loc_service']:
            Dicts.bots[bot_number]['loc_service'].add_optional_arguments(
                [lat, lng], raid)
        log.info("Raid ({}) notification has been triggered!".format(gym_id))
        Dicts.bots[bot_number]['alarm'].raid_alert(
            client, bot_number, raid, user_ids)


async def out_q(bot_number):
    while not Dicts.bots[bot_number]['out_queue'].empty():
        while len(Dicts.bots[bot_number]['timestamps']) >= 120:
            if (datetime.utcnow() - Dicts.bots[bot_number]['timestamps'][
                    0]).total_seconds() > 60:
                Dicts.bots[bot_number]['timestamps'].pop(0)
            else:
                await asyncio.sleep(0.5)
        msg_params = await Dicts.bots[bot_number]['out_queue'].get()
        await msg_params[2]['destination'].send(
            msg_params[2].get('msg'),
            embed=msg_params[2].get('embed')
        )
        log.info('Sent msg to {}'.format(msg_params[2]['destination'].name))
        Dicts.bots[bot_number]['timestamps'].append(datetime.utcnow())
    Dicts.bots[bot_number]['count'] = 0
    await asyncio.sleep(0.5)
