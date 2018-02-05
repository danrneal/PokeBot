import logging
from .Utilities.GenUtils import get_path

log = logging.getLogger('LoadConfig')


def parse_rules_file(manager, filename):
    if str(filename).lower() == 'none':
        return
    filepath = get_path(filename)
    rules = OrderedDict()
    try:
        log.info("Loading Rules from file at {}".format(filepath))
        with open(filepath, 'r') as f:
            rules = json.load(f, object_pairs_hook=OrderedDict)
            
        if type(rules) is not OrderedDict:
            log.critical(
                "Rules files must be a JSON object: { \"monsters\":[...],... }"
            )
            raise ValueError("Rules file did not contain a dict.")
    except ValueError as e:
        log.error("Encountered error while loading Rules: {}: {}".format(
            type(e).__name__, e))
        log.error(
            "PokeAlarm has encountered a 'ValueError' while loading the " +
            "Rules file. This typically means the file isn't in the " +
            "correct json format. Try loading the file contents into a " +
            "json validator."
        )
        sys.exit(1)
    try:
        load_rules_section(manager.add_monster_rule, rules.pop('monsters', {}))
        load_rules_section(manager.add_egg_rule, rules.pop('eggs', {}))
        load_rules_section(manager.add_raid_rule, rules.pop('raids', {}))
        for key in rules:
            raise ValueError((
                "Unknown Event type '{}'. Rules must be defined under the " +
                "correct event type. See example in rules.json.example."
            ).format(key))
    except Exception as e:
        log.error(
            "Encountered error while parsing Rules. This is because of a " +
            "mistake in your Rules file."
        )
        log.error("{}: {}".format(type(e).__name__, e))
        sys.exit(1)

def load_rules_section(set_rule, rules):
    for name, settings in rules.items():
        if 'filters' not in settings:
            raise ValueError("{} rule is missing a `filters` section.".format(
                name))
        if 'alarms' not in settings:
            raise ValueError("{} rule is missing an `alarms` section.".format(
                name))
        filters = settings.pop('filters')
        alarms = settings.pop('alarms')
        set_rule(name, filters, alarms)
        if len(settings) > 0:
            raise ValueError("Rule {} has unknown parameters: {}".format(
                name, settings))
