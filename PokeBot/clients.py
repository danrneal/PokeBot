#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os
import sys
import re
import json
import asyncio
from collections import namedtuple
from aiohttp import web
from .Manager import Manager
from .Bot import Bot
from .Filter import load_pokemon_section, load_egg_section
from .Notification import Notification
from .WebhookStructs import Webhook
from .utils import (get_path, get_args, Dicts, contains_arg, parse_boolean,
                    require_and_remove_key)

logging.basicConfig(
    format='[%(name)10.10s][%(levelname)8.8s] %(message)s',
    level=logging.INFO
)
log = logging.getLogger('clients')

args = get_args()
dicts = Dicts()
data_queue = asyncio.Queue()
entries = []


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
            geofence_file=(
                args.geofences[m_ct]
                if len(args.geofences) > 1
                else args.geofences[0]
            ),
            timezone=(
                args.timezone[m_ct]
                if len(args.timezone) > 1
                else args.timezone[0]
            )
        )
        if m.get_name() not in dicts.managers:
            dicts.managers[m.get_name()] = m
        else:
            log.critical(
                "Names of Manager processes must be unique (regardless of " +
                "capitalization)! Process will exit."
            )
            sys.exit(1)
    return


def bot_init():
    args = get_args()
    for bot_number in range(len(args.tokens)):
        dicts.bots.append({
            'api_req': False,
            'pokemon_name': {},
            'filters': {},
            'pokemon_hist': {},
            'raid_hist': {},
            'geofences': [],
            'in_queue': asyncio.Queue(),
            'out_queue': asyncio.PriorityQueue(),
            'timestamps': [],
            'count': 0,
            'roles': {},
        })
        locale_path = os.path.join(get_path('../locales'), '{}'.format(
            args.locale))
        with open(os.path.join(locale_path, 'pokemon.json'), 'r') as f:
            names = json.loads(f.read())
            for pkmn_id, value in names.items():
                dicts.bots[bot_number]['pokemon_name'][int(pkmn_id)] = value
        try:
            with open(get_path('../user_dicts/user_alarms.json'), 'r') as f:
                alarm = json.load(f)
            if type(alarm) is not dict:
                log.critical("User Alarms file must be a dictionary")
                sys.exit(1)
            args = {
                'street', 'street_num', 'address', 'postal',
                'neighborhood', 'sublocality', 'city', 'county', 'state',
                'country'
            }
            dicts.bots[bot_number]['api_req'] = dicts.bots[bot_number][
                'api_req'] or contains_arg(str(alarm), args)
            dicts.bots[bot_number]['alarm'] = Notification(alarm)
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
        if str(args.geofences[0]).lower() != 'none':
            geofences = []
            name_pattern = re.compile("(?<=\[)([^]]+)(?=\])")
            for geofence_file in args.geofences:
                with open(get_path(geofence_file), 'r') as f:
                    lines = f.read().splitlines()
                for line in lines:
                    line = line.strip()
                    match_name = name_pattern.search(line)
                    if match_name:
                        name = match_name.group(0)
                        geofences.append(name)
            dicts.bots[bot_number]['geofences'] = geofences
            log.info("{} geofences added.".format(len(geofences)))
    try:
        with open(get_path('../user_dicts/user_filters.json')) as f:
            filters = json.load(f)
            for user_id in filters:
                if type(filters[user_id]) is not dict:
                    log.critical(
                        "User pokemon filter file must be a JSON object: { " +
                        "\"pokemon\":{...},... }, it may be corrupted"
                    )
                    sys.exit(1)
                dicts.bots[int(user_id) % len(args.tokens)]['filters'][
                    user_id]['pokemon_settings'] = {}
                dicts.bots[int(user_id) % len(args.tokens)]['filters'][
                    user_id]['egg_settings'] = {}
                dicts.bots[int(user_id) % len(args.tokens)]['filters'][
                    user_id]['raid_settings'] = {}
                dicts.bots[int(user_id) % len(args.tokens)]['filters'][
                    user_id]['paused'] = parse_boolean(require_and_remove_key(
                        'paused', filters[user_id], "User Filters file."))
                dicts.bots[int(user_id) % len(args.tokens)]['filters'][
                    user_id]['areas'] = require_and_remove_key(
                        'areas', filters[user_id], "User Filters file.")
                dicts.bots[int(user_id) % len(args.tokens)]['filters'][
                    user_id]['pokemon_settings'] = load_pokemon_section(
                        require_and_remove_key(
                            'pokemon', filters[user_id], "User Filters file."))
                dicts.bots[int(user_id) % len(args.tokens)]['filters'][
                    user_id]['egg_settings'] = load_egg_section(
                        require_and_remove_key(
                            'eggs', filters[user_id], "User Filters file."))
                dicts.bots[int(user_id) % len(args.tokens)]['filters'][
                    user_id]['raid_settings'] = load_pokemon_section(
                        require_and_remove_key(
                            'raids', filters[user_id], "User Filters file."))
        log.info('Loaded DM filters.')
    except IOError:
        with open(get_path('../user_dicts/user_filters.json'), 'w') as f:
            json.dump({}, f, indent=4)
    log.info('DM bot successfully created.')
    return


async def index(request):
    return web.Response(text="PokeBot Running!")


async def handler(request):
    try:
        data = await request.json()
        await data_queue.put(data)
    except Exception as e:
        log.error("Encountered error while receiving webhook ({}: {})".format(
            type(e).__name__, e))
        raise web.HTTPBadRequest()
    return web.Response()


async def manage_webhook_data(queue):
    while True:
        if queue.qsize() > 300:
            log.warning((
                "Queue length is at {}... this may be causing a delay in " +
                "notifications."
            ).format(queue.qsize()))
        while queue.empty():
            await asyncio.sleep(1)
        data = await queue.get()
        obj = Webhook.make_object(data)
        if obj is not None:
            for name, mgr in dicts.managers.items():
                await mgr.update(obj)


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
    for name, mgr in dicts.managers.items():
        entries.append(Entry(client=mgr, event=asyncio.Event()))
    for entry in entries:
        loop.create_task(wrapped_connect(entry))
    loop.create_task(manage_webhook_data(data_queue))
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_post('/', handler)
    loop.create_task(web.run_app(app, port=args.port))
    loop.run_until_complete(check_close())
    loop.close()
