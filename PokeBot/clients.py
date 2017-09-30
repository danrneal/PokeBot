#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import discord
from queue import PriorityQueue
from collections import namedtuple
from .utils import get_args, Dicts
from .Bot import Bot

logging.basicConfig(format='[%(name)10.10s][%(levelname)8.8s] %(message)s',
                    level=logging.INFO)
log = logging.getLogger('clients')
logging.getLogger("aiohttp").setLevel(logging.ERROR)

args = get_args()
dicts = Dicts()
entries = []


async def login(tokens, number_of_bots):
    bot_num = 0
    for entry in entries:
        bot_num += 1
        log.info("Logging into account number {} of {}".format(
            bot_num, number_of_bots))
        await entry.client.login(tokens.pop(0))


async def wrapped_connect(entry):
    try:
        await entry.client.connect()
    except Exception as e:
        await entry.client.client.close()
        log.info('We got an exception: ', e.__class__.__name__, e)
        entry.event.set()


async def check_close():
    futures = [entry.event.wait() for entry in entries]
    await asyncio.wait(futures)


def start_clients():
    number_of_bots = len(args.tokens)
    loop = asyncio.get_event_loop()
    Entry = namedtuple('Entry', 'client event')
    for bot in range(len(args.tokens)):
        entries.append(Entry(client=Bot(), event=asyncio.Event()))
    loop.run_until_complete(login(args.tokens, number_of_bots))
    for entry in entries:
        loop.create_task(wrapped_connect(entry))
    loop.run_until_complete(check_close())
    loop.close()
