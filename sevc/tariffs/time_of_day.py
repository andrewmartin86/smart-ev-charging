from datetime import datetime, time, timedelta
from dateutil import tz
from typing import Dict, List, Optional, Union

from sevc.tariffs import Tariff


class TimeOfDayTariff(Tariff):
    """Time-of-day tariff"""

    __time_rates: List[Dict[str, Union[time, float]]] = []
    __time_zone: str = 'UTC'

    def __init__(self, array: Optional[dict] = None):
        if array is None:
            array = {}

        super().__init__(array)

        if 'time_zone' in array:
            self.__time_zone = array['time_zone']
        else:
            self.__time_zone = input('Please enter this tariff\'s time zone (e.g. Europe/London): ')

        if 'time_rates' in array:
            for rate in array['time_rates']:
                self.__time_rates.append({
                    'start': time.fromisoformat(rate['start']),
                    'end': time.fromisoformat(rate['end']),
                    'rate': float(rate['rate'])
                })
        else:
            self.__obtain_time_rates()

    def __call__(self, assets: dict):
        """Refresh the rates"""

        now = datetime.now(tz.gettz(self.__time_zone))

        if self._next_update is not None and self._next_update > now:
            return

        next_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if len(self._rates) > 0:
            next_day = self._rates[-1]['end'].astimezone(tz.gettz(self.__time_zone))

        for rate in self.__time_rates:
            new_rate = {
                'start': next_day.replace(
                    hour=rate['start'].hour,
                    minute=rate['start'].minute,
                    second=rate['start'].second
                ).astimezone(tz.UTC),
                'end': None,
                'rate': rate['rate']
            }

            if rate['end'].hour == 0 and rate['end'].minute == 0 and rate['end'].second == 0:
                new_rate['end'] = (next_day + timedelta(days=1)).astimezone(tz.UTC)
            else:
                new_rate['end'] = next_day.replace(
                    hour=rate['end'].hour,
                    minute=rate['end'].minute,
                    second=rate['end'].second
                ).astimezone(tz.UTC)

            self._rates.append(new_rate)

        self._clear_rates()

        if len(self._rates) == 0:
            self._next_update = datetime.now(tz.UTC)
        else:
            self._next_update = (self._rates[-1]['end'] - timedelta(days=1)).astimezone(tz.UTC)

    def dict(self) -> dict:
        """Output the object as a dictionary"""

        rtn = {
            **super().dict(),
            **{
                'time_rates': [],
                'time_zone': self.__time_zone
            }
        }

        for rate in self.__time_rates:
            rtn['time_rates'].append({
                'start': rate['start'].isoformat(),
                'end': rate['end'].isoformat(),
                'rate': float(rate['rate'])
            })

        return rtn

    def __obtain_time_rates(self) -> None:
        """Get time-of-day rates"""

        print()
        print('Please enter times in format 07:00, 23:00, etc, or leave blank to finish.')

        last = '00:00'

        while True:
            rate = float(input('Please enter rate as of ' + last + ': '))
            end = input('Please enter start time of next rate: ')

            if end == '':
                end = '00:00'
            elif end < last:
                continue

            self.__time_rates.append({
                'start': time.fromisoformat(last),
                'end': time.fromisoformat(end),
                'rate': rate
            })

            if end == '00:00':
                return

            last = end
