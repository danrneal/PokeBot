#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import discord
from .DiscordAlarm import Alarm
from .utils import get_args, Dicts, reject_leftover_parameters, get_color

log = logging.getLogger('Notification')
args = get_args()
dicts = Dicts()


class Notification(Alarm):

    _defaults = {
        'pokemon': {
            'content': "",
            'icon_url': (
                "https://raw.githubusercontent.com/kvangent/PokeAlarm/" +
                "master/icons/<pkmn_id>.png"
            ),
            'title': "A wild <pkmn> has appeared!",
            'url': "<gmaps>",
            'body': "Available until <24h_time> (<time_left>).",
            'color': "<iv>"
        },
        'egg': {
            'content': "",
            'icon_url': (
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
            'content': "",
            'icon_url': (
                "https://raw.githubusercontent.com/kvangent/PokeAlarm/" +
                "master/icons/<pkmn_id>.png"
            ),
            'title': "Level <raid_level> Raid is available against <pkmn>!",
            'url': "<gmaps>",
            'body': "The raid is available until <24h_time> (<time_left>).",
            'color': "<raid_level>"
        }
    }

    def __init__(self, settings):
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
            'color': default['color']
        }
        reject_leftover_parameters(settings, "'Alert level in DM alarm.")
        return alert

    def send_alert(self, bot_number, client, alert, info, user_ids):
        msg = self.replace(alert['content'], info)
        em = discord.Embed(
            title=self.replace(alert['title'], info),
            url=self.replace(alert['url'], info),
            description=self.replace(alert['body'], info),
            color=get_color(self.replace(alert['color'], info))
        )
        em.set_thumbnail(url=self.replace(alert['icon_url'], info))
        for user_id in user_ids:
            dicts.bots[bot_number]['out_queue'].put((
                2, dicts.bots[bot_number]['count'], {
                    'destination': discord.utils.get(
                        client.get_all_members(),
                        id=int(user_id)
                    ),
                    'msg': msg,
                    'embed': em
                }
            ))
            dicts.bots[bot_number]['count'] += 1

    def pokemon_alert(self, client, bot_number, pokemon_info, user_ids):
        self.send_alert(
            self.__pokemon, client, bot_number, pokemon_info, user_ids)

    def raid_egg_alert(self, bot_number, raid_info, user_ids):
        self.send_alert(self.__egg, bot_number, raid_info, user_ids)

    def raid_alert(self, bot_number, raid_info, user_ids):
        self.send_alert(self.__raid, bot_number, raid_info, user_ids)
