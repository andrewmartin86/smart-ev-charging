import dateutil.parser
import requests

from dateutil.tz import UTC
from requests.auth import HTTPBasicAuth
from sevc.tariffs import Tariff
from typing import Optional


class OctopusAgileTariff(Tariff):
    __api_endpoint: str = ''
    __api_key: str = ''

    def __init__(self, array: Optional[dict] = None):
        if array is None:
            array = {}

        super().__init__(array)

        if 'api_endpoint' in array:
            self.__api_endpoint = array['api_endpoint']
        else:
            self.__api_endpoint = input("""
Log into your Octopus account and go to https://octopus.energy/dashboard/developer/
Under Unit Rates, you should see a web address.
Please enter that here: """)

        if 'api_key' in array:
            self.__api_key = array['api_key']
        else:
            self.__api_key = input("""
Log into your Octopus account and go to https://octopus.energy/dashboard/developer/
Under Authentication, you should see an API key.
Please enter that here: """)

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        return {
            **super().dict(),
            **{
                'api_endpoint': self.__api_endpoint,
                'api_key': self.__api_key
            }
        }

    def update_rates(self) -> None:
        """Update the rates from the API"""

        request = requests.get(self.__api_endpoint, auth=HTTPBasicAuth(self.__api_key, ''))

        if request.status_code != 200:
            return

        parsed = request.json()
        self._clear_rates()

        for result in parsed['results']:
            self._rates.append({
                'start': dateutil.parser.isoparse(result['valid_from']).astimezone(UTC),
                'end': dateutil.parser.isoparse(result['valid_to']).astimezone(UTC),
                'rate': float(result['value_inc_vat'])
            })
