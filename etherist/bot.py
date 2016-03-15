import os
import time
import telepot
import shelve
import click
import visualize
import re
from datetime import datetime
import const

class Bot:

    def __init__(self, analytics, token):
        self.analytics = analytics
        def on_trigger(operation, trigger, ticker):
            self.trigger_alert(operation, trigger, ticker)
        self.analytics.on_trigger = on_trigger
        self.bot = telepot.Bot(token)
        self.me = self.bot.getMe()
        self.bot.notifyOnMessage(self._on_message)
        self.db = shelve.open(const.DATA_DIR + '/bot.shelve.db')
        self.visualize = visualize.Visualize()
        self._set_alert_triggers()
        click.echo("Telegram Bot running as @{}".format(self.me['username']))

    def run(self):
        while 1:
            time.sleep(10)

    def help(self, user_id):
        self.bot.sendMessage(user_id,
            "Dear chap, I'm here to keep you up to date on everything related to the Ethereum currency.\n\n" +
            "/price - Get latest ETH/BTC price information\n" +
            "/candlesticks - Get candlestick charts\n" +
            "/alerts - Set price alerts\n" +
            "/settings - Change Settings\n" +
            "\nETH data used comes from the awesome Poloniex exchange", reply_markup=self._default_reply_markup())

    def trigger_alert(self, operation, trigger, ticker):
        user_id = trigger['user_id']
        alerts = self._get_user_setting(user_id, 'alerts', [])
        updates = False
        for alert in alerts:
            executed = alert.get('executed', False)
            if alert['threshold'] == trigger['threshold'] and alert['value'] == trigger['value']:
                if operation == 'activate' and executed == False:
                    threshold_text = const.THRESHOLDS[alert['threshold']][1]
                    text = '{} alert! {} {}'.format(alert['type'].capitalize(), threshold_text, alert['value'])
                    text += '\n'
                    text += self._price_text()
                    self.bot.sendMessage(user_id, text)
                    alert['executed'] = True
                    updates = True
                if operation == 'deactivate' and executed == True:
                    alert['executed'] = False
                    updates = True
        if updates == True:
            self._set_user_setting(user_id, 'alerts', alerts)

    def price(self, user_id):
        text = self._price_text()
        self.bot.sendMessage(user_id, text)

    def candlesticks(self, user_id, interval):
        response = self.bot.sendMessage(user_id, "Generating chart..", reply_markup=self._default_reply_markup())
        time_range = self._interval_to_seconds(interval)
        interval = 60
        time_series = self.analytics.ticker_time_series(interval=interval, time_range=time_range)
        filename = "candlesticks-" + str(time_range) + "-" + str(interval) + ".png"
        self.visualize.candlestick_chart(time_series, show=False, filename=filename)
        fd = open(const.DATA_DIR + '/' + filename, 'rb')
        response = self.bot.sendPhoto(user_id, fd)

    def settings(self, user_id):
        self.bot.sendMessage(user_id, "Not implemented yet :)")

    def alerts(self, user_id):
        reply_markup = {'keyboard': [['Back'], ['New Alert', 'Clear Alerts']], 'resize_keyboard': True}
        alerts = self._get_user_setting(user_id, 'alerts', [])
        if len(alerts) == 0:
            alerts_text = 'No alerts configured yet'
        else:
            alerts_text = 'Configured alerts:\n'
            for alert in alerts:
                alerts_text += '- {} alert when price {} {}\n'.format(alert['type'], alert['threshold'], alert['value'])
        self.bot.sendMessage(user_id, alerts_text, reply_markup=reply_markup)

    def new_alert(self, user_id, capture):
        if len(capture) == 0:
            reply_markup = {
                'keyboard': [
                    ['Back'],
                    [const.THRESHOLDS[const.THRESHOLD_PRICE_ABOVE][0]],
                    [const.THRESHOLDS[const.THRESHOLD_PRICE_BELOW][0]]
                ],
                'resize_keyboard': True
            }
            self._set_user_setting(user_id, 'capture', ['new-alert'])
            self.bot.sendMessage(user_id, "Choose a threshold", reply_markup=reply_markup)
        elif len(capture) == 2:
            reply_markup = {'keyboard': [['Back']], 'resize_keyboard': True}
            self._set_user_setting(user_id, 'capture', capture)
            self.bot.sendMessage(user_id, capture[1] + " what value should I alert you?", reply_markup=reply_markup)
        elif len(capture) == 3:
            threshold = None
            for key in const.THRESHOLDS:
                if const.THRESHOLDS[key][0] == capture[1]:
                    threshold = key
            alert = {'type': 'price', 'threshold': threshold, 'value': float(capture[2])}
            self._unset_user_setting(user_id, 'capture')
            self.bot.sendMessage(user_id, "Awesome, {} {}, I will alert you.".format(capture[1], capture[2]), reply_markup=self._default_reply_markup())
            alerts = self._get_user_setting(user_id, 'alerts', [])
            alerts.append(alert)
            self._set_user_setting(user_id, 'alerts', alerts)
            self._set_alert_triggers()

    def clear_alerts(self, user_id):
        self._unset_user_setting(user_id, 'alerts')
        self.bot.sendMessage(user_id, "Cleared out all configured alerts.", reply_markup=self._default_reply_markup())

    def _set_alert_triggers(self):
        self.analytics.triggers = []
        for user_id in self.db:
            alerts = self._get_user_setting(user_id, 'alerts', [])
            for alert in alerts:
                alert['user_id'] = user_id
            self.analytics.triggers = self.analytics.triggers + alerts

    def _interval_to_seconds(self, interval):
        return int(interval[0:len(interval)-1])*60

    def _ts_to_date_str(self, ts):
        return datetime.fromtimestamp(int(ts)/1000).strftime('%Y-%m-%d %H:%M:%S')

    def _fuzzy_match(self, text, strs):
        for str in strs:
            if text.lower().strip() == str:
                return True
            if text.lower().strip() == ('/' + str):
                return True
        return False

    def _default_reply_markup(self):
        return {'keyboard': [['Price', 'Candlesticks'], ['Alerts', 'Settings']], 'resize_keyboard': True}

    def _on_message(self, msg):
        click.echo(click.style("Received message: %s" % msg, fg='black'))
        text = msg['text']
        user_id = msg['from']['id']
        arguments = text.split(' ')
        if len(arguments) == 0:
            return
        command = arguments[0]
        if self._fuzzy_match(text, ["back", "help", "start"]):
            self.help(user_id)
            self._unset_user_setting(user_id, 'capture')
        capture = self._get_user_setting(user_id, 'capture', [])
        if len(capture) > 0 and capture[0] == 'new-alert':
            capture.append(text)
            self.new_alert(user_id, capture)
            return
        if self._fuzzy_match(text, ["price"]):
            self.price(user_id)
        if self._fuzzy_match(text, ["settings"]):
            self.settings(user_id)
        if self._fuzzy_match(text, ["alerts"]):
            self.alerts(user_id)
        if self._fuzzy_match(text, ["new alert"]):
            self.new_alert(user_id, [])
        if self._fuzzy_match(text, ["clear alerts"]):
            self.clear_alerts(user_id)
        if re.compile('^[0-9]+m$').match(command):
            self.candlesticks(user_id, command)
        if self._fuzzy_match(text, ["candlesticks"]):
            reply_markup = {'keyboard': [['Back'], ['5m','60m'], ['10m','120m']], 'resize_keyboard': True}
            self.bot.sendMessage(user_id, "What timeframe?", reply_markup=reply_markup)

    def _price_text(self):
        try:
            last_ticker = self.analytics.get_ticker()
            text = "Last price: %s\n" % last_ticker['last']
            text += "24H Low: %s\n" % last_ticker['low24hr']
            text += "24H High: %s\n" % last_ticker['high24hr']
            text += "Last update: %s\n" % self._ts_to_date_str(last_ticker['_ts'])
        except KeyError:
            text = "No ticker data available currently"
        return text

    def _get_user_setting(self, user_id, key, new_value=None):
        settings = self.db.get(str(user_id), {})
        return settings.get(key, new_value)

    def _set_user_setting(self, user_id, key, value):
        settings = self.db.get(str(user_id), {})
        settings[key] = value
        self.db[str(user_id)] = settings
        self.db.sync()

    def _unset_user_setting(self, user_id, key):
        settings = self.db.get(str(user_id), {})
        try:
            del settings[key]
        except KeyError:
            pass
        self.db[str(user_id)] = settings
        self.db.sync()
