import logging
import requests
import itertools
from .Alarm import Alarm
from ..Utilities.MonUtils import get_color
from ..Utilities.GenUtils import (
    get_image_url, get_static_map_url, reject_leftover_parameters
)

log = logging.getLogger('Discord')

try_sending = Alarm.try_sending
replace = Alarm.replace


class DiscordAlarm(Alarm):

    _defaults = {
        'monsters': {
            'webhook_url': "",
            'username': "<mon_name>",
            'content': "",
            'icon_url': get_image_url(
                "regular/monsters/<mon_id_3>_<form_id_3>.png"),
            'avatar_url': get_image_url(
                "regular/monsters/<mon_id_3>_<form_id_3>.png"),
            'title': "A wild <mon_name> has appeared!",
            'url': "<gmaps>",
            'body': "Available until <24h_time> (<time_left>).",
            'color': "<iv>"
        },
        'eggs': {
            'webhook_url': "",
            'username': "Egg",
            'content': "",
            'icon_url': get_image_url("regular/eggs/<egg_lvl>.png"),
            'avatar_url': get_image_url("regular/eggs/<egg_lvl>.png"),
            'title': "Raid is incoming!",
            'url': "<gmaps>",
            'body': (
                "A level <egg_lvl> raid will hatch at <24h_hatch_time> " +
                "(<hatch_time_left>)."
            ),
            'color': "<egg_lvl>"
        },
        'raids': {
            'webhook_url': "",
            'username': "Raid",
            'content': "",
            'icon_url': get_image_url("regular/monsters/<mon_id_3>_000.png"),
            'avatar_url': get_image_url("regular/monsters/<mon_id_3>_000.png"),
            'title': "Level <raid_lvl> raid is available against <mon_name>!",
            'url': "<gmaps>",
            'body': (
                "The raid is available until <24h_raid_end> " +
                "(<raid_time_left>)."
            ),
            'color': "<raid_lvl>"
        }
    }

    def __init__(self, settings, max_attempts, static_map_key):
        self.__max_attempts = max_attempts
        self.__avatar_url = settings.pop('avatar_url', "")
        self.__map = settings.pop('map', {})
        self.__static_map_key = itertools.cycle(static_map_key)
        self.__monsters = self.create_alert_settings(
            settings.pop('monsters', {}), self._defaults['monsters'])
        self.__eggs = self.create_alert_settings(
            settings.pop('eggs', {}), self._defaults['eggs'])
        self.__raids = self.create_alert_settings(
            settings.pop('raids', {}), self._defaults['raids'])
        reject_leftover_parameters(settings, "'Alarm level in Discord alarm.")
        log.info("Discord Alarm has been created!")

    def create_alert_settings(self, settings, default):
        alert = {
            'webhook_url': settings.pop('webhook_url', default['webhook_url']),
            'username': settings.pop('username', default['username']),
            'avatar_url': settings.pop('avatar_url', default['avatar_url']),
            'content': settings.pop('content', default['content']),
            'icon_url': settings.pop('icon_url', default['icon_url']),
            'title': settings.pop('title', default['title']),
            'url': settings.pop('url', default['url']),
            'body': settings.pop('body', default['body']),
            'color': default['color'],
            'map': get_static_map_url(
                settings.pop('map', self.__map), next(self.__static_map_key))
        }
        reject_leftover_parameters(settings, "'Alert level in Discord alarm.")
        return alert

    def send_alert(self, alert, info):
        payload = {
            'username': replace(alert['username'], info)[:32],
            'content': replace(alert['content'], info),
            'avatar_url': replace(alert['avatar_url'], info),
            'embeds': [{
                'title': replace(alert['title'], info),
                'url': replace(alert['url'], info),
                'description': replace(alert['body'], info),
                'color': get_color(self.replace(alert['color'], info)),
                'thumbnail': {'url': replace(alert['icon_url'], info)}
            }]
        }
        if alert['map'] is not None:
            coords = {
                'lat': info['lat'],
                'lng': info['lng']
            }
            payload['embeds'][0]['image'] = {
                'url': replace(alert['map'], coords)
            }
        args = {
            'url': replace(alert['webhook_url'], info),
            'payload': payload
        }
        try_sending(
            log, "Discord", self.send_webhook, args, self.__max_attempts
        )

    def pokemon_alert(self, pokemon_info):
        self.send_alert(self.__monsters, pokemon_info)

    def raid_egg_alert(self, raid_info):
        self.send_alert(self.__eggs, raid_info)

    def raid_alert(self, raid_info):
        self.send_alert(self.__raids, raid_info)

    def send_webhook(self, url, payload):
        resp = requests.post(url, json=payload, timeout=5)
        if resp.ok is not True:
            raise requests.exceptions.RequestException((
                "Response received {}, webhook not accepted."
            ).format(resp.status_code))
