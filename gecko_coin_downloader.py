import pandas as pd
import time
from pathlib import Path
import pprint
from pycoingecko import CoinGeckoAPI

pd.set_option("display.max_columns", 12)
pp = pprint.PrettyPrinter(indent=4)
client = CoinGeckoAPI()


class GeckoQuotes:
    start_date = 1262300400  # 2010_01_01
    end_date = 1519772400
    quotes_folder = 'GeckoData'

    def __init__(self, ticker):
        self.ticker = ticker
        self.quotes = self.get_quotes()

    def get_quotes(self):
        return client.get_coin_market_chart_range_by_id(self.ticker, vs_currency='USD',
                                                        from_timestamp=self.start_date,
                                                        to_timestamp=self.end_date)

    def check_dir(self):
        path = Path(str(Path.cwd()) + '/' + self.quotes_folder)
        path.mkdir(exist_ok=True)

    def make_as_df(self):
        col_time = (t for t, _ in self.quotes['prices'])
        col_close = (cl for _, cl in self.quotes['prices'])
        col_market_cap = (cap for _, cap in self.quotes['market_caps'])
        col_vol = (vol for _, vol in self.quotes['total_volumes'])

        df = pd.DataFrame(data=zip(col_time, col_close, col_market_cap, col_vol),
                          columns=['time', *self.quotes.keys()]).set_index(keys='time')
        df.index = pd.to_datetime(df.index, unit='ms')
        return df

    def quotes_to_csv(self):
        self.check_dir()
        self.make_as_df().to_csv(f'{self.quotes_folder}\\{self.ticker}_daily.csv')


class GeckoUpdate(GeckoQuotes):
    start_date = 123

    def __init__(self, ticker):
        super().__init__(ticker)
        self.quotes = 123

    def get_last_time_from_csv(self, fname):
        with open(fname, 'r') as f:
            for line in reversed(f.readlines()):
                if line.strip():
                    last_time = int(line.split(',')[0]) / 1000  # sprowadzenie timestamp z milisec do sec
                    break
        return last_time

    def get_new_data(self, fname):
        return client.get_coin_market_chart_range_by_id(self.ticker, vs_currency='USD',
                                                        from_timestamp=self.get_last_time(fname),
                                                        to_timestamp=int(time.time()))

    def update_csv(self):
        new_data = self.make_as_df()


def get_top_alt_in_dataframe():
    """  Possible columns
        'id', 'symbol', 'name', 'image', 'current_price', 'market_cap', 'market_cap_rank', 'fully_diluted_valuation',
         'total_volume', 'high_24h', 'low_24h', 'price_change_24h', 'price_change_percentage_24h',
         'market_cap_change_24h', 'market_cap_change_percentage_24h', 'circulating_supply', 'total_supply',
         'max_supply', 'ath', 'ath_change_percentage', 'ath_date', 'atl', 'atl_change_percentage', 'atl_date', 'roi',
         'last_updated'
    """
    top_100 = client.get_coins_markets(vs_currency='USD')
    cols = ['id', 'market_cap', 'market_cap_rank', 'market_cap_change_percentage_24h',
            'price_change_percentage_24h', 'atl_date']
    return pd.DataFrame(((alt[cols[0]],
                          alt[cols[1]],
                          alt[cols[2]],
                          alt[cols[3]],
                          alt[cols[4]],
                          alt[cols[5]]
                          )
                         for alt in top_100), columns=cols)


def get_top_alts_names():
    return get_top_alt_in_dataframe()['id'].to_list()