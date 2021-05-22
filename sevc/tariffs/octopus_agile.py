from datetime import datetime, timedelta
from typing import Optional

import requests
from dateutil.parser import isoparse
from dateutil.tz import UTC
from requests.auth import HTTPBasicAuth

from sevc.settings import Settings
from sevc.tariffs import Tariff


class OctopusAgileTariff(Tariff):
    """Octopus Energy's Agile tariff, which rates per half-hour, updated daily"""

    __api_endpoint: Optional[str] = None
    __api_key: Optional[str] = None

    def __init__(self, array: Optional[dict] = None, uuid: Optional[str] = None):
        if array is None:
            array = {}

        super().__init__(array, uuid)

        if 'api_endpoint' in array:
            self.__api_endpoint = array['api_endpoint']

        if 'api_key' in array:
            self.__api_key = array['api_key']

        if self.__api_endpoint is None or self.__api_key is None:
            self.__obtain_api_details()

    def call(self, settings: Settings):
        """Update the rates from the API"""

        now = datetime.now(UTC).astimezone()

        if self._next_update is not None and self._next_update > now:
            return

        request = requests.get(self.__api_endpoint, auth=HTTPBasicAuth(self.__api_key, ''))

        if request.status_code != 200:
            return

        parsed = request.json()

        for result in parsed['results']:
            self._rates.append({
                'start': isoparse(result['valid_from']).astimezone(),
                'end': isoparse(result['valid_to']).astimezone(),
                'rate': float(result['value_inc_vat'])
            })

        self._clear_rates()

        # Updates are normally done by 4pm, so try an hour earlier
        self._next_update = now.replace(hour=15, minute=0, second=0)

        if self._next_update <= now:
            # Today's update has already happened: wait until tomorrow
            self._next_update += timedelta(days=1)

        if self._next_update > self._rates[-1]['end']:
            # Next update is after the last rate, so do one in an hour's time
            self._next_update = now.replace(minute=0, second=0) + timedelta(hours=1)

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        return {
            **super().dict(),
            **{
                'api_endpoint': self.__api_endpoint,
                'api_key': self.__api_key
            }
        }

    def __obtain_api_details(self) -> None:
        """Obtain the API details"""

        print()
        print('Please log into your Octopus account then go to https://octopus.energy/dashboard/developer/')
        self.__api_endpoint = input('From Unit Rates, enter the URL: ')
        self.__api_key = input('From Authentication, enter the API key: ')
