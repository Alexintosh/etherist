import os
from pylab import *
import matplotlib.pyplot as plt
from datetime import datetime
import time
import numpy as np
import seaborn as sns
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter, epoch2num
from matplotlib.finance import candlestick_ochl, volume_overlay
import const

from tzlocal import get_localzone

class Visualize:

    def bar_chart(self, time_series, interval=60, show=False, palette="BuGn_d", filename='bar_chart.png'):
        data = np.array(time_series)
        dates = [self._format_time(x, interval) for x in data[:,0]]
        sns.set(style="darkgrid")
        sns.barplot(x=dates, y=data[:,1], palette=palette)
        if show:
            plt.show()
        else:
            plt.savefig(const.DATA_DIR + '/' + filename, bbox_inches='tight')
            plt.close()

    def line_chart(self, time_series, interval=60, show=False, filename='line_chart.png'):
        data = np.array(time_series)
        dates = [datetime.fromtimestamp(x) for x in data[:,0]]
        sns.set(style="darkgrid")
        fig, ax = plt.subplots()
        plt.plot_date(x=dates, y=data[:,1], linestyle='-', markersize=6, marker='o')
        tz = get_localzone()
        ax.xaxis.set_major_formatter(self._date_formatter(interval, tz=tz))
        ax.xaxis_date(tz=tz.zone)
        if show:
            plt.show()
        else:
            plt.savefig(const.DATA_DIR + '/' + filename, bbox_inches='tight')
            plt.close()

    def candlestick_chart(self, time_series, interval=40, show=False, filename='candlestick.png', volume_overlay=None):
        tz = get_localzone()
        adjusted_time_series = []
        for item in time_series:
            item[0] = epoch2num(item[0])
            adjusted_time_series.append(item)
        fig, ax = plt.subplots()
        fig.subplots_adjust(bottom=0.2)

        ax.xaxis.set_major_formatter(self._date_formatter(interval, tz=tz))
        days_interval = interval / 86400.0
        candlestick_ochl(ax, adjusted_time_series, width=(days_interval), colorup='green', colordown='red', alpha=0.9)

        ax.xaxis_date(tz=tz.zone)
        ax.autoscale_view()
        yticks = ax.get_yticks()
        x_start = min(yticks) - ((max(yticks) - min(yticks)) * 0.60)
        plt.ylim([x_start,max(yticks)])
        ax.grid(True)
        plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
        if volume_overlay != None:
            # Add a seconds axis for the volume overlay
            ax2 = ax.twinx()

            yticks = ax.get_yticks()
            print('yticks', yticks)
            # set the position of ax2 so that it is short (y2=0.32) but otherwise the same size as ax
            ax2.set_position(matplotlib.transforms.Bbox([[0.125,0.2],[0.9,0.42]]))
            #print(days_interval * len(adjusted_time_series))
            #ax2.set_position([0.125, 0.2, 0.8, 0.2])

            # get data from candlesticks for a bar plot
            dates = [x[0] for x in adjusted_time_series]
            dates = np.asarray(dates)
            volume = [x[1] for x in volume_overlay]
            volume = np.asarray(volume)

            ax2.bar(dates,volume,color='#aaaaaa',width=(days_interval),align='center',linewidth=0.0,alpha=0.8)

            #scale the x-axis tight
            #ax2.set_xlim(min(dates),max(dates))
            # the y-ticks for the bar were too dense, keep only every third one
            ax2yticks = ax2.get_yticks()
            #print('yticks', ax2yticks)
            #print('yticks2', ax2yticks[::3])
            ax2.set_yticks(ax2yticks[::3])

            ax2.yaxis.set_label_position("right")
            ax2.set_ylabel('Volume', size=20)

            # format the x-ticks with a human-readable date.
            #xt = ax.get_xticks()
            #new_xticks = [datetime.date.isoformat(num2date(d)) for d in xt]
            #ax.set_xticklabels(new_xticks,rotation=45, horizontalalignment='right')

        if show:
            plt.show()
        else:
            plt.savefig(const.DATA_DIR + '/' + filename, bbox_inches='tight')
            plt.close()

    def _format_time(self, ts, interval=40):
        dt = datetime.fromtimestamp(ts)
        return datetime.strftime(dt, self._format_for_interval(interval))

    def _date_formatter(self, interval, tz=get_localzone()):
        return DateFormatter(self._format_for_interval(interval), tz=tz.localize(datetime.now()).tzinfo)

    def _format_for_interval(self, interval):
        format = "%H:%M"
        if interval < 40:
            format = "%H:%M:%S"
        if interval >= 3600:
            format = "%m/%d %I%p"
        return format
