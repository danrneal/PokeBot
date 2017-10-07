#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import time
import requests
from random import randint
from .utils import (get_args, reject_leftover_parameters,
                    require_and_remove_key, get_color, get_static_map_url)

log = logging.getLogger('DiscordAlarm')
args = get_args()


class Alarm(object):

    _defaults = {"pokemon": {}}

    @staticmethod
    def replace(string, pkinfo):
        if string is None:
            return None
        for key in pkinfo:
            string = string.replace("<{}>".format(key), str(pkinfo[key]))
        return string

    @staticmethod
    def try_sending(log, name, send_alert, args, max_attempts=3):
        for i in range(max_attempts):
            try:
                send_alert(**args)
                return
            except Exception as e:
                log.error((
                    "Encountered error while sending notification ({}: {})"
                ).format(type(e).__name__, e))
                log.error((
                    "{} is having connection issues. {} attempt of {}."
                ).format(name, i+1, max_attempts))
                time.sleep(3)
        log.error("Could not send notification... Giving up.")


class DiscordAlarm(Alarm):

    _defaults = {
        'pokemon': {
            'username': "<pkmn>",
            'content': "",
            'icon_url': (
                "https://raw.githubusercontent.com/kvangent/PokeAlarm/" +
                "master/icons/<pkmn_id>.png"
            ),
            'avatar_url': (
                "https://raw.githubusercontent.com/kvangent/PokeAlarm/" +
                "master/icons/<pkmn_id>.png"
            ),
            'title': "A wild <pkmn> has appeared!",
            'url': "<gmaps>",
            'body': "Available until <24h_time> (<time_left>).",
            'color': "<iv>"
        },
        'egg': {
            'username': "Egg",
            'content': "",
            'icon_url': (
                "https://raw.githubusercontent.com/kvangent/PokeAlarm/" +
                "master/icons/egg_<raid_level>.png"
            ),
            'avatar_url': (
                "https://raw.githubusercontent.com/kvangent/PokeAlarm/" +
                "master/icons/egg_<raid_level>.png"
            ),
            'title': "Raid is incoming!",
            'url': "<gmaps>",
            'body': (
                "A level <raid_level> raid will hatch <begin_24h_time> " +
                "(<begin_time_left>)."
            ),
            'color': "<raid_level>"
        },
        'raid': {
            'username': "Raid",
            'content': "",
            'icon_url': (
                "https://raw.githubusercontent.com/kvangent/PokeAlarm/" +
                "master/icons/<pkmn_id>.png"
            ),
            'avatar_url': (
                "https://raw.githubusercontent.com/kvangent/PokeAlarm/" +
                "master/icons/egg_<raid_level>.png"
            ),
            'title': "Level <raid_level> Raid is available against <pkmn>!",
            'url': "<gmaps>",
            'body': "The raid is available until <24h_time> (<time_left>).",
            'color': "<raid_level>"
        }
    }

    def __init__(self, settings, max_attempts):
        self.__webhook_url = require_and_remove_key(
            'webhook_url', settings, "'Discord' type alarms.")
        self.__max_attempts = max_attempts
        self.__avatar_url = settings.pop('avatar_url', "")
        self.__map = settings.pop('map', {})
        self.__pokemon = self.create_alert_settings(
            settings.pop('pokemon', {}), self._defaults['pokemon'])
        self.__egg = self.create_alert_settings(
            settings.pop('egg', {}), self._defaults['egg'])
        self.__raid = self.create_alert_settings(
            settings.pop('raid', {}), self._defaults['raid'])
        reject_leftover_parameters(settings, "'Alarm level in Discord alarm.")
        log.info("Discord Alarm has been created!")

    def create_alert_settings(self, settings, default):
        alert = {
            'webhook_url': settings.pop('webhook_url', self.__webhook_url),
            'username': settings.pop('username', default['username']),
            'avatar_url': settings.pop('avatar_url', default['avatar_url']),
            'content': settings.pop('content', default['content']),
            'icon_url': settings.pop('icon_url', default['icon_url']),
            'title': settings.pop('title', default['title']),
            'url': settings.pop('url', default['url']),
            'body': settings.pop('body', default['body']),
            'color': default['color'],
            'map': get_static_map_url(
                settings.pop('map', self.__map), args.gmaps_keys[randint(
                    0, len(args.gmaps_keys) - 1)])
        }
        reject_leftover_parameters(settings, "'Alert level in Discord alarm.")
        return alert

    def send_alert(self, alert, info):
        payload = {
            'username': self.replace(alert['username'], info)[:32],
            'content': self.replace(alert['content'], info),
            'avatar_url':  self.replace(alert['avatar_url'], info),
            'embeds': [{
                'title': self.replace(alert['title'], info),
                'url': self.replace(alert['url'], info),
                'description': self.replace(alert['body'], info),
                'color': get_color(self.replace(alert['color'], info)),
                'thumbnail': {'url': self.replace(alert['icon_url'], info)}
            }]
        }
        if alert['map'] is not None:
            payload['embeds'][0]['image'] = {
                'url': self.replace(alert['map'], {
                    'lat': info['lat'],
                    'lng': info['lng']
                })
            }
        args = {
            'url': alert['webhook_url'],
            'payload': payload
        }
        self.try_sending(log, "Discord", self.send_webhook, args,
                         self.__max_attempts)

    def pokemon_alert(self, pokemon_info):
        self.send_alert(self.__pokemon, pokemon_info)

    def raid_egg_alert(self, raid_info):
        self.send_alert(self.__egg, raid_info)

    def raid_alert(self, raid_info):
        self.send_alert(self.__raid, raid_info)

    def send_webhook(self, url, payload):
        resp = requests.post(url, json=payload, timeout=(None, 5))
        if resp.ok is True:
            log.info("Notification successful (returned {})".format(
                resp.status_code))
        else:
            log.info("Discord response was {}".format(resp.content))
            raise requests.exceptions.RequestException(
                "Response received {}, webhook not accepted.".format(
                    resp.status_code))
