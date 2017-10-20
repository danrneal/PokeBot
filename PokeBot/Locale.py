import os
import json
import logging
from .utils import get_path

log = logging.getLogger('Locale')


class Locale(object):

    def __init__(self, language):
        with open(os.path.join(get_path('../locales'), 'en.json')) as f:
            default = json.loads(f.read())
        with open(os.path.join(get_path('../locales'), '{}.json'.format(
                language))) as f:
            info = json.loads(f.read())
        self.__pokemon_names = {}
        pokemon = info.get("pokemon", {})
        for id_, val in default["pokemon"].items():
            self.__pokemon_names[int(id_)] = pokemon.get(id_, val)
        self.__move_names = {}
        moves = info.get("moves", {})
        for id_, val in default["moves"].items():
            self.__move_names[int(id_)] = moves.get(id_, val)
        self.__form_names = {}
        all_forms = info.get("forms", {})
        for pkmn_id, forms in default["forms"].items():
            self.__form_names[int(pkmn_id)] = {}
            pkmn_forms = all_forms.get(pkmn_id, {})
            for form_id, form_name in forms.items():
                self.__form_names[int(pkmn_id)][int(form_id)] = pkmn_forms.get(
                    form_id, form_name)

    def get_pokemon_name(self, pokemon_id):
        return self.__pokemon_names.get(pokemon_id, 'unknown')

    def get_move_name(self, move_id):
        return self.__move_names.get(move_id, 'unknown')

    def get_form_name(self, pokemon_id, form_id):
        return self.__form_names.get(pokemon_id, {}).get(form_id, '')
