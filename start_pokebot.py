#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from PokeBot.utils import get_args
from PokeBot.clients import start_clients

logging.basicConfig(
    format='[%(name)10.10s][%(levelname)8.8s] %(message)s',
    level=logging.INFO
)
log = logging.getLogger('server')
logging.getLogger("discord").setLevel(logging.ERROR)
logging.getLogger("websockets").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("geocoder").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)

args = get_args()


def start_bots():
    log.info("{} managers to be loaded".format(args.manager_count))
    log.info("{} locale loaded".format(args.locale))
    log.info("{} geofences loaded".format(len(args.master_geofences)))
    log.info("{} bot(s) to be started".format(len(args.tokens)))
    log.info("{} command channels set".format(len(args.command_channels)))
    log.info("Alert role set {}".format(args.alert_role))
    if args.muted_role is not None:
        log.info("Muted role set to {}".format(args.muted_role))
    else:
        log.info("No muted role set")
    log.info("{} google maps api key(s) loaded".format(len(args.gmaps_keys)))
    if args.all_areas is True:
        log.info("All users will automatically be added to all areas")
    else:
        log.info("All users will automatically be added to no areas")
    log.info('Listening on `0.0.0.0:{}`'.format(args.port))
    log.info("Starting Clients")
    start_clients()

###############################################################################


if __name__ == '__main__':
    log.info("PokeBot is getting ready...")
    start_bots()
