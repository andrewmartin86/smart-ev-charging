import dateutil.parser
import requests

from datetime import datetime
from datetime import timedelta
from requests.auth import HTTPBasicAuth
from sevc.tariffs import Tariff
from typing import Optional

from dateutil.tz import UTC


class OctopusAgileTariff(Tariff):
    """Octopus Energy's Agile tariff, which rates per half-hour, updated daily"""

    __api_endpoint: Optional[str] = None
    __api_key: Optional[str] = None
    __api_next_update: Optional[datetime] = None

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

        if 'api_next_update' in array:
            self.__api_next_update = datetime.fromisoformat(array['api_next_update']).astimezone()
        else:
            self.__api_next_update = datetime.now(UTC).astimezone()

    def __call__(self):
        """Update the rates from the API"""

        now = datetime.now(UTC).astimezone()

        if self.__api_next_update is not None and self.__api_next_update > now:
            return

        request = requests.get(self.__api_endpoint, auth=HTTPBasicAuth(self.__api_key, ''))

        if request.status_code != 200:
            return

        parsed = request.json()

        for result in parsed['results']:
            self._rates.append({
                'start': dateutil.parser.isoparse(result['valid_from']).astimezone(),
                'end': dateutil.parser.isoparse(result['valid_to']).astimezone(),
                'rate': float(result['value_inc_vat'])
            })

        self._clear_rates()

        # Updates are normally done by 4pm, so try an hour earlier
        self.__api_next_update = now.replace(hour=15, minute=0, second=0, microsecond=0)

        if self.__api_next_update <= now:
            # Today's update has already happened: wait until tomorrow
            self.__api_next_update += timedelta(days=1)

        if self.__api_next_update > rates[-1]['end']:
            # Next update is after the last rate, so do one in an hour's time
            self.__api_next_update = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        return {
            **super().dict(),
            **{
                'api_endpoint': self.__api_endpoint,
                'api_key': self.__api_key,
                'api_next_update': self.__api_next_update.astimezone().isoformat()
            }
        }

    def __obtain_api_details(self) -> None:
        """Obtain the API details"""

        print()
        print('Please log into your Octopus account then go to https://octopus.energy/dashboard/developer/')
        self.__api_endpoint = input('From Unit Rates, enter the URL: ')
        self.__api_key = input('From Authentication, enter the API key: ')
