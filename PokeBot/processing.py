#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import discord
import asyncio
from datetime import datetime
from random import randint
from .utils import (get_args, Dicts, get_default_genders,# get_loc,
                    get_static_map_url)

log = logging.getLogger('processing')

args = get_args()
dicts = Dicts()


def clean_hist(bot_number):
    old = []
    for id_ in dicts.bots[bot_number]['pokemon_hist']:
        if dicts.bots[bot_number]['pokemon_hist'][id_] < datetime.utcnow():
            old.append(id_)
    for id_ in old:
        del dicts.bots[bot_number]['pokemon_hist'][id_]
    old = []
    for id_ in dicts.bots[bot_number]['raid_hist']:
        if dicts.bots[bot_number]['raid_hist'][id_][
                'raid_end'] < datetime.utcnow():
            old.append(id_)
    for id_ in old:
        del dicts.bots[bot_number]['raid_hist'][id_]

def check_pokemon_filter(filters, pkmn):
    passed = False
    cp = pkmn['cp']
    level = pkmn['level']
    iv = pkmn['iv']
    size = pkmn['size']
    gender = pkmn['gender']
    name = pkmn['pkmn']
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


def process_pokemon(bot_number, pkmn):
    user_ids = []
    for user_id in dicts.bots[bot_number]['filters']:
        if (dicts.bots[bot_number]['filters'][user_id]['pokemon_setttings'][
            'enabled'] is False or
            pkmn_id not in dicts.bots[bot_number]['filters'][user_id][
                'pokemon_setttings']['filters']):
            return
        filters = dicts.bots[bot_number]['filters'][user_id][
            'pokemon_setttings']['filters'][pkmn_id]
        passed = check_pokemon_filter(filters, pkmn)
        if not passed:
            return
        user_ids.append(user_id)
    log.info("{} DM notification has been triggered!".format(name))
    if len(user_ids) > 0:
        dicts.bots[bot_number]['alarm'].pokemon_alert(
            bot_number, pkmn, user_ids)


async def out_q(bot_number):
    while not dicts.bots[bot_number]['out_queue'].empty():
        while len(dicts.bots[bot_number]['timestamps']) >= 120:
            if (datetime.utcnow() - dicts.bots[bot_number]['timestamps'][
                    0]).total_seconds() > 60:
                dicts.bots[bot_number]['timestamps'].pop(0)
            else:
                await asyncio.sleep(0.5)
        msg_params = await dicts.bots[bot_number]['out_queue'].get()
        await msg_params[2]['destination'].send(
            msg_params[2].get('msg'),
            embed=msg_params[2].get('embed')
        )
        log.info('Sent msg to {}'.format(
            msg_params[2]['destination'].name))
        dicts.bots[bot_number]['timestamps'].append(datetime.utcnow())
    dicts.bots[bot_number]['count'] = 0
    await asyncio.sleep(0.5)


async def in_q(bot_number):
    last_clean = datetime.utcnow()
    while True:
        if not dicts.bots[bot_number]['in_queue'].empty():
            obj = await dicts.bots[bot_number]['in_queue'].get()
            if datetime.utcnow() - last_clean > timedelta(minutes=3):
                clean_hist()
                last_clean = datetime.utcnow()
#            try:
            if obj['type'] == "pokemon":
                process_pokemon(bot_number, obj)
            elif obj['type'] == 'egg':
                process_egg(bot_number, obj)
            elif obj['type'] == "raid":
                process_raid(bot_number, obj)
            else:
                pass
#            except Exception as e:
#                log.error("Encountered error during DM processing: {}: {}".format(
#                    type(e).__name__, e))
        await out_q(bot_number)

