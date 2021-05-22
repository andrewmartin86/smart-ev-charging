import uuid as py_uuid
from typing import Optional

import requests

import sevc
from sevc.settings import Settings
from sevc.tariffs import Tariff


API_KEY = 'Av73UhSnMiyn0ikU68pvish4BGguc_C5RnatjNg4DQSUhEuv8XqojS6Axojv3LjH'


class Location:
    """A geo-location, where a vehicle can charge"""

    uuid: str = ''
    tariff: str = ''
    power: Optional[float] = None

    __name: str = ''
    __north: float = 0
    __east: float = 0
    __south: float = 0
    __west: float = 0

    def __init__(self, array: Optional[dict] = None, uuid: Optional[str] = None,
                 settings: Optional[Settings] = None):
        if array is None:
            array = {}

        if uuid is None:
            self.uuid = str(py_uuid.uuid1())
        else:
            self.uuid = uuid

        if 'name' in array:
            self.__name = array['name']
        else:
            self.__name = sevc.name_object(self.__class__)

        if 'coordinates' in array:
            self.__north, self.__east, self.__south, self.__west = array['coordinates']
        else:
            self.__obtain_coordinates()

        if 'tariff' in array:
            self.tariff = array['tariff']
        elif settings is not None:
            self.__obtain_tariff(settings)

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

    def __call__(self, settings: Settings):
        """Do nothing"""
        return

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        return {
            'name': self.__name,
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

    def __obtain_tariff(self, settings: Settings) -> None:
        """Obtain the tariff used at this location"""

        tariff_uuids = settings.uuid_dict(Tariff)

        if len(tariff_uuids) == 1:
            self.tariff = tariff_uuids[1]
            print('Automatically selected ' + str(settings.assets[self.tariff]))
        else:
            print()
            settings.print_list(Tariff)
            self.tariff = tariff_uuids[int(input('Please enter the tariff to use at this location: '))]
