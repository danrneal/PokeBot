#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import discord
from datetime import datetime
from random import randint
from .DiscordAlarm import Alarm
from .utils import (get_args, Dicts, reject_leftover_parameters, get_color,
                    get_static_map_url, get_image_url)

log = logging.getLogger('Notification')
args = get_args()


class Notification(Alarm):

    _defaults = {
        'pokemon': {
            'content': "",
            'icon_url': get_image_url(
                "monsters/<pkmn_id_3>_<form_id_or_empty>.png"),
            'title': "A wild <pkmn> has appeared!",
            'url': "<gmaps>",
            'body': "Available until <24h_time> (<time_left>).",
            'color': "<iv>"
        },
        'egg': {
            'content': "",
            'icon_url': get_image_url("eggs/<raid_level>.png"),
            'title': "Raid is incoming!",
            'url': "<gmaps>",
            'body': (
                "A level <raid_level> raid will hatch <begin_24h_time> " +
                "(<begin_time_left>)."
            ),
            'color': "<raid_level>"
        },
        'raid': {
            'content': "",
            'icon_url': get_image_url(
                "monsters/<pkmn_id_3>_<form_id_or_empty>.png"),
            'title': "Level <raid_level> Raid is available against <pkmn>!",
            'url': "<gmaps>",
            'body': "The raid is available until <24h_time> (<time_left>).",
            'color': "<raid_level>"
        }
    }

    def __init__(self, settings):
        self.__map = settings.pop('map', {})
        self.__pokemon = self.create_alert_settings(
            settings.pop('pokemon', {}), self._defaults['pokemon'])
        self.__egg = self.create_alert_settings(
            settings.pop('egg', {}), self._defaults['egg'])
        self.__raid = self.create_alert_settings(
            settings.pop('raid', {}), self._defaults['raid'])
        reject_leftover_parameters(settings, "'Alarm level in DM alarm.")
        log.info("DM Alarm has been created!")

    def create_alert_settings(self, settings, default):
        alert = {
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
        reject_leftover_parameters(settings, "'Alert level in DM alarm.")
        return alert

    async def send_alert(self, client, bot_number, alert, info, user_ids):
        msg = self.replace(alert['content'], info)
        em = discord.Embed(
            title=self.replace(alert['title'], info),
            url=self.replace(alert['url'], info),
            description=self.replace(alert['body'], info),
            color=get_color(self.replace(alert['color'], info))
        )
        em.set_thumbnail(url=self.replace(alert['icon_url'], info))
        if alert['map'] is not None:
            em.set_image(
                url=self.replace(alert['map'], {
                    'lat': info['lat'],
                    'lng': info['lng']
                })
            )
        for user_id in user_ids:
            await Dicts.bots[bot_number]['out_queue'].put((
                2, Dicts.bots[bot_number]['count'], {
                    'destination': discord.utils.get(
                        client.get_all_members(),
                        id=int(user_id)
                    ),
                    'msg': msg,
                    'embed': em,
                    'timestamp': datetime.utcnow()
                }
            ))
            Dicts.bots[bot_number]['count'] += 1

    async def pokemon_alert(self, client, bot_number, pokemon_info, user_ids):
        await self.send_alert(
            client, bot_number, self.__pokemon, pokemon_info, user_ids)

    async def raid_egg_alert(self, client, bot_number, raid_info, user_ids):
        await self.send_alert(
            client, bot_number, self.__egg, raid_info, user_ids)

    async def raid_alert(self, client, bot_number, raid_info, user_ids):
        await self.send_alert(
            client, bot_number, self.__raid, raid_info, user_ids)
