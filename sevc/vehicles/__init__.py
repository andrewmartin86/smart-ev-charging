import uuid as py_uuid
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional

from dateutil.tz import UTC

import sevc
from sevc.locations import Location
from sevc.settings import Settings
from sevc.tariffs import Tariff


DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

UNRESPONSIVE = 0
DRIVING = 1
OUTSIDE_LOCATIONS = 2
UNPLUGGED = 3
WAITING = 4
CHARGING = 5
COMPLETE = 6

STATUS_WAIT = {
    UNRESPONSIVE: 15,  # give a bit of time for the vehicle to become responsive again
    DRIVING: 5,        # the vehicle status could change at any time
    CHARGING: 60,      # leave the vehicle alone while charging
    COMPLETE: 360      # the vehicle is unlikely to need charging any time soon
}


class Vehicle:
    """An abstract for an electric vehicle"""

    uuid: str = ''
    name: str = ''

    _battery: Optional[float] = None
    _default_name: Optional[str] = None
    _default_battery: Optional[float] = None

    __module: str = ''
    __class: str = ''
    __next_ping: Optional[datetime] = None
    __status: int = UNRESPONSIVE
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
            self.name = sevc.name_object(self.__class__, self._default_name)

        if 'battery' in array:
            self._battery = float(array['battery'])
        else:
            self.__obtain_battery_size()

        if 'finish_times' in array:
            for finish_time in array['finish_times']:
                self.__finish_times.append(time.fromisoformat(finish_time))
        else:
            self.__obtain_finish_times()

        if 'next_ping' in array:
            self.__next_ping = datetime.fromisoformat(array['next_ping'])
        else:
            self.__next_ping = datetime.now(UTC)

        if 'status' in array:
            self.__status = int(array['status'])

    def __call__(self, settings: Settings):
        """Run any appropriate actions for the vehicle"""

        now = datetime.now(UTC).astimezone()

        if now < self.__next_ping:
            return

        if not self._wake():
            self.__next_ping = now + timedelta(minutes=STATUS_WAIT[UNRESPONSIVE])
            self.__status = UNRESPONSIVE
            return

        status = self._status()

        if status in STATUS_WAIT:
            self.__next_ping = now + timedelta(minutes=STATUS_WAIT[status])
            self.__status = status
            return

        position = self._position()
        location: Optional[Location] = None

        if position is not None:
            for uuid in settings.assets:
                if isinstance(settings.assets[uuid], Location) and position in settings.assets[uuid]:
                    location = settings.assets[uuid]
                    break

        if location is None:
            self.__next_ping = now + timedelta(hours=3)
            self.__status = OUTSIDE_LOCATIONS
            return

        if status == UNPLUGGED:
            if self.__status == UNPLUGGED:
                self.__next_ping = now + timedelta(hours=3)
            else:
                # The vehicle has just arrived at this location, so give a bit more time to plug in
                self.__next_ping = now + timedelta(minutes=10)
                self.__status = UNPLUGGED

            return

        tariff = settings.assets[location.tariff]
        charge_time = self.__charge_time(location.power)

        if charge_time is None:
            if not self._start_charging():
                self.__next_ping = now  # try again next ping
                self.__status = WAITING
                return

            self.__next_ping = now + timedelta(hours=1)
            self.__status = CHARGING
            return

        finish_time = self.__next_finish()
        start_time = tariff.optimal_charge_time(charge_time, finish_time)
        now = datetime.now(UTC).astimezone()

        if start_time <= now and self._start_charging():
            self.__next_ping = finish_time + timedelta(minutes=30)  # leave the vehicle alone while charging
            self.__status = CHARGING
            return

        if now + timedelta(minutes=10) >= start_time:
            # Nearly time to charge: try again in a minute in case it's needed earlier
            self.__next_ping = now + timedelta(minutes=1)
        else:
            # Leave the vehicle alone until it's nearly time to charge
            self.__next_ping = start_time - timedelta(minutes=10)

        self.__status = WAITING

    def _charge_requirement(self) -> Optional[float]:
        """Calculate how much charge is required"""
        pass

    def _position(self) -> Optional[List[float]]:
        """Get the vehicle's current position"""
        pass

    def _start_charging(self) -> bool:
        """Start the vehicle charging"""
        pass

    def _status(self) -> int:
        """Get the vehicle's current status"""
        pass

    def _wake(self) -> bool:
        """Wake up the vehicle"""
        pass

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        rtn = {
            'module': self.__module,
            'class': self.__class,
            'name': self.name,
            'battery': self._battery,
            'next_ping': self.__next_ping.astimezone().replace(second=0, microsecond=0).isoformat(),
            'status': int(self.__status),
            'finish_times': []
        }

        for finish_time in self.__finish_times:
            rtn['finish_times'].append(finish_time.replace(second=0, microsecond=0).isoformat())

        return rtn

    def __charge_time(self, power: float) -> Optional[timedelta]:
        """Calculate how much time is needed to charge"""

        charge = self._charge_requirement()

        if charge is None:
            return None

        return timedelta(seconds=round(charge * 3600 / power) + 600)  # add a 10 minute buffer

    def __next_finish(self, date: Optional[datetime] = None) -> datetime:
        """Calculate the next charge finish time"""

        now = datetime.now(UTC).astimezone()

        if date is None:
            date = now

        finish = self.__finish_times[date.weekday()]
        rtn = date.replace(hour=finish.hour, minute=finish.minute, second=finish.second)

        if rtn <= now:
            # Today's finish time has already passed: return tomorrow's
            return self.__next_finish(date + timedelta(days=1))

        return rtn.astimezone(UTC)

    def __obtain_battery_size(self) -> None:
        """Get the battery size"""

        prompt = 'Please enter the vehicle\'s battery size, in kWh'

        if self._default_battery is not None:
            prompt += ' (default = ' + str(self._default_battery) + ')'

        battery = input(prompt + ': ')

        if battery == '' and self._default_battery is not None:
            self._battery = self._default_battery
            return

        self._battery = float(battery)

    def __obtain_finish_times(self) -> None:
        """Get finish times per day of week"""

        print()
        print('Please enter finish times for each day\'s charge (e.g. 07:00 or 23:00):')

        last_time: Optional[str] = None
        
        for day in DAYS:
            if last_time is None:
                finish_time = input(day + ': ')
            else:
                finish_time = input(day + ' (default = ' + last_time + '): ')

                if finish_time == '':
                    finish_time = last_time

            last_time = finish_time
            self.__finish_times.append(time.fromisoformat(finish_time))
