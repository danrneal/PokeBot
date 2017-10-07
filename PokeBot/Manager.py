#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import json
import asyncio
import os
import sys
import geocoder
import re
from random import randint
from datetime import datetime, timedelta
from .DiscordAlarm import DiscordAlarm
from .Filter import load_pokemon_section, Geofence, load_egg_section
from .utils import (require_and_remove_key, get_path, get_args, contains_arg,
                    get_time_as_str, Dicts)

log = logging.getLogger('Manager')
args = get_args()
dicts = Dicts()


class Manager(object):

    def __init__(self, name, locale, timezone, max_attempts, geofence_file,
                 filter_file, alarm_file):
        self.__name = str(name).lower()
        self.__api_req = {'REVERSE_LOCATION': False}
        self.__locale = locale
        self.__pokemon_name = {}
        self.__move_name = {}
        self.update_locales()
        self.__timezone = timezone
        self.__pokemon_settings = {}
        self.__raid_settings = {}
        self.__egg_settings = {}
        self.__pokemon_hist = {}
        self.__raid_hist = {}
        self.__gym_info = {}
        self.load_filter_file(get_path(filter_file))
        self.__geofences = []
        if str(geofence_file).lower() != 'none':
            self.load_geofence_file(get_path(geofence_file))
        self.load_alarms_file(get_path(alarm_file), int(max_attempts))
        self.__queue = asyncio.Queue()
        log.info("Manager '{}' successfully created.".format(self.__name))

    async def update(self, obj):
        await self.__queue.put(obj)

    def get_name(self):
        return self.__name

    def load_filter_file(self, file_path):
        try:
            with open(file_path, 'r', encoding="utf-8") as f:
                filters = json.load(f)
            if type(filters) is not dict:
                log.critical(
                    "Filters file's must be a JSON object: { " +
                    "\"pokemon\":{...},... }"
                )
                sys.exit(1)
            self.__pokemon_settings = load_pokemon_section(
                require_and_remove_key('pokemon', filters, "Filters file."))
            self.__egg_settings = load_egg_section(
                require_and_remove_key("eggs", filters, "Filters file."))
            self.__raid_settings = load_pokemon_section(
                require_and_remove_key('raids', filters, "Filters file."))
            log.info("Loaded Filters from file at {}".format(file_path))
            return
        except ValueError as e:
            log.critical((
                "Encountered error while loading Filters: {}: {}"
            ).format(type(e).__name__, e))
            log.critical(
                "Encountered a 'ValueError' while loading the Filters file. " +
                "This typically means your file isn't in the correct json " +
                "format. Try loading your file contents into a json validator."
            )
        except IOError as e:
            log.critical((
                "Encountered error while loading Filters: {}: {}"
            ).format(type(e).__name__, e))
            log.critical(
                "Unable to find a filters file at {}. Please check that " +
                "this file exists and has the correct permissions."
            ).format(file_path)
        except Exception as e:
            log.critical((
                "Encountered error while loading Filters: {}: {}"
            ).format(type(e).__name__, e))
        sys.exit(1)

    def load_geofence_file(self, file_path):
        count = 0
        try:
            geofences = []
            name_pattern = re.compile("(?<=\[)([^]]+)(?=\])")
            coor_patter = re.compile("[-+]?[0-9]*\.?[0-9]*" + "[ \t]*,[ \t]*" +
                                     "[-+]?[0-9]*\.?[0-9]*")
            with open(file_path, 'r') as f:
                lines = f.read().splitlines()
            name = "geofence"
            points = []
            for line in lines:
                line = line.strip()
                match_name = name_pattern.search(line)
                if match_name:
                    if len(points) > 0:
                        geofences.append(Geofence(name, points))
                        count += 1
                        points = []
                    name = match_name.group(0)
                elif coor_patter.match(line):
                    lat, lng = map(float, line.split(","))
                    points.append([lat, lng])
                else:
                    log.critical((
                        "Geofence was unable to parse this line: {}"
                    ).format(line))
                    log.critical(
                        "All lines should be either '[name]' or 'lat,lng'."
                    )
                    sys.exit(1)
            geofences.append(Geofence(name, points))
            log.info("{} geofences added.".format(str(count + 1)))
            self.__geofences = geofences
            return
        except IOError as e:
            log.critical((
                "IOError: Please make sure a file with read/write " +
                "permissions exsist at {}").format(file_path))
        except Exception as e:
            log.critical((
                "Encountered error while loading Geofence: {}: {}"
            ).format(type(e).__name__, e))
        sys.exit(1)

    def load_alarms_file(self, file_path, max_attempts):
        try:
            with open(file_path, 'r') as f:
                alarm = json.load(f)
            if type(alarm) is not dict:
                log.critical("Alarms file must be a dictionary")
                sys.exit(1)
            args = {
                'street', 'street_num', 'address', 'postal',
                'neighborhood', 'sublocality', 'city', 'county', 'state',
                'country'
            }
            self.__api_req['REVERSE_LOCATION'] = self.__api_req[
                'REVERSE_LOCATION'] or contains_arg(str(alarm), args)
            self.__alarm = DiscordAlarm(alarm, max_attempts)
            log.info("Active Discord alarm found.")
            return
        except ValueError as e:
            log.critical((
                "Encountered error while loading Alarms file: {}: {}"
            ).format(type(e).__name__, e))
            log.critical(
                "Encountered a 'ValueError' while loading the Alarms file. " +
                "This typically means your file isn't in the correct json " +
                "format. Try loading your file contents into a json validator."
            )
        except IOError as e:
            log.critical((
                "Encountered error while loading Alarms: {}: {}"
            ).format(type(e).__name__, e))
            log.critical((
                "Unable to find a filters file at {}. Please check that " +
                "this file exists and has the correct permissions."
            ).format(file_path))
        except Exception as e:
            log.critical((
                "Encountered error while loading Alarms: {}: {}"
            ).format(type(e).__name__, e))
        sys.exit(1)

    async def connect(self):
        last_clean = datetime.utcnow()
        while True:
            while self.__queue.empty():
                await asyncio.sleep(1)
            obj = await self.__queue.get()
            if datetime.utcnow() - last_clean > timedelta(minutes=3):
                self.clean_hist()
                last_clean = datetime.utcnow()
            try:
                if obj['type'] == "pokemon":
                    self.process_pokemon(obj)
                elif obj['type'] == "gym":
                    self.process_gym(obj)
                elif obj['type'] == 'egg':
                    self.process_egg(obj)
                elif obj['type'] == "raid":
                    self.process_raid(obj)
                else:
                    pass
            except Exception as e:
                log.error("Encountered error during processing: {}: {}".format(
                    type(e).__name__, e))

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

    def check_pokemon_filter(self, filters, pkmn):
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

    def check_egg_filter(self, settings, egg):
        level = egg['raid_level']
        if level < settings['min_level']:
            return False
        if level > settings['max_level']:
            return False
        return True

    def process_pokemon(self, pkmn):
        id_ = pkmn['id']
        if id_ in self.__pokemon_hist:
            return
        self.__pokemon_hist[id_] = pkmn['disappear_time']
        pkmn_id = pkmn['pkmn_id']
        name = self.__pokemon_name[pkmn_id]
        lat, lng = pkmn['lat'], pkmn['lng']
        pkmn['geofence'] = self.check_geofences(name, lat, lng)
        if len(self.__geofences) > 0 and pkmn['geofence'] == 'unknown':
            return
        pkmn['pkmn'] = name
        time_str = get_time_as_str(pkmn['disappear_time'], self.__timezone)
        iv = pkmn['iv']
        quick_id = pkmn['quick_id']
        charge_id = pkmn['charge_id']
        pkmn.update({
            'pkmn': name,
            'time_left': time_str[0],
            '12h_time': time_str[1],
            '24h_time': time_str[2],
            'iv_0': "{:.0f}".format(iv) if iv != '?' else '?',
            'iv': "{:.1f}".format(iv) if iv != '?' else '?',
            'iv_2': "{:.2f}".format(iv) if iv != '?' else '?',
            'quick_move': self.__move_name.get(quick_id, 'unknown'),
            'charge_move': self.__move_name.get(charge_id, 'unknown')
        })
        for bot in dicts.bots:
            bot['in_queue'].put(pkmn)
        if (self.__pokemon_settings['enabled'] is False or
                pkmn_id not in self.__pokemon_settings['filters']):
            return
        filters = self.__pokemon_settings['filters'][pkmn_id]
        passed = self.check_pokemon_filter(filters, pkmn)
        if not passed:
            return
        if self.__api_req['REVERSE_LOCATION']:
            pkmn.update(**self.reverse_location(lat, lng))
        log.info("{} notification has been triggered!".format(name))
        self.__alarm.pokemon_alert(pkmn)

    def process_gym(self, gym):
        gym_id = gym['id']
        if gym_id not in self.__gym_info or gym['name'] != 'unknown':
            self.__gym_info[gym_id] = {
                "name": gym['name'],
                "description": gym['description'],
                "url": gym['url']
            }

    def process_egg(self, egg):
        if self.__egg_settings['enabled'] is False:
            return
        gym_id = egg['id']
        raid_end = egg['raid_end']
        if gym_id in self.__raid_hist:
            old_raid_end = self.__raid_hist[gym_id]['raid_end']
            if old_raid_end == raid_end:
                return
        self.__raid_hist[gym_id] = dict(raid_end=raid_end, pkmn_id=0)
        passed = self.check_egg_filter(self.__egg_settings, egg)
        if not passed:
            return
        lat, lng = egg['lat'], egg['lng']
        egg['geofence'] = self.check_geofences('Raid', lat, lng)
        if len(self.__geofences) > 0 and egg['geofence'] == 'unknown':
            return
        time_str = get_time_as_str(egg['raid_end'], self.__timezone)
        start_time_str = get_time_as_str(egg['raid_begin'], self.__timezone)
        egg.update({
            "gym_name": self.__gym_info.get(gym_id, {}).get('name', 'unknown'),
            "gym_description": self.__gym_info.get(gym_id, {}).get(
                'description', 'unknown'),
            "gym_url": self.__gym_info.get(gym_id, {}).get(
                'url', (
                    'https://gitlab.com/alphapokes/PokeBot/raw/master/' +
                    'icons/gym_0.png'
                )
            ),
            'time_left': time_str[0],
            '12h_time': time_str[1],
            '24h_time': time_str[2],
            'begin_time_left': start_time_str[0],
            'begin_12h_time': start_time_str[1],
            'begin_24h_time': start_time_str[2],
        })
        if self.__api_req['REVERSE_LOCATION']:
            egg.update(**self.reverse_location(lat, lng))
        log.info("Egg ({}) notification has been triggered!".format(gym_id))
        self.__alarm.raid_egg_alert(egg)

    def process_raid(self, raid):
        if self.__raid_settings['enabled'] is False:
            return
        gym_id = raid['id']
        pkmn_id = raid['pkmn_id']
        raid_end = raid['raid_end']
        if gym_id in self.__raid_hist:
            old_raid_end = self.__raid_hist[gym_id]['raid_end']
            old_raid_pkmn = self.__raid_hist[gym_id].get('pkmn_id', 0)
            if old_raid_end == raid_end and old_raid_pkmn == pkmn_id:
                return
        self.__raid_hist[gym_id] = dict(raid_end=raid_end, pkmn_id=pkmn_id)
        if pkmn_id not in self.__raid_settings['filters']:
            return
        quick_id = raid['quick_id']
        charge_id = raid['charge_id']
        name = self.__pokemon_name[pkmn_id]
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
        filters = self.__raid_settings['filters'][pkmn_id]
        passed = self.check_pokemon_filter(filters, raid_pkmn)
        if not passed:
            return
        lat, lng = raid['lat'], raid['lng']
        raid['geofence'] = self.check_geofences('Raid', lat, lng)
        if len(self.__geofences) > 0 and raid['geofence'] == 'unknown':
            return
        time_str = get_time_as_str(raid['raid_end'], self.__timezone)
        start_time_str = get_time_as_str(raid['raid_begin'], self.__timezone)
        raid.update({
            'pkmn': name,
            "gym_name": self.__gym_info.get(gym_id, {}).get('name', 'unknown'),
            "gym_description": self.__gym_info.get(gym_id, {}).get(
                'description', 'unknown'),
            "gym_url": self.__gym_info.get(gym_id, {}).get(
                'url', (
                    'https://gitlab.com/alphapokes/PokeBot/raw/master/' +
                    'icons/gym_0.png'
                )
            ),
            'time_left': time_str[0],
            '12h_time': time_str[1],
            '24h_time': time_str[2],
            'begin_time_left': start_time_str[0],
            'begin_12h_time': start_time_str[1],
            'begin_24h_time': start_time_str[2],
            'quick_move': self.__move_name.get(quick_id, 'unknown'),
            'charge_move': self.__move_name.get(charge_id, 'unknown')
        })
        if self.__api_req['REVERSE_LOCATION']:
            raid.update(**self.reverse_location(lat, lng))
        log.info("Raid ({}) notification has been triggered!".format(gym_id))
        self.__alarm.raid_alert(raid)

    def check_geofences(self, name, lat, lng):
        for gf in self.__geofences:
            if gf.contains(lat, lng):
                return gf.name
        return 'unknown'

    def update_locales(self):
        locale_path = os.path.join(get_path('../locales'), '{}'.format(
            self.__locale))
        with open(os.path.join(locale_path, 'pokemon.json'), 'r') as f:
            names = json.loads(f.read())
            for pkmn_id, value in names.items():
                self.__pokemon_name[int(pkmn_id)] = value
        with open(os.path.join(locale_path, 'moves.json'), 'r') as f:
            moves = json.loads(f.read())
            for move_id, value in moves.items():
                self.__move_name[int(move_id)] = value

    def reverse_location(self, lat, lng):
        details = {
            'street_num': 'unkn',
            'street': 'unknown',
            'address': 'unknown',
            'postal': 'unknown',
            'neighborhood': 'unknown',
            'sublocality': 'unknown',
            'city': 'unknown',
            'county': 'unknown',
            'state': 'unknown',
            'country': 'country'
        }
        if len(args.gmaps_api_key) == 0:
            log.error(
                "No Google Maps API key provided - unable to reverse geocode."
            )
            return details
        try:
            coords = '{},{}'.format(lat, lng)
            map_key = args.gmaps_api_key[randint(0, len(
                args.gmaps_api_key) - 1)]
            loc = geocoder.google(coords, method='reverse', key=map_key)
            details['street_num'] = loc.get('street_number', 'unkn')
            details['street'] = loc.get('route', 'unkn')
            details['address'] = "{} {}".format(details['street_num'], details[
                'street'])
            details['postal'] = loc.get('postal_code', 'unkn')
            details['neighborhood'] = loc.get('neighborhood', "unknown")
            details['sublocality'] = loc.get('sublocality', "unknown")
            details['city'] = loc.get('locality', loc.get(
                'postal_town', 'unknown'))
            details['county'] = loc.get(
                'administrative_area_level_2', 'unknown')
            details['state'] = loc.get(
                'administrative_area_level_1', 'unknown')
            details['country'] = loc.get('country', 'unknown')
        except Exception as e:
            log.error((
                "Encountered error while getting reverse location data ({}: " +
                "{})"
            ).format(type(e).__name__, e))
        return details
