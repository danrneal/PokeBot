#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import asyncio
import discord
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .utils import (get_args, Dicts, update_dicts, parse_command, is_number,
                    truncate, get_default_genders)

log = logging.getLogger('commands')

args = get_args()
dicts = Dicts()


async def donate(client, message):
    em = discord.Embed(
        title="DONATION INFORMATION",
        description=(
            "Support this project!\n" +
            "https://www.paypal.me/dneal12\n\n" +
            "Please note: this donation goes directly into the \n" +
            "pocket of the bot dev, not this Discord server."
        ),
        color=int('0x85bb65', 16)
    )
    dicts.q[bot_number].put((1, dicts.count[bot_number], {
        'destination': message.channel,
        'embed': em
    }))
    dicts.count[bot_number] += 1
    await client.delete_message(message)


async def status(client, message, bot_number):
    await asyncio.sleep(bot_number * 0.1)
    delete = await client.send_message(
        message.channel, 'PokeBot {} (of {}) standing by.'.format(
            bot_number + 1, len(args.tokens)))
    if bot_number == 1:
        await asyncio.sleep(0.1 * int(len(args.tokens)))
        delete_vid = await client.send_message(
            message.channel, 'https://youtu.be/kxH6YErAIgA')
        await asyncio.sleep(60 - (0.1 * (int(len(args.tokens)) + 1)))
        await client.delete_message(delete_vid)
        await client.delete_message(delete)
        await client.delete_message(message)
    else:
        await asyncio.sleep(60 - (0.1 * bot_number))
        await client.delete_message(delete)


async def commands(client, message, bot_number):
    dicts.q[bot_number].put((1, dicts.count[bot_number], {
        'destination': message.channel,
        'msg': dicts.info_msg
    }))
    dicts.count[bot_number] += 1
    await client.delete_message(message)


async def dex(client, message, bot_number):
    pokemon = message.content.lower().split()[1]
    if pokemon in dicts.pokemon:
        dex_number = dicts.pokemon.index(pokemon) + 1

        site = "https://pokemongo.gamepress.gg/pokemon/{}".format(dex_number)
        page = requests.get(site)
        soup = BeautifulSoup(page.content, 'html.parser')

        rating = soup.find_all(class_="pokemon-rating")
        max_cp = soup.find_all(class_="max-cp-number")
        stats = soup.find_all(class_="stat-text")
        types = soup.find_all(class_=("field field--name-field-pokemon-type " +
                                      "field--type-entity-reference " +
                                      "field--label-hidden field__items"))
        female = soup.find_all(class_="female-percentage")
        male = soup.find_all(class_="male-percentage")

        quick = []
        legacy_quick = []
        for quick_move in soup.find_all(class_=(
                "views-field views-field-field-quick-move")):
            quick.append(quick_move.find(class_=(
                "field field--name-title " +
                "field--type-string field--label-hidden")))
            legacy_quick.append(quick_move.find(class_=(
                "move-info")))

        charge = []
        legacy_charge = []
        for charge_move in soup.find_all(class_=(
                "views-field views-field-field-charge-move")):
            charge.append(charge_move.find(class_=(
                "field field--name-title " +
                "field--type-string field--label-hidden")))
            legacy_charge.append(charge_move.find(class_=(
                "move-info")))

        legacy_moves = []
        for (legacy_quick, legacy_charge) in zip(legacy_quick, legacy_charge):
            try:
                if legacy_quick.get_text() == '* ':
                    legacy_moves.append(' (Legacy)')
                else:
                    try:
                        if legacy_charge.get_text() == '* ':
                            legacy_moves.append(' (Legacy)')
                        else:
                            legacy_moves.append('')
                    except:
                        legacy_moves.append('')
            except:
                try:
                    if legacy_charge.get_text() == '* ':
                        legacy_moves.append(' (Legacy)')
                    else:
                        legacy_moves.append('')
                except:
                    legacy_moves.append('')

        offensive_grade = soup.find_all(class_=(
            "views-field views-field-field-offensive-moveset-grade"))
        for index, grade in enumerate(offensive_grade):
            offensive_grade[index] = str(grade.get_text().strip())
        defensive_grade = soup.find_all(class_=(
            "views-field views-field-field-defensive-moveset-grade"))
        for index, grade in enumerate(defensive_grade):
            defensive_grade[index] = str(grade.get_text().strip())

        offensive_moves = sorted(zip(offensive_grade[1:], quick[1:],
                                     charge[1:], legacy_moves[1:]),
                                 key=lambda x: x[0])
        defensive_moves = sorted(zip(defensive_grade[1:], quick[1:],
                                     charge[1:], legacy_moves[1:]),
                                 key=lambda x: x[0])

        if len(soup.find_all(class_=("raid-boss-counters"))) > 0:
            raid_counters = soup.find_all(class_=("raid-boss-counters"))[
                0].find_all(class_=("field field--name-title " +
                                    "field--type-string field--label-hidden"))

        title = "%03d" % dex_number + ' | ' + pokemon.upper()
        try:
            descript = "Rating: " + rating[0].get_text().strip() + ' / 10'
        except:
            descript = "Rating: - / 10"
        if len(types[0].get_text().split()) == 1:
            descript += "\nType: " + types[0].get_text().split()[0]
        else:
            descript += ("\nType: " + types[0].get_text().split()[0] + ' | ' +
                         types[0].get_text().split()[1])
        descript += "\nMax CP: " + max_cp[0].get_text()
        descript += ("\n" + stats[0].get_text().split()[0] + ' ' +
                     stats[0].get_text().split()[1] + ' | ' +
                     stats[1].get_text().split()[0] + ' ' +
                     stats[1].get_text().split()[1] + ' | ' +
                     stats[2].get_text().split()[0] +
                     ' ' + stats[2].get_text().split()[1] + '\n')
        try:
            descript += ("Female: " + female[0].get_text().strip() +
                         " | Male: " + male[0].get_text().strip() + '\n')
        except:
            pass

        if len(offensive_moves) > 0:

            descript += "\nAttacking Movesets:\n```"
            for (grade, quick, charge, legacy) in offensive_moves:
                descript += ('\n[' + grade.strip() + '] ' + quick.get_text() +
                             ' / ' + charge.get_text() + legacy)
            descript += " \n```"

            descript += "\nDefensive Movesets:\n```"
            for (grade, quick, charge, legacy) in defensive_moves:
                descript += ('\n[' + grade.strip() + '] ' + quick.get_text() +
                             ' / ' + charge.get_text() + legacy)
            descript += "\n```"

            if len(soup.find_all(class_=("raid-boss-counters"))) > 0:

                descript += "\nRaid Boss Counters:\n```"
                for counter in raid_counters:

                    descript += '\n' + counter.get_text()
                descript += "\n```"

        else:

            quick_moves = soup.find(class_=("primary-move")).find_all(class_=(
                "field field--name-title field--type-string " +
                "field--label-hidden"))
            charge_moves = soup.find(class_=("secondary-move")).find_all(
                class_=("field field--name-title field--type-string " +
                        "field--label-hidden"))
            if soup.find(class_=("pokemon-legacy-quick-moves")) is not None:
                quick_legacy = soup.find(class_=(
                    "pokemon-legacy-quick-moves")).find_all(class_=(
                        "field field--name-title field--type-string " +
                        "field--label-hidden"))
            if soup.find(class_=(
                    "secondary-move-legacy secondary-move")) is not None:
                charge_legacy = soup.find(class_=(
                    "secondary-move-legacy secondary-move")).find_all(class_=(
                        "field field--name-title field--type-string " +
                        "field--label-hidden"))

            descript += "\nQuick Moves:\n```"
            for quick_move in quick_moves:
                descript += '\n' + quick_move.get_text()
            if soup.find(class_=("pokemon-legacy-quick-moves")) is not None:
                for legacy_move in quick_legacy:
                    descript += '\n' + legacy_move.get_text() + ' (Legacy)'
            descript += "\n```"

            descript += "\nCharge Moves:\n```"
            for charge_move in charge_moves:
                descript += '\n' + charge_move.get_text()
            if soup.find(class_=(
                    "secondary-move-legacy secondary-move")) is not None:
                for legacy_move in charge_legacy:
                    descript += '\n' + legacy_move.get_text() + ' (Legacy)'
            descript += "\n```"

            if len(soup.find_all(class_=("raid-boss-counters"))) > 0:

                descript += "\nRaid Boss Counters:\n```"
                for counter in raid_counters:

                    descript += '\n' + counter.get_text()
                descript += "\n```"

        em = discord.Embed(title=title, url=site, description=descript,
                           color=dicts.type_col[
                               types[0].get_text().split()[0].lower()])
        em.set_thumbnail(
            url=('https://raw.githubusercontent.com/kvangent/PokeAlarm/' +
                 'master/icons/{}.png').format(dex_number))

        dicts.q[bot_number].put((1, dicts.count[bot_number], {
            'destination': message.channel,
            'embed': em
        }))
        dicts.count[bot_number] += 1
    else:
        dicts.q[bot_number].put((1, dicts.count[bot_number], {
            'destination': message.channel,
            'msg': ("That's not any pokemon I know of, check your " +
                      "spelling `{}`").format(message.author.display_name)
        }))
        dicts.count[bot_number] += 1


async def _set(client, message, bot_number):
    msg = message.content.lower().replace('!set ', '').replace(
        '!set\n', '').replace('%', '').replace('nidoran♀', 'nidoranf').replace(
        'nidoran♂', 'nidoranm').replace('mr. mime', 'mr.mime').replace(
        ',\n', ',').replace('\n', ',').replace(', ', ',').split(',')
    for command in msg:
        error, chars, pokemon, genders = parse_command(command)
        if error is True:
            dicts.q[bot_number].put((1, dicts.count[bot_number], {
                'destination': message.channel,
                'msg': '`{}`, this pokemon does not have that gender.'.format(
                    message.author.display_name)
            }))
            dicts.count[bot_number] += 1
            continue
        iv = 0
        level = 1
        cp = 10
        for char in chars:
            if is_number(char):
                if int(char) >= 0 and int(char) <= 100:
                    iv = int(char)
                else:
                    error = True
                    dicts.q[bot_number].put((1, dicts.count[bot_number], {
                        'destination': message.channel,
                        'msg': ('`{}`, pokemon IV must be between 0 and ' +
                                '100.').format(message.author.display_name)
                    }))
                    dicts.count[bot_number] += 1
                    break
            elif char.startswith('l') and is_number(char[1:]):
                if int(char[1:]) >= 1:
                    level = int(char[1:])
                else:
                    error = True
                    dicts.q[bot_number].put((1, dicts.count[bot_number], {
                        'destination': message.channel,
                        'msg': ('`{}`, pokemon level must not be less than ' +
                                '1.').format(message.author.display_name)
                    }))
                    dicts.count[bot_number] += 1
                    break
            elif ((char.endswith('cp') or
                   char.startswith('cp')) and
                  is_number(char.replace('cp', ''))):
                if int(char.replace('cp', '')) >= 10:
                    cp = int(char.replace('cp', ''))
                else:
                    error = True
                    dicts.q[bot_number].put((1, dicts.count[bot_number], {
                        'destination': message.channel,
                        'msg': ('`{}`, pokemon CP must not be less than ' +
                                '10.').format(message.author.display_name)
                    }))
                    dicts.count[bot_number] += 1
                    break
            else:
                error = True
                dicts.q[bot_number].put((1, dicts.count[bot_number], {
                    'destination': message.channel,
                    'msg': ('`{}`, your command has an unrecognized ' +
                            'argument.').format(message.author.display_name)
                }))
                dicts.count[bot_number] += 1
                break
        if error is False:
            if message.author.id not in dicts.users[bot_number]:
                dicts.users[bot_number][message.author.id] = {
                    'pokemon': {},
                    'paused': False
                }
                if args.all_areas is True:
                    dicts.users[bot_number][message.author.id][
                        'areas'] = args.areas
                else:
                    dicts.users[bot_number][message.author.id]['areas'] = []
            for poke in pokemon:
                if poke not in dicts.users[bot_number][message.author.id][
                        'pokemon']:
                    dicts.users[bot_number][message.author.id]['pokemon'][
                        poke] = {}
                if len(pokemon) > 1:
                    genders = get_default_genders(poke)
                for gender in genders:
                    dicts.users[bot_number][message.author.id]['pokemon'][
                        poke][gender] = {
                            'iv': iv,
                            'level': level,
                            'cp': cp
                        }
            if len(pokemon) > 1:
                pokemon = 'pokemon'
                gender = ''
            else:
                pokemon = pokemon[0].replace('nidoranf', 'nidoran♀').replace(
                    'nidoranm', 'nidoran♂').replace(
                        'mr.mime', 'mr. mime').title()
                if (len(genders) == 1 and
                    pokemon not in dicts.male_only and
                    pokemon not in dicts.female_only and
                        pokemon not in dicts.genderless):
                    gender = ' `{}`'.format(genders[0].replace(
                        'female', '♀').replace('male', '♂'))
                else:
                    gender = ''
            update_dicts(len(args.tokens))
            dicts.q[bot_number].put((1, dicts.count[bot_number], {
                'destination': message.channel,
                'msg': ('`{}`, I will alert you if a `{}%+`, level `{}+`, ' +
                        'and CP`{}+` `{}`{} spawns.').format(
                            message.author.display_name, str(iv), str(level),
                            str(cp), pokemon, gender)
            }))
            dicts.count[bot_number] += 1


async def delete(client, message, bot_number):
    msg = message.content.lower().replace('!delete ', '').replace(
        '!delete\n', '').replace('!remove ', '').replace(
        '!remove\n', '').replace('%', '').replace(
        'nidoran♀', 'nidoranf').replace('nidoran♂', 'nidoranm').replace(
        'mr. mime', 'mr.mime').replace(',\n', ',').replace('\n', ',').replace(
        ', ', ',').split(',')
    if message.author.id not in dicts.users[bot_number]:
        dicts.q[bot_number].put((1, dicts.count[bot_number], {
            'destination': message.channel,
            'msg': ("There is nothing to delete, `{}`, you don't have any " +
                    "alerts set.").format(message.author.display_name)
        }))
        dicts.count[bot_number] += 1
    else:
        for command in msg:
            error, chars, pokemon, genders = parse_command(command)
            if error is True:
                dicts.q[bot_number].put((1, dicts.count[bot_number], {
                    'destination': message.channel,
                    'msg': ('`{}`, this pokemon does not have that ' +
                            'gender.').format(message.author.display_name)
                }))
                dicts.count[bot_number] += 1
                continue
            if 'all' in chars:
                chars.remove('all')
            if len(chars) > 0:
                dicts.q[bot_number].put((1, dicts.count[bot_number], {
                    'destination': message.channel,
                    'msg': ('`{}`, your command has an unrecognized ' +
                            'argument.').format(message.author.display_name)
                }))
                dicts.count[bot_number] += 1
                continue
            update = False
            for poke in pokemon:
                if poke in dicts.users[bot_number][message.author.id]['pokemon']:
                    if len(pokemon) > 1:
                        genders = get_default_genders(poke)
                    for gender in genders:
                        if gender in dicts.users[bot_number][
                                message.author.id]['pokemon'][poke]:
                            update = True
                            dicts.users[bot_number][message.author.id][
                                'pokemon'][poke].pop(gender)
                    if len(dicts.users[bot_number][message.author.id][
                            'pokemon'][poke]) == 0:
                        dicts.users[bot_number][message.author.id][
                            'pokemon'].pop(poke)
            if (len(dicts.users[bot_number][message.author.id][
                'pokemon']) == 0 and
                ((args.all_areas is False and
                  len(dicts.users[bot_number][message.author.id][
                      'areas']) == 0) or
                 (args.all_areas is True and
                  len(dicts.users[bot_number][message.author.id][
                      'areas']) == len(args.areas)))):
                dicts.users[bot_number].pop(message.author.id)
            if len(pokemon) > 1:
                pokemon = 'pokemon'
                gender = ''
            else:
                pokemon = pokemon[0].replace('nidoranf', 'nidoran♀').replace(
                    'nidoranm', 'nidoran♂').replace(
                        'mr.mime', 'mr. mime').title()
                if (len(genders) == 1 and
                    pokemon not in dicts.male_only and
                    pokemon not in dicts.female_only and
                        pokemon not in dicts.genderless):
                    gender = ' `{}`'.format(genders[0].replace(
                        'female', '♀').replace('male', '♂'))
                else:
                    gender = ''
            if update is True:
                update_dicts(len(args.tokens))
                dicts.q[bot_number].put((1, dicts.count[bot_number], {
                    'destination': message.channel,
                    'msg': ('`{}`, I will no longer alert you if a `{}`{} ' +
                            'spawns.').format(
                                message.author.display_name, pokemon, gender)
                }))
                dicts.count[bot_number] += 1
            else:
                dicts.q[bot_number].put((1, dicts.count[bot_number], {
                    'destination': message.channel,
                    'msg': ('`{}`, I was not previously alerting you if a ' +
                            '`{}`{} spawns.').format(
                                message.author.display_name, pokemon, gender)
                }))
                dicts.count[bot_number] += 1


async def pause(client, message, bot_number):
    if message.author.id not in dicts.users[bot_number]:
        dicts.q[bot_number].put((1, dicts.count[bot_number], {
            'destination': message.channel,
            'msg': ("There is nothing to pause, `{}`, I'm not alerting you " +
                    "to any pokemon.").format(message.author.display_name)
        }))
        dicts.count[bot_number] += 1
    elif dicts.users[bot_number][message.author.id]['paused'] is True:
        dicts.q[bot_number].put((1, dicts.count[bot_number], {
            'destination': message.channel,
            'msg': 'Your alerts are already paused, `{}`.'.format(
                message.author.display_name)
        }))
        dicts.count[bot_number] += 1
    else:
        dicts.users[bot_number][message.author.id]['paused'] = True
        update_dicts(len(args.tokens))
        dicts.q[bot_number].put((1, dicts.count[bot_number], {
            'destination': message.channel,
            'msg': 'Your alerts have been paused, `{}`.'.format(
                message.author.display_name)
        }))
        dicts.count[bot_number] += 1


async def resume(client, message, bot_number):
    if message.author.id not in dicts.users[bot_number]:
        dicts.q[bot_number].put((1, dicts.count[bot_number], {
            'destination': message.channel,
            'msg': ("There is nothing to resume, `{}`, I'm not alerting you " +
                    "to any pokemon.").format(message.author.display_name)
        }))
        dicts.count[bot_number] += 1
    elif dicts.users[bot_number][message.author.id]['paused'] is False:
        dicts.q[bot_number].put((1, dicts.count[bot_number], {
            'destination': message.channel,
            'msg': 'Your alerts were not previously paused, `{}`.'.format(
                message.author.display_name)
        }))
        dicts.count[bot_number] += 1
    else:
        dicts.users[bot_number][message.author.id]['paused'] = False
        update_dicts(len(args.tokens))
        dicts.q[bot_number].put((1, dicts.count[bot_number], {
            'destination': message.channel,
            'msg': 'You alerts have been resumed, `{}`.'.format(
                message.author.display_name)
        }))
        dicts.count[bot_number] += 1


async def pause_area(client, message, bot_number):
    if message.content.lower() == '!pause all':
        msg = args.areas
    else:
        msg = message.content.lower().replace('!pause ', '').replace(
            '!pause\n', '').replace(',\n', ',').replace('\n', ',').replace(
                ', ', ',').split(',')
    paused_count = 0
    for cmd in msg:
        if cmd in args.areas:
            if message.author.id not in dicts.users[bot_number]:
                if args.all_areas is False:
                    dicts.q[bot_number].put((1, dicts.count[bot_number], {
                        'destination': message.channel,
                        'msg': ("All areas are paused by default, " +
                                "`{}`,").format(message.author.display_name)
                    }))
                    dicts.count[bot_number] += 1
                    break
                else:
                    dicts.users[bot_number][message.author.id] = {
                        'pokemon': {},
                        'paused': False,
                        'areas': args.areas
                    }
                    dicts.users[bot_number][message.author.id][
                        'areas'].remove(cmd)
                    update_dicts(len(args.tokens))
                    paused_count += 1
            elif cmd in dicts.users[bot_number][message.author.id][
                    'areas']:
                dicts.users[bot_number][message.author.id]['areas'].remove(cmd)
                update_dicts(len(args.tokens))
                paused_count += 1
        else:
            dicts.q[bot_number].put((1, dicts.count[bot_number], {
                'destination': message.channel,
                'msg': ("The `{}` area is not any area I know of in this " +
                        "region, `{}`").format(
                            cmd, message.author.display_name)
            }))
            dicts.count[bot_number] += 1
    dicts.q[bot_number].put((1, dicts.count[bot_number], {
        'destination': message.channel,
        'msg': 'Your alerts have been paused for `{}` areas, `{}`.'.format(
            paused_count, message.author.display_name)
    }))
    dicts.count[bot_number] += 1


async def resume_area(client, message, bot_number):
    if (message.content.lower() == '!resume all' and
            message.author.id in args.admins):
        msg = args.areas
    else:
        msg = message.content.lower().replace('!resume ', '').replace(
            '!resume\n', '').replace(',\n', ',').replace('\n', ',').replace(
                ', ', ',').split(',')
    resume_count = 0
    for cmd in msg:
        if cmd in args.areas:
            if message.author.id not in dicts.users[bot_number]:
                if args.all_areas is True:
                    dicts.q[bot_number].put((1, dicts.count[bot_number], {
                        'destination': message.channel,
                        'msg': ("No areas are paused by default, " +
                                "`{}`.").format(message.author.display_name)
                    }))
                    dicts.count[bot_number] += 1
                    break
                else:
                    dicts.users[bot_number][message.author.id] = {
                        'pokemon': {},
                        'paused': False,
                        'areas': []
                    }
                    dicts.users[bot_number][message.author.id]['areas'].append(
                        cmd)
                    update_dicts(len(args.tokens))
                    resume_count += 1
            elif (message.author.id not in args.admins and
                  len(dicts.users[bot_number][message.author.id][
                      'areas']) > 25):
                dicts.q[bot_number].put((1, dicts.count[bot_number], {
                    'destination': message.channel,
                    'msg': ('You have reached the maximum number of areas ' +
                            '`{}`, (25) you need to pause some in order to ' +
                            'resume others.').format(
                                message.author.display_name)
                }))
                dicts.count[bot_number] += 1
                break
            elif cmd not in dicts.users[bot_number][message.author.id][
                    'areas']:
                dicts.users[bot_number][message.author.id]['areas'].append(cmd)
                update_dicts(len(args.tokens))
                resume_count += 1
        else:
            dicts.q[bot_number].put((1, dicts.count[bot_number], {
                'destination': message.channel,
                'msg': ("The `{}` area is not any area I know of in this " +
                        "region, `{}`").format(
                            cmd, message.author.display_name)
            }))
            dicts.count[bot_number] += 1
    dicts.q[bot_number].put((1, dicts.count[bot_number], {
        'destination': message.channel,
        'msg': ('Your alerts have been resumed for `{}` areas, `{}`.').format(
                    resume_count, message.author.display_name)
    }))
    dicts.count[bot_number] += 1


async def alerts(client, message, bot_number):
    msg = message.content.lower().replace('!alerts ', '').replace(
        '!alerts\n', '').replace('!alerts', '').replace('%', '').replace(
        'nidoran♀', 'nidoranf').replace('nidoran♂', 'nidoranm').replace(
        'mr. mime', 'mr.mime').replace(',\n', ',').replace('\n', ',').replace(
        ', ', ',').split(',')
    if message.author.id not in dicts.users[bot_number]:
        dicts.q[bot_number].put((1, dicts.count[bot_number], {
            'destination': message.channel,
            'msg': "`{}`, you don't have any alerts set.".format(
                message.author.display_name)
        }))
        dicts.count[bot_number] += 1        
    else:
        alerts = "`{}`'s Alert Settings:\nBOT NUMBER: {}\nPAUSED: ".format(
            message.author.display_name, str(bot_number + 1))
        if dicts.users[bot_number][message.author.id]['paused'] is True:
            alerts += "TRUE\n\n"
        else:
            alerts += "FALSE\n\n"
        if args.all_areas is True:
            alerts += '__PAUSED AREAS__\n\n'
            if len(args.areas) == len(dicts.users[bot_number][
                    message.author.id]['areas']):
                alerts += 'None\n'
            else:
                for area in list(set(args.areas) - set(dicts.users[bot_number][
                        message.author.id]['areas'])):
                    alerts += '{}, '.format(area.title())
        else:
            alerts += '__ALERT AREAS__\n\n'
            areas = False
            for area in dicts.users[bot_number][message.author.id]['areas']:
                areas = True
                alerts += '{}, '.format(area.title())
            if areas is False:
                alerts += 'None \n'
            alerts = alerts[:-2] + '\n\n'
        for command in msg:
            error, chars, pokemon, genders = parse_command(command)
            if error is True:
                dicts.q[bot_number].put((1, dicts.count[bot_number], {
                    'destination': message.channel,
                    'msg': ('`{}`, this pokemon does not have that ' +
                            'gender.').format(message.author.display_name)
                }))
                dicts.count[bot_number] += 1
                continue
            if 'all' in chars:
                chars.remove('all')
            elif 'areas' in chars:
                chars.remove('areas')
                pokemon = []
            if len(chars) > 0:
                error = True
                dicts.q[bot_number].put((1, dicts.count[bot_number], {
                    'destination': message.channel,
                    'msg': ('`{}`, your command has an unrecognized ' +
                            'argument.').format(message.author.display_name)
                }))
                dicts.count[bot_number] += 1
                continue
            if pokemon != []:
                alerts += '__POKEMON__\n\n'
            for poke in pokemon:
                if poke in dicts.users[bot_number][message.author.id][
                        'pokemon']:
                    poke_str = '{}: '.format(poke)
                    if len(pokemon) > 1:
                        genders = get_default_genders(poke)
                    if (len(genders) > 1 and
                        dicts.users[bot_number][message.author.id]['pokemon'][
                            poke].get('female') == dicts.users[bot_number][
                                message.author.id]['pokemon'][poke].get(
                                    'male')):
                        alerts += '{}{}%+, {}CP+, L{}+ (♀, ♂)\n'.format(
                            poke_str.replace('nidoranf', 'nidoran♀').replace(
                                'nidoranm', 'nidoran♂').replace(
                                    'mr.mime', 'mr. mime').title(),
                                dicts.users[bot_number][message.author.id][
                                    'pokemon'][poke]['male']['iv'],
                                dicts.users[bot_number][message.author.id][
                                    'pokemon'][poke]['male']['cp'],
                                dicts.users[bot_number][message.author.id][
                                    'pokemon'][poke]['male']['level'])
                    else:
                        for gender in genders:
                            if gender in dicts.users[bot_number][
                                    message.author.id]['pokemon'][poke]:
                                alerts += ('{}{}%+, {}CP+, L{}+ ({}) ' +
                                '| ').format(
                                    poke_str.replace(
                                        'nidoranf', 'nidoran♀').replace(
                                        'nidoranm', 'nidoran♂').replace(
                                        'mr.mime', 'mr. mime').title(),
                                    dicts.users[bot_number][message.author.id][
                                        'pokemon'][poke][gender]['iv'],
                                    dicts.users[bot_number][message.author.id][
                                        'pokemon'][poke][gender]['cp'],
                                    dicts.users[bot_number][message.author.id][
                                        'pokemon'][poke][gender]['level'],
                                    gender.replace(
                                        'female', '♀').replace(
                                        'male', '♂').replace(
                                        'genderless', u"\u26B2")
                                )
                                poke_str = ''
                        alerts = alerts[:-3] + '\n'
        if error is False:
            alerts = [alerts]
            while len(alerts[-1]) > 2000:
                for alerts_split in truncate(alerts.pop()):
                    alerts.append(alerts_split)
            for dm in alerts:
                dicts.q[bot_number].put((1, dicts.count[bot_number], {
                    'destination': discord.utils.get(
                        client.get_all_members(), id=message.author.id),
                    'msg': dm
                }))
                dicts.count[bot_number] += 1


async def areas(client, message, bot_number):
    areas = '__AVAILABLE AREAS__ (Your active areas are in **bold**.)\n\n'
    for area in args.areas:
        if (message.author.id in dicts.users[bot_number] and
                area in dicts.users[bot_number][message.author.id]['areas']):
            areas += '**{}**, '.format(area.title())
        else:
            areas += '{}, '.format(area.title())
    areas = [areas[:-2]]
    areas[0] += ('\n\nYou can change your settings by using `!pause ' +
                 '[area]` or `!resume [area]` in #custom_filters')
    while len(areas[-1]) > 2000:
        for areas_split in truncate(areas.pop()):
            areas.append(areas_split)
    for dm in areas:
        dicts.q[bot_number].put((1, dicts.count[bot_number], {
            'destination': discord.utils.get(
                client.get_all_members(), id=message.author.id),
            'msg': dm
        }))
        dicts.count[bot_number] += 1
