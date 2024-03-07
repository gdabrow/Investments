#!/usr/bin/env python3

# import libraries
import yfinance as yf
import pandas as pd
import cloudscraper
from urllib.request import urlopen
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import csv
import random
import json
import time
import utils

# complete api key
fin_apikey = '...'

scraper = cloudscraper.create_scraper(delay=10)


# Downloading necessary tickers from a file
filename = 'candidates.xlsx'
tipranks = pd.read_excel(filename)
tickers = list(tipranks['ticker'])
tipranks.set_index('ticker', inplace=True)


# Downloading necessary information from finance.yahoo
y_f = utils.get_data_from_yf(tickers)
y_f = y_f[utils.COLUMNS_YF]
y_f.rename(columns=utils.COLUMNS_YF_TO_CHANGE, inplace=True)


# Downloading necessary information from finviz
fin = utils.get_data_from_finviz(tickers)
fin = fin[utils.COLUMNS_FIN]


# Downloading necessary information from financialmodelingprep
financialmodelin = utils.get_data_from_financialmodeling(tickers, fin_apikey)
financialmodelin.drop(columns='date', inplace=True)
financialmodelin.rename(columns=utils.COLUMNS_FINMOD_TO_CHANGE, inplace=True)


# Downloading necessary information from zacks
zacks = utils.get_data_from_zacks(tickers)

# redirections to appropriate websites
www = utils.go_to_url(tickers, utils.URLS)

# combining data from all sources
asset = pd.concat([y_f, zacks, tipranks, fin, financialmodelin, www], axis=1)


# converting selected columns to the appropriate numeric format
utils.conversion_to_number(asset, utils.COLUMNS_FIN[1:])
utils.conversion_to_percent(asset, utils.COLUMNS_TO_PERCENT)


# normalization of selected columns
normalized_values = {}
for parameters in utils.PARAMETERS_FOR_RANKING:
  series = asset[parameters['series']]
  max= parameters['max']
  reverse = parameters['reverse']
  normalized = utils.norm(series, max, reverse)
  normalized_values[parameters['series']] = normalized


# creating a ranking
ranking = sum(normalized_values.values())
ranking.name = 'Ranking'


# combining the ranking with the rest of the data
stock_ranking = pd.concat([asset, ranking], axis=1)

#selection of columns to show
stock_ranking = stock_ranking[utils.COLUMNS_TO_SHOW]

# saving the result to an '.xlsx' file on disk
stock_ranking.to_excel('ranking_' + filename)
