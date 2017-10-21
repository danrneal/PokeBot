#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import sys
import json
import asyncio
import copy
from queue import Queue, PriorityQueue
from collections import namedtuple
from aiohttp import web
from .Manager import Manager
from .Bot import Bot
from .Locale import Locale
from .ManageWebhook import ManageWebhook
from .LocationServices import LocationService
from .Filter import load_pokemon_section, load_egg_section
from .Notification import Notification
from .utils import (get_path, get_args, Dicts, contains_arg,
                    require_and_remove_key)

logging.basicConfig(
    format='[%(name)10.10s][%(levelname)8.8s] %(message)s',
    level=logging.INFO
)
log = logging.getLogger('clients')
args = get_args()
entries = []
wh_mgr = ManageWebhook()


def get_managers():
    for m_ct in range(args.manager_count):
        m = Manager(
            name=(
                args.manager_name[m_ct]
                if m_ct < len(args.manager_name)
                else "Manager_{}".format(m_ct)
            ),
            alarm_file=(
                args.alarms[m_ct]
                if len(args.alarms) > 1
                else args.alarms[0]
            ),
            filter_file=(
                args.filters[m_ct]
                if len(args.filters) > 1
                else args.filters[0]
            ),
            geofence_names=(
                args.geofence_names[m_ct]
                if len(args.geofence_names) > 1
                else args.geofence_names[0]
            )
        )
        if m.get_name() not in Dicts.managers:
            Dicts.managers[m.get_name()] = m
        else:
            log.critical(
                "Names of Manager processes must be unique (regardless of " +
                "capitalization)! Process will exit."
            )
            sys.exit(1)
    return


def bot_init():
    if len(args.gmaps_keys) > 0:
        Dicts.loc_service = LocationService()
    else:
        log.warning(
            "NO GOOGLE API KEY SET - Reverse Location DTS will NOT be " +
            "detected."
        )
    if str(args.geofences[0]).lower() != 'none':
        for key in sorted(args.master_geofences.keys()):
            if key not in Dicts.geofences:
                Dicts.geofences.append(key.lower())
            else:
                log.critical("Multiple Geofences with the same name!")
                sys.exit(1)
    Dicts.locale = Locale(args.locale)
    for bot_number in range(len(args.tokens)):
        Dicts.bots.append({
            'filters': {},
            'pokemon_settings': {},
            'raid_settings': {},
            'egg_settings': {},
            'in_queue': Queue(),
            'out_queue': PriorityQueue(),
            'timestamps': [],
            'count': 0
        })
        try:
            with open(get_path('../user_dicts/user_alarms.json'), 'r') as f:
                alarm = json.load(f)
            if type(alarm) is not dict:
                log.critical("User Alarms file must be a dictionary")
                sys.exit(1)
            geo_args = {
                'street', 'street_num', 'address', 'postal', 'neighborhood',
                'sublocality', 'city', 'county', 'state', 'country'
            }
            if contains_arg(str(alarm), geo_args):
                if Dicts.loc_service is None:
                    log.critical(
                        "Reverse location DTS were detected but no API key " +
                        "was provided!"
                    )
                    log.critical(
                        "Please either remove the DTS, add an API key, or " +
                        "disable the alarm and try again."
                    )
                    sys.exit(1)
                Dicts.loc_service.enable_reverse_location()
            Dicts.bots[bot_number]['alarm'] = Notification(alarm)
            log.info('Active DM alarm found.')
        except ValueError as e:
            log.critical((
                "Encountered error while loading Alarms file: {}: {}"
            ).format(type(e).__name__, e))
            log.critical(
                "Encountered a 'ValueError' while loading the Alarms file. " +
                "This typically means your file isn't in the correct json " +
                "format. Try loading your file contents into a json validator."
            )
            sys.exit(1)
        except IOError as e:
            log.critical((
                "Encountered error while loading Alarms: {}: {}"
            ).format(type(e).__name__, e))
            log.critical((
                "Unable to find a filters file at {}. Please check that " +
                "this file exists and has the correct permissions."
            ).format(get_path('../user_dicts/user_alarms.json')))
            sys.exit(1)
        except Exception as e:
            log.critical((
                "Encountered error while loading Alarms: {}: {}"
            ).format(type(e).__name__, e))
            sys.exit(1)
    try:
        with open(get_path(
                '../user_dicts/user_filters.json'), encoding="utf-8") as f:
            filters = json.load(f)
            for user_id in filters:
                if type(filters[user_id]) is not dict:
                    log.critical(
                        "User pokemon filter file must be a JSON object: { " +
                        "\"pokemon\":{...},... }, it may be corrupted"
                    )
                    sys.exit(1)
                Dicts.bots[int(user_id) % len(args.tokens)]['filters'][
                    user_id] = copy.deepcopy(filters[user_id])
                Dicts.bots[int(user_id) % len(args.tokens)][
                    'pokemon_settings'][user_id] = load_pokemon_section(
                        require_and_remove_key(
                            'pokemon', filters[user_id], "User Filters File."))
                Dicts.bots[int(user_id) % len(args.tokens)]['egg_settings'][
                    user_id] = load_egg_section(require_and_remove_key(
                        'eggs', filters[user_id], "User Filters File."))
                Dicts.bots[int(user_id) % len(args.tokens)]['raid_settings'][
                    user_id] = load_pokemon_section(require_and_remove_key(
                        'raids', filters[user_id], "User Filters File."))
        log.info('Loaded DM filters.')
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
            "Unable to find a filters file at user_dicts/user_filters.json. " +
            "Please check that this file exists and has the correct " +
            "permissions."
        )
    except Exception as e:
        log.critical((
            "Encountered error while loading Filters: {}: {}"
        ).format(type(e).__name__, e))
    log.info('DM bot successfully created.')
    return


async def index(request):
    return web.Response(text="PokeBot Running!")


async def handler(request):
    try:
        data = await request.json()
        await wh_mgr.update(data)
    except Exception as e:
        log.error("Encountered error while receiving webhook ({}: {})".format(
            type(e).__name__, e))
        raise web.HTTPBadRequest()
    return web.Response()


async def login():
    bot_num = 0
    for entry in entries:
        bot_num += 1
        await entry.client.login(args.tokens.pop(0))


async def wrapped_connect(entry):
    try:
        await entry.client.connect()
    except Exception as e:
        try:
            await entry.client.close()
        except:
            pass
        log.error('We got an exception: ', e.__class__.__name__, e)
        entry.event.set()


async def check_close():
    futures = [entry.event.wait() for entry in entries]
    await asyncio.wait(futures)


def start_clients():
    get_managers()
    bot_init()
    loop = asyncio.get_event_loop()
    Entry = namedtuple('Entry', 'client event')
    for bot in range(len(args.tokens)):
        entries.append(Entry(client=Bot(), event=asyncio.Event()))
    loop.run_until_complete(login())
    for name, mgr in Dicts.managers.items():
        entries.append(Entry(client=mgr, event=asyncio.Event()))
    entries.append(Entry(client=wh_mgr, event=asyncio.Event()))
    for entry in entries:
        loop.create_task(wrapped_connect(entry))
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_post('/', handler)
    loop.create_task(web.run_app(app, port=args.port))
    loop.run_until_complete(check_close())
    loop.close()
