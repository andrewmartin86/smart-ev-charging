import importlib
import json
import sevc.tariffs


class Settings:
    __filename = None

    locations = []
    tariffs = []
    vehicles = []

    def __init__(self, filename):
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

        for location in parsed['locations']:
            self.locations.append(location)

        for tariff in parsed['tariffs']:
            self.tariffs.append(sevc.tariffs.from_dict(tariff))

        for vehicle in parsed['vehicles']:
            self.vehicles.append(vehicle)

    def __del__(self):
        self.save()

    def dict(self):
        locations = []
        for location in self.locations:
            locations.append(location)

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

    def save(self):
        file = open(self.__filename, 'w')
        file.write(json.dumps(self.dict(), separators=(',', ':')))
        file.close()
