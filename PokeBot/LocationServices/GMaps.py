import collections
import datetime
import logging
import time
import requests
from random import randint
from requests.packages.urllib3.util.retry import Retry
from .. import Unknown

log = logging.getLogger('Gmaps')


class GMaps(object):

    _queries_per_second = 50
    _query_warning_window = datetime.timedelta(minutes=5)

    def __init__(self, api_key):
        self._key = api_key
        self._session = self._create_session()
        self._window = collections.deque(maxlen=self._queries_per_second)
        self._time_limit = time.time()
        self._reverse_geocode_hist = {}

    @staticmethod
    def _create_session(retry_count=3, pool_size=3, backoff=.25):
        session = requests.Session()
        status_forcelist = [500, 502, 503, 504]
        retry_policy = Retry(
            total=retry_count,
            backoff_factor=backoff,
            status_forcelist=status_forcelist
        )
        adapter = requests.adapters.HTTPAdapter(
            max_retries=retry_policy,
            pool_connections=pool_size,
            pool_maxsize=pool_size
        )
        session.mount('https://', adapter)
        return session

    def _make_request(self, service, params=None):
        if len(self._window) == self._queries_per_second:
            elapsed_time = time.time() - self._window[0]
            if elapsed_time > 1:
                time.sleep(1 - elapsed_time)
        url = u'https://maps.googleapis.com/maps/api/{}/json'.format(service)
        if params is None:
            params = {}
        params['key'] = self._key[randint(0, len(self._key) - 1)]
        self._window.append(time.time())
        request = self._session.get(url, params=params, timeout=3)
        if not request.ok:
            request.raise_for_status()
        body = request.json()
        if body['status'] == "OK" or body['status'] == "ZERO_RESULTS":
            return body
        elif body['status'] == "OVER_QUERY_LIMIT":
            self._time_limit = time.time() + datetime.timedelta(minutes=10)
            raise UserWarning(u'API Limit reached.')
        else:
            raise ValueError(u'Unexpected response status:\n {}'.format(body))

    _reverse_geocode_defaults = {
        'street_num': Unknown.SMALL,
        'street': Unknown.REGULAR,
        'address': Unknown.REGULAR,
        'address_eu': Unknown.REGULAR,
        'postal': Unknown.REGULAR,
        'neighborhood': Unknown.REGULAR,
        'sublocality': Unknown.REGULAR,
        'city': Unknown.REGULAR,
        'county': Unknown.REGULAR,
        'state': Unknown.REGULAR,
        'country': Unknown.REGULAR
    }

    def reverse_geocode(self, latlng, language='en'):
        latlng = u'{:.5f},{:.5f}'.format(latlng[0], latlng[1])
        if latlng in self._reverse_geocode_hist:
            return self._reverse_geocode_hist[latlng]
        dts = self._reverse_geocode_defaults.copy()
        try:
            params = {'latlng': latlng, 'language': language}
            response = self._make_request('geocode', params)
            response = response.get('results', [])
            response = response[0] if len(response) > 0 else {}
            details = {}
            for item in response.get('address_components'):
                for category in item['types']:
                    details[category] = item['short_name']
            dts['street_num'] = details.get('street_number', Unknown.EMPTY)
            dts['street'] = details.get('route', Unknown.EMPTY)
            dts['address'] = "{} {}".format(dts['street_num'], dts['street'])
            dts['address_eu'] = "{} {}".format(
                dts['street'], dts['street_num'])
            dts['postal'] = details.get('postal_code', Unknown.REGULAR)
            dts['neighborhood'] = details.get(
                'neighborhood', dts['street'])
            dts['sublocality'] = details.get('sublocality', Unknown.REGULAR)
            dts['city'] = details.get(
                'locality', details.get('postal_town', Unknown.REGULAR))
            dts['county'] = details.get(
                'administrative_area_level_2', Unknown.REGULAR)
            dts['state'] = details.get(
                'administrative_area_level_1', Unknown.REGULAR)
            dts['country'] = details.get('country', Unknown.REGULAR)
            self._reverse_geocode_hist[latlng] = dts
        except requests.exceptions.HTTPError as e:
            log.error("Reverse Geocode failed with HTTPError: {}".format(
                e.message))
        except requests.exceptions.Timeout as e:
            log.error((
                "Reverse Geocode failed with connection issues: {}"
            ).format(e.message))
        except UserWarning:
            log.error("Reverse Geocode failed because of exceeded quota.")
        except Exception as e:
            log.error((
                "Reverse Geocode failed because unexpected error has " +
                "occurred: {} - {}"
            ).format(type(e).__name__, e.message))
        return dts
