#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import configargparse
import os
import sys
import geocoder
import discord
import json
from queue import PriorityQueue

log = logging.getLogger('utils')


def get_path(path):
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), path)
    return path


def get_args():
    if '-cf' not in sys.argv and '--config' not in sys.argv:
        config_files = [get_path('../config/config.ini')]
    parser = configargparse.ArgParser(default_config_files=config_files)
    parser.add_argument('-cf', '--config', is_config_file=True,
                        help='Configuration file')
    parser.add_argument('-token', '--tokens', type=str, action='append',
                        default=[], help='List of tokens for Discord bots',
                        required=True)
    parser.add_argument('-bcid', '--bot_client_ids', type=str,
                        action='append', default=[],
                        help='List of client ids for Discord Bots',
                        required=True)
    parser.add_argument('-feed', '--feed_channels', type=str,
                        action='append', default=[],
                        help='Channel ID that PokeAlarm posts to',
                        required=True)
    parser.add_argument('-com', '--command_channels', type=str,
                        action='append', default=[],
                        help='Channel ID that users input commands',
                        required=True)
    parser.add_argument('-area', '--areas', type=str.lower, action='append',
                        default=[], help='List or areas or geofences')
    parser.add_argument('-alert', '--alert_role', type=str.lower,
                        default='@everyone',
                        help='Role for users that can use the bot')
    parser.add_argument('-map', '--map_role', type=str.lower,
                        help='Role for users that get extras')
    parser.add_argument('-muted', '--muted_role', type=str.lower, default=None,
                        help='Role for muted users')
    parser.add_argument('-admin', '--admins', type=str, action='append',
                        default=[], help='ids for admins')
    parser.add_argument('-gmaps', '--gmaps_api_key', type=str, action='append',
                        default=[],
                        help='Specify a Google API key or list of keys to use')
    parser.add_argument('-geo1', '--geocode_1', type=str.lower,
                        default='neighborhood', help='first geocode for DMs')
    parser.add_argument('-geo2', '--geocode_2', type=str.lower,
                        default='street', help='fallback geocode for DMs')
    parser.add_argument('-aa', '--all_areas', action='store_true',
                        help=('default to sub to all areas when true ' +
                              'otherwise, default is no areas'), default=False)
    parser.add_argument('-host', '--host', type=str,
                        help='Host for webhook', default='127.0.0.1')
    parser.add_argument('-port', '--port', type=int,
                        help='Port for webhook', default=4000)

    args = parser.parse_args()

    if len(args.tokens) != len(args.bot_client_ids):
        log.error("Token - Client ID mismatch")
        sys.exit(1)

    return args


class Dicts(object):
    users = []
    q = []
    timestamps = []
    roles = {}
    count = []
    pokemon = [
        'bulbasaur', 'ivysaur', 'venusaur', 'charmander', 'charmeleon',
        'charizard', 'squirtle', 'wartortle', 'blastoise', 'caterpie',
        'metapod', 'butterfree', 'weedle', 'kakuna', 'beedrill', 'pidgey',
        'pidgeotto', 'pidgeot', 'rattata', 'raticate', 'spearow', 'fearow',
        'ekans', 'arbok', 'pikachu', 'raichu', 'sandshrew', 'sandslash',
        'nidoranf', 'nidorina', 'nidoqueen', 'nidoranm', 'nidorino',
        'nidoking', 'clefairy', 'clefable', 'vulpix', 'ninetales',
        'jigglypuff', 'wigglytuff', 'zubat', 'golbat', 'oddish', 'gloom',
        'vileplume', 'paras', 'parasect', 'venonat', 'venomoth', 'diglett',
        'dugtrio', 'meowth', 'persian', 'psyduck', 'golduck', 'mankey',
        'primeape', 'growlithe', 'arcanine', 'poliwag', 'poliwhirl',
        'poliwrath', 'abra', 'kadabra', 'alakazam', 'machop', 'machoke',
        'machamp', 'bellsprout', 'weepinbell', 'victreebel', 'tentacool',
        'tentacruel', 'geodude', 'graveler', 'golem', 'ponyta', 'rapidash',
        'slowpoke', 'slowbro', 'magnemite', 'magneton', "farfetch'd", 'doduo',
        'dodrio', 'seel', 'dewgong', 'grimer', 'muk', 'shellder', 'cloyster',
        'gastly', 'haunter', 'gengar', 'onix', 'drowzee', 'hypno', 'krabby',
        'kingler', 'voltorb', 'electrode', 'exeggcute', 'exeggutor', 'cubone',
        'marowak', 'hitmonlee', 'hitmonchan', 'lickitung', 'koffing',
        'weezing', 'rhyhorn', 'rhydon', 'chansey', 'tangela', 'kangaskhan',
        'horsea', 'seadra', 'goldeen', 'seaking', 'staryu', 'starmie',
        'mr.mime', 'scyther', 'jynx', 'electabuzz', 'magmar', 'pinsir',
        'tauros', 'magikarp', 'gyarados', 'lapras', 'ditto', 'eevee',
        'vaporeon', 'jolteon', 'flareon', 'porygon', 'omanyte', 'omastar',
        'kabuto', 'kabutops', 'aerodactyl', 'snorlax', 'articuno', 'zapdos',
        'moltres', 'dratini', 'dragonair', 'dragonite', 'mewtwo', 'mew',
        'chikorita', 'bayleef', 'meganium', 'cyndaquil', 'quilava',
        'typhlosion', 'totodile', 'croconaw', 'feraligatr', 'sentret',
        'furret', 'hoothoot', 'noctowl', 'ledyba', 'ledian', 'spinarak',
        'ariados', 'crobat', 'chinchou', 'lanturn', 'pichu', 'cleffa',
        'igglybuff', 'togepi', 'togetic', 'natu', 'xatu', 'mareep', 'flaaffy',
        'ampharos', 'bellossom', 'marill', 'azumarill', 'sudowoodo',
        'politoed', 'hoppip', 'skiploom', 'jumpluff', 'aipom', 'sunkern',
        'sunflora', 'yanma', 'wooper', 'quagsire', 'espeon', 'umbreon',
        'murkrow', 'slowking', 'misdreavus', 'unown', 'wobbuffet', 'girafarig',
        'pineco', 'forretress', 'dunsparce', 'gligar', 'steelix', 'snubbull',
        'granbull', 'qwilfish', 'scizor', 'shuckle', 'heracross', 'sneasel',
        'teddiursa', 'ursaring', 'slugma', 'magcargo', 'swinub', 'piloswine',
        'corsola', 'remoraid', 'octillery', 'delibird', 'mantine', 'skarmory',
        'houndour', 'houndoom', 'kingdra', 'phanpy', 'donphan', 'porygon2',
        'stantler', 'smeargle', 'tyrogue', 'hitmontop', 'smoochum', 'elekid',
        'magby', 'miltank', 'blissey', 'raikou', 'entei', 'suicune',
        'larvitar', 'pupitar', 'tyranitar', 'lugia', 'ho-oh', 'celebi'
    ]
    male_only = [
        'nidoranm', 'nidorino', 'nidoking', 'hitmonlee', 'hitmonchan',
        'tauros', 'tyrogue', 'hitmontop'
    ]
    female_only = [
        'nidoranf', 'nidorina', 'nidoqueen', 'chansey', 'kangaskhan', 'jynx',
        'smoochum', 'militank', 'blissey'
    ]
    genderless = [
        'magnemite', 'magneton', 'voltorb', 'electrode', 'staryu', 'starmie',
        'porygon', 'porygon2'
    ]
    type_col = {
        'bug': 0xA8B820,
        'dark': 0x705848,
        'dragon': 0x7038F8,
        'electric': 0xF8D030,
        'fairy': 0xEE99AC,
        'fighting': 0xC03028,
        'fire': 0xF08030,
        'flying': 0xA890F0,
        'ghost': 0x705898,
        'grass': 0x78C850,
        'ground': 0xE0C068,
        'ice': 0x98D8D8,
        'normal': 0xA8A878,
        'poison': 0xA040A0,
        'psychic': 0xF85888,
        'rock': 0xB8A038,
        'steel': 0xB8B8D0,
        'water': 0x6890F0
    }
    info_msg = (
        "Hello there! I am Professor AlphaPokes.\n\n" +
        "`!set [pokemon] [IV] [gender] CP[CP] L[level]` to add an alert for " +
        "a given pokemon based on it's characteristics, any of the " +
        "characteristics can be left blank,\n\n" +
        "`!delete [pokemon/all] [gender]` to remove an " +
        "alert for a given pokemon based on it's characteristics, gender " +
        "can be left blank,\n\n" +
        "`!pause` or `!p` to pause all notifcations,\n\n" +
        "`!resume` or `!r` to resume all alerts,\n\n" +
        "`!pause [area]` to pause a given area,\n\n" +
        "`!resume [area]` to resume a given area,\n\n" +
        "`!areas` to see what areas area available to pause or resume,\n\n" +
        "`!alerts [pokemon/all/areas]` to see your alert settings,\n\n"
        "`!dex [pokemon]` to get pokedex information for a given " +
        "pokemon,\n\n" +
        "`!status` to see which bots are currently online,\n\n" +
        "`!help` or `!commands` to see this message,\n\n" +
#        "`!donate` to see donation information for this project.\n\n" +
        "It is possible to add or delete multiple pokemon or areas by " +
        "putting pokemon on seperate lines or separating them with commas.\n" +
        "Commands should be in the #custom_filters channel.\n\n"
    )


def get_dicts(number_of_bots):
    dicts = Dicts()
    for bot_num in range(number_of_bots):
        dicts.users.append({})
        dicts.q.append(PriorityQueue())
        dicts.timestamps.append([])
        dicts.count.append(0)
    with open(get_path('../dicts/users.json')) as users_file:
        data = json.load(users_file)
        for user_id in data:
            dicts.users[int(user_id) % int(number_of_bots)][user_id] = data[
                user_id]
    return dicts


def update_dicts(number_of_bots):
    dicts = Dicts()
    master = {}
    for bot_num in range(number_of_bots):
        master.update(dicts.users[bot_num])
    with open(get_path('../dicts/users.json'), 'w') as users_file:
        json.dump(master, users_file, indent=4)


def parse_command(command):
    dicts = Dicts()
    chars = command.split()
    error = False
    if len(set(chars).intersection(set(dicts.pokemon))) > 0:
        pokemon = [list(set(chars).intersection(set(dicts.pokemon)))[0]]
        chars.remove(pokemon[0])
        if (pokemon[0] in dicts.male_only and
            len(set(chars).intersection(set(['female', 'f']))) == 0 or
            (pokemon[0] not in dicts.male_only and
             pokemon[0] not in dicts.female_only and
             pokemon[0] not in dicts.genderless and
             len(set(chars).intersection(set(['male', 'm']))) > 0)):
            genders = ['male']
            if len(set(chars).intersection(set(['male', 'm']))) > 0:
                chars.remove(list(set(chars).intersection(set(['male', 'm'])))[
                    0])
        elif (pokemon[0] in dicts.female_only and
              len(set(chars).intersection(set(['male', 'm']))) == 0 or
              (pokemon[0] not in dicts.male_only and
               pokemon[0] not in dicts.female_only and
               pokemon[0] not in dicts.genderless and
               len(set(chars).intersection(set(['female', 'f']))) > 0)):
            genders = ['female']
            if len(set(chars).intersection(set(['female', 'f']))) > 0:
                chars.remove(list(set(chars).intersection(set(
                    ['female', 'f'])))[0])
        elif (pokemon[0] in dicts.genderless and
              len(set(chars).intersection(set(['female', 'f']))) == 0 and
              len(set(chars).intersection(set(['male', 'm']))) == 0):
            genders = ['genderless']
        elif (pokemon[0] not in dicts.male_only and
              pokemon[0] not in dicts.female_only and
              pokemon[0] not in dicts.genderless):
            genders = ['female', 'male']
        else:
            error = True
            genders = []
    else:
        pokemon = dicts.pokemon
        genders = []

    return error, chars, pokemon, genders


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def truncate(msg):
    msg_split1 = msg[:len(msg[:1999].rsplit('\n', 1)[0])]
    msg_split2 = msg[len(msg[:1999].rsplit('\n', 1)[0]):]
    return [msg_split1, msg_split2]


def get_default_genders(pokemon):
    dicts = Dicts()
    if pokemon in dicts.male_only:
        genders = ['male']
    elif pokemon in dicts.female_only:
        genders = ['female']
    elif pokemon in dicts.genderless:
        genders = ['genderless']
    else:
        genders = ['female', 'male']
    return genders


def get_loc(gmap_url, map_key):
    coords = gmap_url.split('=')[1]
    g = geocoder.google(coords, method='reverse', key=map_key)
    if g[args.geocode_1] is not None:
        return g[args.geocode_1]
    else:
        return g[args.geocode_2]


def get_static_map_url(gmap_url, map_key):
    coords = gmap_url.split('=')[1]
    width = '250'
    height = '125'
    maptype = 'roadmap'
    zoom = '12'
    center = '{}'.format(coords)
    query_center = 'center={}'.format(center)
    query_markers = 'markers=color:red%7C{}'.format(center)
    query_size = 'size={}x{}'.format(width, height)
    query_zoom = 'zoom={}'.format(zoom)
    query_maptype = 'maptype={}'.format(maptype)
    gmap = ('https://maps.googleapis.com/maps/api/staticmap?' +
            query_center + '&' + query_markers + '&' +
            query_maptype + '&' + query_size + '&' + query_zoom)
    gmap += ('&key=%s' % map_key)

    return gmap
