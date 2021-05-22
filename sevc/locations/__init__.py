import uuid as py_uuid
from typing import Dict, Optional

import requests

import sevc
from sevc.tariffs import Tariff


API_KEY = 'Av73UhSnMiyn0ikU68pvish4BGguc_C5RnatjNg4DQSUhEuv8XqojS6Axojv3LjH'


class Location:
    """A geo-location, where a vehicle can charge"""

    uuid: str = ''
    name: str = ''
    tariff: str = ''
    power: Optional[float] = None

    __north: float = 0
    __east: float = 0
    __south: float = 0
    __west: float = 0

    def __init__(self, array: Optional[dict] = None, uuid: Optional[str] = None,
                 tariffs: Optional[Dict[str, Tariff]] = None):
        if array is None:
            array = {}

        if tariffs is None:
            tariffs = []

        if uuid is None:
            self.uuid = str(py_uuid.uuid1())
        else:
            self.uuid = uuid

        if 'name' in array:
            self.name = array['name']
        else:
            self.name = sevc.name_object(self.__class__)

        if 'coordinates' in array:
            self.__north, self.__east, self.__south, self.__west = array['coordinates']
        else:
            self.__obtain_coordinates()

        if 'tariff' in array:
            self.tariff = array['tariff']
        else:
            self.__obtain_tariff(tariffs)

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

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        return {
            'name': self.name,
            'tariff': self.tariff,
            'coordinates': [self.__north, self.__east, self.__south, self.__west],
            'power': self.power
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

    def __obtain_tariff(self, tariffs: Dict[str, Tariff]) -> None:
        print()
        tariff_uuids = sevc.print_list(tariffs)

        if len(tariff_uuids) == 1:
            print('Pre-selecting only available tariff')
            self.tariff = tariff_uuids[1]
        else:
            self.tariff = tariff_uuids[int(input('Please enter the tariff to use at this location: '))]
