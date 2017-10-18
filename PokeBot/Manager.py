#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import json
import asyncio
import sys
from queue import Queue
from .LocationServices import LocationService
from .DiscordAlarm import DiscordAlarm
from .Filter import load_pokemon_section, load_egg_section
from .utils import (require_and_remove_key, get_path, get_args, contains_arg,
                    Dicts)

log = logging.getLogger('Manager')
args = get_args()
dicts = Dicts()


class Manager(object):

    def __init__(self, name, alarm_file, filter_file, geofence_names):
        self.__name = str(name).lower()
        self.__loc_service = None
        if len(args.gmaps_keys) > 0:
            self.__loc_service = LocationService()
        else:
            log.warning(
                "NO GOOGLE API KEY SET - Reverse Location DTS will NOT be " +
                "detected."
            )
        self.__pokemon_settings = {}
        self.__raid_settings = {}
        self.__egg_settings = {}
        self.load_filter_file(get_path(filter_file))
        self.load_alarms_file(get_path(alarm_file), args.max_attempts)
        self.__geofences = []
        if str(args.geofence_names[0]).lower() != 'none':
            self.__geofences = geofence_names
        self.__queue = Queue()
        log.info("Manager '{}' successfully created.".format(self.__name))

    def update(self, obj):
        self.__queue.put(obj)

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
            log.info("Loaded Filters from file at {}".format(
                file_path.split('/')[-1]))
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

    def load_alarms_file(self, file_path, max_attempts):
        try:
            with open(file_path, 'r') as f:
                alarm = json.load(f)
            if type(alarm) is not dict:
                log.critical("Alarms file must be a dictionary")
                sys.exit(1)
            self.set_optional_args(str(alarm))
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

    def set_optional_args(self, line):
        args = {
            'street', 'street_num', 'address', 'postal', 'neighborhood',
            'sublocality', 'city', 'county', 'state', 'country'
        }
        if contains_arg(line, args):
            if self.__loc_service is None:
                log.critical(
                    "Reverse location DTS were detected but no API key was " +
                    "provided!"
                )
                log.critical(
                    "Please either remove the DTS, add an API key, or " +
                    "disable the alarm and try again."
                )
                sys.exit(1)
            self.__loc_service.enable_reverse_location()

    async def connect(self):
        while True:
            while self.__queue.empty():
                await asyncio.sleep(1)
            obj = self.__queue.get()
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
                log.error("Encountered error during processing: {}: {}".format(
                    type(e).__name__, e))

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
        pkmn_id = pkmn['pkmn_id']
        lat, lng = pkmn['lat'], pkmn['lng']
        name = pkmn['pkmn']
        if (self.__pokemon_settings['enabled'] is False or
                pkmn_id not in self.__pokemon_settings['filters']):
            return
        filters = self.__pokemon_settings['filters'][pkmn_id]
        passed = self.check_pokemon_filter(filters, pkmn)
        if not passed:
            return
        if (len(self.__geofences) > 0 and
                pkmn['geofence'] not in self.__geofences):
            return
        if self.__loc_service:
            self.__loc_service.add_optional_arguments([lat, lng], pkmn)
        log.info("{} notification has been triggered!".format(name))
        self.__alarm.pokemon_alert(pkmn)

    def process_egg(self, egg):
        lat, lng = egg['lat'], egg['lng']
        gym_id = egg['id']
        if self.__egg_settings['enabled'] is False:
            return
        passed = self.check_egg_filter(self.__egg_settings, egg)
        if not passed:
            return
        if (len(self.__geofences) > 0 and
                egg['geofence'] not in self.__geofences):
            return
        if self.__loc_service:
            self.__loc_service.add_optional_arguments([lat, lng], egg)
        log.info("Egg ({}) notification has been triggered!".format(gym_id))
        self.__alarm.raid_egg_alert(egg)

    def process_raid(self, raid):
        pkmn_id = raid['pkmn_id']
        lat, lng = raid['lat'], raid['lng']
        gym_id = raid['id']
        if (self.__raid_settings['enabled'] is False or
                pkmn_id not in self.__raid_settings['filters']):
            return
        if (len(self.__geofences) > 0 and
                raid['geofence'] not in self.__geofences):
            return
        if self.__loc_service:
            self.__loc_service.add_optional_arguments([lat, lng], raid)
        log.info("Raid ({}) notification has been triggered!".format(gym_id))
        self.__alarm.raid_alert(raid)
