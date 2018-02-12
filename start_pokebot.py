#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import sys
import configargparse
import asyncio
import logging.handlers
from collections import namedtuple
from aiohttp import web
from PokeBot import config
from PokeBot.Cache import cache_options
from PokeBot.Manager import Manager
from PokeBot.BotManager import BotManager
from PokeBot.Load import parse_rules_file
from PokeBot.Events import event_factory
from PokeBot.Utilities.GenUtils import get_path, LoggerWriter

filehandler = logging.handlers.TimedRotatingFileHandler(
    'pokebot.log',
    when='midnight',
    backupCount=2
)
consolehandler = logging.StreamHandler()
logging.basicConfig(
    format=(
        '%(asctime)s [%(processName)15.15s][%(name)10.10s]' +
        '[%(levelname)8.8s] %(message)s'
    ),
    level=logging.INFO,
    handlers=[filehandler, consolehandler]
)

log = logging.getLogger('Server')
sys.stdout = LoggerWriter(log.info)
sys.stderr = LoggerWriter(log.warning)

managers = {}
bot_managers = {}
entries = []
data_queue = asyncio.Queue()


async def index(request):
    return web.Response(text="PokeBot Running!")


async def handler(request):
    try:
        data = await request.json()
        if type(data) == dict:
            await data_queue.put(data)
        else:
            for frame in data:
                await data_queue.put(frame)
    except Exception as e:
        log.error("Encountered error while receiving webhook ({}: {})".format(
            type(e).__name__, e))
        raise web.HTTPBadRequest()
    return web.Response()


async def manage_webhook_data(queue):
    while True:
        qsize = queue.qsize()
        if qsize > 5000:
            log.warning((
                "Queue length is at {}... this may be causing a significant " +
                "delay in notifications."
            ).format(qsize))
        data = await queue.get()
        obj = event_factory(data)
        if obj is not None:
            for name, mgr in managers.items():
                await mgr.update(obj)
            for name, bot_mgr in bot_managers.items():
                await bot_mgr.update(obj)


def start_server():
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("discord").setLevel(logging.WARNING)
    loop = asyncio.get_event_loop()
    Entry = namedtuple('Entry', 'client event')
    parse_settings(os.path.abspath(os.path.dirname(__file__)), loop, Entry)
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_post('/', handler)
    loop.create_task(manage_webhook_data(data_queue))
    log.info("PokeBot is listening for webhooks on: http://{}:{}".format(
        config['HOST'], config['PORT']))
    loop.run_until_complete(web.run_app(app, port=config['PORT']))
    try:
        loop.run_until_complete(check_close(entries))
    except KeyboardInterrupt:
        loop.close()
    except Exception:
        raise Exception


def parse_settings(root_path, loop, Entry):
    config['ROOT_PATH'] = root_path
    config_files = [get_path('config/config.ini')]
    if '-cf' in sys.argv or '--config' in sys.argv:
        config_files = []
    parser = configargparse.ArgParser(default_config_files=config_files)
    parser.add_argument(
        '-cf', '--config',
        is_config_file=True,
        help='Configuration file'
    )
    parser.add_argument(
        '-H', '--host',
        help='Set web server listening host',
        default='127.0.0.1'
    )
    parser.add_argument(
        '-P', '--port',
        type=int,
        help='Set web server listening port',
        default=4000
    )
    parser.add_argument(
        '-m', '--manager_count',
        type=int,
        default=1,
        help='Number of Manager processes to start.'
    )
    parser.add_argument(
        '-M', '--manager_name',
        type=str,
        action='append',
        default=[],
        help='Names of Manager processes to start.'
    )
    parser.add_argument(
        '-k', '--key',
        type=str,
        action='append',
        default=[None],
        help='Specify a Google API Key to use.'
    )
    parser.add_argument(
        '-f', '--filters',
        type=str,
        action='append',
        default=['filters.json'],
        help='Filters configuration file. default: filters.json'
    )
    parser.add_argument(
        '-a', '--alarms',
        type=str,
        action='append',
        default=['alarms.json'],
        help='Alarms configuration file. default: alarms.json'
    )
    parser.add_argument(
        '-r', '--rules',
        type=str,
        action='append',
        default=[None],
        help='Rules configuration file. default: None'
    )
    parser.add_argument(
        '-gf', '--geofences',
        type=str,
        action='append',
        default=[None],
        help='Alarms configuration file. default: None'
    )
    parser.add_argument(
        '-L', '--locale',
        type=str.lower,
        default='en',
        choices=['de', 'en', 'es', 'fr', 'it', 'ko', 'pt', 'zh_hk'],
        help=(
            'Locale for Pokemon and Move names: default en, check locale ' +
            'folder for more options'
        )
    )
    parser.add_argument(
        '-ct', '--cache_type',
        type=str.lower,
        default='mem',
        choices=cache_options,
        help=(
            "Specify the type of cache to use. Options: ['mem', 'file'] " +
            "(Default: 'mem')"
        )
    )
    parser.add_argument(
        '-ma', '--max_attempts',
        type=int,
        default=3,
        help='Maximum attempts an alarm makes to send a notification.'
    )
    parser.add_argument(
        '-bt', '--bot_tokens',
        type=str,
        action='append',
        default=[],
        help='List of tokens for Discord Bots'
    )
    parser.add_argument(
        '-uf', '--user_filters',
        type=str,
        default='./user_filters/user_filters.json',
        help=(
            'User filters configuration file. default: ' +
            '/user_filters/user_filters.json'
        )
    )
    parser.add_argument(
        '-ua', '--user_alarms',
        type=str,
        default='user_alarms.json',
        help='User alarms configuration file. default: user_alarms.json'
    )
    parser.add_argument(
        '-ugf', '--user_geofences',
        type=str,
        default=None,
        help='User geofences configuration file. default: None'
    )
    parser.add_argument(
        '-cc', '--command_channels',
        type=int,
        action='append',
        default=[],
        help='Channel ID that users input subscription commands'
    )
    parser.add_argument(
        '-alert', '--alert_role',
        type=str.lower,
        default='@everyone',
        help="Role for users that can use the bot (default: '@everyone')"
    )
    parser.add_argument(
        '-muted', '--muted_role',
        type=str.lower,
        default=None,
        help='Role name for muted users'
    )
    parser.add_argument(
        '-aa', '--all_areas',
        action='store_true',
        default=False,
        help=(
            'Set to True to subscribe to all areas by default (default: False)'
        )
    )
    args = parser.parse_args()
    config['HOST'] = args.host
    config['PORT'] = args.port
    for arg in [
        args.filters, args.alarms, args.rules, args.rules, args.geofences
    ]:
        if len(arg) > 1:
            arg.pop(0)
        size = len(arg)
        if size != 1 and size != args.manager_count:
            log.critical(
                "Number of arguments must be either 1 for all managers or " +
                "equal to Manager Count. Please provided the correct number " +
                "of arguments.")
            log.critical(arg)
            sys.exit(1)
    if len(args.key) > 1:
        args.key.pop(0)
    while len(args.manager_name) < args.manager_count:
        m_ct = len(args.manager_name)
        args.manager_name.append("Manager_{}".format(m_ct))
    for m_ct in range(args.manager_count):
        m = Manager(
            name=args.manager_name[m_ct],
            google_key=args.key,
            locale=args.locale,
            max_attempts=args.max_attempts,
            cache_type=args.cache_type,
            filter_file=get_from_list(args.filters, m_ct, args.filters[0]),
            geofence_file=get_from_list(
                args.geofences, m_ct, args.geofences[0]),
            alarm_file=get_from_list(args.alarms, m_ct, args.alarms[0])
        )
        parse_rules_file(m, get_from_list(args.rules, m_ct, args.rules[0]))
        if m.get_name() not in managers:
            managers[m.get_name()] = m
        else:
            log.critical(
                "Names of Manager processes must be unique (not case " +
                "sensitive)! Process will exit."
            )
            sys.exit(1)
    log.info("Starting up the Managers")
    for m_name in managers:
        manager = managers[m_name]
        entries.append(Entry(client=manager, event=asyncio.Event()))
        loop.create_task(manager.run())
    for bm_ct in range(len(args.bot_tokens)):
        bm = BotManager(
            name="Bot_{}".format(bm_ct),
            bot_number=bm_ct,
            google_key=args.key,
            locale=args.locale,
            cache_type=args.cache_type,
            filter_file=args.user_filters,
            geofence_file=args.user_geofences,
            alarm_file=args.user_alarms,
            command_channels=args.command_channels,
            alert_role=args.alert_role,
            muted_role=args.muted_role,
            all_areas=args.all_areas,
            number_of_bots=len(args.bot_tokens)
        )
        bot_managers[bm.get_name()] = bm
    log.info("Starting up the Bots")
    for bm_name in bot_managers:
        bot_manager = bot_managers[bm_name]
        entries.append(Entry(client=bot_manager, event=asyncio.Event()))
        loop.run_until_complete(bot_manager.login(
            args.bot_tokens[bot_manager.get_bot_number()]))
        loop.create_task(bot_manager.connect())
        loop.create_task(bot_manager.run())
        loop.create_task(bot_manager.get_alarm().send_dm())


def get_from_list(arg, i, default):
    return arg[i] if len(arg) > 1 else default


async def check_close(entries):
    futures = [entry.event.wait() for entry in entries]
    await asyncio.wait(futures)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


if __name__ == '__main__':
    log.info("PokeBot is getting ready...")
    start_server()
