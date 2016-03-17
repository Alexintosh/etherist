
import tailer
import json
import time
import math
from datetime import datetime
from threading import Thread
import const

class Analytics:

    def __init__(self):
        self.data = {}
        self.triggers = []
        self.on_trigger = None

    def run(self):
        self.thread = Thread(target=self.track_ticker)
        self.thread.start()

    def get_ticker(self):
        return self.data['last_ticker']

    def ticker_time_series(self, limit=-1, now_ts=0, interval=60, time_range=3600, field='last', operations=['first', 'last', 'max', 'min'], as_datetime=False):
        if limit < 0:
            limit = self._limit_for_time_range(time_range, 'ticker')
        events = []
        for line in tailer.tail(open(const.DATA_DIR + "/ticker.jsons"), limit):
            events.append(json.loads(line))
        now = int(math.ceil(time.time()))
        if now_ts > 0:
            now = int(math.ceil(now_ts / 1000.0))
        return self._compute_time_series(events, now - time_range, now, interval, field, operations, as_datetime)

    def volume_time_series(self, limit=-1, now_ts=0, interval=60, trade_type='ask', time_range=3600, field='amount', operations=['sum'], min_amount=0, as_datetime=False):
        if limit < 0:
            limit = self._limit_for_time_range(time_range, 'trades')
        events = []
        for line in tailer.tail(open(const.DATA_DIR + "/trades.jsons"), limit):
            event = json.loads(line)
            events.append(event)
        now = int(math.ceil(time.time()))
        if now_ts > 0:
            now = int(math.ceil(now_ts / 1000.0))
        time_series = []
        from_ts = now - time_range
        to_ts = now
        for ts in range(from_ts, to_ts, interval):
            values = []
            for event in events:
                event_ts = event['_ts'] / 1000
                #print('ts', ts, event_ts, event_ts >= ts, event_ts <= (ts+interval))
                data = event.get('data', None)
                if data == None:
                    continue
                if trade_type != 'all' and data['type'] != trade_type:
                    continue
                if event_ts >= ts and event_ts <= (ts + interval):
                    value = float(data.get(field, 0.0))
                    if (value < min_amount):
                        continue
                    value = 1
                    values.append(value)
            data_points = []
            for operation in operations:
                data_point = 0
                if len(values) == 0:
                    data_point = 0
                elif operation == 'avg':
                    data_point = sum(values) / len(values)
                elif operation == 'sum':
                    data_point = sum(values)
                elif operation == 'max':
                    data_point = max(values)
                elif operation == 'min':
                    data_point = min(values)
                elif operation == 'first':
                    data_point = values[0]
                elif operation == 'last':
                    data_point = values[len(values)-1]
                data_points.append(float(data_point))
            if as_datetime == True:
                time_series.append([datetime.fromtimestamp(ts)] + data_points)
            else:
                time_series.append([ts] + data_points)
        return time_series

    def track_ticker(self):
        for line in tailer.follow(open(const.DATA_DIR + "/ticker.jsons")):
	    try:
            	ticker = json.loads(line)
            	self.data['last_ticker'] = ticker
                if self.on_trigger != None:
                    for trigger in self.triggers:
                        executed = trigger.get('executed', False)
                        last_price = float(ticker['last'])
                        if executed == False and trigger['threshold'] == const.THRESHOLD_PRICE_ABOVE and last_price > trigger['value']:
                            self.on_trigger('activate', trigger, ticker)
                        if executed == True and trigger['threshold'] == const.THRESHOLD_PRICE_ABOVE and last_price <= trigger['value']:
                            self.on_trigger('deactivate', trigger, ticker)
                        if executed == False and trigger['threshold'] == const.THRESHOLD_PRICE_BELOW and last_price < trigger['value']:
                            self.on_trigger('activate', trigger, ticker)
                        if executed == True and trigger['threshold'] == const.THRESHOLD_PRICE_BELOW and last_price >= trigger['value']:
                            self.on_trigger('deactivate', trigger, ticker)
            except ValueError:
		pass

    def _limit_for_time_range(self, time_range, type='ticker'):
        factor = 0.75
        if type == 'trades':
            factor = 13
        limit = int(round(time_range * factor))
        return limit

    def _compute_time_series(self, events, from_ts, to_ts, interval, field, operations, as_datetime):
        time_series = []
        for ts in range(from_ts, to_ts, interval):
            values = []
            for event in events:
                event_ts = event['_ts'] / 1000
                if event_ts >= ts and event_ts <= (ts + interval):
                    values.append(float(event[field]))
            data_points = []
            for operation in operations:
                data_point = 0
                if len(values) == 0:
                    data_point = 0
                elif operation == 'avg':
                    data_point = sum(values) / len(values)
                elif operation == 'sum':
                    data_point = sum(values)
                elif operation == 'max':
                    data_point = max(values)
                elif operation == 'min':
                    data_point = min(values)
                elif operation == 'first':
                    data_point = values[0]
                elif operation == 'last':
                    data_point = values[len(values)-1]
                data_points.append(float(data_point))
            if as_datetime == True:
                time_series.append([datetime.fromtimestamp(ts)] + data_points)
            else:
                time_series.append([ts] + data_points)
        return time_series
