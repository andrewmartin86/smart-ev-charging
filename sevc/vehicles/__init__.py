import importlib
import inspect
import pkgutil
import sevc
import uuid as py_uuid

from datetime import datetime
from datetime import time
from datetime import timedelta
from sevc.locations import Location
from sevc.tariffs import Tariff
from typing import Dict
from typing import List
from typing import Optional

from dateutil.tz import UTC


DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

UNRESPONSIVE = 0
DRIVING = 1
OUTSIDE_LOCATIONS = 2
UNPLUGGED = 3
WAITING = 4
CHARGING = 5
COMPLETE = 6

STATUS_WAIT = {
    UNRESPONSIVE: 15,
    DRIVING: 5,
    CHARGING: 60,
    COMPLETE: 360
}


class Vehicle:
    uuid: str = ''
    name: str = ''

    __module: str = ''
    __class: str = ''
    __next_ping: Optional[datetime] = None
    __status: Optional[int] = None
    __finish_times: List[time] = []

    def __init__(self, array: Optional[dict] = None, uuid: Optional[str] = None):
        if array is None:
            array = {}

        if uuid is None:
            self.uuid = str(py_uuid.uuid1())
        else:
            self.uuid = uuid

        if 'module' in array:
            self.__module = array['module']
        else:
            self.__module = 'sevc.vehicles.' + self.__class__.__module__

        if 'class' in array:
            self.__class = array['class']
        else:
            self.__class = self.__class__.__name__

        if 'name' in array:
            self.name = array['name']
        else:
            self.name = input('Please enter a name for this vehicle: ')

        if 'finish_times' in array:
            for finish_time in array['finish_times']:
                self.__finish_times.append(time.fromisoformat(finish_time))
        else:
            last_time: Optional[str] = None
            for day in DAYS:
                if last_time is None:
                    finish_time = input('Please enter a finish time for ' + day + '\'s charge (hh:mm): ')
                else:
                    finish_time = input('Please enter a finish time for ' + day + '\'s charge (leave blank to use ' + last_time + '): ')
                    if finish_time == '':
                        finish_time = last_time

                last_time = finish_time
                self.__finish_times.append(time.fromisoformat(finish_time))

        if 'next_ping' in array:
            self.__next_ping = datetime.fromtimestamp(array['next_ping'], UTC)

        if 'status' in array:
            self.__status = int(array['status'])

    def _charge_time(self) -> Optional[timedelta]:
        """Calculate how long to charge the vehicle"""
        pass

    def _position(self) -> Optional[List[float]]:
        """Get the vehicle's current position"""
        pass

    def _start_charging(self) -> None:
        """Start the vehicle charging"""
        pass

    def _status(self) -> int:
        """Get the vehicle's status"""

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        rtn = {
            'module': self.__module,
            'class': self.__class,
            'name': self.name,
            'next_ping': self.__next_ping.timestamp(),
            'status': int(self.__status),
            'finish_times': []
        }

        for finish_time in self.__finish_times:
            rtn['finish_times'].append(finish_time.isoformat())

        return rtn

    def ping(self, locations: Dict[str, Location], tariffs: Dict[str, Tariff]) -> None:
        """Run any appropriate actions for the vehicle"""

        now = datetime.now(UTC)

        if now < self.__next_ping:
            return

        status = self._status()

        if status in STATUS_WAIT:
            self.__next_ping = now + timedelta(minutes=STATUS_WAIT[status])
            self.__status = status
            return

        position = self._position()
        location: Optional[Location] = None

        if position is not None:
            lat, long = position

            for uuid in locations:
                if locations[uuid].position_match(lat, long):
                    location = locations[uuid]
                    break

        if location is None:
            self.__next_ping = now + timedelta(hours=3)
            self.__status = OUTSIDE_LOCATIONS
            return

        if status == UNPLUGGED:
            if self.__status == UNPLUGGED:
                self.__next_ping = now + timedelta(hours=3)
            else:
                self.__next_ping = now + timedelta(minutes=10)
                self.__status = UNPLUGGED

            return

        tariff = tariffs[location.tariff]
        charge_time = self._charge_time()

        if charge_time is None:
            self._start_charging()
            self.__next_ping = now + timedelta(hours=1)
            self.__status = CHARGING
            return

        finish_time = self.__next_finish()
        start_time = tariff.optimal_charge_time(charge_time, finish_time)
        now = datetime.now(UTC)

        if start_time <= now:
            self._start_charging()
            self.__next_ping = finish_time + timedelta(minutes=30)
            self.__status = CHARGING
            return

        if now + timedelta(minutes=10) >= start_time:
            self.__next_ping = now + timedelta(minutes=1)
        else:
            self.__next_ping = finish_time - timedelta(minutes=10)

        self.__status = WAITING

    def __next_finish(self, date: Optional[datetime] = None) -> datetime:
        """Calculate the next charge finish time"""

        now = datetime.now(UTC).astimezone()

        if date is None:
            date = now

        finish = self.__finish_times[date.weekday()]
        rtn = date.replace(hour=finish.hour, minute=finish.minute, second=finish.second, microsecond=finish.microsecond)

        if rtn > now:
            return rtn.astimezone(UTC)

        return self.__next_finish(date + timedelta(days=1))


def create() -> Vehicle:
    """Choose a class to create a new instance"""

    print()
    classes = []
    i = 0

    for importer, modname, ispkg in pkgutil.iter_modules(__path__):
        spec = importer.find_spec(modname)
        module = spec.loader.load_module(modname)
        members = inspect.getmembers(module, lambda member: sevc.is_subclass_of(member, Vehicle))

        for name, obj in members:
            i += 1
            print(str(i) + ': ' + name)

            classes.append({
                'module': module,
                'class': name
            })

        class_def = classes[int(input('Please choose a vehicle type: ')) - 1]
        cls = getattr(class_def['module'], class_def['class'])
        return cls()


def from_dict(array: dict, uuid: Optional[str] = None) -> Vehicle:
    """Create an object from a dictionary"""

    cls = getattr(importlib.import_module(array['module']), array['class'])
    return cls(array, uuid=uuid)
