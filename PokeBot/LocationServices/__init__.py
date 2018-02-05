from .GoogleMaps import GoogleMaps


def location_service_factory(kind, api_key, locale):
    if kind == "GoogleMaps":
        return GoogleMaps(api_key, locale)
    else:
        raise ValueError(
            "{} is not a valid location service!".format(kind))
