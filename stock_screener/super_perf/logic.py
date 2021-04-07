import yfinance as yf
import numpy as np
import sys
import os
import dateutil.relativedelta
import pandas as pd
import multiprocessing
from datetime import datetime, date
from stock_screener.util import post_webhook
from stock_screener.interfaces import ScannerInterface
import time


class Scanner(ScannerInterface):
    def __init__(self, tickers, cfg):
        self.tickers = tickers
        self.cfg = cfg
        self.search_settings = cfg.get("settings", {})

    # get data up to a year for analysis
    def get_data(self, ticker: str, months_cutoff=25) -> pd.DataFrame:
        current_date = datetime.strptime(date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
        past_date = current_date - dateutil.relativedelta.relativedelta(
            months=months_cutoff
        )
        sys.stdout = open(os.devnull, "w")
        data = yf.download(ticker, past_date, current_date)
        sys.stdout = sys.__stdout__
        return data
    
    @staticmethod
    def make_metrics(df_stock: pd.DataFrame)-> dict:
        print(df_stock.columns)
        print("making metrics")
        df_stock['200_MA']=df_stock['Close'].rolling(window=200).mean()
        df_stock['150_MA']=df_stock['Close'].rolling(window=150).mean()
        df_stock['50_MA']=df_stock['Close'].rolling(window=50).mean()
        metrics = {}
        print("200_MA")
        metrics['200 MA'] = df_stock['200_MA'][-1]
        metrics['150 MA'] = df_stock['150_MA'][-1]
        metrics['50 MA'] = df_stock['50_MA'][-1]
        print("200_MA_1mago")
        metrics['200 MA_1mago'] = df_stock['200_MA'][-30]
        metrics['150 MA_1mago'] = df_stock['150_MA'][-30]
        metrics['200 MA_2mago'] = df_stock['200_MA'][-60]
        metrics['150 MA_2mago'] = df_stock['150_MA'][-60]
        metrics['52W_Low'] = df_stock['Close'][-252:].min()
        metrics['52W_High'] = df_stock['Close'][-252:].max()
        metrics['price'] = df_stock['Close'][-1]
        #Condition 6 Current Price is at least 30% above 52 week low (1.3*low_of_52week)
        metrics['Above_30%_low'] = metrics['52W_Low'] * 1.3
        # Condition 7: Current Price is within 25% of 52 week high 
        metrics['Within_25%_high'] = metrics['52W_High'] * 0.7
        return metrics

    @staticmethod
    def check_stonk(df_stock: pd.DataFrame, ticker: str):
        metrics = Scanner.make_metrics(df_stock)

        metrics['c1'] = (metrics['price'] > metrics['200 MA']) & (metrics['price'] > metrics['150 MA'])
        metrics['c2'] = metrics['150 MA'] > metrics['200 MA']
        #3 The 200-day moving average line is trending up for 1 month 
        metrics['c3'] = metrics['200 MA'] > metrics['200 MA_1mago']
        metrics['c4'] = (metrics['50 MA'] > metrics['200 MA']) & (metrics['50 MA'] > metrics['150 MA'])
        metrics['c5'] = metrics['price'] > metrics['50 MA']
        metrics['c6'] = metrics['price'] > metrics['Above_30%_low']
        #7 The current stock price is within at least 25 percent of its 52-week high.
        metrics['c7'] = metrics['price'] > metrics['Within_25%_high']
        conditions_list = [f"c{i+1}" for i in range(7)]
        if all(key in metrics for key in conditions_list):
            # return key data fields
            metrics['Ticker'] = ticker
            metrics['Above_25%'] = metrics['c7']
            metrics['Above_200_MA'] = metrics['c3']
            return metrics
        return None

    def get_match(self, ticker):
        """
        get match for ticker
        """
        MONTH_CUTOFF = self.search_settings.get("month_cutoff", 12)
        df_stock = self.get_data(ticker, MONTH_CUTOFF)
        try:
            return Scanner.check_stonk(df_stock, ticker) 
        except Exception as e:
            print("Index failure for stock")
            print(ticker)
            print(e)

    def main_func(self):
        """
        Main function for the unusual volume scanner

        .. todo
          Determine if this is the best place to send discord messages
          probably with seperation of concerns, no.
        """
        cpus = multiprocessing.cpu_count()
        title = self.cfg.get("name", "")
        with multiprocessing.Pool(cpus) as p:
            positive_scans = p.map(self.get_match, self.tickers)
        curr_date = date.today().strftime("%Y-%m-%d")
        post_webhook(f"**{title} - {curr_date}**")
        not_none_values = filter(None.__ne__, positive_scans)
        list_of_values = list(not_none_values)
        post_webhook(f"Number of stocks: {len(list_of_values)}")
        content_df = pd.DataFrame(list_of_values).reindex(
            columns=["Ticker", "Above_200_MA", "Above_25%"]
        )
        content_str = content_df.to_string(index=False)

        # if else statement in case dataframe is missing
        for chunk in [
            content_str[i : i + 1944] for i in range(0, len(content_str), 1944)
        ]:
            time.sleep(2)
            post_webhook(f"```{chunk}```")
        return content_df
