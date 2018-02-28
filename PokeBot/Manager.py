import logging
import json
import sys
import asyncio
from collections import OrderedDict, namedtuple
from datetime import datetime, timedelta
from .LocationServices.GMaps import GMaps
from .Locale import Locale
from .Geofence import load_geofence_file
from .Cache import cache_factory
from .Alarms import alarm_factory
from .Events import MonEvent, EggEvent, RaidEvent
from .Filters.MonFilter import MonFilter
from .Filters.EggFilter import EggFilter
from .Filters.RaidFilter import RaidFilter
from .Utilities.GenUtils import get_path

log = logging.getLogger('Manager')

Rule = namedtuple('Rule', ['filter_names', 'alarm_names'])


class Manager(object):

    def __init__(self, name, google_key, locale, max_attempts, cache_type,
                 filter_file, geofence_file, alarm_file):
        self.__name = str(name).lower()
        log.info("----------- Manager '{}' is being created.".format(
            self.__name))
        self._google_key = None
        self._gmaps_service = None
        if len(google_key) > 0:
            self._google_key = google_key
            self._gmaps_service = GMaps(google_key)
        self._language = locale
        self.__locale = Locale(locale)
        self.__cache = cache_factory(cache_type, self.__name)
        self.__mons_enabled, self.__mon_filters = False, OrderedDict()
        self.__eggs_enabled, self.__egg_filters = False, OrderedDict()
        self.__raids_enabled, self.__raid_filters = False, OrderedDict()
        self.load_filter_file(get_path(filter_file))
        self.geofences = None
        if str(geofence_file).lower() != 'none':
            self.geofences = load_geofence_file(get_path(geofence_file))
        self.__alarms = {}
        self.load_alarms_file(get_path(alarm_file), int(max_attempts))
        self.__mon_rules = {}
        self.__egg_rules = {}
        self.__raid_rules = {}
        self.__queue = asyncio.Queue()
        log.info("----------- Manager '{}' successfully created.".format(
            self.__name))

    async def update(self, obj):
        await self.__queue.put(obj)

    def get_name(self):
        return self.__name

    def enable_gmaps_reverse_geocoding(self):
        if not self._gmaps_service:
            raise ValueError(
                "Unable to enable Google Maps Reverse Geocoding.  No GMaps " +
                "API key has been set."
            )
        self._gmaps_reverse_geocode = True

    def add_monster_rule(self, name, filters, alarms):
        if name in self.__mon_rules:
            raise ValueError((
                "Unable to add Rule: Monster Rule with the name {} already " +
                "exists!"
            ).format(name))
        for filt in filters:
            if filt not in self.__mon_filters:
                raise ValueError((
                    "Unable to create Rule: No Monster Filter named {}!"
                ).format(filt))
        for alarm in alarms:
            if alarm not in self.__alarms:
                raise ValueError(
                    "Unable to create Rule: No Alarm named {}!".format(alarm))
        self.__mon_rules[name] = Rule(filters, alarms)

    def add_egg_rule(self, name, filters, alarms):
        if name in self.__egg_rules:
            raise ValueError((
                "Unable to add Rule: Egg Rule with the name {} already exists!"
            ).format(name))
        for filt in filters:
            if filt not in self.__egg_filters:
                raise ValueError((
                    "Unable to create Rule: No Egg Filter named {}!"
                ).format(filt))
        for alarm in alarms:
            if alarm not in self.__alarms:
                raise ValueError(
                    "Unable to create Rule: No Alarm named {}!".format(alarm))
        self.__egg_rules[name] = Rule(filters, alarms)

    def add_raid_rule(self, name, filters, alarms):
        if name in self.__raid_rules:
            raise ValueError((
                "Unable to add Rule: Raid Rule with the name {} already " +
                "exists!"
            ).format(name))
        for filt in filters:
            if filt not in self.__raid_filters:
                raise ValueError((
                    "Unable to create Rule: No Raid Filter named {}!"
                ).format(filt))
        for alarm in alarms:
            if alarm not in self.__alarms:
                raise ValueError(
                    "Unable to create Rule: No Alarm named {}!".format(alarm))
        self.__raid_rules[name] = Rule(filters, alarms)

    @staticmethod
    def load_filter_section(section, sect_name, filter_type):
        defaults = section.pop('defaults', {})
        default_dts = defaults.pop('custom_dts', {})
        filter_set = OrderedDict()
        for name, settings in section.pop('filters', {}).items():
            settings = dict(list(defaults.items()) + list(settings.items()))
            try:
                local_dts = dict(
                    list(default_dts.items()) +
                    list(settings.pop('custom_dts', {}).items())
                )
                if len(local_dts) > 0:
                    settings['custom_dts'] = local_dts
                filter_set[name] = filter_type(name, settings)
            except Exception as e:
                log.error("Encountered error inside filter named '{}'.".format(
                    name))
                raise e
        for key in section:
            raise ValueError((
                "'{}' is not a recognized parameter for the '{}' section."
            ).format(key, sect_name))
        return filter_set

    def load_filter_file(self, file_path):
        try:
            log.info("Loading Filters from file at {}".format(file_path))
            with open(file_path, 'r') as f:
                filters = json.load(f, object_pairs_hook=OrderedDict)
            if type(filters) is not OrderedDict:
                log.critical(
                    "Filters files must be a JSON object: { " +
                    "\"monsters\":{...},... }"
                )
                raise ValueError("Filter file did not contain a dict.")
        except ValueError as e:
            log.error("Encountered error while loading Filters: {}: {}".format(
                type(e).__name__, e))
            log.error(
                "PokeBot has encountered a 'ValueError' while loading the "
                "Filters file. This typically means the file isn't in the "
                "correct json format. Try loading the file contents into a "
                "json validator."
            )
            sys.exit(1)
        except IOError as e:
            log.error("Encountered error while loading Filters: {}: {}".format(
                type(e).__name__, e))
            log.error((
                "PokeBot was unable to find a filters file at {}. Please " +
                "check that this file exists and that PA has read permissions."
            ).format(file_path))
            sys.exit(1)
        try:
            log.info("Parsing 'monsters' section.")
            section = filters.pop('monsters', {})
            self.__mons_enabled = bool(section.pop('enabled', False))
            self.__mon_filters = self.load_filter_section(
                section, 'monsters', MonFilter)
            log.info("Parsing 'eggs' section.")
            section = filters.pop('eggs', {})
            self.__eggs_enabled = bool(section.pop('enabled', False))
            self.__egg_filters = self.load_filter_section(
                section, 'eggs', EggFilter)
            log.info("Parsing 'raids' section.")
            section = filters.pop('raids', {})
            self.__raids_enabled = bool(section.pop('enabled', False))
            self.__raid_filters = self.load_filter_section(
                section, 'raids', RaidFilter)
            return
        except Exception as e:
            log.error(
                "Encountered error while parsing Filters. This is because " +
                "of a mistake in your Filters file."
            )
            log.error("{}: {}".format(type(e).__name__, e))
            sys.exit(1)

    def load_alarms_file(self, file_path, max_attempts):
        log.info("Loading Alarms from the file at {}".format(file_path))
        try:
            with open(file_path, 'r') as f:
                alarm_settings = json.load(f)
            if type(alarm_settings) is not dict:
                log.critical(
                    "Alarms file must be an object of Alarms objects - { " +
                    "'alarm1': {...}, ... 'alarm5': {...} }"
                )
                sys.exit(1)
            self.__alarms = {}
            for name, alarm in alarm_settings.items():
                self.__alarms[name] = alarm_factory(
                    alarm, max_attempts, self._google_key, 'discord')
            log.info("{} active alarms found.".format(len(self.__alarms)))
            return
        except ValueError as e:
            log.error((
                "Encountered error while loading Alarms file: {}: {}"
            ).format(type(e).__name__, e))
            log.error(
                "PokeBot has encountered a 'ValueError' while loading the " +
                "Alarms file. This typically means your file isn't in the " +
                "correct json format. Try loading your file contents into a " +
                "json validator."
            )
        except IOError as e:
            log.error((
                "Encountered error while loading Alarms: {}: {}"
            ).format(type(e).__name__, e))
            log.error((
                "PokeBot was unable to find a filters file  at {}. Please " +
                "check that this file exists and PA has read permissions."
            ).format(file_path))
        except Exception as e:
            log.error((
                "Encountered error while loading Alarms: {}: {}"
            ).format(type(e).__name__, e))
        sys.exit(1)

    async def run(self):
        last_clean = datetime.utcnow()
        while True:
            if datetime.utcnow() - last_clean > timedelta(minutes=5):
                self.__cache.clean_and_save()
                last_clean = datetime.utcnow()
            try:
                event = await self.__queue.get()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0)
                continue
            try:
                kind = type(event)
                if kind == MonEvent:
                    self.process_monster(event)
                elif kind == EggEvent:
                    self.process_egg(event)
                elif kind == RaidEvent:
                    self.process_raid(event)
                else:
                    pass
            except Exception as e:
                log.error((
                    "Encountered error during processing: {}: {}"
                ).format(type(e).__name__, e))
        self.__cache.clean_and_save()

    def process_monster(self, mon):
        if self.__mons_enabled is False:
            return
        mon.name = self.__locale.get_pokemon_name(mon.monster_id)
        if self.__cache.monster_expiration(mon.enc_id) is not None:
            return
        self.__cache.monster_expiration(mon.enc_id, mon.disappear_time)
        rules = self.__mon_rules
        if len(rules) == 0:
            rules = {
                "default": Rule(
                    self.__mon_filters.keys(), self.__alarms.keys())
            }
        for r_name, rule in rules.items():
            for f_name in rule.filter_names:
                f = self.__mon_filters.get(f_name)
                passed = f.check_event(mon) and self.check_geofences(f, mon)
                if not passed:
                    continue
                mon.custom_dts = f.custom_dts
                log.info((
                    "{} monster notification has been triggered in rule '{}'!"
                ).format(mon.name, r_name))
                self._trigger_mon(mon, rule.alarm_names)
                break

    def _trigger_mon(self, mon, alarms):
        dts = mon.generate_dts(self.__locale)
        if self._gmaps_reverse_geocode:
            dts.update(self._gmaps_service.reverse_geocode(
                (mon.lat, mon.lng), self._language))
        for name in alarms:
            alarm = self.__alarms.get(name)
            if alarm:
                alarm.pokemon_alert(dts)
            else:
                log.critical("Alarm '{}' not found!".format(name))

    def process_egg(self, egg):
        if self.__eggs_enabled is False:
            return
        if self.__cache.egg_expiration(egg.gym_id) is not None:
            return
        self.__cache.egg_expiration(egg.gym_id, egg.hatch_time)
        rules = self.__egg_rules
        if len(rules) == 0:
            rules = {
                "default": Rule(
                    self.__egg_filters.keys(), self.__alarms.keys())
            }
        for r_name, rule in rules.items():
            for f_name in rule.filter_names:
                f = self.__egg_filters.get(f_name)
                passed = f.check_event(egg) and self.check_geofences(f, egg)
                if not passed:
                    continue
                egg.custom_dts = f.custom_dts
                log.info((
                    "{} egg notification has been triggered in rule '{}'!"
                ).format(egg.name, r_name))
                self._trigger_egg(egg, rule.alarm_names)
                break

    def _trigger_egg(self, egg, alarms):
        dts = egg.generate_dts(self.__locale)
        if self._gmaps_reverse_geocode:
            dts.update(self._gmaps_service.reverse_geocode(
                (egg.lat, egg.lng), self._language))
        for name in alarms:
            alarm = self.__alarms.get(name)
            if alarm:
                alarm.raid_egg_alert(dts)
            else:
                log.critical("Alarm '{}' not found!".format(name))

    def process_raid(self, raid):
        if self.__raids_enabled is False:
            return
        if self.__cache.raid_expiration(raid.gym_id) is not None:
            return
        self.__cache.raid_expiration(raid.gym_id, raid.raid_end)
        rules = self.__raid_rules
        if len(rules) == 0:
            rules = {
                "default": Rule(
                    self.__raid_filters.keys(), self.__alarms.keys())
            }
        for r_name, rule in rules.items():
            for f_name in rule.filter_names:
                f = self.__raid_filters.get(f_name)
                passed = f.check_event(raid) and self.check_geofences(f, raid)
                if not passed:
                    continue
                raid.custom_dts = f.custom_dts
                log.info((
                    "{} raid notification has been triggered in rule '{}'!"
                ).format(raid.name, r_name))
                self._trigger_raid(raid, rule.alarm_names)
                break

    def _trigger_raid(self, raid, alarms):
        dts = raid.generate_dts(self.__locale)
        if self._gmaps_reverse_geocode:
            dts.update(self._gmaps_service.reverse_geocode(
                (raid.lat, raid.lng), self._language))
        for name in alarms:
            alarm = self.__alarms.get(name)
            if alarm:
                alarm.raid_alert(dts)
            else:
                log.critical("Alarm '{}' not found!".format(name))

    def check_geofences(self, f, e):
        if self.geofences is None or f.geofences is None:
            return True
        targets = f.geofences
        if len(targets) == 1 and "all" in targets:
            targets = self.geofences.keys()
        for name in targets:
            gf = self.geofences.get(name)
            if not gf:
                log.error("Cannot check geofence %s: does not exist!", name)
            elif gf.contains(e.lat, e.lng):
                e.geofence = name
                return True
        return False
