from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from datetime import datetime
import backtrader as bt
from backtrader_plotting import Bokeh
from backtrader.feeds import PandasData
import pandas as pd

from backtrader.indicators import Indicator

class TwoLines(Indicator):
    '''
    Rysuje dwie linie na jednym wykresie wskaźnika
    '''
    lines = ('green_line', 'red_line')
    plotlines = dict(green_line = dict(color='lime', _name='buy_line'),
                     red_line=dict(color='red', _name='sell_line'))
    def __init__(self, green_data, red_data):
        self.lines.green_line = green_data
        self.lines.red_line = red_data


class TestStrategy(bt.Strategy):

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries

        self.dataclose = self.datas[0].close
        self.market_cap = self.datas[0].openinterest
        sma21 = bt.ind.SMA(self.dataclose, period=21)
        sma34 = bt.ind.SMA(self.dataclose, period=34)
        sma55 = bt.ind.SMA(self.dataclose, period=55)
        market_cap = bt.ind.SMA(self.market_cap, period=1, subplot=True)



if __name__ == '__main__':
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.addstrategy(TestStrategy)

    # Create a data feed
    dataframe = pd.read_csv('GeckoData/bitcoin_daily.csv',
                            header=0,
                            parse_dates=True,
                            index_col=0)
    dataframe.market_caps = dataframe.market_caps.pct_change().cumsum()
    # dataframe.to_market_caps =
    data = bt.feeds.PandasData(dataname=dataframe, close=0, openinterest=1, volume=2)

    cerebro.adddata(data)
    strats = cerebro.run()
    #strat = strats[0]
    #b = Bokeh( plot_mode='single')
    cerebro.plot()
