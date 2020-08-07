import os
import sevc.settings


base_dir = os.path.realpath(os.path.dirname(__file__) + '/..')

if not os.path.isdir(base_dir + '/var'):
    os.mkdir(base_dir + '/var', 0o777)

settings = sevc.settings.Settings(base_dir + '/var/sevc.json')
