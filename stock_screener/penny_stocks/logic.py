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
        print(tickers)
        self.cfg = cfg
        self.search_settings = cfg.get("settings", {})

    def get_data(self, ticker: str, months_cutoff=1) -> pd.DataFrame:
        current_date = datetime.strptime(date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
        past_date = current_date - dateutil.relativedelta.relativedelta(
            months=months_cutoff
        )
        sys.stdout = open(os.devnull, "w")
        data = yf.download(ticker, past_date, current_date)
        sys.stdout = sys.__stdout__
        return data

    def custom_print(self, d: pd.DataFrame, tick: str):
        print("\n\n\n*******  " + tick.upper() + "  *******")
        print("Ticker is: " + tick.upper())
        print("*********************\n\n\n")

    @staticmethod
    def get_three_month():
        pass
    
    @staticmethod
    def calc_price_vol(ticker_data: pd.DataFrame):
        try:
            price = ticker_data["Close"].iloc[-1]
            volume = ticker_data["Volume"].iloc[-1]
            return price * volume
        except Exception as e:
            print(e)
            return None

    def get_match(self, ticker):
        """
        get match for ticker
        """
        DAY_CUTOFF = self.search_settings.get("day_cutoff", 1)
        ticker_data = self.get_data(ticker, DAY_CUTOFF)
        try:
            last_close = ticker_data["Close"].iloc[-1]
            price_volume = self.calc_price_vol(ticker_data)
            # penny stock with enough liquidity
            if last_close < 5 and price_volume > 10 * 5000:
                stonk = dict()
                stonk["Ticker"] = ticker
                stonk["Volume"] = ticker_data["Volume"].iloc[-1]
                stonk["PriceVolume"] = price_volume
                stonk["Close"] = last_close
                return stonk
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
            columns=["Ticker", "Volume", "PriceVolume", "Close"]
        )
        content_str = content_df.to_string(index=False)

        # if else statement in case dataframe is missing
        for chunk in [
            content_str[i : i + 1994] for i in range(0, len(content_str), 1994)
        ]:
            time.sleep(2)
            post_webhook(f"```{chunk}```")
        return content_df
