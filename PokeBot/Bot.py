#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import discord
import asyncio
from datetime import datetime
from .utils import get_args, Dicts, update_dicts
from .notification import msg_q, notification
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
#        if self.user.id != args.bot_client_ids[0]:
        await self.edit_profile(username='AlphaPokes')
        await self.change_presence(status=discord.Status.invisible)
        for server in self.servers:
            for role in server.roles:
                if role.name.lower() in dicts.roles:
                    dicts.roles[role.name.lower()].append(role)
                else:
                    dicts.roles[role.name.lower()] = [role]
            for member in server.members:
                alert_role = False
                for role in dicts.roles[args.alert_role]:
                    try:
                        if member.top_role >= role:
                            alert_role = True
                            break
                    except:
                        pass
                if alert_role is True and member.id not in users:
                    users.append(member.id)
        count = 0
        area_count = 0
        for user_id in dicts.users[bot_number]:
            if (len(dicts.users[bot_number][user_id]['areas']) > len(
                set(args.areas).intersection(set(dicts.users[bot_number][
                    user_id]['areas'])))):
                dicts.users[bot_number][user_id]['areas'] = list(set(
                    args.areas).intersection(set(dicts.users[bot_number][
                        user_id]['areas'])))
                area_count += 1
            if user_id not in users:
                dicts.users[bot_number].pop(user_id)
                count += 1
        await asyncio.sleep(bot_number)
        if area_count > 0:
            update_dicts(len(args.tokens))
            log.info("Bot number {} removed {} user(s) outdated areas".format(
                bot_number + 1, area_count))
        if count > 0:
            update_dicts(len(args.tokens))
            log.info("Bot number {} removed {} user(s) from dicts".format(
                bot_number + 1, count))
        log.info("Bot number {} is ready".format(bot_number + 1))
        await msg_q(self, bot_number)

    async def on_member_update(self, before, after):
        bot_number = args.bot_client_ids.index(self.user.id)
        if (int(after.id) % len(args.tokens) == bot_number and
            after.id in dicts.users[bot_number] and
                before.roles != after.roles):
            for role in dicts.roles[args.alert_role]:
                try:
                    if after.top_role >= role:
                        alert_role = True
                        break
                except:
                    pass
            if alert_role is False:
                dicts.user[bot_number].pop(member.id)
                update_dicts(len(args.tokens))
            elif (args.muted_role is not None and
                  len(set(dicts.roles[args.muted_role]).intersection(set(
                      after.roles))) > 0 and
                  dicts.users[bot_number][after.id]['paused'] is False):
                dicts.users[bot_number][after.id]['paused'] = True
                update_dicts(len(args.tokens))
                dicts.q[bot_number].put((1, dicts.count[bot_number], {
                    'destination':discord.utils.get(
                        client.get_all_members(), id=after.id),
                    'msg': 'Alerts have been paused for `{}`.'.format(
                        after.display_name)
                }))
                dicts.count[bot_number] += 1

    async def on_member_remove(self, member):
        bot_number = args.bot_client_ids.index(self.user.id)
        if (int(member.id) % int(len(args.tokens)) == bot_number and
                member.id in dicts.users[bot_number]):
            dicts.user[bot_number].pop(member.id)
            update_dicts(len(args.tokens))

    async def on_message(self, message):
        bot_number = args.bot_client_ids.index(self.user.id)
        if (message.channel.id in args.feed_channels and
                len(message.embeds) > 0):
            await notification(self, message, bot_number)
        elif message.channel.is_private is False:
            if message.content.lower() == '!status':
                await status(self, message, bot_number)
            elif int(message.author.id) % int(len(args.tokens)) == bot_number:
                if message.content.lower() in ['!commands', '!help']:
                    await commands(self, message, bot_number)
                elif message.content.lower().startswith ('!dex '):
                    await dex(self, message, bot_number)
#                elif message.content.lower() == '!donate':
#                    await donate(self, message)
                elif message.channel.id in args.command_channels:
                    if message.content.lower().startswith('!set '):
                        await _set(self, message, bot_number)
                    elif message.content.lower().startswith(
                            ('!delete ', '!remove ')):
                        await delete(self, message, bot_number)
                    elif message.content.lower() in ['!pause', '!p']:
                        await pause(self, message, bot_number)
                    elif message.content.lower() in ['!resume', '!r']:
                        await resume(self, message, bot_number)
                    elif message.content.lower().startswith('!pause '):
                        await pause_area(self, message, bot_number)
                    elif message.content.lower().startswith('!resume '):
                        await resume_area(self, message, bot_number)
                    elif message.content.lower().startswith('!alerts'):
                        await alerts(self, message, bot_number)
                    elif message.content.lower() == '!areas':
                        await areas(self, message, bot_number)
