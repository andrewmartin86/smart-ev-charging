import argparse
import os
import sys

import sevc
from sevc.locations import Location
from sevc.settings import Settings
from sevc.tariffs import Tariff
from sevc.vehicles import Vehicle

arg_parser = argparse.ArgumentParser(description='Optimise electric vehicle charging to cheapest rates')

action_group = arg_parser.add_mutually_exclusive_group()

action_group.add_argument(
    '-s',
    '--list',
    action='store_true',
    help='Combine with -l, -t and/or -v (with optional ID) to list those assets. Omit -l/-t/-v to list everything.'
)

action_group.add_argument(
    '-n',
    '--new',
    action='store_true',
    help='Must be combined with -l, -t and/or -v (without an ID) to create a new asset.'
)

action_group.add_argument(
    '-d',
    '--delete',
    action='store_true',
    help='Must be combined with -l, -t and/or -v (with an ID) to delete that asset.'
)

arg_parser.add_argument('-l', '--location', type=int, nargs='*', default=None)
arg_parser.add_argument('-t', '--tariff', type=int, nargs='*', default=None)
arg_parser.add_argument('-v', '--vehicle', type=int, nargs='*', default=None)

try:
    args = arg_parser.parse_args()
except argparse.ArgumentError:
    print('Invalid arguments')
    sys.exit(2)

action_defined = args.list or args.new or args.delete
asset_defined = args.location is not None or args.tariff is not None or args.vehicle is not None

if action_defined != asset_defined and not args.list:
    print('Invalid arguments')
    sys.exit(2)

base_dir = os.path.realpath(os.path.dirname(__file__) + '/..')

if not os.path.isdir(base_dir + '/var'):
    os.mkdir(base_dir + '/var', 0o777)

settings = Settings(base_dir + '/var/sevc.json')

if not action_defined:
    for uuid in settings.tariffs:
        settings.tariffs[uuid]()

    for uuid in settings.vehicles:
        settings.vehicles[uuid](settings.locations, settings.tariffs)

    sys.exit(0)

if args.list:
    if args.location is not None or not asset_defined:
        print('LOCATIONS')
        i = 0
        for uuid in settings.locations:
            i += 1
            if args.location is not None and len(args.location) > 0 and i not in args.location:
                continue
            print(str(i) + ': ' + settings.locations[uuid].name)
        print()

    if args.tariff is not None or not asset_defined:
        print('TARIFFS')
        i = 0
        for uuid in settings.tariffs:
            i += 1
            if args.tariff is not None and len(args.tariff) > 0 and i not in args.tariff:
                continue
            print(str(i) + ': ' + settings.tariffs[uuid].name)
        print()

    if args.vehicle is not None or not asset_defined:
        print('VEHICLES')
        i = 0
        for uuid in settings.vehicles:
            i += 1
            if args.vehicle is not None and len(args.vehicle) > 0 and i not in args.vehicle:
                continue
            print(str(i) + ': ' + settings.vehicles[uuid].name)
        print()

    sys.exit(0)

if args.delete:
    if (args.location is not None and len(args.location) == 0)\
            or (args.tariff is not None and len(args.tariff) == 0)\
            or (args.vehicle is not None and len(args.vehicle) == 0):
        print('Missing IDs')
        sys.exit(2)

    if args.location is not None:
        i = 0
        to_delete = []
        print('Deleting locations...')
        for uuid in settings.locations:
            i += 1
            if i in args.location:
                print(settings.locations[uuid].name)
                to_delete.append(uuid)
        for uuid in to_delete:
            settings.locations.pop(uuid)
        print()

    if args.tariff is not None:
        i = 0
        to_delete = []
        print('Deleting tariffs...')
        for uuid in settings.tariffs:
            i += 1
            if i in args.tariff:
                deleting = True
                for loc in settings.locations:
                    if settings.locations[loc].tariff == uuid:
                        print('Cannot delete ' + settings.tariffs[uuid].name)
                        deleting = False
                        break
                if deleting:
                    print(settings.tariffs[uuid].name)
                    to_delete.append(uuid)
        for uuid in to_delete:
            settings.tariffs.pop(uuid)
        print()

    if args.vehicle is not None:
        i = 0
        to_delete = []
        print('Deleting vehicles...')
        for uuid in settings.vehicles:
            i += 1
            if i in args.vehicle:
                print(settings.vehicles[uuid].name)
                to_delete.append(uuid)
        for uuid in to_delete:
            settings.vehicles.pop(uuid)
        print()

    settings.save()
    sys.exit(0)

if args.new:
    if args.tariff is not None:
        tariff = sevc.instantiate_subclass(Tariff)
        settings.tariffs[tariff.uuid] = tariff

    if args.location is not None:
        location = sevc.instantiate_subclass(Location)
        settings.locations[location.uuid] = location

    if args.vehicle is not None:
        vehicle = sevc.instantiate_subclass(Vehicle)
        settings.vehicles[vehicle.uuid] = vehicle

    settings.save()
    sys.exit(0)
