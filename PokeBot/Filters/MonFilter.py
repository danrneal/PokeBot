import operator
from .BaseFilter import BaseFilter
from ..Utilities.MonUtils import get_monster_id, get_gender_sym, get_size_id


class MonFilter(BaseFilter):

    def __init__(self, name, data):
        super(MonFilter, self).__init__(name)
        self.monster_ids = self.evaluate_attribute(
            event_attribute='monster_id',
            eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(get_monster_id, 'monsters', data)
        )
        self.exclude_monster_ids = self.evaluate_attribute(
            event_attribute='monster_id',
            eval_func=lambda d, v: not operator.contains(d, v),
            limit=BaseFilter.parse_as_set(
                get_monster_id, 'monsters_exclude', data)
        )
        self.min_lvl = self.evaluate_attribute(
            event_attribute='mon_lvl',
            eval_func=operator.le,
            limit=BaseFilter.parse_as_type(int, 'min_lvl', data)
        )
        self.max_lvl = self.evaluate_attribute(
            event_attribute='mon_lvl',
            eval_func=operator.ge,
            limit=BaseFilter.parse_as_type(int, 'max_lvl', data)
        )
        self.min_cp = self.evaluate_attribute(
            event_attribute='cp',
            eval_func=operator.le,
            limit=BaseFilter.parse_as_type(int, 'min_cp', data)
        )
        self.max_cp = self.evaluate_attribute(
            event_attribute='cp',
            eval_func=operator.ge,
            limit=BaseFilter.parse_as_type(int, 'max_cp', data)
        )
        self.min_iv = self.evaluate_attribute(
            event_attribute='iv',
            eval_func=operator.le,
            limit=BaseFilter.parse_as_type(float, 'min_iv', data)
        )
        self.max_iv = self.evaluate_attribute(
            event_attribute='iv',
            eval_func=operator.ge,
            limit=BaseFilter.parse_as_type(float, 'max_iv', data)
        )
        self.genders = self.evaluate_attribute(
            event_attribute='gender',
            eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(get_gender_sym, 'genders', data)
        )
        self.sizes = self.evaluate_attribute(
            event_attribute='size_id',
            eval_func=operator.contains,
            limit=BaseFilter.parse_as_set(get_size_id, 'sizes', data))
        self.geofences = BaseFilter.parse_as_list(str, 'geofences', data)
        self.custom_dts = BaseFilter.parse_as_dict(
            str, str, 'custom_dts', data)
        self.is_missing_info = BaseFilter.parse_as_type(
            bool, 'is_missing_info', data)
        for key in data:
            raise ValueError((
                "'{}' is not a recognized parameter for Monster filters"
            ).format(key))

    def to_dict(self):
        settings = {}
        if self.monster_ids is not None:
            settings['monster_ids'] = self.monster_ids
        if self.min_lvl is not None:
            settings['min_lvl'] = self.min_lvl
        if self.max_lvl is not None:
            settings['max_lvl'] = self.max_lvl
        if self.min_iv is not None:
            settings['min_iv'] = self.min_iv
        if self.max_iv is not None:
            settings['max_iv'] = self.max_iv
        if self.genders is not None:
            settings['genders'] = self.genders
        if self.sizes is not None:
            settings['sizes'] = self.sizes
        if self.geofences is not None:
            settings['geofences'] = self.geofences
        if self.is_missing_info is not None:
            settings['missing_info'] = self.is_missing_info
        return settings
