import os
from pylab import *
import matplotlib.pyplot as plt
from datetime import datetime
import time
from matplotlib.dates import DateFormatter, epoch2num
from matplotlib.finance import candlestick, plot_day_summary, candlestick2
from tzlocal import get_localzone

DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../data'

class Visualize:

    def candlestick_chart(self, time_series, interval=30, show=False, filename='candlestick.png'):
        tz = get_localzone()
        xfmt = DateFormatter('%H:%M:%S', tz=tz.localize(datetime.now()).tzinfo)
        adjusted_time_series = []
        for item in time_series:
            item[0] = epoch2num(item[0])
            #Prices2.append(tuple(item))
            adjusted_time_series.append(item)
        fig, ax = plt.subplots()
        fig.subplots_adjust(bottom=0.2)

        ax.xaxis.set_major_formatter(xfmt)
        #ax.xaxis.set_major_formatter(weekFormatter)
        days_interval = interval / 86400.0
        candlestick(ax, adjusted_time_series, width=days_interval, colorup='green', colordown='red', alpha=0.9)

        ax.xaxis_date(tz=tz.zone)
        ax.autoscale_view(scaley=False)
        ax.grid(True)
        plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
        if show:
            plt.show()
        else:
            savefig(DATA_DIR + '/' + filename, bbox_inches='tight')
