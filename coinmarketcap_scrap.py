import requests
from bs4 import BeautifulSoup
import pandas as pd


''' Obróbka strony coinmarketcap '''

url = 'https://coinmarketcap.com/historical/20170507/'
page = requests.get(url)
soup = BeautifulSoup(page.content, 'html.parser')
table = soup.find_all('table')[-1] # w ostatniej tabelce są interesujace nas dane
table_headers = table.find_all('th')
tbody = table.find('tbody')
rows = tbody.find_all('tr')
data = []
for row in rows:
    cols = row.find_all('td')
    data.append( [ele.text.strip() for ele in cols if ele.text.strip()])

market_cap_ranking = pd.DataFrame(data=data,
                                  columns=[col_name.text.strip() for col_name in table_headers if col_name.text.strip()])\
    .set_index('Rank')

coin_list = market_cap_ranking.Name.to_list()