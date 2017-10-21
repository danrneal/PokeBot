#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import discord
import asyncio
from .processing import in_q
from .utils import get_args, Dicts, update_dicts
from .commands import (status, commands, dex, donate, set_, delete, pause,
                       resume, activate, deactivate, alerts, areas)

log = logging.getLogger('Bot')
args = get_args()


class Bot(discord.Client):

    async def on_ready(self):
        bot_number = args.bot_client_ids.index(self.user.id)
        await asyncio.sleep(bot_number)
        log.info("Bot number {} connected".format(bot_number + 1))
        await asyncio.sleep(len(args.tokens))
        if bot_number != 0:
            await self.change_presence(status=discord.Status.invisible)
        for guild in self.guilds:
            if guild.id not in Dicts.roles:
                Dicts.roles[guild.id] = {}
            for role in guild.roles:
                Dicts.roles[guild.id][role.name.lower()] = role
        users = []
        for member in self.get_all_members():
            if (member.top_role > Dicts.roles[member.guild.id][
                args.alert_role] and
                    str(member.id) not in users):
                users.append(str(member.id))
        user_count = 0
        area_count = 0
        for user_id in Dicts.bots[bot_number]['filters']:
            if user_id not in users:
                Dicts.bots[bot_number]['filters'].pop(user_id)
                for settings in [
                        'pokemon_settings', 'egg_settings', 'raid_settings']:
                    if user_id in Dicts.bots[bot_number][settings]:
                        Dicts.bots[bot_number][settings].pop(user_id)
                user_count += 1
                continue
            for area in Dicts.bots[bot_number]['filters'][user_id]['areas']:
                if area not in Dicts.geofences:
                    Dicts.bots[bot_number]['filters'][user_id]['areas'].remove(
                        area)
                    area_count += 1
        await asyncio.sleep(bot_number)
        if user_count > 0 or area_count > 0:
            update_dicts()
            if user_count > 0:
                log.info("Bot number {} removed {} user(s) from dicts".format(
                    bot_number + 1, user_count))
            if area_count > 0:
                log.info((
                    "Bot number {} removed {} user(s) outdated areas"
                ).format(bot_number + 1, area_count))
        log.info("Bot number {} is ready".format(bot_number + 1))
        await in_q(self, bot_number)

    async def on_member_update(self, before, after):
        bot_number = args.bot_client_ids.index(self.user.id)
        if (after.id % len(args.tokens) == bot_number and
            str(after.id) in Dicts.bots[bot_number]['filters'] and
                before.roles != after.roles):
            if after.top_role < Dicts.roles[after.guild.id][args.alert_role]:
                Dicts.bots[bot_number]['filters'].pop(str(after.id))
                update_dicts()
                for settings in [
                        'pokemon_settings', 'egg_settings', 'raid_settings']:
                    if str(after.id) in Dicts.bots[bot_number][settings]:
                        Dicts.bots[bot_number][settings].pop(str(after.id))
                log.info('Removed {} from dicts'.format(after.display_name))
            elif (args.muted_role is not None and
                  Dicts.roles[after.guild.id][
                      args.muted_role] in after.roles and
                  Dicts.bots[bot_number]['filters'][str(after.id)][
                      'paused'] is False):
                Dicts.bots[bot_number]['filters'][str(after.id)][
                    'paused'] = True
                update_dicts()
                await Dicts.bots[bot_number]['out_queue'].put((
                    1, Dicts.bots[bot_number]['count'], {
                        'destination': discord.utils.get(
                            after.guild.members,
                            id=after.id
                        ),
                        'msg': 'Alerts have been paused for `{}`.'.format(
                            after.display_name)
                    }
                ))
                Dicts.bots[bot_number]['count'] += 1
                log.info('Paused {} on mute.'.fotmat(after.display_name))

    async def on_member_remove(self, member):
        bot_number = args.bot_client_ids.index(self.user.id)
        if (member.id % len(args.tokens) == bot_number and
            str(member.id) in Dicts.bots[bot_number]['filters'] and
                member not in self.get_all_members()):
            Dicts.bots[bot_number]['filters'].pop(str(member.id))
            update_dicts()
            for settings in [
                    'pokemon_settings', 'egg_settings', 'raid_settings']:
                if str(member.id) in Dicts.bots[bot_number][settings]:
                    Dicts.bots[bot_number][settings].pop(str(member.id))
            log.info('Removed {} from Dicts.'.format(member.display_name))

    async def on_message(self, message):
        bot_number = args.bot_client_ids.index(self.user.id)
        if isinstance(message.channel, discord.abc.GuildChannel) is True:
            if message.content.lower() == '!status':
                await status(self, bot_number, message)
            elif message.author.id % len(args.tokens) == bot_number:
                if message.content.lower() in ['!commands', '!help']:
                    await commands(bot_number, message)
                elif message.content.lower().startswith('!dex '):
                    dex(bot_number, message)
                elif message.content.lower() == '!donate':
                    await donate(bot_number, message)
                elif message.channel.id in args.command_channels:
                    if message.content.lower().startswith('!set '):
                        set_(self, message, bot_number)
                    elif message.content.lower().startswith(
                            ('!delete ', '!remove ')):
                        delete(bot_number, message)
                    elif message.content.lower() in ['!pause', '!p']:
                        pause(bot_number, message)
                    elif message.content.lower() in ['!resume', '!r']:
                        resume(bot_number, message)
                    elif message.content.lower().startswith('!activate '):
                        activate(bot_number, message)
                    elif message.content.lower().startswith('!deactivate '):
                        deactivate(bot_number, message)
                    elif message.content.lower() == '!alerts':
                        alerts(bot_number, message)
                    elif message.content.lower() == '!areas':
                        areas(bot_number, message)
