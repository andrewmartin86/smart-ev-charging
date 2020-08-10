import importlib
import importlib.util
import inspect
import pkgutil
import sevc

from datetime import datetime
from datetime import timedelta
from typing import Dict
from typing import List
from typing import Optional
from typing import Union


class Tariff:
    _name: str = ''
    _rates: List[Dict[str, Union[datetime, float]]] = []

    __module: str = ''
    __class: str = ''

    def __init__(self, array: Optional[dict] = None):
        if array is None:
            array = {}

        if 'name' in array:
            self._name = array['name']
        else:
            self._name = input('Please enter a name for this tariff: ')

        self._rates = []
        if 'rates' in array:
            for rate in array['rates']:
                self._rates.append({
                    'start': datetime.utcfromtimestamp(rate['start']),
                    'end': datetime.utcfromtimestamp(rate['end']),
                    'rate': float(rate['float'])
                })

        if 'module' in array:
            self.__module = array['module']
        else:
            self.__module = 'sevc.tariffs.' + self.__class__.__module__

        if 'class' in array:
            self.__class = array['class']
        else:
            self.__class = self.__class__.__name__

    def update_rates(self) -> None:
        """Update the unit rates"""
        pass

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        rates = []

        for rate in self._rates:
            rates.append({
                'start': rate['start'].timestamp(),
                'end': rate['end'].timestamp(),
                'rate': float(rate['rate'])
            })

        return {
            'module': self.__module,
            'class': self.__class,
            'name': self._name,
            'rates': rates
        }

    def optimal_charge_time(self, length: timedelta, finish: datetime) -> datetime:
        """Calculate the optimal start time for a charge"""

        now = datetime.utcnow()

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

                if start['start'] + length < rate['end']:
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

        rates = []
        now = datetime.utcnow()

        for rate in self._rates:
            if rate['end'] < now:
                continue

            rates.append(rate)

        self._rates = rates


def create() -> Tariff:
    """Choose a class to create a new instance"""

    print()

    classes = []
    i = 0

    for importer, modname, ispkg in pkgutil.iter_modules(__path__):
        spec = importer.find_spec(modname)
        module = spec.loader.load_module(modname)
        members = inspect.getmembers(module, lambda member: sevc.is_subclass_of(member, Tariff))

        for name, obj in members:
            i += 1
            print(str(i) + ': ' + name)

            classes.append({
                'module': module,
                'class': name
            })

    class_id = input("""
Please choose a tariff type: """)

    class_def = classes[int(class_id) - 1]
    module = class_def['module']
    cls = getattr(module, class_def['class'])
    return cls()


def from_dict(array: dict) -> Tariff:
    """Create an object from a dictionary"""

    module = importlib.import_module(array['module'])
    cls = getattr(module, array['class'])
    return cls(array)
