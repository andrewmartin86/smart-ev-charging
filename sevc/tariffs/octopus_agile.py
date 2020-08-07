from sevc.tariffs import Tariff

import dateutil.parser
import dateutil.tz.tz
import requests
import requests.auth


class OctopusAgileTariff(Tariff):
    api_endpoint = ''
    api_key = ''

    def __init__(self, array=None):
        if array is None:
            array = {}

        super().__init__(array)

        if 'api_endpoint' in array:
            self.api_endpoint = array['api_endpoint']
        else:
            self.api_endpoint = input("""
Log into your Octopus account and go to https://octopus.energy/dashboard/developer/
Under Unit rates, you should see a web address.
Please enter that here: """)

        if 'api_key' in array:
            self.api_key = array['api_key']
        else:
            self.api_key = input("""
Log into your Octopus account and go to https://octopus.energy/dashboard/developer/
Under Authentication, you should see an API key.
Please enter that here: """)

    def dict(self):
        return {
            **super().dict(),
            **{
                'api_end_point': self.api_endpoint,
                'api_key': self.api_key
            }
        }

    def update_rates(self):
        request = requests.get(self.api_endpoint, auth=requests.auth.HTTPBasicAuth(self.api_key, ''))

        if request.status_code != 200:
            return

        parsed = request.json()
        self._clear_rates()

        for result in parsed['results']:
            self.rates.append({
                'start': dateutil.parser.isoparse(result['valid_from']).astimezone(dateutil.tz.UTC),
                'end': dateutil.parser.isoparse(result['valid_to']).astimezone(dateutil.tz.UTC),
                'rate': float(result['value_inc_vat'])
            })
