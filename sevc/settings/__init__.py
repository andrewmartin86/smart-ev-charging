import json
import sevc.tariffs
import sevc.vehicles

from sevc.locations import Location
from sevc.tariffs import Tariff
from sevc.vehicles import Vehicle
from typing import Dict


class Settings:
    """Stores all locations, tariffs and vehicles"""

    __filename: str = ''

    locations: Dict[str, Location] = {}
    tariffs: Dict[str, Tariff] = {}
    vehicles: Dict[str, Vehicle] = {}

    def __init__(self, filename: str):
        self.__filename = filename

        try:
            file = open(self.__filename, 'r')
            raw = file.read()
            file.close()
        except IOError:
            file = open(self.__filename, 'w')
            raw = '{"locations":{},"tariffs":{},"vehicles":{}}'
            file.write(raw)
            file.close()

        if raw == '':
            parsed = {}
        else:
            parsed = json.loads(raw)

        if 'tariffs' in parsed:
            for uuid in parsed['tariffs']:
                self.tariffs[uuid] = sevc.object_from_dict(parsed['tariffs'][uuid], uuid)

        if len(self.tariffs) == 0:
            tariff = sevc.instantiate_subclass(Tariff)
            self.tariffs[tariff.uuid] = tariff

        if 'locations' in parsed:
            for uuid in parsed['locations']:
                self.locations[uuid] = Location(parsed['locations'][uuid], uuid)

        if len(self.locations) == 0:
            location = Location(tariffs=self.tariffs)
            self.locations[location.uuid] = location

        if 'vehicles' in parsed:
            for uuid in parsed['vehicles']:
                self.vehicles[uuid] = sevc.object_from_dict(parsed['vehicles'][uuid], uuid)

        if len(self.vehicles) == 0:
            vehicle = sevc.instantiate_subclass(Vehicle)
            self.vehicles[vehicle.uuid] = vehicle

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
        file.write(json.dumps(self.dict(), separators=(',', ':')))
        file.close()
