import os
import time
import telepot
import shelve
import click
import visualize
from datetime import datetime

DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../data'

class Bot:

    def __init__(self, analytics, token):
        self.analytics = analytics
        self.bot = telepot.Bot(token)
        self.me = self.bot.getMe()
        self.bot.notifyOnMessage(self._on_message)
        self.db = shelve.open(DATA_DIR + '/bot.shelve.db')
        self.visualize = visualize.Visualize()
        click.echo("Telegram Bot running as @{}".format(self.me['username']))

    def run(self):
        while 1:
            time.sleep(10)

    def help(self, user_id):
        self.bot.sendMessage(user_id,
            "Hi there, I'm here to keep you up to date on everything related to the Ethereum currency\n" +
            "Here are some commands:\n\n" +
            "/price  -  Get latest ETH/BTC price information\n" +
            "/candlesticks 10m  -  Get candlestick chart for last 10 minutes\n" +
            "\nAll information used comes from the http://poloniex.com/ exchange")

    def price(self, user_id):
        try:
            last_ticker = self.analytics.get_ticker()
            text = "Last price: %s\n" % last_ticker['last']
            text += "24H Low: %s\n" % last_ticker['low24hr']
            text += "24H High: %s\n" % last_ticker['high24hr']
            text += "Last update: %s\n" % self._ts_to_date_str(last_ticker['_ts'])
        except KeyError:
            text = "No ticker data available currently"
        self.bot.sendMessage(user_id, text)

    def candlesticks(self, user_id, arguments):
        interval = '10m'
        if len(arguments) > 0:
            interval = arguments[0]
        time_range = self._interval_to_seconds(interval)
        interval = 60
        time_series = self.analytics.ticker_time_series(interval=interval, time_range=time_range)
        filename = "candlesticks-" + str(time_range) + "-" + str(interval) + ".png"
        self.visualize.candlestick_chart(time_series, show=False, filename=filename)
        fd = open(DATA_DIR + '/' + filename, 'rb')
        response = self.bot.sendPhoto(user_id, fd)

    def _interval_to_seconds(self, interval):
        return int(interval[0:len(interval)-1])*60

    def _ts_to_date_str(self, ts):
        return datetime.fromtimestamp(int(ts)/1000).strftime('%Y-%m-%d %H:%M:%S')

    def _on_message(self, msg):
        click.echo(click.style("Received message: %s" % msg, fg='black'))
        text = msg['text']
        user_id = msg['from']['id']
        arguments = text.split(' ')
        if len(arguments) == 0:
            return
        command = arguments[0]
        if command == '/help' or command == '/start':
            self.help(user_id)
        if command == '/price':
            self.price(user_id)
        if command == '/candlesticks':
            self.candlesticks(user_id, arguments[1:])
