#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import discord
import asyncio
from datetime import datetime
from .utils import get_args, Dicts, update_dicts
from .processing import in_q
from .commands import (donate, status, commands, dex, _set, delete, pause,
                       resume, pause_area, resume_area, alerts, areas)

log = logging.getLogger('Bot')

args = get_args()
dicts = Dicts()
users = []


class Bot(discord.Client):

    async def on_ready(self):
        bot_number = args.bot_client_ids.index(self.user.id)
        await asyncio.sleep(bot_number)
        log.info("Bot number {} connected".format(bot_number + 1))
        await asyncio.sleep(len(args.tokens))
        if bot_number != 0:
            await self.change_presence(status=discord.Status.invisible)
        for guild in self.guilds:
            for role in guild.roles:
                if role.name.lower() in dicts.bots[bot_number]['roles']:
                    dicts.bots[bot_number]['roles'][role.name.lower()].append(
                        role)
                else:
                    dicts.bots[bot_number]['roles'][role.name.lower()] = [role]
        for member in self.get_all_members():
            alert_role = False
            for role in dicts.bots[bot_number]['roles'][args.alert_role]:
                try:
                    if member.top_role > role:
                        alert_role = True
                        break
                except:
                    pass
            if alert_role is True and member.id not in users:
                users.append(str(member.id))
        user_count = 0
        area_count = 0
        for user_id in dicts.bots[bot_number]['filters']:
            if user_id not in users:
                dicts.bots[bot_number]['filters'].pop(user_id)
                user_count += 1
                continue
            for area in dicts.bots[bot_number]['filters'][user_id]['areas']:
                if area not in dicts.bots[bot_number]['geofences']:
                    dicts.bots[bot_number]['filters'][user_id]['areas'].pop(
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
        await in_q(bot_number)

    async def on_member_update(self, before, after):
        bot_number = args.bot_client_ids.index(self.user.id)
        if (after.id % len(args.tokens) == bot_number and
            str(after.id) in dicts.bots[bot_number]['filters'] and
                before.roles != after.roles):
            alert_role = False
            for role in dicts.bots[bot_number]['roles'][args.alert_role]:
                try:
                    if after.top_role > role:
                        alert_role = True
                        break
                except:
                    pass
            if alert_role is False:
                dicts.bots[bot_number]['filters'].pop(str(after.id))
                update_dicts()
                log.info('Removed {} from dicts'.format(str(after.id)))
            elif (args.muted_role is not None and
                  len(set(dicts.bots[bot_number]['roles'][
                      args.muted_role]).intersection(set(after.roles))) > 0 and
                  dicts.bots[bot_number][str(after.id)]['filters'][
                      'paused'] is False):
                dicts.bots[bot_number][str(after.id)]['filters']['paused'] = True
                update_dicts()
                await dicts.bots[bot_number]['out_queue'].put((
                    1, dicts.bots[bot_number]['count'], {
                        'destination': discord.utils.get(
                            after.guild.members,
                            id=after.id
                        ),
                        'msg': 'Alerts have been paused for `{}`.'.format(
                            after.display_name)
                    }
                ))
                dicts.bots[bot_number]['count'] += 1

    async def on_member_remove(self, member):
        bot_number = args.bot_client_ids.index(self.user.id)
        if (member.id % len(args.tokens) == bot_number and
                str(member.id) in dicts.bots[bot_number]['filters']):
            dicts.bots[bot_number]['filters'].pop(str(member.id))
            update_dicts()

    async def on_message(self, message):
        bot_number = args.bot_client_ids.index(self.user.id)
        if isinstance(message.channel, discord.abc.GuildChannel) is True:
            if message.content.lower() == '!status':
                await status(self, bot_number, message)
            elif message.author.id % len(args.tokens) == bot_number:
                if message.content.lower() in ['!commands', '!help']:
                    await commands(bot_number, message)
                elif message.content.lower().startswith('!dex '):
                    await dex(bot_number, message)
                elif message.content.lower() == '!donate':
                    await donate(bot_number, message)
                elif message.channel.id in args.command_channels:
##                    if message.content.lower().startswith('!set '):
##                        await _set(self, message, bot_number)
                    if message.content.lower().startswith(
                            ('!delete ', '!remove ')):
                        await delete(bot_number, message)
                    elif message.content.lower() in ['!pause', '!p']:
                        await pause(bot_number, message)
                    elif message.content.lower() in ['!resume', '!r']:
                        await resume(bot_number, message)
##                    elif message.content.lower().startswith('!pause '):
##                        await pause_area(self, message, bot_number)
##                    elif message.content.lower().startswith('!resume '):
##                        await resume_area(self, message, bot_number)
##                    elif message.content.lower().startswith('!alerts'):
##                        await alerts(self, message, bot_number)
                    elif message.content.lower() == '!areas':
                        await areas(self, message, bot_number)
