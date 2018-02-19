import logging
import json
from glob import glob
from .GenUtils import get_path
from .. import Unknown

log = logging.getLogger('GenUtils')


def get_monster_id(pokemon_name):
    try:
        name = str(pokemon_name).lower()
        if not hasattr(get_monster_id, 'ids'):
            get_monster_id.ids = {}
            files = glob(get_path('locales/*.json'))
            for file_ in files:
                with open(file_, 'r') as f:
                    j = json.loads(f.read())
                    j = j['pokemon']
                    for id_ in j:
                        nm = j[id_].lower()
                        get_monster_id.ids[nm] = int(id_)

        if name in get_monster_id.ids:
            return get_monster_id.ids[name]
        else:
            return int(name)
    except ValueError:
        raise ValueError((
            "Unable to interpret `{}` as a valid  monster name or id."
        ).format(pokemon_name))


def get_gender_sym(gender):
    gender = str(gender).lower()
    if gender == '?':
        return '?'
    elif gender == '1' or gender == 'male':
        return u'\u2642'
    elif gender == '2' or gender == 'female':
        return u'\u2640'
    elif gender == '3' or gender == 'neutral':
        return u'\u26b2'
    else:
        raise ValueError((
            "Unable to interpret `{}` as a supported  gender name or id."
        ).format(gender))


def get_move_type(move_id):
    if not hasattr(get_move_type, 'info'):
        get_move_type.info = {}
        file_ = get_path('data/move_info.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
        for id_ in j:
            get_move_type.info[int(id_)] = j[id_]['type']
    return get_move_type.info.get(move_id, Unknown.SMALL)


def get_move_damage(move_id):
    if not hasattr(get_move_damage, 'info'):
        get_move_damage.info = {}
        file_ = get_path('data/move_info.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
        for id_ in j:
            get_move_damage.info[int(id_)] = j[id_]['damage']
    return get_move_damage.info.get(move_id, 'unkn')


def get_move_dps(move_id):
    if not hasattr(get_move_dps, 'info'):
        get_move_dps.info = {}
        file_ = get_path('data/move_info.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
        for id_ in j:
            get_move_dps.info[int(id_)] = j[id_]['dps']
    return get_move_dps.info.get(move_id, 'unkn')


def get_move_duration(move_id):
    if not hasattr(get_move_duration, 'info'):
        get_move_duration.info = {}
        file_ = get_path('data/move_info.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
        for id_ in j:
            get_move_duration.info[int(id_)] = j[id_]['duration']
    return get_move_duration.info.get(move_id, 'unkn')


def get_move_energy(move_id):
    if not hasattr(get_move_energy, 'info'):
        get_move_energy.info = {}
        file_ = get_path('data/move_info.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
        for id_ in j:
            get_move_energy.info[int(id_)] = j[id_]['energy']
    return get_move_energy.info.get(move_id, 'unkn')


def get_base_height(pokemon_id):
    if not hasattr(get_base_height, 'info'):
        get_base_height.info = {}
        file_ = get_path('data/base_stats.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
        for id_ in j:
            get_base_height.info[int(id_)] = j[id_].get('height')
    return get_base_height.info.get(pokemon_id)


def get_base_weight(pokemon_id):
    if not hasattr(get_base_weight, 'info'):
        get_base_weight.info = {}
        file_ = get_path('data/base_stats.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
        for id_ in j:
            get_base_weight.info[int(id_)] = j[id_].get('weight')
    return get_base_weight.info.get(pokemon_id)


def get_base_stats(pokemon_id):
    if not hasattr(get_base_stats, 'info'):
        get_base_stats.info = {}
        file_ = get_path('data/base_stats.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
        for id_ in j:
            get_base_stats.info[int(id_)] = {
                "attack": float(j[id_].get('attack')),
                "defense": float(j[id_].get('defense')),
                "stamina": float(j[id_].get('stamina'))
            }
    return get_base_stats.info.get(pokemon_id)


def get_pokemon_cp_range(pokemon_id, level):
    stats = get_base_stats(pokemon_id)
    if not hasattr(get_pokemon_cp_range, 'info'):
        get_pokemon_cp_range.info = {}
        file_ = get_path('data/cp_multipliers.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
        for lvl_ in j:
            get_pokemon_cp_range.info[lvl_] = j[lvl_]

    cp_multi = get_pokemon_cp_range.info["{}".format(level)]
    min_cp = int(
        ((stats['attack'] + 10.0) * pow((stats['defense'] + 10.0), 0.5)
         * pow((stats['stamina'] + 10.0), 0.5) * pow(cp_multi, 2)) / 10.0)
    max_cp = int(
        ((stats['attack'] + 15.0) * pow((stats['defense'] + 15.0), 0.5) *
         pow((stats['stamina'] + 15.0), 0.5) * pow(cp_multi, 2)) / 10.0)
    return min_cp, max_cp


def get_size_id(size_name):
    try:
        name = str(size_name).lower()
        if not hasattr(get_size_id, 'sizes'):
            get_size_id.ids = {}

            files = glob(get_path('locales/*.json'))
            for file_ in files:
                with open(file_, 'r') as f:
                    j = json.loads(f.read())
                    j = j['sizes']
                    for id_ in j:
                        nm = j[id_].lower()
                        get_size_id.ids[nm] = int(id_)

        if name in get_size_id.ids:
            return get_size_id.ids[name]
        else:
            return int(name)
    except Exception:
        raise ValueError((
            "Unable to interpret `{}` as a valid size name or id."
        ).format(size_name))


def size_ratio(pokemon_id, height, weight):
    height_ratio = height / get_base_height(pokemon_id)
    weight_ratio = weight / get_base_weight(pokemon_id)
    return height_ratio + weight_ratio


def get_pokemon_size(pokemon_id, height, weight):
    size = size_ratio(pokemon_id, height, weight)
    if size < 1.5:
        return 1
    elif size <= 1.75:
        return 2
    elif size <= 2.25:
        return 3
    elif size <= 2.5:
        return 4
    else:
        return 5


def is_weather_boosted(pokemon_id, weather_id):
    if not hasattr(is_weather_boosted, 'info'):
        is_weather_boosted.info = {}
        file_ = get_path('data/weather_boosts.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
        for w_id in j:
            is_weather_boosted.info[w_id] = j[w_id]
    boosted_types = is_weather_boosted.info.get(str(weather_id), {})
    types = get_base_types(pokemon_id)
    return types[0] in boosted_types or types[1] in boosted_types


def get_base_types(pokemon_id):
    if not hasattr(get_base_types, 'info'):
        get_base_types.info = {}
        file_ = get_path('data/base_stats.json')
        with open(file_, 'r') as f:
            j = json.loads(f.read())
            for id_ in j:
                get_base_types.info[int(id_)] = [
                    j[id_].get('type1'),
                    j[id_].get('type2')
                ]
    return get_base_types.info.get(pokemon_id)


def get_type_emoji(type_id):
    return {
        1: "<:type_normal:408293834305306624>",
        2: "<:type_fighting:408293833747595275>",
        3: "<:type_flying:408293834024419328>",
        4: "<:type_poison:408293833990864898>",
        5: "<:type_ground:408293834112630784>",
        6: "<:type_rock:408293834284335106>",
        7: "<:type_bug:408293832451686403>",
        8: "<:type_ghost:408293833663578113>",
        9: "<:type_steel:408293834297180160>",
        10: "<:type_fire:408293833680486401>",
        11: "<:type_water:408293834200449024>",
        12: "<:type_grass:408293834242523136>",
        13: "<:type_electric:408293833864904704>",
        14: "<:type_psychic:408293833802121220>",
        15: "<:type_ice:408293833885876235>",
        16: "<:type_dragon:408293833512845312>",
        17: "<:type_fairy:408293834397712384>",
        18: "<:type_dark:408293833055666176>"
    }.get(type_id, '')


def get_color(color_id):
    try:
        if float(color_id) == 1:
            return 0xffb3d9
        elif float(color_id) == 2:
            return 0xff3377
        elif float(color_id) == 3:
            return 0xffcc99
        elif float(color_id) == 4:
            return 0xffcc33
        elif float(color_id) == 5:
            return 0x660066
        elif float(color_id) < 25:
            return 0x9d9d9d
        elif float(color_id) < 50:
            return 0xffffff
        elif float(color_id) < 82:
            return 0x1eff00
        elif float(color_id) < 90:
            return 0x0070dd
        elif float(color_id) < 100:
            return 0xa335ee
        elif float(color_id) == 100:
            return 0xff8000
    except ValueError:
        return 0x4F545C
