import datetime


class Tariff:
    rates = {}

    def update_rates(self):
        pass

    def optimal_charge_time(self, length, finish):
        now = datetime.datetime.utcnow()

        if now + length >= finish:
            return now

        rates = []

        for timestamp in self.rates:
            time = datetime.datetime.utcfromtimestamp(timestamp)

            if now > time or time > finish:
                continue

            if len(rates) > 0:
                rates[-1]['end'] = time

            rates.append({
                'start': time,
                'end': None,
                'rate': self.rates[timestamp]
            })

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
