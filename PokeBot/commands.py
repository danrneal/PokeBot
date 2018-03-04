import logging
import discord
import asyncio
import requests
import json
from collections import OrderedDict
from bs4 import BeautifulSoup
from .Utilities.MonUtils import get_monster_id
from .Utilities.GenUtils import (
    get_image_url, get_path, msg_split, is_number, update_filters
)

log = logging.getLogger('Commands')

female_only = [
    29, 30, 31, 113, 115, 124, 238, 241, 242, 314, 380, 413, 416, 440, 478,
    488, 548, 549, 629, 630, 669, 670, 671
]
male_only = [
    32, 33, 34, 106, 107, 128, 236, 237, 313, 381, 414, 475, 538, 539, 627,
    628, 641, 642, 645, 658
]
genderless = [
    81, 82, 100, 101, 120, 121, 132, 137, 144, 145, 146, 150, 151, 201, 233,
    243, 244, 245, 249, 250, 251, 292, 337, 338, 343, 344, 374, 375, 376, 377,
    378, 379, 382, 383, 384, 385, 386, 436, 437, 462, 474, 479, 480, 481, 482,
    483, 484, 486, 487, 489, 490, 491, 492, 493, 494, 599, 600, 601, 615, 622,
    623, 638, 639, 640, 643, 644, 646, 647, 648, 649, 703, 716, 717, 718, 719,
    720, 721
]


async def status(client, message, bot_number, number_of_bots):
    await asyncio.sleep(bot_number * 0.1)
    embeds = discord.Embed(
        description='PokeBot **{}** (of **{}**) standing by.'.format(
            bot_number + 1, number_of_bots),
        color=int('0x71cd40', 16)
    )
    await client.get_alarm().update(1, {
        'destination': message.channel,
        'embeds': embeds
    })
    log.info('Sent status message for bot {}'.format(bot_number))


async def commands(client, message):
    embeds = discord.Embed(
        description=(
            "Hello there!\n\n" +
            "`!set [pokemon/default/all] [IV] CP[CP] L[level] [gender]` to " +
            "add an alert for a given pokemon based on it's " +
            "characteristics, any of the characteristics can be left " +
            "blank,\n\n" +
            "`!delete [pokemon/default/all]` to remove an alert for a given " +
            "pokemon\n\n" +
            "`!reset [pokemon/all]` to reset an alert for a given pokemon " +
            "to your default alert characteristics\n\n" +
            "`!set  raids [pokemon/lvl] [ex]` to add an alert for a given " +
            "raid pokemon or a raid level, add 'ex' to the end of your " +
            "command to only get ex eligible gyms for a level,\n\n" +
            "`!delete raids [pokemon/lvl]` to remove an alert for a given " +
            "raid pokemon or a raid level\n\n" +
            "`!set  eggs [lvl] [ex]` to add an alert for a given egg level, " +
            "add 'ex' to the end of your command to only get ex eligible " +
            "gyms for a level,\n\n" +
            "`!delete eggs [lvl]` to remove an alert for a given egg " +
            "level\n\n" +
            "`!pause [pokemon/raids/eggs]` or `!p` to pause alerts,\n\n" +
            "`!resume [pokemon/raids/eggs` or `!r` to resume alerts,\n\n" +
            "`!activate [area/all]` to resume a given area,\n\n" +
            "`!deactivate [area/all]` to pause a given area,\n\n" +
            "`!areas` to see what areas area available to pause or " +
            "resume,\n\n" +
            "`!alerts [pokemon/raids/eggs]` to see your alert settings,\n\n"
            "`!dex [pokemon]` to get pokedex information for a given " +
            "pokemon,\n\n" +
            "`!status` to see which bots are currently online,\n\n" +
            "`!help` or `!commands` to see this message,\n\n" +
            "It is possible to add or delete multiple pokemon or areas by " +
            "putting pokemon on seperate lines or separating them with " +
            "commas.\n" +
            "Commands should be in the #custom_filters channel.\n\n"
        ),
        color=int('0x71cd40', 16)
    )
    await client.get_alarm().update(1, {
        'destination': message.channel,
        'embeds': embeds
    })
    log.info('Sent help message for {}.'.format(message.author.display_name))


async def dex(client, message):
    pokemon = message.content.lower().split()[1]
    try:
        dex_number = get_monster_id(pokemon)
        site = "https://pokemongo.gamepress.gg/pokemon/{}".format(dex_number)
        page = requests.get(site)
        soup = BeautifulSoup(page.content, 'html.parser')
        rating = soup.find_all(class_="pokemon-rating")
        max_cp = soup.find_all(class_="max-cp-number")
        stats = soup.find_all(class_="stat-text")
        types = soup.find_all(class_=(
            "field field--name-field-pokemon-type " +
            "field--type-entity-reference field--label-hidden field__items"
        ))
        female = soup.find_all(class_="female-percentage")
        male = soup.find_all(class_="male-percentage")
        quick = []
        legacy_quick = []
        for quick_move in soup.find_all(class_=(
                "views-field views-field-field-quick-move")):
            quick.append(quick_move.find(class_=(
                "field field--name-title " +
                "field--type-string field--label-hidden"
            )))
            if (quick_move.find(class_=("move-info")) is not None and
                    quick_move.find(class_=("move-info")).get_text() == '*'):
                legacy_quick.append('*')
            else:
                legacy_quick.append('')
        charge = []
        legacy_charge = []
        for charge_move in soup.find_all(class_=(
                "views-field views-field-field-charge-move")):
            charge.append(charge_move.find(class_=(
                "field field--name-title " +
                "field--type-string field--label-hidden"
            )))
            if (charge_move.find(class_=("move-info")) is not None and
                    charge_move.find(class_=("move-info")).get_text() == '*'):
                legacy_charge.append('*')
            else:
                legacy_charge.append('')
        offensive_grade = soup.find_all(class_=(
            "views-field views-field-field-offensive-moveset-grade"))
        for index, grade in enumerate(offensive_grade):
            offensive_grade[index] = str(grade.get_text().strip())
        defensive_grade = soup.find_all(class_=(
            "views-field views-field-field-defensive-moveset-grade"))
        for index, grade in enumerate(defensive_grade):
            defensive_grade[index] = str(grade.get_text().strip())
        offensive_moves = sorted(
            zip(
                offensive_grade[1:], quick[1:], legacy_quick[1:], charge[1:],
                legacy_charge[1:]
            ),
            key=lambda x: x[0]
        )
        defensive_moves = sorted(
            zip(
                defensive_grade[1:], quick[1:], legacy_quick[1:], charge[1:],
                legacy_charge[1:]),
            key=lambda x: x[0]
        )
        title = "%03d" % dex_number + ' | ' + pokemon.upper()
        try:
            descript = "Rating: " + rating[0].get_text().strip() + ' / 5'
        except IndexError:
            descript = "Rating: - / 5"
        if len(types[0].get_text().split()) == 1:
            descript += "\nType: " + types[0].get_text().split()[0]
        else:
            descript += (
                "\nType: " + types[0].get_text().split()[0] + ' | ' +
                types[0].get_text().split()[1]
            )
        descript += "\nMax CP: " + max_cp[0].get_text()
        descript += (
            "\n" + stats[0].get_text().split()[0] + ' ' +
            stats[0].get_text().split()[1] + ' | ' +
            stats[1].get_text().split()[0] + ' ' +
            stats[1].get_text().split()[1] + ' | ' +
            stats[2].get_text().split()[0] +
            ' ' + stats[2].get_text().split()[1] + '\n'
        )
        try:
            descript += (
                "Female: " + female[0].get_text().strip() +
                " | Male: " + male[0].get_text().strip() + '\n'
            )
        except IndexError:
            pass
        if len(offensive_moves) > 0:
            descript += "\nAttacking Movesets:\n```"
            for (grade, quick, q_legacy, charge, c_legacy) in offensive_moves:
                descript += (
                    '\n[' + grade.strip() + '] ' + quick.get_text() +
                    q_legacy + ' / ' + charge.get_text() + c_legacy
                )
            descript += " \n```\nDefensive Movesets:\n```"
            for (grade, quick, q_legacy, charge, c_legacy) in defensive_moves:
                descript += (
                    '\n[' + grade.strip() + '] ' + quick.get_text() +
                    q_legacy + ' / ' + charge.get_text() + c_legacy
                )
            descript += "\n```"
        else:
            quick_moves = soup.find(class_=("primary-move")).find_all(class_=(
                "field field--name-title field--type-string " +
                "field--label-hidden"
            ))
            charge_moves = soup.find(class_=("secondary-move")).find_all(
                class_=(
                    "field field--name-title field--type-string " +
                    "field--label-hidden"
                ))
            if soup.find(class_=("pokemon-legacy-quick-moves")) is not None:
                quick_legacy = soup.find(class_=(
                    "pokemon-legacy-quick-moves")).find_all(class_=(
                        "field field--name-title field--type-string " +
                        "field--label-hidden"
                    ))
            if soup.find(class_=(
                    "secondary-move-legacy secondary-move")) is not None:
                charge_legacy = soup.find(class_=(
                    "secondary-move-legacy secondary-move")).find_all(class_=(
                        "field field--name-title field--type-string " +
                        "field--label-hidden"
                    ))
            descript += "\nQuick Moves:\n```"
            for quick_move in quick_moves:
                descript += '\n' + quick_move.get_text()
            if soup.find(class_=("pokemon-legacy-quick-moves")) is not None:
                for legacy_move in quick_legacy:
                    descript += '\n' + legacy_move.get_text() + ' *'
            descript += "\n```"
            descript += "\nCharge Moves:\n```"
            for charge_move in charge_moves:
                descript += '\n' + charge_move.get_text()
            if soup.find(class_=(
                    "secondary-move-legacy secondary-move")) is not None:
                for legacy_move in charge_legacy:
                    descript += '\n' + legacy_move.get_text() + ' *'
            descript += "\n```"
        if '*' in descript:
            descript += '\n* Legacy Moveset'
        type_ = types[0].get_text().split()[0].lower()
        if type_ == 'bug':
            col = 0xA8B820
        elif type_ == 'dark':
            col = 0x705848
        elif type_ == 'dragon':
            col = 0x7038F8
        elif type_ == 'electric':
            col = 0xF8D030
        elif type_ == 'fairy':
            col = 0xEE99AC
        elif type_ == 'fighting':
            col = 0xC03028
        elif type_ == 'fire':
            col = 0xF08030
        elif type_ == 'flying':
            col = 0xA890F0
        elif type_ == 'ghost':
            col = 0x705898
        elif type_ == 'grass':
            col = 0x78C850
        elif type_ == 'ground':
            col = 0xE0C068
        elif type_ == 'ice':
            col = 0x98D8D8
        elif type_ == 'normal':
            col = 0xA8A878
        elif type_ == 'poison':
            col = 0xA040A0
        elif type_ == 'psychic':
            col = 0xF85888
        elif type_ == 'rock':
            col = 0xB8A038
        elif type_ == 'steel':
            col = 0xB8B8D0
        elif type_ == 'water':
            col = 0x6890F0
        else:
            col = 0x4F545C
        mobile = False
        if descript.count('\n') > 26:
            d_split = descript.split('\nDefensive Movesets:')
            descript = d_split[0]
            if '*' in descript:
                descript += '\n* Legacy Moveset'
            mobile = True
        embeds = discord.Embed(
            title=title,
            url=site,
            description=descript,
            color=col
        )
        embeds.set_thumbnail(
            url=(get_image_url("regular/monsters/{:03}_000.png")).format(
                dex_number))
        await client.get_alarm().update(1, {
            'destination': message.channel,
            'embeds': embeds
        })
        if mobile:
            embeds = discord.Embed(
                description='Defensive Movesets:' + d_split[1],
                color=col
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
        log.info('Sent dex info for {}'.format(message.author.display_name))
    except ValueError:
        embeds = discord.Embed(
            description=((
                "{} **{}** is not a recognized pokemon, check your spelling."
            ).format(message.author.mention, pokemon.title())),
            color=int('0xee281f', 16)
        )
        await client.get_alarm().update(1, {
            'destination': message.channel,
            'embeds': embeds
        })
        log.info('Unrecognized pokemon for dex info from {}.'.format(
            message.author.display_name))


async def set_raids(client, message, geofences, all_areas, ex_parks,
                    filter_file):
    msg = message.content.lower().replace('!set raid ', '').replace(
        '!set raids ', '').replace('!set raid\n', '').replace(
        '!set raids\n', '').replace('%', '').replace(
        'nidoranf', 'nidoran♀').replace('nidoranm', 'nidoran♂').replace(
        'mr. mime', 'mr.mime').replace('mime jr.', 'mimejr.').replace(
        'farfetchd', "farfetch'd").replace(
        'flabebe', 'flab\u00E9b\u00E9').replace(',\n', ',').replace(
        '\n', ',').replace(', ', ',').split(',')
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters.get(str(message.author.id))
        set_count = 0
        for command in msg:
            if len(command) == 0:
                continue
            else:
                command = command.strip()
            new_user = False
            if user_dict is None:
                if all_areas is True:
                    gfs = ['all']
                else:
                    gfs = []
                user_filters[str(message.author.id)] = {
                    "monsters": {
                        "enabled": True,
                        "defaults": {
                            "geofences": gfs
                        },
                        "filters": {}
                    },
                    "eggs": {
                        "enabled": True,
                        "defaults": {
                            "geofences": gfs
                        },
                        "filters": {}
                    },
                    "raids": {
                        "enabled": True,
                        "defaults": {
                            "geofences": gfs
                        },
                        "filters": {}
                    }
                }
                new_user = True
                user_dict = user_filters[str(message.author.id)]
            try:
                if is_number(command.split()[0]):
                    raise ValueError
                pokemon = get_monster_id(command.split()[0].replace(
                    'mr.mime', 'mr. mime').replace('mimejr.', 'mime jr.'))
                if '0' in user_dict['raids']['filters']:
                    if pokemon not in user_dict['raids']['filters']['0'][
                            'monsters']:
                        user_dict['raids']['filters']['0']['monsters'].append(
                            pokemon)
                        user_dict['raids']['filters']['0'][
                            'monsters'] = sorted(user_dict['raids']['filters'][
                                '0']['monsters'])
                else:
                    user_dict['raids']['filters']['0'] = {
                        'monsters': [pokemon]
                    }
                set_count += 1
            except ValueError:
                if 'ex' == command:
                    for lvl in range(1, 6):
                        user_dict['raids']['filters'].update({
                            str(lvl): {
                                "sponsored": True,
                                "min_egg_lvl": lvl,
                                "max_egg_lvl": lvl,
                                "is_missing_info": False
                            },
                            str(lvl) + 'a': {
                                "park_contains": ex_parks,
                                "min_egg_lvl": lvl,
                                "max_egg_lvl": lvl,
                                "is_missing_info": False
                            }
                        })
                        set_count += 1
                elif is_number(command) and 0 < int(command) < 6:
                    user_dict['raids']['filters'][command] = {
                        'min_raid_lvl': int(command),
                        'max_raid_lvl': int(command)
                    }
                    if command + 'a' in user_dict['raids']['filters']:
                        user_dict['raids']['filters'].pop(command + 'a')
                    set_count += 1
                elif ('ex' in command and
                      is_number(command.replace('ex', '').strip()) and
                      0 < int(command.replace('ex', '').strip()) < 6):
                    lvl = command.replace('ex', '').strip()
                    user_dict['raids']['filters'][lvl] = {
                        "sponsored": True,
                        'min_raid_lvl': int(lvl),
                        'max_raid_lvl': int(lvl),
                        'is_missing_info': False
                    }
                    user_dict['raids']['filters'][lvl + 'a'] = {
                        "park_contains": ex_parks,
                        'min_raid_lvl': int(lvl),
                        'max_raid_lvl': int(lvl),
                        'is_missing_info': False
                    }
                    set_count += 1
                else:
                    if new_user:
                        user_filters.pop(str(message.author.id))
                    embeds = discord.Embed(
                        description=((
                            '{} Your command has an unrecognized ' +
                            'argumnet (**{}**).'
                        ).format(message.author.mention, command)),
                        color=int('0xee281f', 16)
                    )
                    await client.get_alarm().update(1, {
                        'destination': message.channel,
                        'embeds': embeds
                    })
                    log.info((
                        'Unrecognized arg passed from {}.'
                    ).format(message.author.display_name))
        if set_count > 0:
            update_filters(user_filters, filter_file, f)
            embeds = discord.Embed(
                description=(
                    '{} You have set **{}** raid filters.'
                ).format(message.author.mention, str(set_count)),
                color=int('0x71cd40', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info('Activated {} raid filters for {}.'.format(
                str(set_count), message.author.display_name))
    if set_count > 0:
        client.load_filter_file(get_path(filter_file))


async def set_eggs(client, message, geofences, all_areas, ex_parks,
                   filter_file):
    msg = message.content.lower().replace('!set egg ', '').replace(
        '!set eggs ', '').replace('!set egg\n', '').replace(
        '!set eggs\n', '').replace('%', '').replace(
        'nidoranf', 'nidoran♀').replace('nidoranm', 'nidoran♂').replace(
        'mr. mime', 'mr.mime').replace('mime jr.', 'mimejr.').replace(
        'farfetchd', "farfetch'd").replace(
        'flabebe', 'flab\u00E9b\u00E9').replace(',\n', ',').replace(
        '\n', ',').replace(', ', ',').split(',')
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters.get(str(message.author.id))
        set_count = 0
        for command in msg:
            if len(command) == 0:
                continue
            else:
                command = command.strip()
            new_user = False
            if user_dict is None:
                if all_areas is True:
                    gfs = ['all']
                else:
                    gfs = []
                user_filters[str(message.author.id)] = {
                    "monsters": {
                        "enabled": True,
                        "defaults": {
                            "geofences": gfs
                        },
                        "filters": {}
                    },
                    "eggs": {
                        "enabled": True,
                        "defaults": {
                            "geofences": gfs
                        },
                        "filters": {}
                    },
                    "raids": {
                        "enabled": True,
                        "defaults": {
                            "geofences": gfs
                        },
                        "filters": {}
                    }
                }
                new_user = True
                user_dict = user_filters[str(message.author.id)]
            if 'ex' == command:
                for lvl in range(1, 6):
                    user_dict['eggs']['filters'].update({
                        str(lvl): {
                            "sponsored": True,
                            "min_egg_lvl": lvl,
                            "max_egg_lvl": lvl,
                            "is_missing_info": False
                        },
                        str(lvl) + 'a': {
                            "park_contains": ex_parks,
                            "min_egg_lvl": lvl,
                            "max_egg_lvl": lvl,
                            "is_missing_info": False
                        }
                    })
                    set_count += 1
            elif is_number(command) and 0 < int(command) < 6:
                user_dict['eggs']['filters'][command] = {
                    'min_egg_lvl': int(command),
                    'max_egg_lvl': int(command)
                }
                if command + 'a' in user_dict['eggs']['filters']:
                    user_dict['eggs']['filters'].pop(command + 'a')
                set_count += 1
            elif ('ex' in command and
                  is_number(command.replace('ex', '').strip()) and
                  0 < int(command.replace('ex', '').strip()) < 6):
                lvl = command.replace('ex', '').strip()
                user_dict['eggs']['filters'][lvl] = {
                    "sponsored": True,
                    'min_egg_lvl': int(lvl),
                    'max_egg_lvl': int(lvl),
                    'is_missing_info': False
                }
                user_dict['eggs']['filters'][lvl + 'a'] = {
                    "park_contains": ex_parks,
                    'min_egg_lvl': int(lvl),
                    'max_egg_lvl': int(lvl),
                    'is_missing_info': False
                }
                set_count += 1
            else:
                if new_user:
                    user_filters.pop(str(message.author.id))
                embeds = discord.Embed(
                    description=((
                        '{} Your command has an unrecognized ' +
                        'argumnet (**{}**).'
                    ).format(message.author.mention, command)),
                    color=int('0xee281f', 16)
                )
                await client.get_alarm().update(1, {
                    'destination': message.channel,
                    'embeds': embeds
                })
                log.info((
                    'Unrecognized arg passed from {}.'
                ).format(message.author.display_name))
        if set_count > 0:
            update_filters(user_filters, filter_file, f)
            embeds = discord.Embed(
                description=(
                    '{} You have set **{}** egg filters.'
                ).format(message.author.mention, str(set_count)),
                color=int('0x71cd40', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info('Activated {} egg filters for {}.'.format(
                str(set_count), message.author.display_name))
    if set_count > 0:
        client.load_filter_file(get_path(filter_file))


async def delete_raids(client, message, geofences, all_areas, filter_file,
                       locale):
    msg = message.content.lower().replace('!delete raid ', '').replace(
        '!delete raids ', '').replace('!delete raid\n', '').replace(
        '!delete raids\n', '').replace('!remove raid ', '').replace(
        '!remove raids ', '').replace('!remove raid\n', '').replace(
        '!remove raids\n', '').replace('%', '').replace(
        'nidoranf', 'nidoran♀').replace('nidoranm', 'nidoran♂').replace(
        'mr. mime', 'mr.mime').replace('mime jr.', 'mimejr.').replace(
        'farfetchd', "farfetch'd").replace(
        'flabebe', 'flab\u00E9b\u00E9').replace(',\n', ',').replace(
        '\n', ',').replace(', ', ',').split(',')
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters.get(str(message.author.id))
        del_count = 0
        if user_dict is None:
            embeds = discord.Embed(
                description=(
                    "{} There is nothing to delete, you don't have any " +
                    "alerts set."
                ).format(message.author.mention),
                color=int('0xee281f', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info((
                'Nothing to delete for {}.'
            ).format(message.author.display_name))
        else:
            for command in msg:
                if len(command) == 0:
                    continue
                else:
                    command = command.strip()
                try:
                    if is_number(command):
                        raise ValueError
                    pokemon = get_monster_id(command.replace(
                        'mr.mime', 'mr. mime').replace(
                            'mimejr.', 'mime jr.'))
                    if ('0' in user_dict['raids']['filters'] and
                        pokemon in user_dict['raids']['filters']['0'][
                            'monsters']):
                        user_dict['raids']['filters']['0'][
                            'monsters'].remove(pokemon)
                        if user_dict['raids']['filters']['0'][
                                'monsters'] == []:
                            user_dict['raids']['filters'].pop('0')
                        del_count += 1
                    else:
                        embeds = discord.Embed(
                            description=(
                                "{} You did not previously have any alerts " +
                                "set for **{}**."
                            ).format(
                                message.author.mention,
                                locale.get_pokemon_name(pokemon)
                            ),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            '{} not previously set for {}.'
                        ).format(
                            locale.get_pokemon_name(pokemon),
                            message.author.display_name
                        ))
                except ValueError:
                    if 'all' == command:
                        if len(user_dict['raids']['filters']) > 0:
                            if '0' in user_dict['raids']['filters']:
                                del_count += len(user_dict['raids'][
                                    'filters']['0']['monsters'])
                            for lvl in range(1, 6):
                                if str(lvl) in user_dict['raids']['filters']:
                                    del_count += 1
                            user_dict['raids']['filters'] = {}
                        else:
                            embeds = discord.Embed(
                                description=(
                                    "{} There is nothing to delete, you " +
                                    "don't have any raid alerts set."
                                ).format(message.author.mention),
                                color=int('0xee281f', 16)
                            )
                            await client.get_alarm().update(1, {
                                'destination': message.channel,
                                'embeds': embeds
                            })
                            log.info((
                                'No raids to delete for {}.'
                            ).format(message.author.display_name))
                    elif is_number(command) and 0 < int(command) < 6:
                        if command in user_dict['raids']['filters']:
                            user_dict['raids']['filters'].pop(command)
                            if command + 'a' in user_dict['eggs']['filters']:
                                user_dict['eggs']['filters'].pop(command + 'a')
                            del_count += 1
                        else:
                            embeds = discord.Embed(
                                description=(
                                    "{} You did not previously have any " +
                                    "alerts set for **Level {}** raids."
                                ).format(message.author.mention, command),
                                color=int('0xee281f', 16)
                            )
                            await client.get_alarm().update(1, {
                                'destination': message.channel,
                                'embeds': embeds
                            })
                            log.info((
                                'Level {} raids not previously set for {}.'
                            ).format(command, message.author.display_name))
                    else:
                        embeds = discord.Embed(
                            description=((
                                '{} Your command has an unrecognized ' +
                                'argumnet (**{}**).'
                            ).format(message.author.mention, command)),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            'Unrecognized arg passed from {}.'
                        ).format(message.author.display_name))
        if del_count > 0:
            if all_areas is True:
                gfs = ['all']
            else:
                gfs = []
            if user_filters[str(message.author.id)] == {
                "monsters": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                },
                "eggs": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                },
                "raids": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                }
            }:
                user_filters.pop(str(message.author.id))
            update_filters(user_filters, filter_file, f)
            embeds = discord.Embed(
                description=(
                    "{} You have removed **{}** raid filters."
                ).format(message.author.mention, str(del_count)),
                color=int('0x71cd40', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info('Removed {} raid filters for {}.'.format(
                str(del_count), message.author.display_name))
    if del_count > 0:
        client.load_filter_file(get_path(filter_file))


async def delete_eggs(client, message, geofences, all_areas, filter_file,
                      locale):
    msg = message.content.lower().replace('!delete egg ', '').replace(
        '!delete eggs ', '').replace('!delete egg\n', '').replace(
        '!delete eggs\n', '').replace('!remove egg ', '').replace(
        '!remove eggs ', '').replace('!remove egg\n', '').replace(
        '!remove eggs\n', '').replace('%', '').replace(
        'nidoranf', 'nidoran♀').replace('nidoranm', 'nidoran♂').replace(
        'mr. mime', 'mr.mime').replace('mime jr.', 'mimejr.').replace(
        'farfetchd', "farfetch'd").replace(
        'flabebe', 'flab\u00E9b\u00E9').replace(',\n', ',').replace(
        '\n', ',').replace(', ', ',').split(',')
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters.get(str(message.author.id))
        del_count = 0
        if user_dict is None:
            embeds = discord.Embed(
                description=(
                    "{} There is nothing to delete, you don't have any " +
                    "alerts set."
                ).format(message.author.mention),
                color=int('0xee281f', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info((
                'Nothing to delete for {}.'
            ).format(message.author.display_name))
        else:
            for command in msg:
                if len(command) == 0:
                    continue
                else:
                    command = command.strip()
                if 'all' == command:
                    if len(user_dict['eggs']['filters']) > 0:
                        for lvl in range(1, 6):
                            if str(lvl) in user_dict['eggs']['filters']:
                                del_count += 1
                        user_dict['eggs']['filters'] = {}
                    else:
                        embeds = discord.Embed(
                            description=(
                                "{} There is nothing to delete, you " +
                                "don't have any egg alerts set."
                            ).format(message.author.mention),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            'No eggs to delete for {}.'
                        ).format(message.author.display_name))
                elif is_number(command) and 0 < int(command) < 6:
                    if command in user_dict['eggs']['filters']:
                        user_dict['eggs']['filters'].pop(command)
                        if command + 'a' in user_dict['eggs']['filters']:
                            user_dict['eggs']['filters'].pop(command + 'a')
                        del_count += 1
                    else:
                        embeds = discord.Embed(
                            description=(
                                "{} You did not previously have any " +
                                "alerts set for **Level {}** eggs."
                            ).format(message.author.mention, command),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            'Level {} eggs not previously set for {}.'
                        ).format(command, message.author.display_name))
                else:
                    embeds = discord.Embed(
                        description=((
                            '{} Your command has an unrecognized ' +
                            'argumnet (**{}**).'
                        ).format(message.author.mention, command)),
                        color=int('0xee281f', 16)
                    )
                    await client.get_alarm().update(1, {
                        'destination': message.channel,
                        'embeds': embeds
                    })
                    log.info((
                        'Unrecognized arg passed from {}.'
                    ).format(message.author.display_name))
        if del_count > 0:
            if all_areas is True:
                gfs = ['all']
            else:
                gfs = []
            if user_filters[str(message.author.id)] == {
                "monsters": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                },
                "eggs": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                },
                "raids": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                }
            }:
                user_filters.pop(str(message.author.id))
            update_filters(user_filters, filter_file, f)
            embeds = discord.Embed(
                description=(
                    "{} You have removed **{}** egg filters."
                ).format(message.author.mention, str(del_count)),
                color=int('0x71cd40', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info('Removed {} egg filters for {}.'.format(
                str(del_count), message.author.display_name))
    if del_count > 0:
        client.load_filter_file(get_path(filter_file))


async def set_(client, message, geofences, all_areas, filter_file, locale):
    msg = message.content.lower().replace('!set ', '').replace(
        '!set\n', '').replace('%', '').replace('nidoranf', 'nidoran♀').replace(
        'nidoranm', 'nidoran♂').replace('mr. mime', 'mr.mime').replace(
        'mime jr.', 'mimejr.').replace('farfetchd', "farfetch'd").replace(
        'flabebe', 'flab\u00E9b\u00E9').replace(',\n', ',').replace(
        '\n', ',').replace(', ', ',').split(',')
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters.get(str(message.author.id))
        set_count = 0
        for command in msg:
            if len(command) == 0:
                continue
            else:
                command = command.strip()
            error = False
            try:
                if is_number(command.split()[0]):
                    raise ValueError
                pokemon = get_monster_id(command.split()[0].replace(
                    'mr.mime', 'mr. mime').replace('mimejr.', 'mime jr.'))
                command = command.replace(locale.get_pokemon_name(
                    pokemon).lower().replace(' ', ''), '').strip().split('|')
                if len(command) > 3:
                    embeds = discord.Embed(
                        description=((
                            '{} You can only set a maximum of 3 filters for ' +
                            'a given pokemon.'
                        ).format(message.author.mention)),
                        color=int('0xee281f', 16)
                    )
                    await client.get_alarm().update(1, {
                        'destination': message.channel,
                        'embeds': embeds
                    })
                    log.info((
                        'Too many filters for a single pokemon from {}.'
                    ).format(message.author.display_name))
                    continue
                input_ = []
                filters = []
                for filter_ in command:
                    input_.append(filter_.split())
                    filters.append({
                        'monsters': [pokemon],
                        'min_iv': '0',
                        'min_cp': '0',
                        'min_lvl': '0',
                        'genders': None
                    })
            except ValueError:
                pokemon = 0
                if (user_dict is not None and
                        '000' in user_dict['monsters']['filters']):
                    im = user_dict['monsters']['filters']['000'][
                        'monsters_exclude']
                else:
                    im = []
                command = command.replace('default', '').replace(
                    'all', '').strip()
                input_ = [command.split()]
                filters = [{
                    'monsters_exclude': im,
                    'min_iv': '0',
                    'min_cp': '0',
                    'min_lvl': '0',
                    'genders': None
                }]
            for inp, filt in zip(input_, filters):
                if pokemon > 0:
                    if (len(set(inp).intersection(
                            set(['female', 'f']))) > 0 and
                        get_monster_id(pokemon) not in male_only and
                            get_monster_id(pokemon) not in genderless):
                        filt['genders'] = ['female']
                        filt['is_missing_info'] = False
                        inp.remove(list(set(inp).intersection(set(
                            ['female', 'f'])))[0])
                    elif (len(set(inp).intersection(
                            set(['male', 'm']))) > 0 and
                          get_monster_id(pokemon) not in female_only and
                          get_monster_id(pokemon) not in genderless):
                        filt['genders'] = ['male']
                        filt['is_missing_info'] = False
                        inp.remove(list(set(inp).intersection(set(
                            ['male', 'm'])))[0])
                    elif (len(set(inp).intersection(set(
                          ['female', 'f', 'male', 'm']))) > 0):
                        error = True
                        embeds = discord.Embed(
                            description=((
                                '{} **{}** does not have that gender.'
                            ).format(
                                message.author.mention,
                                locale.get_pokemon_name(pokemon)
                            )),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            'Improper gender passed from {}.'
                        ).format(message.author.display_name))
                        break
                for char in inp:
                    if is_number(char):
                        if int(char) > 5 and int(char) <= 100:
                            filt['min_iv'] = str(char)
                            if int(char) > 5:
                                filt['is_missing_info'] = False
                        else:
                            error = True
                            embeds = discord.Embed(
                                description=((
                                    '{} Pokemon IV must be between 5 and 100.'
                                ).format(message.author.mention)),
                                color=int('0xee281f', 16)
                            )
                            await client.get_alarm().update(1, {
                                'destination': message.channel,
                                'embeds': embeds
                            })
                            log.info((
                                'Improper iv passed from {}.'
                            ).format(message.author.display_name))
                            break
                    elif char.startswith('l') and is_number(char[1:]):
                        if int(char[1:]) >= 1:
                            filt['min_lvl'] = str(char[1:])
                            if int(char[1:]) > 1:
                                filt['is_missing_info'] = False
                        else:
                            error = True
                            embeds = discord.Embed(
                                description=((
                                    '{} Pokemon level must not be less than 1.'
                                ).format(message.author.mention)),
                                color=int('0xee281f', 16)
                            )
                            await client.get_alarm().update(1, {
                                'destination': message.channel,
                                'embeds': embeds
                            })
                            log.info((
                                'Improper lvl passed from {}.'
                            ).format(message.author.display_name))
                            break
                    elif ((char.startswith('cp') or
                           char.endswith('cp')) and
                          is_number(char.replace('cp', ''))):
                        if int(char.replace('cp', '')) >= 10:
                            filt['min_cp'] = str(char.replace('cp', ''))
                            if int(char.replace('cp', '')) > 10:
                                filt['is_missing_info'] = False
                        else:
                            error = True
                            embeds = discord.Embed(
                                description=((
                                    '{} Pokemon CP must not be less than 10.'
                                ).format(message.author.mention)),
                                color=int('0xee281f', 16)
                            )
                            await client.get_alarm().update(1, {
                                'destination': message.channel,
                                'embeds': embeds
                            })
                            log.info((
                                'Improper cp passed from {}.'
                            ).format(message.author.display_name))
                            break
                    else:
                        error = True
                        embeds = discord.Embed(
                            description=((
                                '{} Your command has an unrecognized ' +
                                'argumnet (**{}**).'
                            ).format(message.author.mention, char)),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            'Unrecognized arg passed from {}.'
                        ).format(message.author.display_name))
                        break
                if error is True:
                    break
            if error is True:
                continue
            suffix = ''
            filter_dict = {}
            for filt in filters:
                filter_dict["{:03}{}".format(pokemon, suffix)] = filt
                if suffix == '':
                    suffix = 'a'
                elif suffix == 'a':
                    suffix = 'b'
            if user_dict is None:
                if all_areas is True:
                    gfs = ['all']
                else:
                    gfs = []
                user_filters[str(message.author.id)] = {
                    "monsters": {
                        "enabled": True,
                        "defaults": {
                            "geofences": gfs
                        },
                        "filters": filter_dict
                    },
                    "eggs": {
                        "enabled": True,
                        "defaults": {
                            "geofences": gfs
                        },
                        "filters": {}
                    },
                    "raids": {
                        "enabled": True,
                        "defaults": {
                            "geofences": gfs
                        },
                        "filters": {}
                    }
                }
                set_count += 1
                user_dict = user_filters[str(message.author.id)]
            else:
                for filt_name in user_dict['monsters']['filters'].copy():
                    if int(filt_name[:3]) == pokemon:
                        user_dict['monsters']['filters'].pop(filt_name)
                user_dict['monsters']['filters'].update(filter_dict)
                set_count += 1
            if '000' in user_dict['monsters']['filters']:
                for filt_name in user_dict['monsters']['filters']:
                    if (int(filt_name[:3]) not in user_dict['monsters'][
                        'filters']['000']['monsters_exclude'] and
                            int(filt_name[:3]) > 0):
                        user_dict['monsters']['filters']['000'][
                            'monsters_exclude'].append(int(filt_name[:3]))
                        user_dict['monsters']['filters']['000'][
                            'monsters_exclude'] = sorted(user_dict['monsters'][
                                'filters']['000']['monsters_exclude'])
        if set_count > 0:
            update_filters(user_filters, filter_file, f)
            embeds = discord.Embed(
                description=(
                    '{} You have set **{}** pokemon spawn filters.'
                ).format(message.author.mention, str(set_count)),
                color=int('0x71cd40', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info('Activated {} pokemon filters for {}.'.format(
                str(set_count), message.author.display_name))
    if set_count > 0:
        client.load_filter_file(get_path(filter_file))


async def delete(client, message, geofences, all_areas, filter_file, locale):
    msg = message.content.lower().replace('!delete ', '').replace(
        '!delete\n', '').replace('!remove ', '').replace(
        '!remove\n', '').replace('%', '').replace(
        'nidoranf', 'nidoran♀').replace('nidoranm', 'nidoran♂').replace(
        'mr. mime', 'mr.mime').replace('mime jr.', 'mimejr.').replace(
        'farfetchd', "farfetch'd").replace(
        'flabebe', 'flab\u00E9b\u00E9').replace(',\n', ',').replace(
        '\n', ',').replace(', ', ',').split(',')
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters.get(str(message.author.id))
        del_count = 0
        if user_dict is None:
            embeds = discord.Embed(
                description=(
                    "{} There is nothing to delete, you don't have any " +
                    "alerts set."
                ).format(message.author.mention),
                color=int('0xee281f', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info((
                'Nothing to delete for {}.'
            ).format(message.author.display_name))
        else:
            for command in msg:
                if len(command) == 0:
                    continue
                else:
                    command = command.strip()
                try:
                    if is_number(command):
                        raise ValueError
                    if command == 'default':
                        pokemon = 0
                    else:
                        pokemon = get_monster_id(command.replace(
                            'mr.mime', 'mr. mime').replace(
                                'mimejr.', 'mime jr.'))
                    deleted = False
                    for filt_name in user_dict['monsters']['filters'].copy():
                        if int(filt_name[:3]) == pokemon:
                            user_dict['monsters']['filters'].pop(filt_name)
                            if deleted is False:
                                del_count += 1
                                deleted = True
                    if ('000' in user_dict['monsters']['filters'] and
                        pokemon not in user_dict['monsters']['filters']['000'][
                            'monsters_exclude']):
                        deleted = True
                        user_dict['monsters']['filters']['000'][
                            'monsters_exclude'].append(pokemon)
                        user_dict['monsters']['filters']['000'][
                            'monsters_exclude'] = sorted(user_dict['monsters'][
                                'filters']['000']['monsters_exclude'])
                        del_count += 1
                    elif deleted is False:
                        if pokemon == 0:
                            name = 'default'
                        else:
                            name = locale.get_pokemon_name(pokemon)
                        embeds = discord.Embed(
                            description=(
                                "{} You did not previously have any alerts " +
                                "set for **{}**."
                            ).format(message.author.mention, name),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            '{} not previously set for {}.'
                        ).format(name, message.author.display_name))
                except ValueError:
                    if command == 'all':
                        deleted = []
                        if len(user_dict['monsters']['filters']) > 0:
                            for filt_name in user_dict['monsters'][
                                    'filters'].copy():
                                user_dict['monsters']['filters'].pop(filt_name)
                                if filt_name not in deleted:
                                    del_count += 1
                                    deleted.append(filt_name)
                        else:
                            embeds = discord.Embed(
                                description=(
                                    "{} You did not previously have any " +
                                    "alerts set."
                                ).format(message.author.mention),
                                color=int('0xee281f', 16)
                            )
                            await client.get_alarm().update(1, {
                                'destination': message.channel,
                                'embeds': embeds
                            })
                            log.info((
                                'Alerts not previously set for {}.'
                            ).format(message.author.display_name))
                    else:
                        embeds = discord.Embed(
                            description=(
                                "{} **{}** is not a recognized pokemon, " +
                                "check your spelling."
                            ).format(message.author.mention, command.title()),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            'Unrecognized pokemon from {}.'
                        ).format(message.author.display_name))
        if del_count > 0:
            if all_areas is True:
                gfs = ['all']
            else:
                gfs = []
            if user_filters[str(message.author.id)] == {
                "monsters": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                },
                "eggs": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                },
                "raids": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                }
            }:
                user_filters.pop(str(message.author.id))
            update_filters(user_filters, filter_file, f)
            embeds = discord.Embed(
                description=(
                    "{} You have removed **{}** pokemon spawn filters."
                ).format(message.author.mention, str(del_count)),
                color=int('0x71cd40', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info('Removed {} pokemon filters for {}.'.format(
                str(del_count), message.author.display_name))
    if del_count > 0:
        client.load_filter_file(get_path(filter_file))


async def reset(client, message, geofences, all_areas, filter_file, locale):
    msg = message.content.lower().replace('!reset ', '').replace(
        '!reset\n', '').replace('%', '').replace(
        'nidoranf', 'nidoran♀').replace('nidoranm', 'nidoran♂').replace(
        'mr. mime', 'mr.mime').replace('mime jr.', 'mimejr.').replace(
        'farfetchd', "farfetch'd").replace(
        'flabebe', 'flab\u00E9b\u00E9').replace(',\n', ',').replace(
        '\n', ',').replace(', ', ',').split(',')
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters.get(str(message.author.id))
        reset_count = 0
        if user_dict is None:
            embeds = discord.Embed(
                description=(
                    "{} There is nothing to reset, you don't have any " +
                    "alerts set."
                ).format(message.author.mention),
                color=int('0xee281f', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info((
                'Nothing to reset for {}.'
            ).format(message.author.display_name))
        else:
            for command in msg:
                if len(command) == 0:
                    continue
                else:
                    command = command.strip()
                try:
                    if is_number(command):
                        raise ValueError
                    pokemon = get_monster_id(command.replace(
                        'mr.mime', 'mr. mime').replace('mimejr.', 'mime jr.'))
                    reset = False
                    for filt_name in user_dict['monsters']['filters'].copy():
                        if int(filt_name[:3]) == pokemon:
                            user_dict['monsters']['filters'].pop(filt_name)
                            reset = True
                    if ('000' in user_dict['monsters']['filters'] and
                        pokemon in user_dict['monsters']['filters']['000'][
                            'monsters_exclude']):
                        reset = True
                        reset_count += 1
                        user_dict['monsters']['filters']['000'][
                            'monsters_exclude'].remove(pokemon)
                    if reset is False:
                        embeds = discord.Embed(
                            description=(
                                '{}, **{}** was already set at your default.'
                            ).format(
                                message.author.mention,
                                locale.get_pokemon_name(pokemon)
                            ),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            '{} not previously set for {}.'
                        ).format(
                            locale.get_pokemon_name(pokemon),
                            message.author.display_name
                        ))
                except ValueError:
                    if command == 'all':
                        reset = []
                        if len(user_dict['monsters']['filters']) > 0:
                            for filt_name in user_dict['monsters'][
                                    'filters'].copy():
                                if int(filt_name[:3]) > 0:
                                    user_dict['monsters']['filters'].pop(
                                        filt_name)
                                    if int(filt_name[:3]) not in reset:
                                        reset.append(int(filt_name[:3]))
                                        reset_count += 1
                            if ('000' in user_dict['monsters']['filters']):
                                user_dict['monsters']['filters']['000'][
                                    'monsters_exclude'] = []
                        else:
                            embeds = discord.Embed(
                                description=(
                                    "{} You did not previously have any " +
                                    "alerts set."
                                ).format(message.author.mention),
                                color=int('0xee281f', 16)
                            )
                            await client.get_alarm().update(1, {
                                'destination': message.channel,
                                'embeds': embeds
                            })
                            log.info((
                                'Alerts not previously set for {}.'
                            ).format(message.author.display_name))
                    else:
                        embeds = discord.Embed(
                            description=(
                                "{} **{}** is not a recognized pokemon, " +
                                "check your spelling."
                            ).format(message.author.mention, command.title()),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            'Unrecognized pokemon from {}.'
                        ).format(message.author.display_name))
        if reset_count > 0:
            if all_areas is True:
                gfs = ['all']
            else:
                gfs = []
            if user_filters[str(message.author.id)] == {
                "monsters": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                },
                "eggs": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                },
                "raids": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                }
            }:
                user_filters.pop(str(message.author.id))
            update_filters(user_filters, filter_file, f)
            embeds = discord.Embed(
                description=(
                        "{} You have reset **{}** pokemon spawn filters to " +
                        "your default filter."
                    ).format(message.author.mention, str(reset_count)),
                color=int('0x71cd40', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info('Reset {} pokemon filters for {}.'.format(
                str(reset_count), message.author.display_name))
    if reset_count > 0:
        client.load_filter_file(get_path(filter_file))


async def pause(client, message, geofences, all_areas, filter_file):
    msg = message.content.lower().split()
    if len(msg) > 1:
        kind = msg[1]
    else:
        kind = 'all'
    if kind in ['all', 'pokemon', 'raids', 'eggs']:
        reload = False
        with open(filter_file, 'r+', encoding="utf-8") as f:
            user_filters = json.load(f, object_pairs_hook=OrderedDict)
            user_dict = user_filters.get(str(message.author.id))
            if user_dict is None:
                embeds = discord.Embed(
                    description=((
                        "{} There is nothing to pause, you don't have any " +
                        "alerts set."
                    ).format(message.author.mention)),
                    color=int('0xee281f', 16)
                )
                await client.get_alarm().update(1, {
                    'destination': message.channel,
                    'embeds': embeds
                })
                log.info('{} tried to pause but nothing to pause.'.format(
                    message.author.display_name))
            else:
                if (kind in ['all', 'pokemon'] and
                        user_dict['monsters']['enabled'] is True):
                    user_dict['monsters']['enabled'] = False
                    reload = True
                if (kind in ['all', 'eggs'] and
                        user_dict['eggs']['enabled'] is True):
                    user_dict['eggs']['enabled'] = False
                    reload = True
                if (kind in ['all', 'raids'] and
                        user_dict['raids']['enabled'] is True):
                    user_dict['raids']['enabled'] = False
                    reload = True
                if reload:
                    if all_areas is True:
                        gfs = ['all']
                    else:
                        gfs = []
                    if user_filters[str(message.author.id)] == {
                        "monsters": {
                            "enabled": True,
                            "defaults": {
                                "geofences": gfs
                            },
                            "filters": {}
                        },
                        "eggs": {
                            "enabled": True,
                            "defaults": {
                                "geofences": gfs
                            },
                            "filters": {}
                        },
                        "raids": {
                            "enabled": True,
                            "defaults": {
                                "geofences": gfs
                            },
                            "filters": {}
                        }
                    }:
                        user_filters.pop(str(message.author.id))
                    update_filters(user_filters, filter_file, f)
                    embeds = discord.Embed(
                        description=("{}, {} alerts have been paused.").format(
                            message.author.mention, kind.strip('s')),
                        color=int('0x71cd40', 16)
                    )
                    await client.get_alarm().update(1, {
                        'destination': message.channel,
                        'embeds': embeds
                    })
                    log.info('Paused {} alerts for {}.'.format(
                        kind.strip('s'), message.author.display_name))
                else:
                    embeds = discord.Embed(
                        description=((
                            "{}, {} alerts are already paused."
                        ).format(message.author.mention, kind.strip('s'))),
                        color=int('0xee281f', 16)
                    )
                    await client.get_alarm().update(1, {
                        'destination': message.channel,
                        'embeds': embeds
                    })
                    log.info('{} tried to pause but already paused.'.format(
                        message.author.display_name))
        if reload:
            client.load_filter_file(get_path(filter_file))
    else:
        embeds = discord.Embed(
            description=((
                "{} **{}** is not a pause command, try 'all', 'pokemon', " +
                "'raids', or 'eggs'."
            ).format(message.author.mention, kind)),
            color=int('0xee281f', 16)
        )
        await client.get_alarm().update(1, {
            'destination': message.channel,
            'embeds': embeds
        })
        log.info('Unrecognized pause command from {}.'.format(
            message.author.display_name))


async def resume(client, message, geofences, all_areas, filter_file):
    msg = message.content.lower().split()
    if len(msg) > 1:
        kind = msg[1]
    else:
        kind = 'all'
    if kind in ['all', 'pokemon', 'raids', 'eggs']:
        reload = False
        with open(filter_file, 'r+', encoding="utf-8") as f:
            user_filters = json.load(f, object_pairs_hook=OrderedDict)
            user_dict = user_filters.get(str(message.author.id))
            if user_dict is None:
                embeds = discord.Embed(
                    description=((
                        "{} There is nothing to resume, you don't have any " +
                        "alerts set."
                    ).format(message.author.mention)),
                    color=int('0xee281f', 16)
                )
                await client.get_alarm().update(1, {
                    'destination': message.channel,
                    'embeds': embeds
                })
                log.info('{} tried to resume but nothing to resume.'.format(
                    message.author.display_name))
            else:
                if (kind in ['all', 'pokemon'] and
                        user_dict['monsters']['enabled'] is False):
                    user_dict['monsters']['enabled'] = True
                    reload = True
                if (kind in ['all', 'eggs'] and
                        user_dict['eggs']['enabled'] is False):
                    user_dict['eggs']['enabled'] = True
                    reload = True
                if (kind in ['all', 'raids'] and
                        user_dict['raids']['enabled'] is False):
                    user_dict['raids']['enabled'] = True
                    reload = True
                if reload:
                    if all_areas is True:
                        gfs = ['all']
                    else:
                        gfs = []
                    if user_filters[str(message.author.id)] == {
                        "monsters": {
                            "enabled": True,
                            "defaults": {
                                "geofences": gfs
                            },
                            "filters": {}
                        },
                        "eggs": {
                            "enabled": True,
                            "defaults": {
                                "geofences": gfs
                            },
                            "filters": {}
                        },
                        "raids": {
                            "enabled": True,
                            "defaults": {
                                "geofences": gfs
                            },
                            "filters": {}
                        }
                    }:
                        user_filters.pop(str(message.author.id))
                    update_filters(user_filters, filter_file, f)
                    embeds = discord.Embed(
                        description=((
                            "{}, {} alerts have been resumed."
                        ).format(message.author.mention, kind.strip('s'))),
                        color=int('0x71cd40', 16)
                    )
                    await client.get_alarm().update(1, {
                        'destination': message.channel,
                        'embeds': embeds
                    })
                    log.info('Resumed {} alerts for {}.'.format(
                        kind.strip('s'), message.author.display_name))
                else:
                    embeds = discord.Embed(
                        description=((
                            "{}, {} alerts were not previously paused."
                        ).format(message.author.mention, kind.strip('s'))),
                        color=int('0xee281f', 16)
                    )
                    await client.get_alarm().update(1, {
                        'destination': message.channel,
                        'embeds': embeds
                    })
                    log.info("{} tried to resume but wasn't paused.".format(
                        message.author.display_name))
        if reload:
            client.load_filter_file(get_path(filter_file))
    else:
        embeds = discord.Embed(
            description=((
                "{} **{}** is not a resume command, try 'all', 'pokemon', " +
                "'raids', or 'eggs'."
            ).format(message.author.mention, kind)),
            color=int('0xee281f', 16)
        )
        await client.get_alarm().update(1, {
            'destination': message.channel,
            'embeds': embeds
        })
        log.info('Unrecognized resume command from {}.'.format(
            message.author.display_name))


async def activate(client, message, geofences, all_areas, filter_file):
    msg = message.content.lower().replace('!activate ', '').replace(
        '!activate\n', '').replace(',\n', ',').replace('\n', ',').replace(
            ', ', ',').split(',')
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters.get(str(message.author.id))
        gf_lower = [gf.lower() for gf in list(geofences.keys())]
        activate_count = 0
        for command in msg:
            if len(command) == 0:
                continue
            else:
                command = command.strip()
            if command in gf_lower or command == 'all':
                if command != 'all':
                    idx = next(
                        i for i, gf in enumerate(
                            list(geofences.keys())) if gf.lower() == command
                    )
                    command = list(geofences.keys())[idx]
                if user_dict is None:
                    if all_areas is True:
                        embeds = discord.Embed(
                            description=((
                                "{} All areas are on by default."
                            ).format(message.author.mention)),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            'Sent all areas are on by default to {}.'
                        ).format(message.author.display_name))
                        break
                    else:
                        user_filters[str(message.author.id)] = {
                            "monsters": {
                                "enabled": True,
                                "defaults": {
                                    "geofences": [command]
                                },
                                "filters": {}
                            },
                            "eggs": {
                                "enabled": True,
                                "defaults": {
                                    "geofences": [command]
                                },
                                "filters": {}
                            },
                            "raids": {
                                "enabled": True,
                                "defaults": {
                                    "geofences": [command]
                                },
                                "filters": {}
                            }
                        }
                        user_dict = user_filters[str(message.author.id)]
                        if command == 'all':
                            activate_count += len(geofences)
                        else:
                            activate_count += 1
                else:
                    if ('all' not in user_dict['monsters']['defaults'][
                        'geofences'] and
                        command not in user_dict['monsters']['defaults'][
                            'geofences']):
                        if command == 'all':
                            user_dict['monsters']['defaults']['geofences'] = [
                                command]
                            user_dict['eggs']['defaults']['geofences'] = [
                                command]
                            user_dict['raids']['defaults']['geofences'] = [
                                command]
                            activate_count += (
                                len(geofences.keys()) - len(user_dict[
                                    'monsters']['defaults']['geofences'])
                            )
                        else:
                            user_dict['monsters']['defaults'][
                                'geofences'].append(command)
                            user_dict['eggs']['defaults']['geofences'].append(
                                command)
                            user_dict['raids']['defaults']['geofences'].append(
                                command)
                            activate_count += 1
                    else:
                        if command == 'all':
                            descript = ((
                                "{} **{}** areas are already active for you."
                            ).format(message.author.mention, command.title()))
                        else:
                            descript = ((
                                "{} The **{}** area is already active for you."
                            ).format(message.author.mention, command))
                        embeds = discord.Embed(
                            description=descript,
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            'Area already active for {}.'
                        ).format(message.author.display_name))
            else:
                embeds = discord.Embed(
                    description=((
                        "{} The **{}** area is an unrecognized area for " +
                        "this region."
                    ).format(message.author.mention, command)),
                    color=int('0xee281f', 16)
                )
                await client.get_alarm().update(1, {
                    'destination': message.channel,
                    'embeds': embeds
                })
                log.info((
                    'Unrecognized area from {}.'
                ).format(message.author.display_name))
        if activate_count > 0:
            if all_areas is True:
                gfs = ['all']
            else:
                gfs = []
            if user_filters[str(message.author.id)] == {
                "monsters": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                },
                "eggs": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                },
                "raids": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                }
            }:
                user_filters.pop(str(message.author.id))
            update_filters(user_filters, filter_file, f)
            embeds = discord.Embed(
                description=((
                    "{} Your alerts have been activated for **{}** areas."
                ).format(message.author.mention, str(activate_count))),
                color=int('0x71cd40', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info('Activated {} areas for {}.'.format(
                str(activate_count), message.author.display_name))
    if activate_count > 0:
        client.load_filter_file(get_path(filter_file))


async def deactivate(client, message, geofences, all_areas, filter_file):
    if message.content.lower() == '!deactivate all':
        msg = [gf.lower() for gf in list(geofences.keys())]
    else:
        msg = message.content.lower().replace('!deactivate ', '').replace(
            '!deactivate\n', '').replace(',\n', ',').replace(
                '\n', ',').replace(', ', ',').split(',')
    deactivate_count = 0
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters.get(str(message.author.id))
        gf_lower = [gf.lower() for gf in list(geofences.keys())]
        for command in msg:
            if len(command) == 0:
                continue
            else:
                command = command.strip()
            if command in gf_lower:
                idx = next(
                    i for i, gf in enumerate(
                        list(geofences.keys())) if gf.lower() == command
                )
                command = list(geofences.keys())[idx]
                if user_dict is None:
                    if all_areas is False:
                        embeds = discord.Embed(
                            description=((
                                "{} All areas are off by default."
                            ).format(message.author.mention)),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            'Sent all areas are off by default to {}.'
                        ).format(message.author.display_name))
                        break
                    else:
                        gfs = list(geofences.keys())
                        gfs.remove(command)
                        user_filters[str(message.author.id)] = {
                            "monsters": {
                                "enabled": True,
                                "defaults": {
                                    "geofences": list(gfs)
                                },
                                "filters": {}
                            },
                            "eggs": {
                                "enabled": True,
                                "defaults": {
                                    "geofences": list(gfs)
                                },
                                "filters": {}
                            },
                            "raids": {
                                "enabled": True,
                                "defaults": {
                                    "geofences": list(gfs)
                                },
                                "filters": {}
                            }
                        }
                        user_dict = user_filters[str(message.author.id)]
                        deactivate_count += 1
                else:
                    if ('all' in user_dict['monsters']['defaults'][
                        'geofences'] or
                        command in user_dict['monsters']['defaults'][
                            'geofences']):
                        deactivate_count += 1
                        if 'all' in user_dict['monsters']['defaults'][
                                'geofences']:
                            gfs = list(geofences.keys())
                            gfs.remove(command)
                            user_dict['monsters']['defaults'][
                                'geofences'] = list(gfs)
                            user_dict['eggs']['defaults']['geofences'] = list(
                                gfs)
                            user_dict['raids']['defaults']['geofences'] = list(
                                gfs)
                        else:
                            user_dict['monsters']['defaults'][
                                'geofences'].remove(command)
                            user_dict['eggs']['defaults']['geofences'].remove(
                                command)
                            user_dict['raids']['defaults']['geofences'].remove(
                                command)
                    elif message.content.lower() != '!deactivate all':
                        embeds = discord.Embed(
                            description=((
                                "{} The **{}** area was not previously " +
                                "active for you."
                            ).format(message.author.mention, command)),
                            color=int('0xee281f', 16)
                        )
                        await client.get_alarm().update(1, {
                            'destination': message.channel,
                            'embeds': embeds
                        })
                        log.info((
                            'Area not previously active for {}.'
                        ).format(message.author.display_name))
            else:
                embeds = discord.Embed(
                    description=((
                        "{} The **{}** area is an unrecognized area for " +
                        "this region."
                    ).format(message.author.mention, command)),
                    color=int('0xee281f', 16)
                )
                await client.get_alarm().update(1, {
                    'destination': message.channel,
                    'embeds': embeds
                })
                log.info((
                    'Unrecognized area from {}.'
                ).format(message.author.display_name))
        if deactivate_count > 0:
            if all_areas is True:
                gfs = ['all']
            else:
                gfs = []
            if user_filters[str(message.author.id)] == {
                "monsters": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                },
                "eggs": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                },
                "raids": {
                    "enabled": True,
                    "defaults": {
                        "geofences": gfs
                    },
                    "filters": {}
                }
            }:
                user_filters.pop(str(message.author.id))
            update_filters(user_filters, filter_file, f)
            embeds = discord.Embed(
                description=((
                    "{} Your alerts have been deactivated for **{}** areas."
                ).format(message.author.mention, str(deactivate_count))),
                color=int('0x71cd40', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info('Deactivated {} areas for {}.'.format(
                str(deactivate_count), message.author.display_name))
        elif message.content.lower() == '!deactivate all':
            embeds = discord.Embed(
                description=((
                    "{} **All** areas were not previously active for you."
                ).format(message.author.mention)),
                color=int('0xee281f', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info('Area not previously active for {}.').format(
                message.author.display_name)
    if deactivate_count > 0:
        client.load_filter_file(get_path(filter_file))


async def alerts_raids(client, message, bot_number, geofences, all_areas,
                       filter_file, locale):
    with open(filter_file, encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters.get(str(message.author.id))
    if user_dict is None:
        embeds = discord.Embed(
            description=((
                "{} You don't have any alerts set."
            ).format(message.author.mention)),
            color=int('0xee281f', 16)
        )
        await client.get_alarm().update(1, {
            'destination': message.channel,
            'embeds': embeds
        })
        log.info('No alerts set for {}.'.format(message.author.display_name))
    else:
        alerts = ((
            "**{}**'s Raid Alert Settings:\nBOT NUMBER: {}\n\nPAUSED: "
        ).format(message.author.mention, str(bot_number + 1)))
        if user_dict['raids']['enabled'] is True:
            alerts += "**FALSE**\n\n"
        else:
            alerts += "**TRUE**\n\n"
        if all_areas is True:
            alerts += '__PAUSED AREAS__\n\n```\n'
            if ('all' in user_dict['raids']['defaults']['geofences'] or
                len(user_dict['raids']['defaults']['geofences']) == len(
                    geofences)):
                alerts += 'None \n'
            else:
                for area in list(
                        set(geofences.keys()) - set(user_dict['raids'][
                            'defaults']['geofences'])):
                    alerts += '{}, '.format(area)
        else:
            alerts += '__ALERT AREAS__\n\n```\n'
            if len(user_dict['raids']['defaults']['geofences']) == 0:
                alerts += (
                    "You don't any areas set.  Type `!activate raids " +
                    "[area/all]` in #custom_filters to set one! \n"
                )
            elif 'all' in user_dict['raids']['defaults']['geofences']:
                for area in list(geofences.keys()):
                    alerts += '{}, '.format(area)
            else:
                for area in user_dict['raids']['defaults']['geofences']:
                    alerts += '{}, '.format(area)
        alerts = alerts[:-2] + '\n```\n'
        alerts += '__LEVELS__\n\n```\n'
        for lvl in range(1, 6):
            if str(lvl) + 'a' in user_dict['raids']['filters']:
                alerts += "{}: EX Only\n".format(lvl)
            elif str(lvl) in user_dict['raids']['filters']:
                alerts += "{}: All\n".format(lvl)
            else:
                alerts += "{}: None\n".format(lvl)
        alerts = alerts[:-1] + '\n```\n'
        alerts += '__POKEMON__\n\n```\n'
        if '0' not in user_dict['raids']['filters']:
            alerts += 'None \n'
        else:
            for pkmn in user_dict['raids']['filters']['0']['monsters']:
                alerts += '{}, '.format(locale.get_pokemon_name(pkmn))
        alerts = alerts[:-2] + '\n```'
        alerts = [alerts]
        while len(alerts[-1]) > 2000:
            for alerts_split in msg_split(alerts.pop()):
                alerts.append(alerts_split)
        for dm in alerts:
            await client.get_alarm().update(1, {
                'destination': message.author,
                'content': dm
            })
            log.info('Sent raid alerts message to {}.'.format(
                message.author.display_name))


async def alerts_eggs(client, message, bot_number, geofences, all_areas,
                      filter_file, locale):
    with open(filter_file, encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters.get(str(message.author.id))
    if user_dict is None:
        embeds = discord.Embed(
            description=((
                "{} You don't have any alerts set."
            ).format(message.author.mention)),
            color=int('0xee281f', 16)
        )
        await client.get_alarm().update(1, {
            'destination': message.channel,
            'embeds': embeds
        })
        log.info('No alerts set for {}.'.format(message.author.display_name))
    else:
        alerts = ((
            "**{}**'s Egg Alert Settings:\nBOT NUMBER: {}\n\nPAUSED: "
        ).format(message.author.mention, str(bot_number + 1)))
        if user_dict['eggs']['enabled'] is True:
            alerts += "**FALSE**\n\n"
        else:
            alerts += "**TRUE**\n\n"
        if all_areas is True:
            alerts += '__PAUSED AREAS__\n\n```\n'
            if ('all' in user_dict['eggs']['defaults']['geofences'] or
                len(user_dict['eggs']['defaults']['geofences']) == len(
                    geofences)):
                alerts += 'None \n'
            else:
                for area in list(
                        set(geofences.keys()) - set(user_dict['eggs'][
                            'defaults']['geofences'])):
                    alerts += '{}, '.format(area)
        else:
            alerts += '__ALERT AREAS__\n\n```\n'
            if len(user_dict['eggs']['defaults']['geofences']) == 0:
                alerts += (
                    "You don't any areas set.  Type `!activate eggs " +
                    "[area/all]` in #custom_filters to set one! \n"
                )
            elif 'all' in user_dict['eggs']['defaults']['geofences']:
                for area in list(geofences.keys()):
                    alerts += '{}, '.format(area)
            else:
                for area in user_dict['eggs']['defaults']['geofences']:
                    alerts += '{}, '.format(area)
        alerts = alerts[:-2] + '\n```\n'
        alerts += '__LEVELS__\n\n```\n'
        for lvl in range(1, 6):
            if str(lvl) + 'a' in user_dict['eggs']['filters']:
                alerts += "{}: EX Only\n".format(lvl)
            elif str(lvl) in user_dict['eggs']['filters']:
                alerts += "{}: All\n".format(lvl)
            else:
                alerts += "{}: None\n".format(lvl)
        alerts = alerts[:-1] + '\n```'
        alerts = [alerts]
        while len(alerts[-1]) > 2000:
            for alerts_split in msg_split(alerts.pop()):
                alerts.append(alerts_split)
        for dm in alerts:
            await client.get_alarm().update(1, {
                'destination': message.author,
                'content': dm
            })
            log.info('Sent egg alerts message to {}.'.format(
                message.author.display_name))


async def alerts(client, message, bot_number, geofences, all_areas,
                 filter_file, locale):
    with open(filter_file, encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters.get(str(message.author.id))
    if user_dict is None:
        embeds = discord.Embed(
            description=((
                "{} You don't have any alerts set."
            ).format(message.author.mention)),
            color=int('0xee281f', 16)
        )
        await client.get_alarm().update(1, {
            'destination': message.channel,
            'embeds': embeds
        })
        log.info('No alerts set for {}.'.format(message.author.display_name))
    else:
        alerts = ((
            "**{}**'s Pokemon Alert Settings:\nBOT NUMBER: {}\n\nPAUSED: "
        ).format(message.author.mention, str(bot_number + 1)))
        if user_dict['monsters']['enabled'] is True:
            alerts += "**FALSE**\n\n"
        else:
            alerts += "**TRUE**\n\n"
        if all_areas is True:
            alerts += '__PAUSED AREAS__\n\n```\n'
            if ('all' in user_dict['monsters']['defaults']['geofences'] or
                len(user_dict['monsters']['defaults']['geofences']) == len(
                    geofences)):
                alerts += 'None \n'
            else:
                for area in list(
                        set(geofences.keys()) - set(user_dict['monsters'][
                            'defaults']['geofences'])):
                    alerts += '{}, '.format(area)
        else:
            alerts += '__ALERT AREAS__\n\n```\n'
            if len(user_dict['monsters']['defaults']['geofences']) == 0:
                alerts += (
                    "You don't any areas set.  Type `!activate [area/all]` " +
                    "in #custom_filters to set one! \n"
                )
            elif 'all' in user_dict['monsters']['defaults']['geofences']:
                for area in list(geofences.keys()):
                    alerts += '{}, '.format(area)
            else:
                for area in user_dict['monsters']['defaults']['geofences']:
                    alerts += '{}, '.format(area)
        alerts = alerts[:-2] + '\n```\n'
        alerts += '__POKEMON__\n\n```\n'
        if '000' in user_dict['monsters']['filters']:
            alerts += 'Default (all unlisted): '
            if int(user_dict['monsters']['filters']['000']['min_iv']) > 0:
                alerts += '{}%+, '.format(
                    user_dict['monsters']['filters']['000']['min_iv'])
            if int(user_dict['monsters']['filters']['000']['min_cp']) > 0:
                alerts += '{}CP+, '.format(
                    user_dict['monsters']['filters']['000']['min_cp'])
            if int(user_dict['monsters']['filters']['000']['min_lvl']) > 0:
                alerts += 'L{}+, '.format(
                    user_dict['monsters']['filters']['000']['min_lvl'])
            alerts = alerts[:-2] + '\n\n'
        else:
            alerts += 'Default: None\n\n'
        for pokemon in range(721):
            if ('000' in user_dict['monsters']['filters'] and
                pokemon not in user_dict['monsters']['filters']['000'][
                    'monsters_exclude']):
                continue
            elif '{:03}'.format(pokemon) not in user_dict['monsters'][
                    'filters']:
                if '000' in user_dict['monsters']['filters']:
                    alerts += '{}: None\n'.format(
                        locale.get_pokemon_name(pokemon))
                else:
                    continue
            else:
                alerts += '{}: '.format(locale.get_pokemon_name(pokemon))
                for filt_name in user_dict['monsters']['filters']:
                    if filt_name.startswith('{:03}'.format(pokemon)):
                        if (int(user_dict['monsters']['filters'][filt_name][
                                'min_iv']) == 0 and
                            int(user_dict['monsters']['filters'][filt_name][
                                'min_cp']) == 0 and
                            int(user_dict['monsters']['filters'][filt_name][
                                'min_lvl']) == 0 and
                            user_dict['monsters']['filters'][filt_name].get(
                                'genders') is None):
                            alerts += 'All  '
                        else:
                            if int(user_dict['monsters']['filters'][filt_name][
                                    'min_iv']) > 0:
                                alerts += '{}%+, '.format(user_dict[
                                    'monsters']['filters'][filt_name][
                                        'min_iv'])
                            if int(user_dict['monsters']['filters'][filt_name][
                                    'min_cp']) > 0:
                                alerts += '{}CP+, '.format(user_dict[
                                    'monsters']['filters'][filt_name][
                                        'min_cp'])
                            if int(user_dict['monsters']['filters'][filt_name][
                                    'min_lvl']) > 0:
                                alerts += 'L{}+, '.format(user_dict[
                                    'monsters']['filters'][filt_name][
                                        'min_lvl'])
                            if user_dict['monsters']['filters'][filt_name].get(
                                    'genders') is not None:
                                if user_dict['monsters']['filters'][filt_name][
                                        'genders'] == ['female']:
                                    alerts += '♀, '
                                else:
                                    alerts += '♂, '
                        alerts = alerts[:-2] + ' | '
                alerts = alerts[:-3] + '\n'
        alerts += '```'
        alerts = [alerts]
        while len(alerts[-1]) > 2000:
            for alerts_split in msg_split(alerts.pop()):
                alerts.append(alerts_split)
        for dm in alerts:
            await client.get_alarm().update(1, {
                'destination': message.author,
                'content': dm
            })
            log.info('Sent pokemon alerts message to {}.'.format(
                message.author.display_name))


async def areas(client, message, geofences, filter_file):
    with open(filter_file, encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
    user_dict = user_filters.get(str(message.author.id))
    areas = '__AVAILABLE AREAS__ (Your active areas are in **bold**.)\n\n'
    for gf in list(geofences.keys()):
        if (user_dict is not None and
            (gf in user_dict['monsters']['defaults']['geofences'] or
             'all' in user_dict['monsters']['defaults']['geofences'])):
            areas += '**{}**, '.format(gf)
        else:
            areas += '{}, '.format(gf)
    areas = [areas[:-2]]
    areas[0] += (
        '\n\nYou can change your settings by using `!activate [area/all]` ' +
        'or `!deactivate [area/all]` in #custom_filters'
    )
    while len(areas[-1]) > 2000:
        for areas_split in msg_split(areas.pop()):
            areas.append(areas_split)
    for dm in areas:
        await client.get_alarm().update(1, {
            'destination': message.author,
            'content': dm
        })
    log.info('Sent areas message to {}'.format(message.author.display_name))
