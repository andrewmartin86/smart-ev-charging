import json


class Settings:
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

    def __repr__(self):
        return json.dumps({
            'tariffs': json.loads(repr(self.tariffs)),
            'vehicles': json.loads(repr(self.vehicles))
        })

    def __del__(self):
        file = open(self.filename, 'w')
        file.write(repr(self))
        file.close()
