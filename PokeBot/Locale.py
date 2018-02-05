import os
import json
import logging
from .Utilities.GenUtils import get_path

log = logging.getLogger('Locale')


class Locale(object):

    def __init__(self, language):
        with open(os.path.join(get_path('locales'), 'en.json')) as f:
            default = json.loads(f.read())
        with open(os.path.join(get_path('locales'), '{}.json'.format(
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
        self.__team_names = {}
        teams = info.get("teams", {})
        for id_, val in default["teams"].items():
            self.__team_names[int(id_)] = teams.get(id_, val)
        self.__leader_names = {}
        leaders = info.get("leaders", {})
        for id_, val in default["leaders"].items():
            self.__leader_names[int(id_)] = leaders.get(id_, val)
        self.__weather_names = {}
        weather = info.get("weather", {})
        for id_, val in default["weather"].items():
            self.__weather_names[int(id_)] = weather.get(id_, val)
        self.__size_names = {}
        sizes = info.get("sizes", {})
        for id_, val in default["sizes"].items():
            self.__size_names[int(id_)] = sizes.get(id_, val)
        self.__type_names = {}
        types = info.get("types", {})
        for id_, val in default["types"].items():
            self.__type_names[int(id_)] = types.get(id_, val)
        self.__form_names = {}
        all_forms = info.get("forms", {})
        for pkmn_id, forms in default["forms"].items():
            self.__form_names[int(pkmn_id)] = {}
            pkmn_forms = all_forms.get(pkmn_id, {})
            for form_id, form_name in forms.items():
                self.__form_names[int(pkmn_id)][int(form_id)] = pkmn_forms.get(
                    form_id, form_name)
        self.__misc = info.get('misc', {})

    def get_pokemon_name(self, pokemon_id):
        return self.__pokemon_names.get(pokemon_id, 'unknown')

    def get_move_name(self, move_id):
        return self.__move_names.get(move_id, 'unknown')

    def get_team_name(self, team_id):
        return self.__team_names.get(team_id, 'unknown')

    def get_leader_name(self, team_id):
        return self.__leader_names.get(team_id, 'unknown')

    def get_weather_name(self, weather_id):
        return self.__weather_names.get(weather_id, 'unknown')

    def get_size_name(self, size_id):
        return self.__size_names.get(size_id, 'unknown')

    def get_type_name(self, type_id):
        return self.__type_names.get(type_id, 'unknown')

    def get_form_name(self, pokemon_id, form_id):
        return self.__form_names.get(pokemon_id, {}).get(form_id, 'unknown')

    def get_boosted_text(self):
        return self.__misc.get('boosted', '')
