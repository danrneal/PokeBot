#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from PokeBot.utils import get_args, get_dicts
from PokeBot.clients import start_clients

logging.basicConfig(format='[%(name)10.10s][%(levelname)8.8s] %(message)s',
                    level=logging.INFO)
log = logging.getLogger('server')
logging.getLogger("discord").setLevel(logging.ERROR)
logging.getLogger("websockets").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("geocoder").setLevel(logging.ERROR)

args = get_args()
dicts = get_dicts(len(args.tokens))


def start_bots():
    log.info("{} bot(s) to be started".format(len(args.tokens)))
    if len(args.feed_channels) > 1:
        log.info("{} feed channels set".format(len(args.feed_channels)))
    else:
        log.info("Feed channel set to {}".format(args.feed_channels[0]))
    if len(args.command_channels) > 1:
        log.info("{} command channels set".format(len(args.command_channels)))
    else:
        log.info("Command channel set to {}".format(args.command_channels[0]))
    log.info("{} areas set".format(len(args.areas)))
    if args.muted_role is not None:
        log.info("Muted role set to {}".format(args.muted_role))
    else:
        log.info("No muted role set")
    if args.gmaps_api_key is not None:
        log.info("{} google maps api key(s) loaded".format(len(
            args.gmaps_api_key)))
    else:
        log.info("No google maps api keys loaded")
    if args.all_areas is True:
        log.info("All users will automatically be added to all areas")
    else:
        log.info("All users will automatically be added to no areas")
    log.info('Listening on `{}:{}`'.format(args.host, args.port))
    log.info("Starting Clients")
    start_clients()

###############################################################################


if __name__ == '__main__':
    log.info("PokeBot is getting ready...")
    start_bots()
