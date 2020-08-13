import requests

from datetime import datetime
from datetime import timedelta
from sevc.vehicles import Vehicle
from typing import Optional

from dateutil.tz import UTC


API_URI = 'https://owner-api.teslamotors.com'
CLIENT_ID = '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384'
CLIENT_SECRET = 'c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3'


class TeslaVehicle(Vehicle):
    __access_token: Optional[str] = None
    __refresh_token: Optional[str] = None
    __token_expires: Optional[datetime] = None
    __vehicle_id: Optional[str] = None

    def __init__(self, array: Optional[dict] = None, uuid: Optional[str] = None):
        if array is None:
            array = {}

        super().__init__(array, uuid)

        if 'access_token' in array:
            self.__access_token = array['access_token']
        else:
            self.__login()

        if 'refresh_token' in array:
            self.__refresh_token = array['refresh_token']

        if 'token_expires' in array:
            self.__token_expires = datetime.fromtimestamp(array['token_expires'], UTC)

        if self.__token_expires is None or self.__token_expires < datetime.now(UTC):
            self.__refresh_access_token()

        if 'vehicle_id' in array:
            self.__vehicle_id = array['vehicle_id']
        else:
            self.__obtain_vehicle_id()

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        return {
            **super().dict(),
            **{
                'access_token': self.__access_token,
                'refresh_token': self.__refresh_token,
                'token_expires': self.__token_expires.timestamp(),
                'vehicle_id': self.__vehicle_id
            }
        }

    def __api_get(self, endpoint: str, params: Optional[dict] = None):
        """Send a GET to API and return the response"""

        if params is None:
            params = {}

        request = requests.get(API_URI + '/api/1/' + endpoint, params=params, headers={
            'Authorization': 'Bearer ' + self.__access_token
        })

        if request.status_code != 200:
            return None

        return request.json()

    def __api_post(self, endpoint: str, params: Optional[dict] = None):
        """Send a POST to API and return the response"""

        if params is None:
            params = {}

        request = requests.post(API_URI + '/api/1/' + endpoint, params=params, headers={
            'Authorization': 'Bearer ' + self.__access_token
        })

        if request.status_code != 200:
            return None

        return request.json()

    def __login(self) -> None:
        """Log into the Tesla API to obtain an access token"""

        email = input("""Please enter your email address to log into Tesla: """)
        password = input("""Please enter your Tesla password: """)

        request = requests.post(API_URI + '/oauth/token', {
            'grant_type': 'password',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'email': email,
            'password': password
        })

        if request.status_code != 200:
            return

        parsed = request.json()

        self.__access_token = parsed['access_token']
        self.__refresh_token = parsed['refresh_token']
        self.__token_expires = datetime.now(UTC) + timedelta(seconds=parsed['expires_in']) - timedelta(days=1)

    def __obtain_vehicle_id(self) -> None:
        """Obtain the vehicle ID"""

        response = self.__api_get('/vehicles')

        if response is None:
            return

        i: int = 0
        print()

        for vehicle in response['response']:
            i += 1
            options = vehicle['option_codes'].split(',')

            if 'MDLX' in options:
                model = 'Model X'
            elif 'MDL3' in options:
                model = 'Model 3'
            elif 'MDLY' in options:
                model = 'Model Y'
            else:
                model = 'Model S'

            print(str(i) + ': ' + vehicle['display_name'] + ' (' + model + ')')

        self.__vehicle_id = response['response'][int(input('Please enter your vehicle: ')) - 1]['id']

    def __refresh_access_token(self) -> None:
        """Refresh the Tesla API access token"""

        if self.__refresh_token is None:
            return self.__login()

        request = requests.post(API_URI + '/oauth/token', {
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
        self.__token_expires = datetime.now(UTC) + timedelta(seconds=parsed['expires_in']) - timedelta(days=1)
