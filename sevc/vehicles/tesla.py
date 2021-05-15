import base64
import hashlib
import random
import requests
import string
import sevc.vehicles
import time

from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
from sevc.vehicles import Vehicle
from typing import List
from typing import Optional

from dateutil.tz import UTC
from urllib.parse import parse_qs
from urllib.parse import urlencode

API_URI = 'https://owner-api.teslamotors.com/'
CLIENT_ID = '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384'
CLIENT_SECRET = 'c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3'

AUTH_URI = 'https://auth.tesla.com/oauth2/v3/'
AUTH_CALLBACK = 'https://auth.tesla.com/void/callback'

MODEL_CODES = {
    'MDL3': 'Model 3',
    'MDLX': 'Model X',
    'MDLY': 'Model Y',
}

BATTERY_CODES = {
    'BR03': 60,
    'BR05': 75,
    'BT37': 75,
    'BT40': 40,
    'BT60': 60,
    'BT70': 70,
    'BT85': 85,
    'BTX4': 90,
    'BTX5': 75,
    'BTX6': 100,
    'BTX7': 75,
    'BTX8': 85,
    'PBT8': 85
}


class TeslaVehicle(Vehicle):
    """Tesla Model S/3/X/Y"""

    __access_token: Optional[str] = None
    __refresh_token: Optional[str] = None
    __token_expires: Optional[datetime] = None
    __vehicle_id: Optional[str] = None

    def __init__(self, array: Optional[dict] = None, uuid: Optional[str] = None):
        if array is None:
            array = {}

        if 'refresh_token' in array:
            self.__refresh_token = array['refresh_token']

        if 'token_expires' in array:
            self.__token_expires = datetime.fromisoformat(array['token_expires'])

        if 'access_token' in array:
            self.__access_token = array['access_token']
        else:
            self.__login()

        if self.__token_expires is None or self.__token_expires < datetime.now(UTC):
            self.__refresh_access_token()

        if 'vehicle_id' in array:
            self.__vehicle_id = array['vehicle_id']
        else:
            self.__obtain_vehicle_id()

        super().__init__(array, uuid)

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        return {
            **super().dict(),
            **{
                'access_token': self.__access_token,
                'refresh_token': self.__refresh_token,
                'token_expires': self.__token_expires.astimezone().replace(second=0, microsecond=0).isoformat(),
                'vehicle_id': self.__vehicle_id
            }
        }

    def _charge_requirement(self) -> Optional[float]:
        """Calculate how much charge is required"""

        if self._battery is None:
            return None

        response = self.__api_request('data_request/charge_state')

        if response is None:
            return None

        return (response['charge_limit_soc'] - response['battery_level']) * self._battery / 100

    def _position(self) -> Optional[List[float]]:
        """Get the vehicle's current position"""

        response = self.__api_request('data_request/drive_state')

        if response is None:
            return None

        return [response['latitude'], response['longitude']]

    def _start_charging(self) -> bool:
        """Start the vehicle charging"""

        return self.__api_request('command/charge_start', method='POST', result_key='result')

    def _status(self) -> int:
        """Get the vehicle's current status"""

        response = self.__api_request('data_request/drive_state')

        if response is None:
            return sevc.vehicles.UNRESPONSIVE

        if response['shift_state'] is not None:
            return sevc.vehicles.DRIVING

        response = self.__api_request('data_request/charge_state')

        if response is None:
            return sevc.vehicles.UNRESPONSIVE

        if response['charging_state'] == 'Disconnected':
            return sevc.vehicles.UNPLUGGED
        elif response['charging_state'] == 'Charging':
            return sevc.vehicles.CHARGING
        elif response['charging_state'] == 'Complete':
            return sevc.vehicles.COMPLETE
        else:
            return sevc.vehicles.WAITING

    def _wake(self) -> bool:
        """Wake up the vehicle"""

        for i in range(18):  # 18 * 10 seconds = 3 minutes
            if self.__api_request('vehicle_data') is not None:  # is the vehicle awake?
                return True

            self.__api_request('wake_up', method='POST')

            # Don't flood the API
            time.sleep(10)

        return self.__api_request('vehicle_data') is not None  # check one last time

    def __api_request(self, endpoint: str, params: Optional[dict] = None,
                      method: str = 'GET', result_key: str = 'response', vehicle_specific: bool = True):
        """Send a request to the API and return the response"""

        if params is None:
            params = {}

        if vehicle_specific and self.__vehicle_id is not None:
            # All vehicle-specific endpoints share the same node
            endpoint = 'vehicles/' + str(self.__vehicle_id) + '/' + endpoint

        request = requests.request(method, API_URI + 'api/1/' + endpoint, params=params, headers={
            'Authorization': 'Bearer ' + self.__access_token
        })

        if request.status_code != 200:
            return None

        parsed = request.json()

        if result_key in parsed:
            return parsed[result_key]

        return None

    def __login(self) -> None:
        """Log into the API to obtain an access token"""

        print()
        print('Please enter your credentials to log into Tesla.')
        print('These will be used purely to generate an API access token, and will not be stored.')

        code_verifier = ''.join(random.choice(string.hexdigits) for i in range(86))

        code_challenge = base64.b64encode(hashlib.sha256(code_verifier.encode('ascii')).hexdigest().encode('ascii'))\
            .decode('ascii')

        auth_get = {
            'client_id': 'ownerapi',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'redirect_uri': AUTH_CALLBACK,
            'response_type': 'code',
            'scope': 'openid email offline_access',
            'state': 'sevc'
        }

        form_request = requests.get(AUTH_URI + 'authorize', auth_get)

        if form_request.status_code != 200:
            return

        cookie = form_request.headers.get('set-cookie')
        hidden = BeautifulSoup(form_request.text).find('form').find_all('input', {'type': 'hidden'})
        auth_post = {}

        for field in hidden:
            auth_post[field.get('name')] = field.get('value')

        # Storing the credentials would be bad, wouldn't it?
        auth_request = requests.post(AUTH_URI + 'authorize?' + urlencode(auth_get), {
            **auth_post,
            **{
                'identity': input('Email: '),
                'credential': input('Password: ')
            }
        }, headers={
            'Cookie': cookie
        })

        if auth_request.status_code != 302:
            return

        auth_redirect = auth_request.headers.get('location')
        auth_code = parse_qs(auth_redirect)['code']

        temp_request = requests.post(AUTH_URI + 'token', json={
            'grant_type': 'authorization_code',
            'client_id': 'ownerapi',
            'code': auth_code,
            'code_verifier': code_verifier,
            'redirect_uri': AUTH_CALLBACK
        })

        if temp_request.status_code != 200:
            return

        temp_parsed = temp_request.json()
        temp_token = temp_parsed['access_token']

        token_request = requests.post(API_URI + 'oauth/token', {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }, headers={
            'Authorization': 'Bearer ' + temp_token
        })

        if token_request.status_code != 200:
            return

        token_parsed = token_request.json()

        self.__access_token = token_parsed['access_token']
        self.__refresh_token = token_parsed['refresh_token']

        # Use the day before the expiry date to make sure the token doesn't expire
        self.__token_expires = datetime.now(UTC) + timedelta(seconds=token_parsed['expires_in']) - timedelta(days=1)

    def __obtain_vehicle_id(self) -> None:
        """Obtain the vehicle ID"""

        vehicles = self.__api_request('vehicles', vehicle_specific=False)

        if vehicles is None:
            return

        i: int = 0
        print()

        for vehicle in vehicles:
            i += 1

            # The model ID is buried amongst the option codes
            vehicle['options'] = vehicle['option_codes'].split(',')
            vehicle['model'] = match_option(vehicle['options'], MODEL_CODES, 'Model S')

            if vehicle['display_name'] == '':
                print(str(i) + ': ' + vehicle['model'])
            else:
                print(str(i) + ': ' + vehicle['display_name'] + ' (' + vehicle['model'] + ')')

        vehicle = vehicles[int(input('Please choose your vehicle: ')) - 1]
        self.__vehicle_id = vehicle['id']

        if vehicle['display_name'] == '':
            self._default_name = vehicle['model']
        else:
            self._default_name = vehicle['display_name']

        self._default_battery = float(match_option(vehicle['options'], BATTERY_CODES, 0))

        if self._default_battery == 0:
            self._default_battery = None

    def __refresh_access_token(self) -> None:
        """Refresh the API access token"""

        if self.__refresh_token is None:
            # No refresh token, so log in from scratch
            return self.__login()

        request = requests.post(API_URI + 'oauth/token', {
            'grant_type': 'refresh_token',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': self.__refresh_token
        })

        if request.status_code != 200:
            return self.__login()

        parsed = request.json()

        self.__access_token = parsed['access_token']
        self.__refresh_token = parsed['refresh_token']

        # Use the day before the expiry date to make sure the token doesn't expire
        self.__token_expires = datetime.now(UTC) + timedelta(seconds=parsed['expires_in']) - timedelta(days=1)


def match_option(options: List[str], match: dict, default=None):
    """Match option codes"""

    for code in match:
        if code in options:
            return match[code]

    return default
