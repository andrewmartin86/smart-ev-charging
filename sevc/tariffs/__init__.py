import sevc
import uuid as py_uuid

from datetime import datetime
from datetime import timedelta
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from dateutil.tz import UTC


class Tariff:
    """An abstract for an electricity tariff"""

    uuid: str = ''
    name: str = ''

    _rates: List[Dict[str, Union[datetime, float]]] = []

    __module: str = ''
    __class: str = ''

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
            self.__module = 'sevc.tariffs.' + self.__class__.__module__

        if 'class' in array:
            self.__class = array['class']
        else:
            self.__class = self.__class__.__name__

        if 'name' in array:
            self.name = array['name']
        else:
            self.name = sevc.name_object(self.__class__)

        self._rates = []
        if 'rates' in array:
            for rate in array['rates']:
                self._rates.append({
                    'start': datetime.fromtimestamp(rate['start'], UTC),
                    'end': datetime.fromtimestamp(rate['end'], UTC),
                    'rate': float(rate['rate'])
                })

    def update_rates(self) -> None:
        """Update the unit rates"""
        pass

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        rtn = {
            'module': self.__module,
            'class': self.__class,
            'name': self.name,
            'rates': []
        }

        for rate in self._rates:
            rtn['rates'].append({
                'start': int(rate['start'].timestamp()),
                'end': int(rate['end'].timestamp()),
                'rate': float(rate['rate'])
            })

        return rtn

    def optimal_charge_time(self, length: timedelta, finish: datetime) -> datetime:
        """Calculate the optimal start time for a charge"""

        now = datetime.now(UTC)

        if now + length >= finish:
            return now

        self._clear_rates()
        rates = []

        for rate in self._rates:
            if rate['start'] > finish:
                continue

            rates.append(rate)

        rates[0]['start'] = now
        rates[-1]['end'] = finish

        if rates[0]['start'] + length >= finish:
            return rates[0]['start']

        optimal_time = None
        optimal_cost = None

        for start in rates:
            if start['start'] + length > finish:
                continue

            cost = 0
            time = start['start']

            for rate in rates:
                if rate['start'] < start['start']:
                    continue

                full_period_cost = rate['rate'] * (rate['end'] - rate['start']).seconds / 3600

                if start['start'] + length >= rate['end']:
                    cost += full_period_cost
                    continue

                if start['rate'] <= rate['rate']:
                    cost += rate['rate'] * (length - (rate['start'] - start['start'])).seconds / 3600
                    break

                cost += full_period_cost
                cost -= start['rate'] * (start['end'] - start['start']).seconds / 3600
                cost += start['rate'] * (length - (rate['end'] - start['end'])).seconds / 3600

                time = rate['end'] - length
                break

            if optimal_cost is None or cost < optimal_cost:
                optimal_cost = cost
                optimal_time = time

        return optimal_time

    def _clear_rates(self) -> None:
        """Clear historic rates"""

        if len(self._rates) == 0:
            return

        rates = []
        now = datetime.now(UTC)

        for rate in self._rates:
            if rate['end'] < now:
                continue

            rates.append(rate)

        self._rates = rates
