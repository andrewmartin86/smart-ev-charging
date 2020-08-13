import requests
import uuid

from sevc.tariffs import Tariff
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

    def __init__(self, array: Optional[dict] = None, tariffs: Optional[List[Tariff]] = None):
        if array is None:
            array = {}

        if tariffs is None:
            tariffs = []

        if 'uuid' in array:
            self.__uuid = array['uuid']
        else:
            self.__uuid = str(uuid.uuid1())

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
            t: int = 0

            for tariff in tariffs:
                t += 1
                print(str(t) + ': ' + tariff.name)

            tariff_id = input("""
Please enter the tariff used at this location: """)

            self.tariff = tariffs[int(tariff_id) - 1].uuid


def find_coordinates(search: str) -> Optional[List[float]]:
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
