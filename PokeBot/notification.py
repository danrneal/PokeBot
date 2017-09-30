#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import discord
import asyncio
from datetime import datetime
from random import randint
from .utils import (get_args, Dicts, get_default_genders, get_loc,
                    get_static_map_url)

log = logging.getLogger('notification')

args = get_args()
dicts = Dicts()


async def msg_q(client, bot_number):
    while True:
        while dicts.q[bot_number].empty():
            if dicts.count[bot_number] != 0:
                dicts.count[bot_number] = 0
            await asyncio.sleep(0.5)
        while len(dicts.timestamps[bot_number]) >= 120:
            if (datetime.utcnow() - dicts.timestamps[bot_number][
                    0]).total_seconds() > 60:
                dicts.timestamps[bot_number].pop(0)
            else:
                await asyncio.sleep(0.5)
        msg_params = dicts.q[bot_number].get()[2]
        await client.send_message(
            msg_params['destination'],
            msg_params.get('msg'),
            embed=msg_params.get('embed')
        )
        dicts.timestamps[bot_number].append(datetime.utcnow())


async def notification(client, message, bot_number):
    msg = '{}\n{}\n{}'.format(
        message.author.display_name.lower(),
        message.embeds[0]['title'].lower(),
        message.embeds[0]['description'].lower()
    ).replace(':', '').replace('(', '').replace(')', '').replace(
        '-', '').replace('nidoran♀', 'nidoranf').replace(
            'nidoran♂', 'nidoranm').replace('mr. mime', 'mr.mime').replace(
                '\n', ' ').split()
    pokemon = list(set(msg).intersection(set(dicts.pokemon)))[0]
    if len(set(msg).intersection(set(args.areas))) > 0:
        area = list(set(msg).intersection(set(args.areas)))[0]
    else:
        area = None
    for word in reversed(msg):
        if '♀' in word or pokemon in dicts.female_only:
            genders = ['female']
        elif '♂' in word or pokemon in dicts.male_only:
            genders = ['male']
        elif u'\u26b2' in word or pokemon in dicts.genderless:
            genders = ['genderless']
        elif 'cp' in word:
            cp = int(word.replace('cp', '').replace('?', '10'))
        elif 'lvl' in word:
            level = int(word.replace('lvl', '').replace('?', '1'))
        elif '%' in word:
            iv = float(word.replace('%', '').replace('?', '0'))
    try:
        genders
    except NameError:
        genders = get_default_genders(pokemon)
    gmaps = False
    made = False
    for member_id in dicts.users[bot_number]:        
        for gender in genders:
            try:
                if (dicts.users[bot_number][member_id]['paused'] is False and
                    (area in dicts.users[bot_number][member_id]['areas'] or
                     (area == None and
                      len(dicts.users[bot_number][member_id]['areas']) == 0)) and
                    pokemon in dicts.users[bot_number][member_id]['pokemon'] and
                    gender in dicts.users[bot_number][member_id]['pokemon'][
                        pokemon] and
                    dicts.users[bot_number][member_id]['pokemon'][pokemon][gender][
                        'iv'] <= iv and
                    dicts.users[bot_number][member_id]['pokemon'][pokemon][gender][
                        'cp'] <= cp and
                    dicts.users[bot_number][member_id]['pokemon'][pokemon][gender][
                        'level'] <= level):
                    try:
                        col = msg['color']
                    except:
                        col = int('0x4F545C', 16)
                    map_role = False
                    if args.map_role is not None:
                        for role in dicts.roles[args.map_role]:
                            try:
                                if (discord.utils.get(client.get_all_members(),
                                        id=member_id).top_role >= role):
                                    map_role = True
                                    break
                            except:
                                pass
                    if map_role is True:                    
                        if gmaps is False:
                            map_key = args.gmaps_api_key[randint(0, len(
                                args.gmaps_api_key) - 1)]
                            try:
                                descript = '{}\n{}'.format(
                                    get_loc(message.embeds[0]['url'], map_key),
                                    message.embeds[0]['description'])
                            except:
                                descript = message.embeds[0]['description']
                            em_premium = discord.Embed(
                                title=message.embeds[0]['title'],
                                url=message.embeds[0]['url'],
                                description=descript,
                                color=col
                            )
                            em_premium.set_thumbnail(
                                url=message.embeds[0]['thumbnail']['url'])
                            em_premium.set_image(url=get_static_map_url(
                                message.embeds[0]['url'], map_key))
                            em_send = em_premium
                            gmaps = True
                        else:
                            em_send = em_premium
                    else:
                        if made is False:
                            em = discord.Embed(
                                title=message.embeds[0]['title'],
                                url=message.embeds[0]['url'],
                                description=message.embeds[0]['description'],
                                color=col
                            )
                            em.set_thumbnail(
                                url=message.embeds[0]['thumbnail']['url'])
                            try:
                                em.set_image(url=message.embeds[0]['image']['url'])
                            except:
                                pass
                            em_send = em
                            made = True
                        else:
                            em_send = em
                    dicts.q[bot_number].put((2, dicts.count[bot_number], {
                        'destination':discord.utils.get(
                            client.get_all_members(), id=member_id),
                        'embed': em_send
                    }))
                    dicts.count[bot_number] += 1
                    break
            except:
                pass

