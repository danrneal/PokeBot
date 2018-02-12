import json
from glob import glob
from collections import OrderedDict


def get_monster_id(pokemon_name):
    try:
        name = str(pokemon_name).lower()
        if not hasattr(get_monster_id, 'ids'):
            get_monster_id.ids = {}
            files = glob('../locales/*.json')
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


def converter():
    with open('user_filters.json', encoding="utf-8") as f:
        user_filters = json.load(f)

    new_filters = {}
    for user_id in user_filters:
        user_filter = user_filters[user_id]
        print("Converting {}'s filters".format(user_id))

        new_filter = OrderedDict({
            'monsters': OrderedDict({
                'enabled': True,
                'defaults': {
                    'geofences': []
                },
                'filters': OrderedDict({})
            }),
            'eggs': OrderedDict({
                'enabled': True,
                'defaults': {
                    'geofences': []
                },
                'filters': OrderedDict({})
            }),
            'raids': OrderedDict({
                'enabled': True,
                'defaults': {
                    'geofences': []
                },
                'filters': OrderedDict({})
            })
        })

        new_filter['monsters']['enabled'] = not user_filter['paused']
        new_filter['monsters']['defaults']['geofences'] = user_filter['areas']
        new_filter['eggs']['defaults']['geofences'] = user_filter['areas']
        new_filter['raids']['defaults']['geofences'] = user_filter['areas']

        default_monsters = []
        pokemon_name = {}
        for monster in user_filter['pokemon']:
            if monster == 'default':
                pokemon = 0
            elif monster == 'enabled':
                continue
            else:
                pokemon = get_monster_id(monster)

            pokemon_name["{:03}".format(pokemon)] = monster

            if user_filter['pokemon'][monster] is True:
                default_monsters.append(pokemon)

        if len(default_monsters) > 0:
            new_filter['monsters']['filters']['000'] = {
                'monsters': default_monsters,
                'min_iv': user_filter['pokemon']['default']['min_iv'],
                'min_cp': user_filter['pokemon']['default']['min_cp'],
                'min_lvl': user_filter['pokemon']['default']['min_level'],
                'is_missing_info': False
            }

        for pokemon in range(1, 722):
            if pokemon_name.get("{:03}".format(pokemon)) is not None:
                filt = user_filter['pokemon'].get(pokemon_name[
                    "{:03}".format(pokemon)])
                if type(filt) == list:
                    suffix = ''
                    for f in filt:
                        new_filter['monsters']['filters'][
                            "{:03}{}".format(pokemon, suffix)] = {
                                'monsters': [pokemon],
                                'min_iv': f['min_iv'],
                                'min_cp': f['min_cp'],
                                'min_lvl': f['min_level'],
                                'genders': f['gender']
                            }
                        if f.get('ignore_missing') is True:
                            new_filter['monsters']['filters'][
                                "{:03}{}".format(pokemon, suffix)][
                                    'is_missing_info'] = False
                        if suffix == '':
                            suffix = 'a'
                        elif suffix == 'a':
                            suffix = 'b'

        new_filters[user_id] = new_filter

    with open('user_filters_converted.json', 'w+', encoding="utf-8") as f:
        json.dump(new_filters, f, indent=4)

    print('done.')


if __name__ == '__main__':
    converter()
