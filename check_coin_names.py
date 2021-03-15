from gecko_coin_downloader import GeckoQuotes
from coinmarketcap_scrap import coin_list
from pathlib import Path

coin_list = [coin.lower().replace(' ', '-') for coin in coin_list]
dic = {'xrp': 'ripple',
       'obyte':'byteball',
       'firstblood':'dawn',
       'storjcoin-x':'storj',
       'navcoin': 'nav-coin',
       'agoras-tokens': 'agoras',
       'chrono.tech': 'chronobank',
       'i/o-coin':'iocoin',
       'gridcoin': 'gridcoin-research',
       'bela': 'belacoin',
       'dubaicoin': 'dubaicoin-dbix'}
coin_list = [dic.get(coin, coin) for coin in coin_list]
dead_coins = []


class GQ(GeckoQuotes):
    quotes_folder = 'Gecko_coins_from_2017buble_top200'


cnt = 0
for coin in coin_list:

    p = Path(str(Path.cwd()) + f'//{GQ.quotes_folder}//{coin}_daily.csv')
    if p.exists():
        print(f'{coin} in folder skipped')
    else:
        try:
            alt = GQ(coin)
            alt.quotes_to_csv()
        except ValueError as e:
            cnt += 1
            dead_coins.append(coin)
            coin_list.remove(coin)
            print(f'{e} not downloaded symbols ({coin}): {cnt}')
