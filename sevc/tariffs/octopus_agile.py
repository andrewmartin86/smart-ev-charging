from sevc.tariffs import Tariff

import dateutil.parser
import requests
from requests.auth import HTTPBasicAuth


class OctopusAgileTariff(Tariff):
    api_endpoint = ''
    api_key = ''

    def __init__(self, array=None):
        if array is None:
            array = {}

        super().__init__(array)

        self.api_endpoint = array['api_endpoint'] or input("""
        Log into your Octopus account and go to https://octopus.energy/dashboard/developer/
        Under Unit rates, you should see a web address.
        Please enter that here: """)

        self.api_key = array['api_key'] or input("""
        Log into your Octopus account and go to https://octopus.energy/dashboard/developer/
        Under Authentication, you should see an API key.
        Please enter that here: """)

    def dict(self):
        return super().dict() + {
            'api_endpoint': self.api_endpoint,
            'api_key': self.api_key
        }

    def update_rates(self):
        request = requests.get(self.api_endpoint, auth=HTTPBasicAuth(self.api_key, ''))

        if request.status_code != 200:
            return

        parsed = request.json()
        rates = parsed['results']
        self.rates = {}

        for rate in rates:
            time = dateutil.parser.parse(rate['valid_from'])
            self.rates[time.timestamp()] = rates['value_inc_vat']
