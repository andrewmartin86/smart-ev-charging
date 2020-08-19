import os

from sevc.settings import Settings


base_dir = os.path.realpath(os.path.dirname(__file__) + '/..')

if not os.path.isdir(base_dir + '/var'):
    os.mkdir(base_dir + '/var', 0o777)

settings = Settings(base_dir + '/var/sevc.json')

for uuid in settings.tariffs:
    settings.tariffs[uuid]()

for uuid in settings.vehicles:
    settings.vehicles[uuid](settings.locations, settings.tariffs)
