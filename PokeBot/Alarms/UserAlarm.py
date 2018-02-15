import logging
import discord
import asyncio
import json
from collections import OrderedDict
from datetime import datetime, timedelta
from .Alarm import Alarm
from ..Utilities.MonUtils import get_color
from ..Utilities.GenUtils import (
    get_image_url, get_static_map_url, reject_leftover_parameters,
    update_filters, get_path
)

log = logging.getLogger('Discord')

try_sending = Alarm.try_sending
replace = Alarm.replace


class UserAlarm(Alarm):

    _defaults = {
        'monsters': {
            'content': "",
            'icon_url': get_image_url(
                "regular/monsters/<mon_id_3>_<form_id_3>.png"),
            'title': "A wild <mon_name> has appeared!",
            'url': "<gmaps>",
            'body': "Available until <24h_time> (<time_left>).",
            'color': "<iv>"
        },
        'eggs': {
            'content': "",
            'icon_url': get_image_url("regular/eggs/<egg_lvl>.png"),
            'title': "Raid is incoming!",
            'url': "<gmaps>",
            'body': (
                "A level <egg_lvl> raid will hatch at <24h_hatch_time> " +
                "(<hatch_time_left>)."
            ),
            'color': "<egg_lvl>"
        },
        'raids': {
            'content': "",
            'icon_url': get_image_url("regular/monsters/<mon_id_3>_000.png"),
            'title': "Level <raid_lvl> raid is available against <mon_name>!",
            'url': "<gmaps>",
            'body': (
                "The raid is available until <24h_raid_end> " +
                "(<raid_time_left>)."
            ),
            'color': "<raid_lvl>"
        }
    }

    def __init__(self, settings, static_map_key, client):
        self.__client = client
        self.__queue = asyncio.PriorityQueue()
        self.__snowflake = 0
        self.__map = settings.pop('map', {})
        self.__static_map_key = static_map_key
        self.__monsters = self.create_alert_settings(
            settings.pop('monsters', {}), self._defaults['monsters'])
        self.__eggs = self.create_alert_settings(
            settings.pop('eggs', {}), self._defaults['eggs'])
        self.__raids = self.create_alert_settings(
            settings.pop('raids', {}), self._defaults['raids'])
        reject_leftover_parameters(settings, "'Alarm level in Discord alarm.")
        log.info("Discord Alarm has been created!")

    async def update(self, priority, obj):
        self.__snowflake += 1
        await self.__queue.put((
            priority, datetime.utcnow(), self.__snowflake, obj
        ))

    def create_alert_settings(self, settings, default):
        alert = {
            'content': settings.pop('content', default['content']),
            'icon_url': settings.pop('icon_url', default['icon_url']),
            'title': settings.pop('title', default['title']),
            'url': settings.pop('url', default['url']),
            'body': settings.pop('body', default['body']),
            'color': default['color'],
            'map': get_static_map_url(
                settings.pop('map', self.__map), self.__static_map_key)
        }
        reject_leftover_parameters(settings, "'Alert level in Discord alarm.")
        return alert

    async def send_alert(self, alert, info, dest):
        content = replace(alert['content'], info)
        embeds = discord.Embed(
            title=replace(alert['title'], info),
            url=replace(alert['url'], info),
            description=replace(alert['body'], info),
            color=get_color(replace(alert['color'], info))
        )
        embeds.set_thumbnail(url=self.replace(alert['icon_url'], info))
        if alert['map'] is not None:
            coords = {
                'lat': info['lat'],
                'lng': info['lng']
            }
            embeds.set_image(url=replace(alert['map'], coords))
        await self.update(2, {
            'destination': dest,
            'content': content,
            'embeds': embeds
        })

    async def pokemon_alert(self, pokemon_info, dest):
        await self.send_alert(self.__monsters, pokemon_info, dest)

    async def raid_egg_alert(self, raid_info, dest):
        await self.send_alert(self.__eggs, raid_info, dest)

    async def raid_alert(self, raid_info, dest):
        await self.send_alert(self.__raids, raid_info, dest)

    async def send_dm(self, filter_file):
        timestamps = []
        user_timestamps = {}
        while True:
            while len(timestamps) >= 120:
                if datetime.utcnow() - timestamps[0] > timedelta(minutes=1):
                    timestamps.pop(0)
            try:
                message = await self.__queue.get()
            except asyncio.QueueEmpty:
                self.__count = 0
                await asyncio.sleep(0)
                continue
            if datetime.utcnow() - message[1] > timedelta(minutes=1):
                log.warning((
                    "Bot queue is {} seconds behind..., consider adding " +
                    "more bots."
                ).format((datetime.utcnow() - message[1]).total_seconds()))
            destination = message[3]['destination']
            if (destination.guild is not None and
                    destination.id in user_timestamps):
                paused = False
                while len(user_timestamps[destination.id]) > 6:
                    if datetime.utcnow() - user_timestamps[destination.id][
                            0] > timedelta(seconds=30):
                        user_timestamps[destination.id].pop(0)
                    else:
                        with open(filter_file, 'r+', encoding="utf-8") as f:
                            user_filters = json.load(
                                f,
                                object_pairs_hook=OrderedDict
                            )
                            user_dict = user_filters[str(destination.id)]
                            user_dict['monsters']['enabled'] = False
                            user_dict['eggs']['enabled'] = False
                            user_dict['raids']['enabled'] = False
                            paused = True
                            embeds = discord.Embed(
                                description=((
                                    "{} Your alerts have been paused for" +
                                    "exceeding messaging rate limits, please" +
                                    "adjust your filters before resuming."
                                ).format(destination.mention)),
                                color=int('0xee281f', 16)
                            )
                            await destination.send(embed=embeds)
                            timestamps.append(datetime.utcnow())
                            log.info((
                                'Paused {} for exceeding DM limit.'
                            ).format(destination.display_name))
                            update_filters(user_filters, filter_file, f)
                        self.__client.load_filter_file(get_path(filter_file))
                        break
                if paused:
                    continue
            elif destination.guild is not None:
                user_timestamps[destination.id] = []
            try:
                await destination.send(
                    message[3].get('content'),
                    embed=message[3].get('embeds')
                )
                user_timestamps[destination.id].append(datetime.utcnow())
                timestamps.append(datetime.utcnow())
            except Exception as e:
                log.error((
                    "Encountered error during DM processing: {}: {}"
                ).format(type(e).__name__, e))
                log.error("Error sending DM to {}".format(
                    message[3]['destination']))
