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


class Scanner(ScannerInterface):
    def __init__(self, tickers, cfg):
        self.tickers = tickers
        self.cfg = cfg
        self.search_settings = cfg.get("settings", {})

    def get_data(self, ticker: str, days_cutoff=5) -> pd.DataFrame:
        current_date = datetime.strptime(date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
        past_date = current_date - dateutil.relativedelta.relativedelta(
            days=days_cutoff
        )
        sys.stdout = open(os.devnull, "w")
        data = yf.download(ticker, past_date, current_date)
        sys.stdout = sys.__stdout__
        return data[["Volume", "Close"]]

    def custom_print(self, d: pd.DataFrame, tick: str):
        print("\n\n\n*******  " + tick.upper() + "  *******")
        print("Ticker is: " + tick.upper())
        print("*********************\n\n\n")

    def get_match(self, ticker):
        """
        get match for ticker
        """
        DAY_CUTOFF = self.search_settings.get("day_cutoff", 5)
        ticker_data = self.get_data(ticker, DAY_CUTOFF)
        last_close = ticker_data["Close"].iloc[-1]
        if last_close < 5:
            stonk = dict()
            stonk["Ticker"] = ticker
            stonk["Volume"] = ticker_data["Volume"].iloc[-1]
            return stonk

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
        post_webhook(f"**{title}**")
        not_none_values = filter(None.__ne__, positive_scans)
        list_of_values = list(not_none_values)
        content_df = pd.DataFrame(list_of_values).reindex(columns=["Ticker", "Volume"])
        content_str = content_df.to_string(index=False)
        # move later, just return df
        for chunk in [
            content_str[i : i + 1994] for i in range(0, len(content_str), 1994)
        ]:
            post_webhook(f"```{chunk}```")
        return content_df
