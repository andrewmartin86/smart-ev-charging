from datetime import tzinfo
from dateutil import tz
from typing import Dict, Optional

import requests

import sevc
from sevc.tariffs import Tariff


API_KEY = 'Av73UhSnMiyn0ikU68pvish4BGguc_C5RnatjNg4DQSUhEuv8XqojS6Axojv3LjH'


class Location:
    """A geo-location, where a vehicle can charge"""

    tariff: str = ''
    power: Optional[float] = None
    time_zone: str = 'UTC'

    __name: str = ''
    __north: float = 0
    __east: float = 0
    __south: float = 0
    __west: float = 0

    def __init__(self, array: Optional[dict] = None, assets: Optional[dict] = None):
        if array is None:
            array = {}

        if 'name' in array:
            self.__name = array['name']
        else:
            self.__name = sevc.name_object(self.__class__)

        if 'coordinates' in array:
            self.__north, self.__east, self.__south, self.__west = array['coordinates']
        else:
            self.__obtain_coordinates()

        if 'time_zone' in array:
            self.time_zone = array['time_zone']
        else:
            self.__obtain_timezone()

        if 'tariff' in array:
            self.tariff = array['tariff']
        elif assets is not None:
            self.__obtain_tariff(assets)

        if 'power' in array:
            self.power = float(array['power'])
        else:
            self.power = float(input('Please enter the power (in kW) of the charger at this location: '))

    def __contains__(self, coordinates):
        """Are the given coordinates in this location?"""

        if not isinstance(coordinates, list):
            return False

        lat, long = coordinates

        return self.__south <= lat <= self.__north\
            and (self.__west <= long <= self.__east) == (self.__east > self.__west)

    def __str__(self):
        """Return the location's name"""

        return self.__name

    def __call__(self, assets: dict):
        """Do nothing"""
        return

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        return {
            'name': self.__name,
            'tariff': self.tariff,
            'coordinates': [self.__north, self.__east, self.__south, self.__west],
            'power': self.power,
            'time_zone': self.time_zone
        }

    def __obtain_coordinates(self) -> None:
        """Obtain the coordinates for a given location"""

        location = input('Please enter an accurate location (eg a post code): ')

        request = requests.get('https://dev.virtualearth.net/REST/v1/Locations', {
            'query': location,
            'key': API_KEY
        })

        if request.status_code != 200:
            return

        parsed = request.json()

        for resource_set in parsed['resourceSets']:
            for resource in resource_set['resources']:
                self.__south, self.__west, self.__north, self.__east = resource['bbox']
                return

    def __obtain_tariff(self, assets: dict) -> None:
        """Obtain the tariff used at this location"""

        tariff_uuids: Dict[int, str] = {}
        i: int = 0

        for uuid in assets:
            if not isinstance(assets[uuid], Tariff):
                continue

            i += 1
            tariff_uuids[i] = uuid

        if len(tariff_uuids) == 1:
            self.tariff = tariff_uuids[1]
            print('Automatically selected ' + str(assets[self.tariff]))

        else:
            print()

            for i in tariff_uuids:
                print(str(i) + '. ' + str(assets[tariff_uuids[i]]))

            self.tariff = tariff_uuids[int(input('Please enter the tariff to use at this location: '))]

    def __obtain_timezone(self) -> None:
        """Obtain the timezone for this location"""

        request = requests.get(
            'https://dev.virtualearth.net/REST/v1/TimeZone/' + str(self.__north) + ',' + str(self.__west),
            {'key': API_KEY}
        )

        if request.status_code != 200:
            return

        parsed = request.json()

        for resource_sets in parsed['resourceSets']:
            for resource in resource_sets['resources']:
                self.time_zone = resource['timeZone']['ianaTimeZoneId']
                return
