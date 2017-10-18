#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder
from .WebhookStructs import Webhook
from .Locale import Locale
from .utils import Dicts, get_args, get_time_as_str

logging.basicConfig(
    format='[%(name)10.10s][%(levelname)8.8s] %(message)s',
    level=logging.INFO
)
log = logging.getLogger('ManageWebhook')
args = get_args()
tf = TimezoneFinder()


class ManageWebhook(object):

    def __init__(self):
        self.__locale = Locale(args.locale)
        self.__pokemon_hist = {}
        self.__raid_hist = {}
        self.__geofences = []
        if str(args.geofences[0]).lower() != 'none':
            self.__geofences = list(args.master_geofences.values())
        self.__queue = asyncio.Queue()

    async def update(self, obj):
        await self.__queue.put(obj)

    async def connect(self):
        last_clean = datetime.utcnow()
        while True:
            if self.__queue.qsize() > 300:
                log.warning((
                    "Queue length is at {}... this may be causing a delay " +
                    "in notifications."
                ).format(self.__queue.qsize()))
            while self.__queue.empty():
                await asyncio.sleep(1)
            data = await self.__queue.get()
            obj = Webhook.make_object(data)
            if obj is not None:
                if datetime.utcnow() - last_clean > timedelta(minutes=3):
                    self.clean_hist()
                    last_clean = datetime.utcnow()
                try:
                    if obj['type'] == "pokemon":
                        self.process_pokemon(obj)
                    elif obj['type'] == 'egg':
                        self.process_egg(obj)
                    elif obj['type'] == "raid":
                        self.process_raid(obj)
                    else:
                        pass
                except Exception as e:
                    log.error((
                        "Encountered error during processing: {}: {}"
                    ).format(type(e).__name__, e))

    def clean_hist(self):
        old = []
        for id_ in self.__pokemon_hist:
            if self.__pokemon_hist[id_] < datetime.utcnow():
                old.append(id_)
        for id_ in old:
            del self.__pokemon_hist[id_]
        old = []
        for id_ in self.__raid_hist:
            if self.__raid_hist[id_]['raid_end'] < datetime.utcnow():
                old.append(id_)
        for id_ in old:
            del self.__raid_hist[id_]

    def process_pokemon(self, pkmn):
        id_ = pkmn['id']
        if id_ in self.__pokemon_hist:
            return
        self.__pokemon_hist[id_] = pkmn['disappear_time']
        pkmn_id = pkmn['pkmn_id']
        name = self.__locale.get_pokemon_name(pkmn_id)
        lat, lng = pkmn['lat'], pkmn['lng']
        pkmn['geofence'] = self.check_geofences(name, lat, lng)
        if len(self.__geofences) > 0 and pkmn['geofence'] == 'unknown':
            return
        pkmn['pkmn'] = name
        quick_id = pkmn['quick_id']
        charge_id = pkmn['charge_id']
        time_str = get_time_as_str(
            pkmn['disappear_time'], tf.timezone_at(lng=lng, lat=lat))
        iv = pkmn['iv']
        pkmn.update({
            'pkmn': name,
            'time_left': time_str[0],
            '12h_time': time_str[1],
            '24h_time': time_str[2],
            'iv_0': "{:.0f}".format(iv) if iv != '?' else '?',
            'iv': "{:.1f}".format(iv) if iv != '?' else '?',
            'iv_2': "{:.2f}".format(iv) if iv != '?' else '?',
            'quick_move': self.__locale.get_move_name(quick_id),
            'charge_move': self.__locale.get_move_name(charge_id),
            'form': self.__locale.get_form_name(pkmn_id, pkmn['form_id'])
        })
        for name, mgr in Dicts.managers.items():
            mgr.update(pkmn)
        for bot in Dicts.bots:
            bot['in_queue'].put(pkmn)

    def process_egg(self, egg):
        gym_id = egg['id']
        raid_end = egg['raid_end']
        if gym_id in self.__raid_hist:
            old_raid_end = self.__raid_hist[gym_id]['raid_end']
            if old_raid_end == raid_end:
                return
        self.__raid_hist[gym_id] = dict(raid_end=raid_end, pkmn_id=0)
        lat, lng = egg['lat'], egg['lng']
        egg['geofence'] = self.check_geofences('Raid', lat, lng)
        if len(self.__geofences) > 0 and egg['geofence'] == 'unknown':
            return
        time_str = get_time_as_str(
            egg['raid_end'], tf.timezone_at(lng=lng, lat=lat))
        start_time_str = get_time_as_str(
            egg['raid_begin'], tf.timezone_at(lng=lng, lat=lat))
        egg.update({
            'time_left': time_str[0],
            '12h_time': time_str[1],
            '24h_time': time_str[2],
            'begin_time_left': start_time_str[0],
            'begin_12h_time': start_time_str[1],
            'begin_24h_time': start_time_str[2]
        })
        for name, mgr in Dicts.managers.items():
            mgr.update(egg)
        for bot in Dicts.bots:
            bot['in_queue'].put(egg)

    def process_raid(self, raid):
        gym_id = raid['id']
        pkmn_id = raid['pkmn_id']
        raid_end = raid['raid_end']
        if gym_id in self.__raid_hist:
            old_raid_end = self.__raid_hist[gym_id]['raid_end']
            old_raid_pkmn = self.__raid_hist[gym_id].get('pkmn_id', 0)
            if old_raid_end == raid_end and old_raid_pkmn == pkmn_id:
                return
        self.__raid_hist[gym_id] = dict(raid_end=raid_end, pkmn_id=pkmn_id)
        lat, lng = raid['lat'], raid['lng']
        raid['geofence'] = self.check_geofences('Raid', lat, lng)
        if len(self.__geofences) > 0 and raid['geofence'] == 'unknown':
            return
        quick_id = raid['quick_id']
        charge_id = raid['charge_id']
        name = self.__locale.get_pokemon_name(pkmn_id)
        raid_pkmn = {
            'pkmn': name,
            'cp': raid['cp'],
            'iv': 100,
            'level': 20,
            'def': 15,
            'atk': 15,
            'sta': 15,
            'gender': 'unknown',
            'size': 'unknown',
            'form_id': '?',
            'quick_id': quick_id,
            'charge_id': charge_id
        }
        time_str = get_time_as_str(
            raid['raid_end'], tf.timezone_at(lng=lng, lat=lat))
        start_time_str = get_time_as_str(
            raid['raid_begin'], tf.timezone_at(lng=lng, lat=lat))
        raid.update({
            'pkmn': name,
            'time_left': time_str[0],
            '12h_time': time_str[1],
            '24h_time': time_str[2],
            'begin_time_left': start_time_str[0],
            'begin_12h_time': start_time_str[1],
            'begin_24h_time': start_time_str[2],
            'quick_move': self.__locale.get_move_name(quick_id),
            'charge_move': self.__locale.get_move_name(charge_id),
            'form': self.__locale.get_form_name(pkmn_id, raid_pkmn['form_id'])
        })
        for name, mgr in Dicts.managers.items():
            mgr.update(raid)
        for bot in Dicts.bots:
            bot['in_queue'].put(raid)

    def check_geofences(self, name, lat, lng):
        for gf in self.__geofences:
            if gf.contains(lat, lng):
                return gf.get_name()
        return 'unknown'
