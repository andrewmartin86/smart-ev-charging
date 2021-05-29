from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from dateutil.tz import UTC

import sevc


class Tariff:
    """An abstract for an electricity tariff"""

    _rates: List[Dict[str, Union[datetime, float]]] = []
    _next_update: Optional[datetime] = None

    __name: str = ''

    def __init__(self, array: Optional[dict] = None):
        if array is None:
            array = {}

        if 'name' in array:
            self.__name = array['name']
        else:
            self.__name = sevc.name_object(self.__class__)

        if 'next_update' in array:
            self._next_update = datetime.fromisoformat(array['next_update']).astimezone()
        else:
            self._next_update = datetime.now(UTC).astimezone()

        self._rates = []
        if 'rates' in array:
            for rate in array['rates']:
                self._rates.append({
                    'start': datetime.fromisoformat(rate['start']).astimezone(UTC),
                    'end': datetime.fromisoformat(rate['end']).astimezone(UTC),
                    'rate': float(rate['rate'])
                })

    def __str__(self):
        """Return the tariff's name"""

        return self.__name

    def __call__(self, assets: dict):
        """Update the tariff rates"""
        pass

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        module = self.__class__.__module__

        if not module.startswith('sevc.tariffs.'):
            module = 'sevc.tariffs.' + module

        rtn = {
            'module': module,
            'class': self.__class__.__name__,
            'name': self.__name,
            'next_update': self._next_update.astimezone(UTC).replace(second=0, microsecond=0).isoformat(),
            'rates': []
        }

        for rate in self._rates:
            rtn['rates'].append({
                'start': rate['start'].astimezone(UTC).replace(second=0, microsecond=0).isoformat(),
                'end': rate['end'].astimezone(UTC).replace(second=0, microsecond=0).isoformat(),
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

        rates = sorted(self._rates, key=lambda item: item['start'])
        self._rates = rates

        rates = []
        latest = None
        now = datetime.now(UTC)

        for rate in self._rates:
            if (latest is not None and rate['start'] == latest['start']) or rate['end'] < now:
                continue

            if latest is not None and rate['rate'] == latest['rate']:
                rates[-1]['end'] = rate['end']
                latest['end'] = rate['end']
                continue

            rates.append(rate)
            latest = rate

        self._rates = rates
