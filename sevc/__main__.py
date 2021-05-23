import argparse
import os
import sys
import uuid as py_uuid

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
    settings()
    sys.exit(0)

if args.list:
    if args.location is not None or not asset_defined:
        print('LOCATIONS')
        settings.print_list(Location, args.location)
        print()

    if args.tariff is not None or not asset_defined:
        print('TARIFFS')
        settings.print_list(Tariff, args.tariff)
        print()

    if args.vehicle is not None or not asset_defined:
        print('VEHICLES')
        settings.print_list(Vehicle, args.vehicle)
        print()

    sys.exit(0)

if args.delete:
    if (args.location is not None and len(args.location) == 0)\
            or (args.tariff is not None and len(args.tariff) == 0)\
            or (args.vehicle is not None and len(args.vehicle) == 0):
        print('Missing IDs')
        sys.exit(2)

    if args.location is not None:
        print('DELETING LOCATIONS')
        settings.delete_assets(Location, args.location)
        print()

    if args.tariff is not None:
        print('DELETING TARIFFS')
        settings.delete_assets(Tariff, args.tariff)
        print()

    if args.vehicle is not None:
        print('DELETING VEHICLES')
        settings.delete_assets(Vehicle, args.vehicle)
        print()

    settings.save()
    sys.exit(0)

if args.new:
    if args.tariff is not None:
        tariff = sevc.instantiate_subclass(Tariff)
        settings.assets[str(py_uuid.uuid1())] = tariff
        settings.save()

    if args.location is not None:
        location = Location(assets=settings.assets)
        settings.assets[str(py_uuid.uuid1())] = location
        settings.save()

    if args.vehicle is not None:
        vehicle = sevc.instantiate_subclass(Vehicle)
        settings.assets[str(py_uuid.uuid1())] = vehicle
        settings.save()

    sys.exit(0)
