import operator
from .BaseFilter import BaseFilter
from ..Utilities.MonUtils import get_monster_id
from ..Utilities.GymUtils import get_team_id, create_regex, match_regex_dict


class RaidFilter(BaseFilter):

    def __init__(self, name, data):
        super(RaidFilter, self).__init__(name)
        self.mon_ids = self.evaluate_attribute(
            event_attribute='mon_id',
            eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(get_monster_id, 'monsters', data)
        )
        self.exclude_mon_ids = self.evaluate_attribute(
            event_attribute='mon_id',
            eval_func=lambda d, v: not operator.contains(d, v),
            limit=BaseFilter.parse_as_set(
                get_monster_id, 'monsters_exclude', data)
        )
        self.min_lvl = self.evaluate_attribute(
            event_attribute='raid_lvl',
            eval_func=operator.le,
            limit=BaseFilter.parse_as_type(int, 'min_raid_lvl', data)
        )
        self.max_lvl = self.evaluate_attribute(
            event_attribute='raid_lvl',
            eval_func=operator.ge,
            limit=BaseFilter.parse_as_type(int, 'max_raid_lvl', data)
        )
        self.is_sponsor = self.evaluate_attribute(
            event_attribute='sponsor_id',
            eval_func=lambda y, x: (x > 0) == y,
            limit=BaseFilter.parse_as_type(bool, 'is_sponsor', data)
        )
        self.park_contains = self.evaluate_attribute(
            event_attribute='park',
            eval_func=match_regex_dict,
            limit=BaseFilter.parse_as_set(create_regex, 'park_contains', data)
        )
        self.old_team = self.evaluate_attribute(
            event_attribute='current_team_id',
            eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(get_team_id, 'current_teams', data)
        )
        self.geofences = BaseFilter.parse_as_list(str, 'geofences', data)
        self.custom_dts = BaseFilter.parse_as_dict(
            str, str, 'custom_dts', data)
        self.is_missing_info = BaseFilter.parse_as_type(
            bool, 'is_missing_info', data)
        for key in data:
            raise ValueError((
                "'{}' is not a recognized parameter for Raid filters"
            ).format(key))

    def to_dict(self):
        settings = {}
        if self.mon_ids is not None:
            settings['monster_ids'] = self.mon_ids
        if self.min_lvl is not None:
            settings['min_lvl'] = self.min_lvl
        if self.max_lvl is not None:
            settings['max_lvl'] = self.max_lvl
        if self.is_sponsor is not None:
            settings['is_sponsor'] = self.is_sponsor
        if self.park_contains is not None:
            settings['park_contains'] = self.park_contains
        if self.geofences is not None:
            settings['geofences'] = self.geofences
        if self.is_missing_info is not None:
            settings['is_missing_info'] = self.is_missing_info
        return settings
