import requests
import uuid as py_uuid

from sevc.tariffs import Tariff
from typing import Dict
from typing import List
from typing import Optional


class Location:
    uuid: str = ''
    name: str = ''
    tariff: str = ''

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
            self.name = input('Please enter a name for this location: ')

        if 'coordinates' in array:
            self.__north, self.__east, self.__south, self.__west = array['coordinates']
        else:
            coordinates = find_coordinates(input('Please enter an accurate location: '))
            if coordinates is not None:
                self.__north, self.__east, self.__south, self.__west = coordinates

        if 'tariff' in array:
            self.tariff = array['tariff']
        else:
            print()
            tariff_uuids: List[str] = []
            t: int = 0

            for tariff_uuid in tariffs:
                tariff_uuids.append(tariff_uuid)
                t += 1
                print(str(t) + ': ' + tariffs[tariff_uuid].name)

            self.tariff = tariff_uuids[int(input('Please enter the tariff to use at this location: ')) - 1]

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        return {
            'name': self.name,
            'tariff': self.tariff,
            'coordinates': [self.__north, self.__east, self.__south, self.__west]
        }

    def position_match(self, lat: float, long: float) -> bool:
        """Are the given coordinates in this location?"""
        return self.__south <= lat <= self.__north\
            and (self.__west <= long <= self.__east) == (self.__east > self.__west)


def find_coordinates(search: str) -> Optional[List[float]]:
    """Fetch coordinates from a search query"""

    request = requests.get('https://dev.virtualearth.net/REST/v1/Locations', {
        'query': search,
        'key': 'Av73UhSnMiyn0ikU68pvish4BGguc_C5RnatjNg4DQSUhEuv8XqojS6Axojv3LjH'
    })

    if request.status_code != 200:
        return None

    parsed = request.json()

    for resource_set in parsed['resourceSets']:
        for resource in resource_set['resources']:
            return resource['bbox']

    return None
