import operator
import re
from .BaseFilter import BaseFilter
from ..Utilities.GymUtils import get_team_id, match_regex_dict


class EggFilter(BaseFilter):

    def __init__(self, name, data):
        super(EggFilter, self).__init__(name)
        self.min_lvl = self.evaluate_attribute(
            event_attribute='egg_lvl',
            eval_func=operator.le,
            limit=BaseFilter.parse_as_type(int, 'min_egg_lvl', data)
        )
        self.max_lvl = self.evaluate_attribute(
            event_attribute='egg_lvl',
            eval_func=operator.ge,
            limit=BaseFilter.parse_as_type(int, 'max_egg_lvl', data)
        )
        self.gym_sponsor_index_contains = self.evaluate_attribute(
            event_attribute='gym_sponsor',
            eval_func=match_regex_dict,
            limit=BaseFilter.parse_as_set(
                re.compile, 'gym_sponsor_index_contains', data))
        self.gym_park_contains = self.evaluate_attribute(
            event_attribute='gym_park',
            eval_func=match_regex_dict,
            limit=BaseFilter.parse_as_set(
                re.compile, 'gym_park_contains', data))
        self.old_team = self.evaluate_attribute(
            event_attribute='current_team_id',
            eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(get_team_id, 'current_teams', data)
        )
        self.geofences = BaseFilter.parse_as_set(str, 'geofences', data)
        self.custom_dts = BaseFilter.parse_as_dict(
            str, str, 'custom_dts', data)
        self.is_missing_info = BaseFilter.parse_as_type(
            bool, 'is_missing_info', data)
        for key in data:
            raise ValueError((
                "'{}' is not a recognized parameter for Egg filters"
            ).format(key))

    def to_dict(self):
        settings = {}
        if self.min_lvl is not None:
            settings['min_lvl'] = self.min_lvl
        if self.max_lvl is not None:
            settings['max_lvl'] = self.max_lvl
        if self.gym_sponsor_index_contains is not None:
            settings['gym_sponsor_matches'] = self.gym_sponsor_index_contains
        if self.gym_park_contains is not None:
            settings['gym_park_matches'] = self.gym_park_contains
        if self.geofences is not None:
            settings['geofences'] = self.geofences
        if self.is_missing_info is not None:
            settings['missing_info'] = self.is_missing_info
        return settings
