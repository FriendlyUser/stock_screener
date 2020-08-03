import yfinance as yf
import numpy as np
import sys
import os
import dateutil.relativedelta
import pandas as pd
from datetime import datetime, date
from get_stocks import TickerController
# Change variables to your liking then run the script
MONTH_CUTTOFF = 5
DAY_CUTTOFF = 3
STD_CUTTOFF = 0.5


class MarketScanner:
  def __init__(self):
    pass


  @staticmethod
  def get_data(ticker: str):
    currentDate = datetime.strptime(
        date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
    pastDate = currentDate - \
        dateutil.relativedelta.relativedelta(months=MONTH_CUTTOFF)
    sys.stdout = open(os.devnull, "w")
    data = yf.download(ticker, pastDate, currentDate)
    sys.stdout = sys.__stdout__
    return data[["Volume"]]

  @staticmethod
  def find_anomalies(data: pd.DataFrame):
    indexs = []
    outliers = []
    data_std = np.std(data['Volume'])
    data_mean = np.mean(data['Volume'])
    anomaly_cut_off = data_std * STD_CUTTOFF
    upper_limit = data_mean + anomaly_cut_off
    data.reset_index(level=0, inplace=True)
    for i in range(len(data)):
        temp = data['Volume'].iloc[i]
        if temp > upper_limit:
            indexs.append(str(data['Date'].iloc[i])[:-9])
            outliers.append(temp)
    d = {'Dates': indexs, 'Volume': outliers}
    return d

  @staticmethod
  def custom_print(d: pd.DataFrame, tick: str):
    print("\n\n\n*******  " + tick.upper() + "  *******")
    print("Ticker is: "+tick.upper())
    for i in range(len(d['Dates'])):
      str1 = str(d['Dates'][i])
      str2 = str(d['Volume'][i])
      print(str1 + " - " + str2)
    print("*********************\n\n\n")

  @staticmethod
  def days_between(d1: str, d2: str):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d2 - d1).days)

  def parallel_wrapper(self, x, currentDate, positive_scans):
    d = (self.find_anomalies(self.get_data(x)))
    if d['Dates']:
      for i in range(len(d['Dates'])):
        if self.days_between(str(currentDate)[:-9], str(d['Dates'][i])) <= DAY_CUTTOFF:
          self.custom_print(d, x)
          stonk = dict()
          stonk['Ticker'] = x
          stonk['TargetDate'] = d['Dates'][0]
          stonk['TargetVolume'] = str(
              '{:,.2f}'.format(d['Volume'][0]))[:-3]
          positive_scans.append(stonk)
    return positive_scans

  def get_matches(self):
    ticker_controller = TickerController()
    tickers = ticker_controller.get_ytickers()
    currentDate = datetime.strptime(
            date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
    positive_scans = []
    for ticker in tickers:
      d = (self.find_anomalies(self.get_data(ticker)))
      print(ticker)
      if d['Dates']:
        for i in range(len(d['Dates'])):
          if self.days_between(str(currentDate)[:-9], str(d['Dates'][i])) <= DAY_CUTTOFF:
            self.custom_print(d, ticker)
            stonk = dict()
            stonk['Ticker'] = ticker
            stonk['TargetDate'] = d['Dates'][0]
            stonk['TargetVolume'] = str(
                '{:,.2f}'.format(d['Volume'][0]))[:-3]
            positive_scans.append(stonk)
    print(positive_scans)
    return positive_scans


if __name__ == '__main__':
  market_scanner = MarketScanner()
  market_scanner.get_matches()
