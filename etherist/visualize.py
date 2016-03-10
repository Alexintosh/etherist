import os
from pylab import *
import matplotlib.pyplot as plt
from datetime import datetime
import time
from matplotlib.dates import DateFormatter, epoch2num
from matplotlib.finance import candlestick_ochl, volume_overlay

from tzlocal import get_localzone

DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../data'

class Visualize:

    def candlestick_chart(self, time_series, interval=30, show=False, filename='candlestick.png', volume_overlay=None):
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
        candlestick_ochl(ax, adjusted_time_series, width=days_interval, colorup='green', colordown='red', alpha=0.9)

        ax.xaxis_date(tz=tz.zone)
        ax.autoscale_view()
        ax.grid(True)
        plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

        if volume_overlay != None:
            # Add a seconds axis for the volume overlay
            ax2 = ax.twinx()

            # set the position of ax2 so that it is short (y2=0.32) but otherwise the same size as ax
            ax2.set_position(matplotlib.transforms.Bbox([[0.125,0.1],[0.9,0.32]]))

            # get data from candlesticks for a bar plot
            dates = [x[0] for x in adjusted_time_series]
            dates = np.asarray(dates)
            volume = [x[1] for x in volume_overlay]
            volume = np.asarray(volume)

            ax2.bar(dates,volume,color='#cccccc',width=days_interval,align='center')

            #scale the x-axis tight
            ax2.set_xlim(min(dates),max(dates))
            # the y-ticks for the bar were too dense, keep only every third one
            yticks = ax2.get_yticks()
            ax2.set_yticks(yticks[::3])

            ax2.yaxis.set_label_position("right")
            ax2.set_ylabel('Volume', size=20)

            # format the x-ticks with a human-readable date.
            #xt = ax.get_xticks()
            #new_xticks = [datetime.date.isoformat(num2date(d)) for d in xt]
            #ax.set_xticklabels(new_xticks,rotation=45, horizontalalignment='right')

        if show:
            plt.show()
        else:
            plt.savefig(DATA_DIR + '/' + filename, bbox_inches='tight')
