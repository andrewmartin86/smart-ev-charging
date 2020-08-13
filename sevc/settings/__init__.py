import json
import sevc.tariffs

from sevc.locations import Location
from sevc.tariffs import Tariff
from typing import List


class Settings:
    __filename: str = ''

    locations: List[Location] = []
    tariffs: List[Tariff] = []
    vehicles: list = []

    def __init__(self, filename: str):
        self.__filename = filename

        try:
            file = open(self.__filename, 'r')
            raw = file.read()
            file.close()
        except IOError:
            file = open(self.__filename, 'w')
            raw = '{"locations":[],"tariffs":[],"vehicles":[]}'
            file.write(raw)
            file.close()

        parsed = json.loads(raw)

        for tariff in parsed['tariffs']:
            self.tariffs.append(sevc.tariffs.from_dict(tariff))

        if len(self.tariffs) == 0:
            self.tariffs.append(sevc.tariffs.create())

        for location in parsed['locations']:
            self.locations.append(Location(location))

        if len(self.locations) == 0:
            self.locations.append(Location(None, self.tariffs))

        for vehicle in parsed['vehicles']:
            self.vehicles.append(vehicle)

    def __del__(self):
        self.save()

    def dict(self) -> dict:
        """Output the object as a dictionary"""
        
        locations = []
        for location in self.locations:
            locations.append(location.dict())

        tariffs = []
        for tariff in self.tariffs:
            tariffs.append(tariff.dict())

        vehicles = []
        for vehicle in self.vehicles:
            vehicles.append(vehicle)

        return {
            'locations': locations,
            'tariffs': tariffs,
            'vehicles': vehicles
        }

    def save(self) -> None:
        """Save the settings to the file"""

        file = open(self.__filename, 'w')
        file.write(json.dumps(self.dict(), separators=(',', ':')))
        file.close()
