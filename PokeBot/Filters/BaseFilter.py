import logging
from .. import Unknown

log = logging.getLogger('Filter')


class BaseFilter(object):

    def __init__(self, name):
        self._name = name
        self._check_list = []
        self.is_missing_info = None

    def check_event(self, event):
        missing = False
        for check in self._check_list:
            result = check(self, event)
            if result is False:
                return False
            elif Unknown.is_(result):
                missing = True
        if (self.is_missing_info is not None and
                missing != self.is_missing_info):
            return False
        return True

    def evaluate_attribute(self, limit, eval_func, event_attribute):
        if limit is None:
            return None
        check = CheckFunction(limit, eval_func, event_attribute)
        self._check_list.append(check)
        return limit

    @staticmethod
    def parse_as_type(kind, param_name, data):
        try:
            value = data.pop(param_name, None)
            if value is None:
                return None
            else:
                return kind(value)
        except Exception:
            raise ValueError((
                'Unable to interpret the value "{}" as a valid {} for ' +
                'parameter {}.'
            ).format(value, kind, param_name))

    @staticmethod
    def parse_as_set(value_type, param_name, data):
        values = data.pop(param_name, None)
        if values is None or len(values) == 0:
            return None
        if not isinstance(values, list):
            raise ValueError((
                'The "{0}" parameter must formatted as a list containing '
                'different values. Example: "{0}": '
                '[ "value1", "value2", "value3" ]'
            ).format(param_name))
        allowed = set()
        for value in values:
            allowed.add(value_type(value))
        return allowed

    @staticmethod
    def parse_as_dict(key_type, value_type, param_name, data):
        values = data.pop(param_name, {})
        if not isinstance(values, dict):
            raise ValueError((
                'The "{0}" parameter must formatted as a dict containing '
                'key-value pairs. Example: "{0}": '
                '{{ "key1": "value1", "key2": "value2" }}'
            ).format(param_name))
        out = {}
        for k, v in values.items():
            try:
                out[key_type(k)] = value_type(v)
            except Exception:
                raise ValueError((
                    'There was an error while parsing \'"{}": "{}"\' in '
                    'parameter name "{}"'
                ).format(k, v, param_name))
        return out


class CheckFunction(object):

    def __init__(self, limit, eval_func, attr_name):
        self._limit = limit
        self._eval_func = eval_func
        self._attr_name = attr_name

    def __call__(self, filtr, event):
        value = getattr(event, self._attr_name)
        if Unknown.is_(value):
            return Unknown.TINY
        result = self._eval_func(self._limit, value)
        return result
