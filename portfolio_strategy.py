from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
import pandas as pd
from pathlib import Path
from datetime import datetime


class PandasWithPct(bt.feeds.PandasData):
    params = (('pct', 3),)
    lines = ('pct',)


class TestStrat(bt.Strategy):
    params = dict(
        return_period=5,
        num_of_coins=3,
        reserve=0.05,
        hold=5

    )

    def log(self, arg):
        print(f"{self.datetime.date()} {arg}")

    def check_bar(self):
        begin = self.p.return_period + 1
        after_begin = (len(self) - begin) % self.p.hold
        if (len(self)) == begin or (after_begin == 0):
            return True
        else:
            return False

    def __init__(self):
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.prc_target = (1 - self.p.reserve) / self.p.num_of_coins
        self.pct_rank = {d: bt.ind.PctChange(d.close, period=self.p.return_period, plot=False) for d in self.datas}

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        if self.check_bar():
            ranks = sorted(
                self.pct_rank.items(),  # get the (d, rank), pair
                key=lambda x: x[1][0],  # use rank (elem 1) and current time "0"
                reverse=True,  # highest ranked 1st ... please
            )
            self.log('DrawDown: %.2f' % self.stats.drawdown.drawdown[-1])
            self.log('MaxDrawDown: %.2f' % self.stats.drawdown.maxdrawdown[-1])
            coins_in = dict(ranks[:self.p.num_of_coins])
            coins_out = dict(ranks[self.p.num_of_coins:])
            posdata = [d for d, pos in self.getpositions().items() if pos]

            for d in (d for d in posdata if d not in coins_in):
                self.log(f'out {d._name} prc_val {coins_out[d][0]:.2f}')
                self.order_target_percent(d, target=0)
            for d in (d for d in posdata if d in coins_in):
                self.log((f"rebalancing {d._name} prc_val {coins_in[d][0]:.2f}"))
                self.order_target_percent(d, target=self.prc_target)
                del coins_in[d]
            for d in coins_in:
                self.log(f"new {d._name} prc_val {coins_in[d][0]:.2f}")
                self.order = self.order_target_percent(d, target=self.prc_target)
                self.log(f'Size: {self.position.size}')


if __name__ == '__main__':
    start_cash = 1000000
    cerebro = bt.Cerebro()
    p = Path(".//PortfolioTestData")
    start_date = datetime(2017, 3, 1).date()
    end_date = datetime(2018, 3, 1).date()
    data0 = bt.feeds.GenericCSVData(dataname="PortfolioTestData//bitcoin_daily.csv",
                                    dtformat="%Y-%m-%d",
                                    datetime=0,
                                    close=1,
                                    openinterest=2,
                                    volume=3,
                                    fromdate=start_date,
                                    todate=end_date
                                    )
    cerebro.adddata(data0, name="BTC")
    for file in p.glob("*.csv"):
        if file.name != "bitcoin_daily.csv":
            ticker = file.name.rstrip("_daily.csv")
            data = bt.feeds.GenericCSVData(dataname=file,
                                           dtformat="%Y-%m-%d",
                                           datetime=0,
                                           close=1,
                                           openinterest=2,
                                           volume=3,
                                           fromdate=start_date,
                                           todate=end_date,
                                           plot=False
                                           )
            cerebro.adddata(data, name=ticker)

    cerebro.addstrategy(TestStrat)
    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.broker.set_cash(start_cash)

    cerebro.run()
    end_val = cerebro.broker.get_value()
    print(f"PNL {end_val - start_cash}")
    cerebro.plot(volume=False)
