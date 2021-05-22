import json
from json import JSONDecodeError
from typing import Dict

import sevc
from sevc.locations import Location
from sevc.tariffs import Tariff
from sevc.vehicles import Vehicle


class Settings:
    """Stores all locations, tariffs and vehicles"""

    __filename: str = ''

    locations: Dict[str, Location] = {}
    tariffs: Dict[str, Tariff] = {}
    vehicles: Dict[str, Vehicle] = {}

    def __init__(self, filename: str):
        self.__filename = filename

        parsed: dict = {}

        try:
            file = open(self.__filename, 'r')
            parsed = json.load(file)
            file.close()
        except IOError:
            self.save()
        except JSONDecodeError:
            self.save()

        if 'tariffs' in parsed:
            for uuid in parsed['tariffs']:
                self.tariffs[uuid] = sevc.object_from_dict(parsed['tariffs'][uuid], uuid)

        if 'locations' in parsed:
            for uuid in parsed['locations']:
                self.locations[uuid] = Location(parsed['locations'][uuid], uuid)

        if 'vehicles' in parsed:
            for uuid in parsed['vehicles']:
                self.vehicles[uuid] = sevc.object_from_dict(parsed['vehicles'][uuid], uuid)

    def __del__(self):
        self.save()

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        rtn = {
            'locations': {},
            'tariffs': {},
            'vehicles': {}
        }
        
        for uuid in self.locations:
            rtn['locations'][uuid] = self.locations[uuid].dict()

        for uuid in self.tariffs:
            rtn['tariffs'][uuid] = self.tariffs[uuid].dict()

        for uuid in self.vehicles:
            rtn['vehicles'][uuid] = self.vehicles[uuid].dict()

        return rtn

    def save(self) -> None:
        """Save the settings to the file"""

        file = open(self.__filename, 'w')
        json.dump(self.dict(), file, separators=(',', ':'))
        file.close()
