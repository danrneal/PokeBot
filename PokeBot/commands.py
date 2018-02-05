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


async def status(client ,message, bot_number, number_of_bots):
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
    if bot_number == 0:
        await asyncio.sleep(0.1 * number_of_bots)
        await client.get_alarm().update(1, {
                'destination': message.channel,
                'content': 'https://youtu.be/kxH6YErAIgA'
        })
        log.info('Sent standing by video')


async def commands(client, message):
    embeds = discord.Embed(
        description=(
            "Hello there!\n\n" +
            "`!set [pokemon/default/all] [IV] CP[CP] L[level] [gender]` to add " +
            "an alert for a given pokemon based on it's characteristics, any of " +
            "the characteristics can be left blank,\n\n" +
            "`!delete [pokemon/default/all]` to remove an alert for a given " +
            "pokemon\n\n" +
            "`!reset [pokemon/all]` to reset an alert for a given pokemon to " +
            "your default alert characteristics\n\n" +
            "`!pause` or `!p` to pause all notifcations,\n\n" +
            "`!resume` or `!r` to resume all alerts,\n\n" +
            "`!activate [area/all]` to resume a given area,\n\n" +
            "`!deactivate [area/all]` to pause a given area,\n\n" +
            "`!areas` to see what areas area available to pause or resume,\n\n" +
            "`!alerts` to see your alert settings,\n\n"
            "`!dex [pokemon]` to get pokedex information for a given " +
            "pokemon,\n\n" +
            "`!status` to see which bots are currently online,\n\n" +
            "`!help` or `!commands` to see this message,\n\n" +
            "It is possible to add or delete multiple pokemon or areas by " +
            "putting pokemon on seperate lines or separating them with commas.\n" +
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
            legacy_quick.append(quick_move.find(class_=("move-info")))
        charge = []
        legacy_charge = []
        for charge_move in soup.find_all(class_=(
                "views-field views-field-field-charge-move")):
            charge.append(charge_move.find(class_=(
                "field field--name-title " +
                "field--type-string field--label-hidden"
            )))
            legacy_charge.append(charge_move.find(class_=("move-info")))
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
        offensive_moves = sorted(
            zip(offensive_grade[1:], quick[1:], charge[1:], legacy_moves[1:]),
            key=lambda x: x[0]
        )
        defensive_moves = sorted(
            zip(defensive_grade[1:], quick[1:], charge[1:], legacy_moves[1:]),
            key=lambda x: x[0]
        )
        if len(soup.find_all(class_=("raid-boss-counters"))) > 0:
            raid_counters = soup.find_all(class_=("raid-boss-counters"))[
                0].find_all(class_=(
                    "field field--name-title " +
                    "field--type-string field--label-hidden"
                ))
        title = "%03d" % dex_number + ' | ' + pokemon.upper()
        try:
            descript = "Rating: " + rating[0].get_text().strip() + ' / 10'
        except IndexError:
            descript = "Rating: - / 10"
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
            for (grade, quick, charge, legacy) in offensive_moves:
                descript += (
                    '\n[' + grade.strip() + '] ' + quick.get_text() +
                    ' / ' + charge.get_text() + legacy
                )
            descript += " \n```\nDefensive Movesets:\n```"
            for (grade, quick, charge, legacy) in defensive_moves:
                descript += (
                    '\n[' + grade.strip() + '] ' + quick.get_text() +
                    ' / ' + charge.get_text() + legacy
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


async def set_(client, message, all_areas, filter_file, locale):
    msg = message.content.lower().replace('!set ', '').replace(
        '!set\n', '').replace('%', '').replace('nidoranf', 'nidoran♀').replace(
        'nidoranm', 'nidoran♂').replace('mr. mime', 'mr.mime').replace(
        ',\n', ',').replace('\n', ',').replace(', ', ',').split(',')
    set_count = 0
    reload = False
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters[str(message.author.id)]
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
                    'mr.mime', 'mr. mime'))
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
                command = command.replace('default', '').replace(
                    'all', '').strip()
                input_ = [command.split()]
                filters = [{
                    'monsters': [],
                    'min_iv': '0',
                    'min_cp': '0',
                    'min_lvl': '0'
                }]
            for inp, filt in zip(input_, filters):
                if pokemon > 0:
                    if (len(set(inp).intersection(set(['female', 'f']))) > 0 and
                        get_monster_id(pokemon) not in Dicts.male_only and
                            get_monster_id(pokemon) not in Dicts.genderless):
                        filt['genders'] = ['female']
                        filt['is_missing_info'] = False
                        inp.remove(list(set(inp).intersection(set(
                            ['female', 'f'])))[0])
                    elif (len(set(inp).intersection(set(['male', 'm']))) > 0 and
                          get_monster_id(pokemon) not in Dicts.female_only and
                          get_monster_id(pokemon) not in Dicts.genderless):
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
                        if int(char) >= 0 and int(char) <= 100:
                            filt['min_iv'] = str(char)
                            if int(char) > 0:
                                filt['is_missing_info'] = False
                        else:
                            error = True
                            embeds = discord.Embed(
                                description=((
                                    '{} Pokemon IV must be between 0 and 100.'
                                ).format(
                                    message.author.mention)),
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
                                ).format(
                                    message.author.mention)),
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
                                ).format(
                                    message.author.mention)),
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
                            ).format(
                                message.author.mention, char)),
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
            for filt in filters:
                filter_dict = {
                    "{:03}{}".format(pokemon, suffix): filt
                }
                if suffix == '':
                    suffix = 'a'
                elif suffix == 'a':
                    suffix = 'b'
            if user_dict is None:
                if all_areas is True:
                    gfs = list(geofences.keys())
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
                reload = True
                user_dict = user_filters[str(message.author.id)]
            else:
                for filt_name in user_dict['monsters']['filters'].copy():
                    if int(filt_name[:3]) == pokemon:
                        user_dict['monsters']['filters'].pop(filt_name)
                user_dict['monsters']['filters'].update(filter_dict)
                set_count += 1
                reload = True
            already_filtered = []
            for filt_name in user_dict['monsters']['filters']:
                if int(filt_name[:3]) not in already_filtered:
                    already_filtered.append(int(filt_name[:3]))
            if '000' in user_dict['monsters']['filters']:
                user_dict['monsters']['filters']['000']['monsters'] = sorted(
                    list(set(list(range(1, 722))) - set(already_filtered)))
            user_dict['monsters']['filters'] = user_dict['monsters']['filters']
        if reload:
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
    if reload:
        client.load_filter_file(get_path(filter_file))


async def delete(client, message, geofences, all_areas, filter_file, locale):
    msg = message.content.lower().replace('!delete ', '').replace(
        '!delete\n', '').replace('!remove ', '').replace(
        '!remove\n', '').replace('%', '').replace(
        'nidoranf', 'nidoran♀').replace('nidoranm', 'nidoran♂').replace(
        'mr. mime', 'mr.mime').replace(',\n', ',').replace('\n', ',').replace(
        ', ', ',').split(',')
    del_count = 0
    reload = False
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters[str(message.author.id)]
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
                    deleted = False
                    if command == 'default':
                        pokemon = 0
                    else:
                        pokemon = get_monster_id(command.replace(
                            'mr.mime', 'mr. mime'))
                    for filt_name in user_dict['monsters']['filters'].copy():
                        if int(filt_name[:3]) == pokemon:
                            deleted = True
                            user_dict['monsters']['filters'].pop(filt_name)
                    if ('000' in user_dict['monsters']['filters'] and
                        pokemon in user_dict['monsters']['filters']['000'][
                            'monsters']):
                        deleted = True
                        user_dict['monsters']['filters']['000'][
                            'monsters'].remove(pokemon)
                    if deleted is True:
                        reload = True
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
                    if command == 'all':
                        deleted = []
                        if len(user_dict['monsters']['filters']) > 0:
                            for filt_name in user_dict['monsters'][
                                    'filters'].copy():
                                if int(filt_name[:3]) not in deleted:
                                    deleted.append(int(filt_name[:3]))
                                    del_count += 1
                                    reload = True
                                user_dict['monsters']['filters'].pop(filt_name)
                        else:
                            embeds = discord.Embed(
                                description=(
                                    "{} You did not previously have any alerts " +
                                    "set."
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
        if reload:                
            if all_areas is True:
                gfs = list(geofences.keys())
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
    if reload:
        client.load_filter_file(get_path(filter_file))


async def reset(client, message, geofences, all_areas, filter_file, locale):
    msg = message.content.lower().replace('!reset ', '').replace(
        '!reset\n', '').replace('%', '').replace(
        'nidoranf', 'nidoran♀').replace('nidoranm', 'nidoran♂').replace(
        'mr. mime', 'mr.mime').replace(',\n', ',').replace('\n', ',').replace(
        ', ', ',').split(',')
    reset_count = 0
    reload = False
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        user_dict = user_filters[str(message.author.id)]    
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
                    reset = False
                    pokemon = get_monster_id(command.replace(
                        'mr.mime', 'mr. mime'))
                    for filt_name in user_dict['monsters']['filters'].copy():
                        if int(filt_name[:3]) == pokemon:
                            user_dict['monsters']['filters'].pop(filt_name)
                            if reset == False:
                                reset_count += 1
                                reload = True
                            reset = True
                    if ('000' in user_dict['monsters']['filters'] and
                        pokemon not in user_dict['monsters']['filters']['000'][
                            'monsters']):
                        reset = True
                        user_dict['monsters']['filters']['000'][
                            'monsters'].append(pokemon)
                        user_dict['monsters']['filters']['000'][
                            'monsters'] = sorted(user_dict['monsters'][
                                'filters']['000']['monsters'])
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
                    if command != 'all':
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
                    else:
                        reset = []
                        if user_dict['monsters']['filters'] > 0:
                            for filt_name in user_dict['monsters'][
                                    'filters'].copy():
                                if int(filt_name[:3]) not in reset:
                                    reset.append(int(filt_name[:3]))
                                    reset_count += 1
                                    reload = True
                                user_dict['monsters']['filters'].pop(filt_name)
                            if ('000' in user_dict['monsters']['filters']):
                                user_dict['monsters']['filters']['000'][
                                    'monsters'] = list(range(1, 722))                  
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
        if reload:
            if all_areas is True:
                gfs = list(geofences.keys())
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
                        "{} You have reset **{}** pokemon spawn filters to your " +
                        "default filter."
                    ).format(message.author.mention, str(reset_count)),
                color=int('0x71cd40', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info('Reset {} pokemon filters for {}.'.format(
                str(reset_count), message.author.display_name))
    if reload:
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
            if str(message.author.id) in list(user_filters.keys()):
                filters = user_filters[str(message.author.id)]
                if (kind in ['all', 'pokemon'] and
                        filters['monsters']['enabled'] is True):
                    filters['monsters']['enabled'] = False
                    reload = True
                if (kind in ['all', 'eggs'] and
                        filters['eggs']['enabled'] is True):
                    filters['eggs']['enabled'] = False
                    reload = True
                if (kind in ['all', 'raids'] and
                        filters['raids']['enabled'] is True):
                    filters['raids']['enabled'] = False
                    reload = True
                if reload:
                    if all_areas is True:
                        gfs = list(geofences.keys())
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
            else:
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
            if str(message.author.id) in list(user_filters.keys()):
                filters = user_filters[str(message.author.id)]
                if (kind in ['all', 'pokemon'] and
                        filters['monsters']['enabled'] is False):
                    filters['monsters']['enabled'] = True
                    reload = True
                if (kind in ['all', 'eggs'] and
                        filters['eggs']['enabled'] is False):
                    filters['eggs']['enabled'] = True
                    reload = True
                if (kind in ['all', 'raids'] and
                        filters['raids']['enabled'] is False):
                    filters['raids']['enabled'] = True
                    reload = True
                if reload:
                    if all_areas is True:
                        gfs = list(geofences.keys())
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
            else:
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
    activate_count = 0
    reload = False
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        filters = user_filters.get(str(message.author.id))
        gf_lower = [gf.lower() for gf in list(geofences.keys())]
        for command in msg:
            if len(command) == 0:
                continue
            else:
                command = command.strip()
            if command in gf_lower or command == 'all':
                if command != 'all':
                    command = list(geofences.keys())[gf_lower.index(command)]
                if filters is None:
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
                        activate_count += 1
                        reload = True
                else:
                    mon_geofences = filters['monsters']['defaults'][
                        'geofences']
                    egg_geofences = filters['eggs']['defaults']['geofences']
                    raid_geofences = filters['raids']['defaults']['geofences']
                    if (('all' not in mon_geofences and
                         command not in mon_geofences) or
                        ('all' not in egg_geofences and
                         command not in egg_geofences) or
                        ('all' not in raid_geofences and
                         command not in raid_geofences)):
                        if command == 'all':
                            activate_count += (
                                len(list(geofences.keys())) -
                                len(mon_geofences)
                            )
                        else:
                            activate_count += 1
                        reload = True
                        if ('all' not in mon_geofences and
                                command not in mon_geofences):
                            if command == 'all':
                                mon_geofences = [command]
                            else:
                                mon_geofences.append(command)
                        if ('all' not in egg_geofences and
                                command not in egg_geofences):
                            if command == 'all':
                                egg_geofences = [command]
                            else:
                                egg_geofences.append(command)
                        if ('all' not in raid_geofences and
                                command not in raid_geofences):
                            if command == 'all':
                                raid_geofences = [command]
                            else:
                                raid_geofences.append(command)
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
        if reload:
            if all_areas is True:
                gfs = list(geofences.keys())
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
    if reload:
        client.load_filter_file(get_path(filter_file))


async def deactivate(client, message, geofences, all_areas, filter_file):
    if message.content.lower() == '!deactivate all':
        msg = list(geofences.keys())
    else:
        msg = message.content.lower().replace('!deactivate ', '').replace(
            '!deactivate\n', '').replace(',\n', ',').replace(
                '\n', ',').replace(', ', ',').split(',')
    deactivate_count = 0
    reload = False
    with open(filter_file, 'r+', encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
        filters = user_filters.get(str(message.author.id))
        gf_lower = [gf.lower() for gf in list(geofences.keys())]
        for command in msg:
            if len(command) == 0:
                continue
            else:
                command = command.strip()
            if command in gf_lower:
                if filters is None:
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
                        user_filters[str(message.author.id)] = {
                            "monsters": {
                                "enabled": True,
                                "defaults": {
                                    "geofences": list(geofences.keys()).remove(
                                        command)
                                },
                                "filters": {}
                            },
                            "eggs": {
                                "enabled": True,
                                "defaults": {
                                    "geofences": list(geofences.keys()).remove(
                                        command)
                                },
                                "filters": {}
                            },
                            "raids": {
                                "enabled": True,
                                "defaults": {
                                    "geofences": list(geofences.keys()).remove(
                                        command)
                                },
                                "filters": {}
                            }
                        }
                        deactivate_count += 1
                        reload = True
                else:
                    mon_geofences = filters['monsters']['defaults'][
                        'geofences']
                    egg_geofences = filters['eggs']['defaults']['geofences']
                    raid_geofences = filters['raids']['defaults']['geofences']
                    if ('all' in mon_geofences or
                        command in mon_geofences or
                        'all' in egg_geofences or
                        command in egg_geofences or
                        'all' in raid_geofences or
                            command in raid_geofences):
                        deactivate_count += 1
                        reload = True
                        if 'all' in mon_geofences:
                            mon_geofences = list(geofences.keys()).remove(
                                command)
                        elif command in mon_geofences:
                            mon_geofences.remove(command)
                        if 'all' in egg_geofences:
                            egg_geofences = list(geofences.keys()).remove(
                                command)
                        elif command in egg_geofences:
                            egg_geofences.remove(command)
                        if 'all' in raid_geofences:
                            raid_geofences = list(geofences.keys()).remove(
                                command)
                        elif command in raid_geofences:
                            raid_geofences.remove(command)
                    elif message.content.lower() != '!deactivate all':
                        embeds = discord.Embed(
                            description=((
                                "{} The **{}** area was not previously active " +
                                "for you."
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
        if reload:
            if all_areas is True:
                gfs = list(geofences.keys())
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
                ).format(message.author.mention, str(activate_count))),
                color=int('0x71cd40', 16)
            )
            await client.get_alarm().update(1, {
                'destination': message.channel,
                'embeds': embeds
            })
            log.info('Deactivated {} areas for {}.'.format(
                str(activate_count), message.author.display_name))
    if reload:
        client.load_filter_file(get_path(filter_file))


async def alerts(client, message, bot_number, geofences, all_areas,
                 filter_file, locale):
    with open(filter_file, encoding="utf-8") as f:
        user_filters = json.load(f, object_pairs_hook=OrderedDict)
    filters = user_filters.get(str(message.author.id))
    if filters is None:
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
            "**{}**'s Pokemon Alert Settings:\nBOT NUMBER: {}\nPAUSED: "
        ).format(message.author.mention, str(bot_number + 1)))
        if filters['monsters']['enabled'] is True:
            alerts += "**TRUE**\n\n"
        else:
            alerts += "**FALSE**\n\n"
        if all_areas is True:
            alerts += '__PAUSED AREAS__\n\n```\n'
            if len(filters['monsters']['defaults']['geofences']) == len(
                    geofences):
                alerts += 'None\n'
            else:
                for area in list(
                        set(geofences.keys()) - set(filters['monsters'][
                            'defaults']['geofences'])):
                    alerts += '{}, '.format(area)
        else:
            alerts += '__ALERT AREAS__\n\n```\n'
            if len(filters['monsters']['defaults']['geofences']) == 0:
                alerts += (
                    "You don't any areas set.  Type `!activate [area/all]` " +
                    "in #custom_filters to set one! \n"
                )
            else:
                for area in filters['monsters']['defaults']['geofences']:
                    alerts += '{}, '.format(area)
        alerts = alerts[:-2] + '\n```\n'
        alerts += '__POKEMON__\n\n```\n'
        if '000' in filters['monsters']['filters']:
            alerts += 'Default (all unlisted): '
            if int(filters['monsters']['filters']['000']['min_iv']) > 0:
                alerts += '{}%+, '.format(
                    filters['monsters']['filters']['000']['min_iv'])
            if int(filters['monsters']['filters']['000']['min_cp']) > 0:
                alerts += '{}CP+, '.format(
                    filters['monsters']['filters']['000']['min_cp'])
            if int(filters['monsters']['filters']['000']['min_lvl']) > 0:
                alerts += 'L{}+, '.format(
                    filters['monsters']['filters']['000']['min_lvl'])
            alerts = alerts[:-2] + '\n\n'
        else:
            alerts += 'Default: None\n\n'
        for pkmn_id in range(721):
            if ('000' in filters['monsters']['filters'] and
                    pkmn_id in filters['monsters']['filters']['monsters']):
                continue
            elif '{:03}'.format(pkmn_id) not in filters['monsters']['filters']:
                if '000' in filters['monsters']['filters']:
                    alerts += '{}: None\n'.format(
                        locale.get_pokemon_name(pkmn_id))
                else:
                    continue
            else:
                alerts += '{}: '.format(locale.get_pokemon_name(pkmn_id))
                for filt_name in filters['monsters']['filters']:
                    if filt_name.startswith('{:03}'.format(pkmn_id)):
                        if (int(filters['monsters']['filters'][filt_name][
                                'min_iv']) == 0 and
                            int(filters['monsters']['filters'][filt_name][
                                'min_cp']) == 0 and
                            int(filters['monsters']['filters'][filt_name][
                                'min_lvl']) == 0 and
                            filters['monsters']['filters'][filt_name][
                                'genders'] is None):
                            alerts += 'All  '
                        else:
                            if int(filters['monsters']['filters'][filt_name][
                                    'min_iv']) > 0:
                                alerts += '{}%+, '.format(filters['monsters'][
                                    'filters'][filt_name]['min_iv'])
                            if int(filters['monsters']['filters'][filt_name][
                                    'min_cp']) > 0:
                                alerts += '{}CP+, '.format(filters['monsters'][
                                    'filters'][filt_name]['min_cp'])
                            if int(filters['monsters']['filters'][filt_name][
                                    'min_lvl']) > 0:
                                alerts += 'L{}+, '.format(filters['monsters'][
                                    'filters'][filt_name]['min_lvl'])
                            if filters['monsters']['filters'][filt_name][
                                    'genders'] is not None:
                                if filters['monsters']['filters'][filt_name][
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
    filters = user_filters.get(str(message.author.id))
    areas = '__AVAILABLE AREAS__ (Your active areas are in **bold**.)\n\n'
    for gf in list(geofences.keys()):
        if (filters is not None and
                gf in filters['monsters']['defaults']['geofences']):
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
