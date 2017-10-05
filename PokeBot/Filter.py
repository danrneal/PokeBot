#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import sys
from .utils import reject_leftover_parameters, get_pkmn_id, parse_boolean

log = logging.getLogger('Filters')


def create_multi_filter(location, FilterType, settings, default):
    bool = parse_boolean(settings)
    if bool is not None:
        if bool is True:
            return [FilterType({}, default, location)]
        else:
            return None
    elif type(settings) == dict:
        return [FilterType(settings, default, location)]
    elif type(settings) == list:
        rtn = []
        for filt in settings:
            rtn.append(FilterType(filt, default, location))
        return rtn
    else:
        log.critical((
            "{} contains filter that is not in the proper format. Accepted " +
            "formats are: "
        ).format(location))
        log.critical("'True' for default filter, 'False' for disabled,")
        log.critical("{ ... filter info ...} for a single filter,")
        log.critical(
            "[ {filter1}, {filter2}, {filter3} ] for multiple filters."
        )
        log.critical("Please check the documentation for more information.")
        sys.exit(1)


def load_pokemon_section(settings):
    pokemon = {
        "enabled": bool(parse_boolean(settings.pop('enabled', None)) or False)
    }
    default_filt = PokemonFilter(settings.pop('default', {}), {
        "ignore_missing": False,
        "min_cp": 0,
        "max_cp": 999999,
        "min_level": 0,
        "max_level": 40,
        "min_iv": 0.0,
        "max_iv": 100.0,
        "size": None,
        "gender": None,
    }, 'default')
    default = default_filt.to_dict()
    filters = {}
    for name in settings:
        pkmn_id = get_pkmn_id(name)
        if pkmn_id is None:
            log.critical("Unable to find pokemon named '{}'...".format(name))
            log.critical(
                "Please see documentation for proper Filter file formatting."
            )
            sys.exit(1)
        if pkmn_id in filters:
            log.critical(
                "Multiple entries detected for Pokemon {}. Please remove " +
                "any extra names."
            )
            sys.exit(1)
        f = create_multi_filter(name, PokemonFilter, settings[name], default)
        if f is not None:
            filters[pkmn_id] = f
    pokemon['filters'] = filters
    return pokemon


def load_egg_section(settings):
    egg = {
        "enabled": bool(parse_boolean(settings.pop('enabled', None)) or False),
        "min_level": int(settings.pop('min_level', 0) or 0),
        "max_level": int(settings.pop('max_level', 10) or 10)
    }
    return egg


class Filter(object):

    @staticmethod
    def check_sizes(sizes):
        if sizes is None:
            return None
        list_ = set()
        valid_sizes = ['tiny', 'small', 'normal', 'large', 'big']
        for raw_size in sizes:
            size = raw_size
            if size in valid_sizes:
                list_.add(size)
            else:
                log.critical("{} is not a valid size name.".format(size))
                log.critical("Please use one of the following: {}".format(
                    valid_sizes))
                sys.exit(1)
        return list_

    @staticmethod
    def check_genders(genders):
        if genders is None:
            return None
        list_ = set()
        valid_genders = ['male', 'female', 'neutral']
        for raw_gender in genders:
            gender = raw_gender
            if raw_gender == u'\u2642':
                gender = 'male'
            if raw_gender == u'\u2640':
                gender = 'female'
            if raw_gender == u'\u26b2':
                gender = 'neutral'
            if gender in valid_genders:
                if gender == 'male':
                    list_.add(u'\u2642')
                if gender == 'female':
                    list_.add(u'\u2640')
                if gender == 'neutral':
                    list_.add(u'\u26b2')
            else:
                log.critical("{} is not a valid gender name.".format(gender))
                log.critical("Please use one of the following: {}".format(
                    valid_genders))
                sys.exit(1)
        return list_


class PokemonFilter(Filter):

    def __init__(self, settings, default, location):
        self.ignore_missing = bool(parse_boolean(settings.pop(
            'ignore_missing', default['ignore_missing'])))
        self.min_cp = int(settings.pop('min_cp', None) or default['min_cp'])
        self.max_cp = int(settings.pop('max_cp', None) or default['max_cp'])
        self.min_level = int(settings.pop('min_level', None) or
                             default['min_level'])
        self.max_level = int(settings.pop('max_level', None) or
                             default['max_level'])
        self.min_iv = float(settings.pop('min_iv', None) or default['min_iv'])
        self.max_iv = float(settings.pop('max_iv', None) or default['max_iv'])
        self.sizes = PokemonFilter.check_sizes(settings.pop(
            "size", default['size']))
        self.genders = PokemonFilter.check_genders(settings.pop(
            "gender", default['gender']))
        reject_leftover_parameters(
            settings, "pokemon filter under '{}'".format(location))

    def check_cp(self, cp):
        return self.min_cp <= cp <= self.max_cp

    def check_level(self, level):
        return self.min_level <= level <= self.max_level

    def check_iv(self, iv):
        return self.min_iv <= iv <= self.max_iv

    def check_size(self, size):
        if self.sizes is None:
            return True
        return size in self.sizes

    def check_gender(self, gender):
        if self.genders is None:
            return True
        return gender in self.genders

    def to_dict(self):
        return {
            "min_cp": self.min_cp,
            "max_cp": self.max_cp,
            "min_level": self.min_level,
            "max_level": self.max_level,
            "min_iv": self.min_iv,
            "max_iv": self.max_iv,
            "size": self.sizes,
            "gender": self.genders,
            "ignore_missing": self.ignore_missing
        }


class Geofence(object):

    def __init__(self, name, points):
        self.name = name
        self.__points = points
        self.__min_x = points[0][0]
        self.__max_x = points[0][0]
        self.__min_y = points[0][1]
        self.__max_y = points[0][1]
        for p in points:
            self.__min_x = min(p[0], self.__min_x)
            self.__max_x = max(p[0], self.__max_x)
            self.__min_y = min(p[1], self.__min_y)
            self.__max_y = max(p[1], self.__max_y)

    def contains(self, x, y):
        if (self.__max_x < x or
            x < self.__min_x or
            self.__max_y < y or
                y < self.__min_y):
            return False
        inside = False
        p1x, p1y = self.__points[0]
        n = len(self.__points)
        for i in range(1, n+1):
            p2x, p2y = self.__points[i % n]
            if min(p1y, p2y) < y <= max(p1y, p2y) and x <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def get_name(self):
        return self.__name
