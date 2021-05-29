import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode

import requests
from dateutil.tz import UTC

import sevc
from sevc.vehicles import Vehicle


CLIENT_ID = '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384'
CLIENT_SECRET = 'c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3'

AUTH_VERIFIER = '9CFc7d5A8BF3abAbFfD5b42B25aEB0f5a5ffcbb86eF9cBcA43AD2A7c86C6f8DfdA6e04ED62fAfDAe3897ee'
AUTH_CHALLENGE = 'YzJmOTM2YTBhMTA2OWNlN2IwZDgwMzY1OWU1MjkwYzM2ZjdkNTk3NWQxMmFjNzkzOTdiOTc0YzM5OTcyY2MyZg=='

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

    def __init__(self, array: Optional[dict] = None):
        if array is None:
            array = {}

        if 'refresh_token' in array:
            self.__refresh_token = array['refresh_token']

        if 'token_expires' in array:
            self.__token_expires = datetime.fromisoformat(array['token_expires']).astimezone(UTC)

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

        super().__init__(array)

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        return {
            **super().dict(),
            **{
                'access_token': self.__access_token,
                'refresh_token': self.__refresh_token,
                'token_expires': self.__token_expires.astimezone(UTC).replace(second=0, microsecond=0).isoformat(),
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

        request = requests.request(
            method,
            'https://owner-api.teslamotors.com/api/1/' + endpoint,
            params=params,
            headers={'Authorization': 'Bearer ' + self.__access_token}
        )

        if request.status_code != 200:
            return None

        parsed = request.json()

        if result_key in parsed:
            return parsed[result_key]

        return None

    def __login(self) -> None:
        """Log into the API to obtain an access token"""

        auth_get = {
            'client_id': 'ownerapi',
            'code_challenge': AUTH_CHALLENGE,
            'code_challenge_method': 'S256',
            'redirect_uri': 'https://auth.tesla.com/void/callback',
            'response_type': 'code',
            'scope': 'openid email offline_access',
            'state': 'sevc'
        }

        print()
        print('In Chrome or another Chromium-based browser, open the developer tools by pressing F12.')
        print('In the browser, go to the below address and follow Tesla\'s login process.')
        print()
        print('https://auth.tesla.com/oauth2/v3/authorize?' + urlencode(auth_get))
        print()
        print('Once logged in, you\'ll end up with a 404 Page Not Found message.')
        print('In Developer tools, go to the Network tab. Look for a request beginning with callback?code=')
        print('Right-click on that request, copy the full URL and paste it below.')

        callback = input('Callback: ')
        callback_parsed = parse_qs(callback)

        if 'code' in callback_parsed:
            auth_code = callback_parsed['code']
        elif auth_get['redirect_uri'] + '?code' in callback_parsed:
            auth_code = callback_parsed[auth_get['redirect_uri'] + '?code']
        else:
            print()
            print('No auth code found in callback')
            return

        outer_response = requests.post('https://auth.tesla.com/oauth2/v3/token', json={
            'grant_type': 'authorization_code',
            'client_id': 'ownerapi',
            'code': auth_code,
            'code_verifier': AUTH_VERIFIER,
            'redirect_uri': auth_get['redirect_uri']
        })

        if outer_response.status_code != 200:
            print()
            print('Bad authorization code response')
            return

        outer_parsed = outer_response.json()
        outer_token = outer_parsed['access_token']
        self.__refresh_token = outer_parsed['refresh_token']

        inner_response = requests.post('https://owner-api.teslamotors.com/oauth/token', {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }, headers={
            'Authorization': 'Bearer ' + outer_token
        })

        if inner_response.status_code != 200:
            print()
            print('Bad access token response')
            return

        inner_parsed = inner_response.json()

        self.__access_token = inner_parsed['access_token']

        # Use the day before the expiry date to make sure the token doesn't expire
        self.__token_expires = datetime.now(UTC) + timedelta(seconds=inner_parsed['expires_in']) - timedelta(days=1)

    def __obtain_vehicle_id(self) -> None:
        """Obtain the vehicle ID"""

        vehicles: List[Dict[str, str]] = self.__api_request('vehicles', vehicle_specific=False)

        if vehicles is None:
            return

        if len(vehicles) == 1:
            vehicle: Dict[str, str] = vehicles[0]

            # The model ID is buried amongst the option codes
            model: str = match_option(vehicle['option_codes'].split(','), MODEL_CODES, 'Model S')

            if vehicle['display_name'] == '':
                print('Automatically selected ' + model)
            else:
                print('Automatically selected ' + vehicle['display_name'] + ' (' + model + ')')

        else:
            i: int = 0
            print()

            for vehicle in vehicles:
                i += 1

                # The model ID is buried amongst the option codes
                model: str = match_option(vehicle['option_codes'].split(','), MODEL_CODES, 'Model S')

                if vehicle['display_name'] == '':
                    print(str(i) + ': ' + model)
                else:
                    print(str(i) + ': ' + vehicle['display_name'] + ' (' + model + ')')

            vehicle = vehicles[int(input('Please choose your vehicle: ')) - 1]

        self.__vehicle_id = vehicle['id']

        if vehicle['display_name'] == '':
            self._default_name = match_option(vehicle['option_codes'].split(','), MODEL_CODES, 'Model S')
        else:
            self._default_name = vehicle['display_name']

        self._default_battery = float(match_option(vehicle['option_codes'].split(','), BATTERY_CODES, 0))

        if self._default_battery == 0:
            self._default_battery = None

    def __refresh_access_token(self) -> None:
        """Refresh the API access token"""

        if self.__refresh_token is None:
            # No refresh token, so log in from scratch
            return self.__login()

        outer_request = requests.post('https://auth.tesla.com/oauth2/v3/token', json={
            'grant_type': 'refresh_token',
            'client_id': 'ownerapi',
            'refresh_token': self.__refresh_token,
            'scope': 'openid email offline_access'
        })

        if outer_request.status_code != 200:
            return self.__login()

        outer_parsed = outer_request.json()

        outer_token = outer_parsed['access_token']
        self.__refresh_token = outer_parsed['refresh_token']

        inner_request = requests.post('https://owner-api.teslamotors.com/oauth/token', {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }, headers={
            'Authorization': 'Bearer ' + outer_token
        })

        if inner_request.status_code != 200:
            return self.__login()

        inner_parsed = inner_request.json()

        self.__access_token = inner_parsed['access_token']

        # Use the day before the expiry date to make sure the token doesn't expire
        self.__token_expires = datetime.now(UTC) + timedelta(seconds=inner_parsed['expires_in']) - timedelta(days=1)


def match_option(options: List[str], match: dict, default=None):
    """Match option codes"""

    for code in match:
        if code in options:
            return match[code]

    return default
