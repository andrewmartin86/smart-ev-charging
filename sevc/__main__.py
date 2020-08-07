import os
import sevc.settings


path = os.path.dirname(os.path.realpath(__file__)) + '/../var'

if not os.path.isdir(path):
    os.mkdir(path, mode=0o777)

settings = sevc.settings.Settings(path + '/sevc.json')
