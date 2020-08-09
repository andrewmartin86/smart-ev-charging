import datetime
import importlib
import importlib.util
import inspect
import pkgutil
import sys


class Tariff:
    name = ''
    rates = []

    def __init__(self, array):
        if array is None:
            array = {}

        if 'name' in array:
            self.name = array['name']
        else:
            self.name = input('Please enter a name for this tariff: ')

        self.rates = []
        if 'rates' in array:
            for rate in array['rates']:
                self.rates.append({
                    'start': datetime.datetime.utcfromtimestamp(rate['start']),
                    'end': datetime.datetime.utcfromtimestamp(rate['end']),
                    'rate': float(rate['float'])
                })

    def update_rates(self):
        pass

    def dict(self):
        rates = []

        for rate in self.rates:
            rates.append({
                'start': rate['start'].timestamp(),
                'end': rate['end'].timestamp(),
                'rate': float(rate['rate'])
            })

        return {
            'module': self.__class__.__module__,
            'class': self.__class__.__name__,
            'name': self.name,
            'rates': rates
        }

    def optimal_charge_time(self, length, finish):
        now = datetime.datetime.utcnow()

        if now + length >= finish:
            return now

        self._clear_rates()
        rates = []

        for rate in self.rates:
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

    def _clear_rates(self):
        rates = []
        now = datetime.datetime.utcnow()

        for rate in self.rates:
            if rate['end'] < now:
                continue

            rates.append(rate)

        self.rates = rates


def create():
    print()

    classes = []
    i = 0

    for importer, modname, ispkg in pkgutil.iter_modules(__path__):
        spec = importer.find_spec(modname)
        module = spec.loader.load_module(modname)
        members = inspect.getmembers(module, inspect.isclass)

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


def from_dict(array):
    module = importlib.import_module(array['module'])
    cls = getattr(module, array['class'])
    return cls(array)
