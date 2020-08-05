import yfinance as yf
import numpy as np
import sys
import os
import dateutil.relativedelta
import pandas as pd
import glob
import json
import multiprocessing
from datetime import datetime, date
from get_stocks import TickerController
from util import post_webhook

search_settings = dict()

def get_data(ticker: str, month_cutoff=5)-> pd.DataFrame:
  currentDate = datetime.strptime(
      date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
  pastDate = currentDate - \
      dateutil.relativedelta.relativedelta(months=month_cutoff)
  sys.stdout = open(os.devnull, "w")
  data = yf.download(ticker, pastDate, currentDate)
  sys.stdout = sys.__stdout__
  return data[["Volume"]]

def find_anomalies(data: pd.DataFrame, STD_CUTOFF = 1)-> dict:
  indexs = []
  outliers = []
  data_std = np.std(data['Volume'])
  data_mean = np.mean(data['Volume'])
  anomaly_cut_off = data_std * STD_CUTOFF
  upper_limit = data_mean + anomaly_cut_off
  data.reset_index(level=0, inplace=True)
  for i in range(len(data)):
      temp = data['Volume'].iloc[i]
      if temp > upper_limit:
          indexs.append(str(data['Date'].iloc[i])[:-9])
          outliers.append(temp)
  d = {'Dates': indexs, 'Volume': outliers}
  return d

def custom_print(d: pd.DataFrame, tick: str):
  print("\n\n\n*******  " + tick.upper() + "  *******")
  print("Ticker is: "+tick.upper())
  for i in range(len(d['Dates'])):
    str1 = str(d['Dates'][i])
    str2 = str(d['Volume'][i])
    print(str1 + " - " + str2)
  print("*********************\n\n\n")

def days_between(d1: str, d2: str):
  d1 = datetime.strptime(d1, "%Y-%m-%d")
  d2 = datetime.strptime(d2, "%Y-%m-%d")
  return abs((d2 - d1).days)

def get_match(ticker):
  """
    get match for ticker
  """
  MONTH_CUTOFF = search_settings.get('month_cutoff', 5)
  DAY_CUTOFF = search_settings.get('day_cutoff', 3)
  STD_CUTOFF = search_settings.get('std_cutoff', 0.75)
  currentDate = datetime.strptime(
      date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
  ticker_data = get_data(ticker, MONTH_CUTOFF)
  d = find_anomalies(ticker_data, STD_CUTOFF)
  if d['Dates']:
    for i in range(len(d['Dates'])):
      # Within current date
      if days_between(str(currentDate)[:-9], str(d['Dates'][i])) <= DAY_CUTOFF:
        custom_print(d, ticker)
        stonk = dict()
        stonk['Ticker'] = ticker
        stonk['TargetDate'] = d['Dates'][0]
        stonk['TargetVolume'] = str(
            '{:,.2f}'.format(d['Volume'][0]))[:-3]
        return stonk

def get_stock_matches(tickers):
  """
    parallelize this
  """
  MONTH_CUTOFF = search_settings.get('month_cutoff', 5)
  DAY_CUTOFF = search_settings.get('day_cutoff', 3)
  STD_CUTOFF = search_settings.get('std_cutoff', 0.75)
  currentDate = datetime.strptime(
          date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
  positive_scans = []
  for ticker in tickers:
    ticker_data = get_data(ticker, MONTH_CUTOFF)
    d = find_anomalies(ticker_data, STD_CUTOFF)
    if d['Dates']:
      for i in range(len(d['Dates'])):
        if days_between(str(currentDate)[:-9], str(d['Dates'][i])) <= DAY_CUTOFF:
          custom_print(d, ticker)
          stonk = dict()
          stonk['Ticker'] = ticker
          stonk['TargetDate'] = d['Dates'][0]
          stonk['TargetVolume'] = str(
              '{:,.2f}'.format(d['Volume'][0]))[:-3]
          positive_scans.append(stonk)
  return positive_scans


def scan_markets():
  global search_settings
  from datetime import datetime
  start_time = datetime.now()
  # every json file has settings controlling what tickers will be "found"
  for cfg_file in glob.glob("cfg/*.json"):
    positive_scans = []
    with open(cfg_file) as file_:
      cfg = json.load(file_)
    search_settings = cfg.get('settings')
    ticker_controller = TickerController(cfg)
    tickers = ticker_controller.get_ytickers()
    cpus = multiprocessing.cpu_count()
    with multiprocessing.Pool(cpus) as p:
      positive_scans = p.map(get_match, tickers)
    
    title = cfg.get('name', '')
    post_webhook(f"{title} for {cfg_file}")
    not_none_values = filter(None.__ne__, positive_scans)
    list_of_values = list(not_none_values)
    content_df = pd.DataFrame(list_of_values).reindex(columns=['Ticker','TargetDate','TargetVolume'])
    content_str = content_df.to_string()
    for chunk in [content_str[i:i+2000] for i in range(0, len(content_str), 2000)]:
      post_webhook(chunk)

  end_time = datetime.now()
  print(end_time - start_time)

if __name__ == '__main__':
  scan_markets()
