from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
import pandas as pd
from pathlib import Path
from datetime import datetime

from stats_functions import trade_list, trans_format
import jinja2  # to jakbym chcial poprawić output htmla

pd.set_option('colheader_justify', 'center')
pd.set_option('display.float_format', '{:,.5f}'.format)


class TestStrat(bt.Strategy):
    params = dict(
        return_period=7,
        num_of_coins=3,
        reserve=0.05,
        hold=5

    )

    def __init__(self):
        # ustalam jaki podzial procentowy kapitału do wykorzystania na jeden coin
        self.prc_target = (1 - self.p.reserve) / self.p.num_of_coins
        # tworze dictionary z wartosciamy stop zwrotu dla każdego instrumentu
        self.pct_rank = {d: bt.ind.PctChange(d.close, period=self.p.return_period, plot=False) for d in self.datas}

    def log(self, arg):
        print(f"{self.datetime.date()} {arg}")

    # Funkcja w ktorej ustawiam co ile swieczek sprawdzać warunki (parametr hold)
    def check_bar(self):
        begin = self.p.return_period + 1
        after_begin = (len(self) - begin) % self.p.hold
        if (len(self)) == begin or (after_begin == 0):
            return True
        else:
            return False

    def next(self):
        if self.check_bar():
            ranks = sorted(
                self.pct_rank.items(),
                key=lambda x: x[1][0],  # sortowanie wg klucza rank (elem 1) and obecny czas "0"
                reverse=True,
            )
            # posortowane coiny coins in - najlepsze wchodza do portela, coins_out pozostale
            coins_in = dict(ranks[:self.p.num_of_coins])
            coins_out = dict(ranks[self.p.num_of_coins:])
            posdata = [d for d, pos in self.getpositions().items() if pos]  # aktualne pozycje

            # order_target percent kupuje walor za ustaloną częśc kapitału wyrazona w %
            # Te ktore posiadamy ale juz nie sa w topie pozbywamy się:
            for d in (d for d in posdata if d not in coins_in):
                self.order_target_percent(d, target=0)
            # Te ktore posiadamy i sa dalej w topie robie rebalancing:
            for d in (d for d in posdata if d in coins_in):
                self.order_target_percent(d, target=self.prc_target)
                del coins_in[d]
            # Tych ktorych nie mamy a sa w topie kupujemy:
            for d in coins_in:
                self.order = self.order_target_percent(d, target=self.prc_target)

    def stop(self):
        self.log(f'\nPARAMETRY: Z ilu świeczek stopa zwrotu: {self.p.return_period} Ile coinow: {self.p.num_of_coins} '
                 f'Ile trzymane: {self.p.hold}     Wynik: {self.broker.getvalue():_.2f}\n'
                 f'***************************************************************************************************')


if __name__ == '__main__':
    start_cash = 10000
    cerebro = bt.Cerebro()
    # jesli chcesz optymalizować odkomentuj linijke ponizej i wykomentuj cerebro.addstrategy
    strats = cerebro.optstrategy(TestStrat, return_period=range(4, 11))
    # jezeli chcesz testować strategie z wykresami odkomentuj linijke ponizej i wykomentuj cerebro.optstrategy
    # cerebro.addstrategy(TestStrat)
    p = Path(".//PortfolioTestData")
    start_date = datetime(2017, 3, 1).date()
    end_date = datetime(2018, 3, 1).date()
    # Jesli chce wrzucic bitcoina na wykres jako głowny plot odkomentuj kod ponizej
    # data0 = bt.feeds.GenericCSVData(dataname="PortfolioTestData//bitcoin_daily.csv",
    #                                 dtformat="%Y-%m-%d",
    #                                 datetime=0,
    #                                 close=1,
    #                                 openinterest=2,
    #                                 volume=3,
    #                                 fromdate=start_date,
    #                                 todate=end_date
    #                                 )
    # cerebro.adddata(data0, name="BTC")
    for file in p.glob("*.csv"):
        # jesli rysujesz bitcoina jako głowny plot odkomentuj linijke ponizej
        # if file.name != "bitcoin_daily.csv":
        ticker = file.name.rstrip("_daily.csv")
        data = bt.feeds.GenericCSVData(dataname=file,
                                       dtformat="%Y-%m-%d",
                                       datetime=0,
                                       close=1,
                                       openinterest=2,
                                       volume=3,
                                       fromdate=start_date,
                                       todate=end_date,
                                       plot=False,
                                       reverse=False
                                       )
        cerebro.adddata(data, name=ticker)

    cerebro.broker.set_cash(start_cash)

    # Analyzers
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trans')
    cerebro.addanalyzer(trade_list, _name='trade_list')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    # Observers
    # cerebro.addobserver(bt.observers.DrawDown)

    s = cerebro.run(tradehistory=True, optreturn=False, maxcpus=1)

# Otwieram wszystkie template:
with open("OUTPUT/template/template.html", "r") as f_template, \
        open("OUTPUT/template/returns_table.html", "r") as f_returns, \
        open("OUTPUT/template/drawdown_table.html", "r") as f_drawdown:
    html_string = f_template.read()
    returns_format = f_returns.read()
    drawdown_format = f_drawdown.read()

# wrzucam statystki w html dla każdej strategi odddzielnie
for i, strategy in enumerate(s, start=1):
    output_path = f'OUTPUT/portfolio_strat_{i}'
    trans = strategy[0].analyzers.trans.get_analysis()
    trade_list = strategy[0].analyzers.trade_list.get_analysis()
    sharpe = strategy[0].analyzers.sharpe.get_analysis()
    returns = strategy[0].analyzers.returns.get_analysis()
    ddown = strategy[0].analyzers.drawdown.get_analysis()
    sqn = strategy[0].analyzers.sqn.get_analysis()
    trades_table = pd.DataFrame(trade_list)
    trans_format(trans, output_path)
    draw = drawdown_format.format(
        len=ddown['len'],
        drawdown=f"{ddown['drawdown']:,.2f}",
        moneydown=f"{ddown['moneydown']:,.2f}",
        mlen=ddown['max']['len'],
        mdrawdown=f"{ddown['max']['drawdown']:,.2f}",
        mmoneydown=f"{ddown['max']['moneydown']:,.2f}"
    )
    ret = returns_format.format(
        rtot=f"{returns['rtot']:,.4f}",
        ravg=f"{returns['ravg']:,.4f}",
        rnorm=f"{returns['rnorm']:,.4f}",
        rnorm100=f"{returns['rnorm100']:,.1f}"

    )
    with open(f"{output_path}.html", "w") as f:
        f.write(html_string.format(name=strategy[0].__class__.__name__,
                                   params=strategy[0].params._gettuple(),
                                   sqn=f"SQN: {sqn['sqn']:.2f} Trades {sqn['trades']}",
                                   table=trades_table.to_html(classes='mystyle'),
                                   sh=f"{sharpe['sharperatio']:.4f}",
                                   ret=ret,
                                   dd=draw)

                )
