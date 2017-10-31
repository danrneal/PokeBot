#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import asyncio
import discord
import requests
import copy
from datetime import datetime
from bs4 import BeautifulSoup
from .Locale import Locale
from .Filter import load_pokemon_section, load_egg_section
from .utils import (get_args, Dicts, update_dicts, is_number, truncate,
                    get_pkmn_id, require_and_remove_key, parse_boolean)

log = logging.getLogger('commands')
args = get_args()


async def status(client, bot_number, message):
    await asyncio.sleep(bot_number * 0.1)
    delete_msg = await message.channel.send((
        'PokeBot {} (of {}) standing by.'
    ).format(bot_number + 1, len(args.tokens)))
    Dicts.bots[bot_number]['timestamps'].append(datetime.utcnow())
    if bot_number == 0:
        await asyncio.sleep(0.1 * int(len(args.tokens)))
        delete_vid = await message.channel.send('https://youtu.be/kxH6YErAIgA')
        Dicts.bots[bot_number]['timestamps'].append(datetime.utcnow())
        await asyncio.sleep(60 - (0.1 * (int(len(args.tokens)) + 1)))
        await delete_vid.delete()
        await delete_msg.delete()
        await message.delete()
    else:
        await asyncio.sleep(60 - (0.1 * bot_number))
        await delete_msg.delete()


async def commands(bot_number, message):
    Dicts.bots[bot_number]['out_queue'].put((
        1, Dicts.bots[bot_number]['count'], {
            'destination': message.channel,
            'msg': Dicts.info_msg,
            'timestamp': datetime.utcnow()
        }
    ))
    Dicts.bots[bot_number]['count'] += 1
    await message.delete()


def dex(bot_number, message):
    pokemon = message.content.lower().split()[1]
    dex_number = get_pkmn_id(pokemon)
    if dex_number is not None:
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
                    except AttributeError:
                        legacy_moves.append('')
            except AttributeError:
                try:
                    if legacy_charge.get_text() == '* ':
                        legacy_moves.append(' (Legacy)')
                    else:
                        legacy_moves.append('')
                except AttributeError:
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
        except IndexError:
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
        except IndexError:
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
                           color=Dicts.type_col[
                               types[0].get_text().split()[0].lower()])
        em.set_thumbnail(
            url=('https://raw.githubusercontent.com/kvangent/PokeAlarm/' +
                 'master/icons/{}.png').format(dex_number))

        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'embed': em,
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1
    else:
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'msg': (
                    "**{}** is not any pokemon I know of, check your " +
                    "spelling **{}**"
                ).format(pokemon.title(), message.author.display_name),
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1


async def donate(bot_number, message):
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
    Dicts.bots[bot_number]['out_queue'].put((
        1, Dicts.bots[bot_number]['count'], {
            'destination': message.channel,
            'embed': em,
            'timestamp': datetime.utcnow()
        }
    ))
    Dicts.bots[bot_number]['count'] += 1
    await message.delete()


def set_(client, message, bot_number):
    msg = message.content.lower().replace('!set ', '').replace(
        '!set\n', '').replace('%', '').replace('nidoranf', 'nidoran♀').replace(
        'nidoranm', 'nidoran♂').replace('mr. mime', 'mr.mime').replace(
        ',\n', ',').replace('\n', ',').replace(', ', ',').split(',')
    set_count = 0
    for command in msg:
        if len(command) == 0:
            continue
        error = False
        if (get_pkmn_id(command.split()[0].replace(
            'mr.mime', 'mr. mime')) is None or
                command.split()[0] == 'default'):
            pokemon = 'default'
            command = command.replace(pokemon.lower(), '').strip()
            input_ = [command.split()]
            filters = [{
                'min_iv': '0',
                'min_cp': '0',
                'min_level': '0',
                'gender': None,
            }]
        else:
            log.info(command)
            pokemon = Dicts.locale.get_pokemon_name(get_pkmn_id(
                command.split()[0].replace('mr.mime', 'mr. mime')))
            command = command.replace(
                pokemon.lower().replace(' ', ''), '').strip().split('|')
            log.info(command)
            if len(command) > 3:
                Dicts.bots[bot_number]['out_queue'].put((
                    1, Dicts.bots[bot_number]['count'], {
                        'destination': message.channel,
                        'msg': (
                            '**{}**, you can set a maximum of 3 filters for ' +
                            'a given pokemon.'
                        ).format(message.author.display_name),
                        'timestamp': datetime.utcnow()
                    }
                ))
                Dicts.bots[bot_number]['count'] += 1
                continue
            input_ = []
            filters = []
            for filter_ in command:
                input_.append(filter_.split())
                filters.append({
                    'min_iv': '0',
                    'min_cp': '0',
                    'min_level': '0',
                    'gender': None
                })
        for inp, filt in zip(input_, filters):
            if pokemon != 'default':
                if (len(set(inp).intersection(set(['female', 'f']))) > 0 and
                    get_pkmn_id(pokemon) not in Dicts.male_only and
                        get_pkmn_id(pokemon) not in Dicts.genderless):
                    filt['gender'] = ['female']
                    filt['ignore_missing'] = True
                    inp.remove(list(set(inp).intersection(set(
                        ['female', 'f'])))[0])
                elif (len(set(inp).intersection(set(['male', 'm']))) > 0 and
                      get_pkmn_id(pokemon) not in Dicts.female_only and
                      get_pkmn_id(pokemon) not in Dicts.genderless):
                    filt['gender'] = ['male']
                    filt['ignore_missing'] = True
                    inp.remove(list(set(inp).intersection(set(
                        ['male', 'm'])))[0])
                elif (len(set(inp).intersection(set(
                      ['female', 'f', 'male', 'm']))) > 0):
                    error = True
                    Dicts.bots[bot_number]['out_queue'].put((
                        1, Dicts.bots[bot_number]['count'], {
                            'destination': message.channel,
                            'msg': (
                                '**{}**, **{}** does not have that gender.'
                            ).format(message.author.display_name, pokemon),
                            'timestamp': datetime.utcnow()
                        }
                    ))
                    Dicts.bots[bot_number]['count'] += 1
                    break
            for char in inp:
                if is_number(char):
                    if int(char) >= 0 and int(char) <= 100:
                        filt['min_iv'] = str(char)
                        filt['ignore_missing'] = True
                    else:
                        error = True
                        Dicts.bots[bot_number]['out_queue'].put((
                            1, Dicts.bots[bot_number]['count'], {
                                'destination': message.channel,
                                'msg': (
                                    '**{}**, pokemon IV must be between 0 ' +
                                    'and 100.'
                                ).format(message.author.display_name),
                                'timestamp': datetime.utcnow()
                            }
                        ))
                        Dicts.bots[bot_number]['count'] += 1
                        break
                elif char.startswith('l') and is_number(char[1:]):
                    if int(char[1:]) >= 1:
                        filt['min_level'] = str(char[1:])
                        filt['ignore_missing'] = True
                    else:
                        error = True
                        Dicts.bots[bot_number]['out_queue'].put((
                            1, Dicts.bots[bot_number]['count'], {
                                'destination': message.channel,
                                'msg': (
                                    '**{}**, pokemon level must not be less ' +
                                    'than 1.'
                                ).format(message.author.display_name),
                                'timestamp': datetime.utcnow()
                            }
                        ))
                        Dicts.bots[bot_number]['count'] += 1
                        break
                elif ((char.startswith('cp') or
                       char.endswith('cp')) and
                      is_number(char.replace('cp', ''))):
                    if int(char.replace('cp', '')) >= 10:
                        filt['min_cp'] = str(char.replace('cp', ''))
                        filt['ignore_missing'] = True
                    else:
                        error = True
                        Dicts.bots[bot_number]['out_queue'].put((
                            1, Dicts.bots[bot_number]['count'], {
                                'destination': message.channel,
                                'msg': (
                                    '**{}**, pokemon CP must not be less ' +
                                    'than 10.'
                                ).format(message.author.display_name),
                                'timestamp': datetime.utcnow()
                            }
                        ))
                        Dicts.bots[bot_number]['count'] += 1
                        break
                else:
                    error = True
                    Dicts.bots[bot_number]['out_queue'].put((
                        1, Dicts.bots[bot_number]['count'], {
                            'destination': message.channel,
                            'msg': (
                                '**{}**, your command has an unrecognized ' +
                                'argumnet (**{}**).'
                            ).format(message.author.display_name, char),
                            'timestamp': datetime.utcnow()
                        }
                    ))
                    Dicts.bots[bot_number]['count'] += 1
                    break
            if error is True:
                break
        if error is True:
            continue
        user_dict = Dicts.bots[bot_number]['filters'].get(
            str(message.author.id))
        if user_dict is None:
            Dicts.bots[bot_number]['filters'][str(message.author.id)] = {
                'pokemon': {'enabled': True},
                'eggs': {'enabled': False},
                'raids': {'enabled': False},
                'paused': False
            }
            user_dict = Dicts.bots[bot_number]['filters'][
                str(message.author.id)]
            if args.all_areas is True:
                user_dict['areas'] = Dicts.geofences
            else:
                user_dict['areas'] = []
        if pokemon == 'default':
            user_dict['pokemon'][pokemon] = filters[0]
            for pkmn_id in range(721):
                user_dict['pokemon'][
                    Dicts.locale.get_pokemon_name(pkmn_id + 1)] = True
        else:
            user_dict['pokemon'][pokemon] = filters
        set_count += 1
    if set_count > 0:
        usr_dict = copy.deepcopy(user_dict)
        Dicts.bots[bot_number]['pokemon_settings'][
            str(message.author.id)] = load_pokemon_section(
                require_and_remove_key('pokemon', usr_dict, 'User command.'))
        Dicts.bots[bot_number]['egg_settings'][
            str(message.author.id)] = load_egg_section(
                require_and_remove_key('eggs', usr_dict, 'User command.'))
        Dicts.bots[bot_number]['raid_settings'][
            str(message.author.id)] = load_pokemon_section(
                require_and_remove_key('raids', usr_dict, 'User command.'))
        update_dicts()
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'msg': (
                    '**{}**, I have set **{}** pokemon spawn filters.'
                ).format(message.author.display_name, str(set_count)),
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1


def delete(bot_number, message):
    msg = message.content.lower().replace('!delete ', '').replace(
        '!delete\n', '').replace('!remove ', '').replace(
        '!remove\n', '').replace('%', '').replace(
        'nidoranf', 'nidoran♀').replace('nidoranm', 'nidoran♂').replace(
        'mr. mime', 'mr.mime').replace(',\n', ',').replace('\n', ',').replace(
        ', ', ',').split(',')
    user_dict = Dicts.bots[bot_number]['filters'].get(str(message.author.id))
    if user_dict is None:
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'msg': (
                    "There is nothing to delete, **{}**, you don't have any " +
                    "alerts set."
                ).format(message.author.display_name),
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1
    else:
        del_count = 0
        for command in msg:
            if len(command) == 0:
                continue
            if command != 'all' and get_pkmn_id(command) is None:
                Dicts.bots[bot_number]['out_queue'].put((
                    1, Dicts.bots[bot_number]['count'], {
                        'destination': message.channel,
                        'msg': (
                            "{} is not any pokemon I know of, check your " +
                            "spelling **{}**"
                        ).format(command.title(), message.author.display_name),
                        'timestamp': datetime.utcnow()
                    }
                ))
                Dicts.bots[bot_number]['count'] += 1
            elif get_pkmn_id(command) is not None:
                if Dicts.locale.get_pokemon_name(get_pkmn_id(command.replace(
                        'mr.mime', 'mr. mime'))) in user_dict['pokemon']:
                    user_dict['pokemon'].pop(Dicts.locale.get_pokemon_name(
                        get_pkmn_id(command.replace('mr.mime', 'mr. mime'))))
                    del_count += 1
                else:
                    Dicts.bots[bot_number]['out_queue'].put((
                        1, Dicts.bots[bot_number]['count'], {
                            'destination': message.channel,
                            'msg': (
                                '**{}**, I was not previously alerting you ' +
                                'if a(n) **{}** spawns.'
                            ).format(
                                message.author.display_name, command.title()
                            ),
                            'timestamp': datetime.utcnow()
                        }
                    ))
                    Dicts.bots[bot_number]['count'] += 1
            else:
                if len(user_dict['pokemon']) > 1:
                    for filter_ in user_dict['pokemon']:
                        bool = parse_boolean(user_dict['pokemon'][filter_])
                        if bool is not True:
                            del_count += 1
                    user_dict['pokemon'] = {'enabled': True}
                else:
                    Dicts.bots[bot_number]['out_queue'].put((
                        1, Dicts.bots[bot_number]['count'], {
                            'destination': message.channel,
                            'msg': (
                                '**{}**, I was not previously alerting you ' +
                                'of any pokemon spawns.'
                            ).format(message.author.display_name),
                            'timestamp': datetime.utcnow()
                        }
                    ))
                    Dicts.bots[bot_number]['count'] += 1
        if (len(user_dict['pokemon']) <= 1 and
            len(user_dict['eggs']) <= 1 and
            len(user_dict['raids']) <= 1 and
            ((len(user_dict['areas']) == 0 and
              args.all_areas is False) or
             (len(user_dict['areas']) == len(Dicts.geofences) and
              args.all_areas is True))):
            Dicts.bots[bot_number]['filters'].pop(str(message.author.id))
            Dicts.bots[bot_number]['pokemon_settings'].pop(
                str(message.author.id))
            Dicts.bots[bot_number]['egg_settings'].pop(str(message.author.id))
            Dicts.bots[bot_number]['raid_settings'].pop(str(message.author.id))
        if del_count > 0:
            if str(message.author.id) in Dicts.bots[bot_number]['filters']:
                usr_dict = copy.deepcopy(user_dict)
                Dicts.bots[bot_number]['pokemon_settings'][
                    str(message.author.id)] = load_pokemon_section(
                        require_and_remove_key(
                            'pokemon', usr_dict, 'User Command.'))
                Dicts.bots[bot_number]['egg_settings'][
                    str(message.author.id)] = load_egg_section(
                        require_and_remove_key(
                            'eggs', usr_dict, 'User Command.'))
                Dicts.bots[bot_number]['raid_settings'][
                    str(message.author.id)] = load_pokemon_section(
                        require_and_remove_key(
                            'raids', usr_dict, 'User Command.'))
            update_dicts()
            Dicts.bots[bot_number]['out_queue'].put((
                1, Dicts.bots[bot_number]['count'], {
                    'destination': message.channel,
                    'msg': (
                        '**{}**, I have removed **{}** pokemon spawn filters.'
                    ).format(message.author.display_name, str(del_count)),
                    'timestamp': datetime.utcnow()
                }
            ))
            Dicts.bots[bot_number]['count'] += 1


def pause(bot_number, message):
    user_dict = Dicts.bots[bot_number]['filters'].get(str(message.author.id))
    if user_dict is None:
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'msg': (
                    "There is nothing to pause, **{}**, I'm not alerting " +
                    "you to any pokemon."
                ).format(message.author.display_name),
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1
    elif user_dict['paused'] is True:
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'msg': 'Your alerts are already paused, **{}**.'.format(
                    message.author.display_name),
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1
    else:
        user_dict['paused'] = True
        update_dicts()
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'msg': 'Your alerts have been paused, **{}**.'.format(
                    message.author.display_name),
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1


def resume(bot_number, message):
    user_dict = Dicts.bots[bot_number]['filters'].get(str(message.author.id))
    if user_dict is None:
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'msg': (
                    "There is nothing to resume, **{}**, I'm not alerting " +
                    "you to any pokemon."
                ).format(message.author.display_name),
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1
    elif user_dict['paused'] is False:
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'msg': (
                    'Your alerts were not previously paused, **{}**.'
                ).format(message.author.display_name),
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1
    else:
        user_dict['paused'] = False
        update_dicts()
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'msg': 'You alerts have been resumed, **{}**.'.format(
                    message.author.display_name),
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1


def activate(bot_number, message):
    if message.content.lower() == '!activate all':
        msg = Dicts.geofences
    else:
        msg = message.content.lower().replace('!activate ', '').replace(
            '!activate\n', '').replace(',\n', ',').replace('\n', ',').replace(
                ', ', ',').split(',')
    activate_count = 0
    user_dict = Dicts.bots[bot_number]['filters'].get(str(message.author.id))
    for cmd in msg:
        if len(cmd) == 0:
            continue
        if cmd in Dicts.geofences:
            if user_dict is None:
                if args.all_areas is True:
                    Dicts.bots[bot_number]['out_queue'].put((
                        1, Dicts.bots[bot_number]['count'], {
                            'destination': message.channel,
                            'msg': (
                                "**{}**, all areas are on by default."
                            ).format(message.author.display_name),
                            'timestamp': datetime.utcnow()
                        }
                    ))
                    Dicts.bots[bot_number]['count'] += 1
                    break
                else:
                    Dicts.bots[bot_number]['filters'][
                            str(message.author.id)] = {
                        'pokemon': {'enabled': True},
                        'eggs': {'enabled': False},
                        'raids': {'enabled': False},
                        'paused': False,
                        'areas': []
                    }
                    user_dict = Dicts.bots[bot_number]['filters'][
                        str(message.author.id)]
                    usr_dict = copy.deepcopy(user_dict)
                    Dicts.bots[bot_number]['pokemon_settings'][
                        str(message.author.id)] = load_pokemon_section(
                            require_and_remove_key(
                                'pokemon', usr_dict, 'User Command.'))
                    Dicts.bots[bot_number]['egg_settings'][
                        str(message.author.id)] = load_egg_section(
                            require_and_remove_key(
                                'eggs', usr_dict, 'User Command.'))
                    Dicts.bots[bot_number]['raid_settings'][
                        str(message.author.id)] = load_pokemon_section(
                            require_and_remove_key(
                                'raids', usr_dict, 'User Command.'))
                    user_dict['areas'].append(cmd)
                    activate_count += 1
            elif cmd not in user_dict['areas']:
                user_dict['areas'].append(cmd)
                activate_count += 1
        else:
            Dicts.bots[bot_number]['out_queue'].put((
                1, Dicts.bots[bot_number]['count'], {
                    'destination': message.channel,
                    'msg': (
                        "The **{}** area is not any area I know of in this " +
                        "region, **{}**"
                    ).format(cmd.title(), message.author.display_name),
                    'timestamp': datetime.utcnow()
                }
            ))
            Dicts.bots[bot_number]['count'] += 1
    if (user_dict is not None and
        len(user_dict['pokemon']) <= 1 and
        len(user_dict['eggs']) <= 1 and
        len(user_dict['raids']) <= 1 and
        (len(user_dict['areas']) == len(Dicts.geofences) and
         args.all_areas is True)):
        Dicts.bots[bot_number]['filters'].pop(str(message.author.id))
        Dicts.bots[bot_number]['pokemon_settings'].pop(str(message.author.id))
        Dicts.bots[bot_number]['egg_settings'].pop(str(message.author.id))
        Dicts.bots[bot_number]['raid_settings'].pop(str(message.author.id))
    if activate_count > 0:
        update_dicts()
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'msg': (
                    'Your alerts have been activated for **{}** areas, **{}**.'
                ).format(activate_count, message.author.display_name),
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1


def deactivate(bot_number, message):
    if message.content.lower() == '!deactivate all':
        msg = Dicts.geofences
    else:
        msg = message.content.lower().replace('!deactivate ', '').replace(
            '!deactivate\n', '').replace(',\n', ',').replace(
                '\n', ',').replace(', ', ',').split(',')
    deactivate_count = 0
    user_dict = Dicts.bots[bot_number]['filters'].get(str(message.author.id))
    for cmd in msg:
        if len(cmd) == 0:
            continue
        if cmd in Dicts.geofences:
            if user_dict is None:
                if args.all_areas is False:
                    Dicts.bots[bot_number]['out_queue'].put((
                        1, Dicts.bots[bot_number]['count'], {
                            'destination': message.channel,
                            'msg': (
                                "**{}**, all areas are off by default."
                            ).format(message.author.display_name),
                            'timestamp': datetime.utcnow()
                        }
                    ))
                    Dicts.bots[bot_number]['count'] += 1
                    break
                else:
                    Dicts.bots[bot_number]['filters'][
                            str(message.author.id)] = {
                        'pokemon': {'enabled': True},
                        'eggs': {'enabled': False},
                        'raids': {'enabled': False},
                        'paused': False,
                        'areas': []
                    }
                    user_dict = Dicts.bots[bot_number]['filters'][
                        str(message.author.id)]
                    usr_dict = copy.deepcopy(user_dict)
                    Dicts.bots[bot_number]['pokemon_settings'][
                        str(message.author.id)] = load_pokemon_section(
                            require_and_remove_key(
                                'pokemon', usr_dict, 'User command.'))
                    Dicts.bots[bot_number]['egg_settings'][
                        str(message.author.id)] = load_egg_section(
                            require_and_remove_key(
                                'eggs', usr_dict, 'User command.'))
                    Dicts.bots[bot_number]['raid_settings'][
                        str(message.author.id)] = load_pokemon_section(
                            require_and_remove_key(
                                'raids', usr_dict, 'User command.'))
                    user_dict['areas'].remove(cmd)
                    deactivate_count += 1
            elif cmd in user_dict['areas']:
                user_dict['areas'].remove(cmd)
                deactivate_count += 1
        else:
            Dicts.bots[bot_number]['out_queue'].put((
                1, Dicts.bots[bot_number]['count'], {
                    'destination': message.channel,
                    'msg': (
                        "The **{}** area is not any area I know of in this " +
                        "region, **{}**"
                    ).format(cmd.title(), message.author.display_name),
                    'timestamp': datetime.utcnow()
                }
            ))
            Dicts.bots[bot_number]['count'] += 1
    if (user_dict is not None and
        len(user_dict['pokemon']) <= 1 and
        len(user_dict['eggs']) <= 1 and
        len(user_dict['raids']) <= 1 and
        (len(user_dict['areas']) == 0 and
         args.all_areas is False)):
        Dicts.bots[bot_number]['filters'].pop(str(message.author.id))
        Dicts.bots[bot_number]['pokemon_settings'].pop(str(message.author.id))
        Dicts.bots[bot_number]['egg_settings'].pop(str(message.author.id))
        Dicts.bots[bot_number]['raid_settings'].pop(str(message.author.id))
    if deactivate_count > 0:
        update_dicts()
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'msg': (
                    'Your alerts have been deactivated for **{}** areas, ' +
                    '**{}**.'
                ).format(deactivate_count, message.author.display_name),
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1


def alerts(bot_number, message):
    user_dict = Dicts.bots[bot_number]['filters'].get(str(message.author.id))
    if user_dict is None:
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.channel,
                'msg': "**{}**, you don't have any alerts set.".format(
                    message.author.display_name),
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1
    else:
        alerts = "**{}**'s Alert Settings:\nBOT NUMBER: {}\nPAUSED: ".format(
            message.author.display_name, str(bot_number + 1))
        if user_dict['paused'] is True:
            alerts += "TRUE\n\n"
        else:
            alerts += "FALSE\n\n"
        if args.all_areas is True:
            alerts += '__PAUSED AREAS__\n\n'
            if len(user_dict['areas']) == len(
                    Dicts.geofences):
                alerts += 'None  \n'
            else:
                for area in list(
                        set(Dicts.geofences) - set(user_dict['areas'])):
                    alerts += '{}, '.format(area.title())
        else:
            alerts += '__ALERT AREAS__\n\n'
            if len(user_dict['areas']) == 0:
                alerts += (
                    "You don't any areas set type `!activate " "[area/all]` " +
                    "in #custom_filters to set one! \n"
                )
            else:
                for area in user_dict['areas']:
                    alerts += '{}, '.format(area.title())
        alerts = alerts[:-2] + '\n\n'
        alerts += '__POKEMON__\n\n'
        if 'default' in user_dict['pokemon']:
            alerts += 'Default (all unlisted): '
            if int(user_dict['pokemon']['default']['min_iv']) > 0:
                alerts += '{}%+, '.format(
                    user_dict['pokemon']['default']['min_iv'])
            if int(user_dict['pokemon']['default']['min_cp']) > 0:
                alerts += '{}CP+, '.format(
                    user_dict['pokemon']['default']['min_cp'])
            if int(user_dict['pokemon']['default']['min_level']) > 0:
                alerts += 'L{}+, '.format(
                    user_dict['pokemon']['default']['min_level'])
            alerts = alerts[:-2] + '\n\n'
        else:
            alerts += 'Default: None\n\n'
        for pkmn_id in range(721):
            pkmn = Dicts.locale.get_pokemon_name(pkmn_id + 1)
            if user_dict['pokemon'].get(pkmn) is True:
                continue
            elif user_dict['pokemon'].get(pkmn) is None:
                if 'default' in user_dict['pokemon']:
                    alerts += '{}: None\n'.format(pkmn.title())
                else:
                    continue
            else:
                alerts += '{}: '.format(pkmn)
                for filter_ in user_dict['pokemon'][pkmn]:
                    if (int(filter_['min_iv']) == 0 and
                        int(filter_['min_cp']) == 0 and
                        int(filter_['min_level']) == 0 and
                            filter_['gender'] is None):
                        alerts += 'All  '
                    else:
                        if int(filter_['min_iv']) > 0:
                            alerts += '{}%+, '.format(filter_['min_iv'])
                        if int(filter_['min_cp']) > 0:
                            alerts += '{}CP+, '.format(filter_['min_cp'])
                        if int(filter_['min_level']) > 0:
                            alerts += 'L{}+, '.format(filter_['min_level'])
                        if filter_['gender'] is not None:
                            if filter_['gender'] == ['female']:
                                alerts += '♀, '
                            else:
                                alerts += '♂, '
                    alerts = alerts[:-2] + ' | '
                alerts = alerts[:-3] + '\n'
        alerts = [alerts[:-1]]
        while len(alerts[-1]) > 2000:
            for alerts_split in truncate(alerts.pop()):
                alerts.append(alerts_split)
        for dm in alerts:
            Dicts.bots[bot_number]['out_queue'].put((
                1, Dicts.bots[bot_number]['count'], {
                    'destination': message.author,
                    'msg': dm,
                    'timestamp': datetime.utcnow()
                }
            ))
            Dicts.bots[bot_number]['count'] += 1


def areas(bot_number, message):
    user_dict = Dicts.bots[bot_number]['filters'].get(str(message.author.id))
    areas = '__AVAILABLE AREAS__ (Your active areas are in **bold**.)\n\n'
    for area in Dicts.geofences:
        if (user_dict is not None and area in user_dict['areas']):
            areas += '**{}**, '.format(area.title())
        else:
            areas += '{}, '.format(area.title())
    areas = [areas[:-2]]
    areas[0] += (
        '\n\nYou can change your settings by using `!activate [area/all]` ' +
        'or `!deactivate [area/all]` in #custom_filters'
    )
    while len(areas[-1]) > 2000:
        for areas_split in truncate(areas.pop()):
            areas.append(areas_split)
    for dm in areas:
        Dicts.bots[bot_number]['out_queue'].put((
            1, Dicts.bots[bot_number]['count'], {
                'destination': message.author,
                'msg': dm,
                'timestamp': datetime.utcnow()
            }
        ))
        Dicts.bots[bot_number]['count'] += 1
