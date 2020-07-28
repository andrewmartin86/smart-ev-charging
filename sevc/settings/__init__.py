import json


class Settings:
    """
    All settings.
    """
    
    filename = None

    tariffs = []
    vehicles = []

    def __init__(self, filename):
        self.filename = filename

        try:
            file = open(self.filename, 'r')
            raw = file.read()
            file.close()
        except OSError:
            file = open(self.filename, 'w')
            raw = '{"tariffs":[],"vehicles":[]}'
            file.write(raw)
            file.close()

        parsed = json.loads(raw)

        for tariff in parsed['tariffs']:
            self.tariffs.append(tariff)

        for vehicle in parsed['vehicles']:
            self.vehicles.append(vehicle)

    def dict(self):
        tariffs = []
        for tariff in self.tariffs:
            tariffs.append(tariff)

        vehicles = []
        for vehicle in self.vehicles:
            vehicles.append(vehicle)

        return {
            'tariffs': tariffs,
            'vehicles': vehicles
        }

    def save(self):
        file = open(self.filename, 'w')
        file.write(json.dumps(self.dict()))
        file.close()

    def __del__(self):
        self.save()
