"""
Scans for stocks with a change from the low to high with a high number
"""
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
from stock_screener.util import post_webhook
from stock_screener.interfaces import ScannerInterface


class Scanner(ScannerInterface):
    def __init__(self, tickers, cfg):
        self.tickers = tickers
        self.cfg = cfg
        self.search_settings = cfg.get("settings", {})

    def get_data(self, ticker: str, day_cutoff=5) -> pd.DataFrame:
        """
        Grab daily days for high and low
        """
        current_date = datetime.strptime(date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
        past_date = current_date - dateutil.relativedelta.relativedelta(days=day_cutoff)
        sys.stdout = open(os.devnull, "w")
        data = yf.download(ticker, past_date, current_date)
        sys.stdout = sys.__stdout__
        return data

    def find_anomaly(self, data: pd.DataFrame, PERCENT_CUTOFF=0.40) -> dict:
        max_value = data["High"].max()
        min_value = data["Low"].min()
        value_diff = abs(max_value - min_value)
        max_per_diff = value_diff / max_value
        min_per_diff = value_diff / min_value
        if max_per_diff >= PERCENT_CUTOFF or min_per_diff >= PERCENT_CUTOFF:
            Direction = "N/A"
            try:
                if data.empty == False:
                    d_open = data["Open"].iloc[1]
                    d_close = data["Close"].iloc[-1]
                    Direction = "up" if d_open > d_close else "down"
            except Exception as e:
                print(e)
            d = dict(
                Max=max_value,
                Min=min_value,
                Diff=value_diff,
                MaxPercentDiff=max_per_diff,
                MinPercentDiff=min_per_diff,
                Direction=Direction,
            )
        else:
            d = dict(Max=max_value, Min=min_value, Diff=value_diff)
        return d

    def get_match(self, ticker):
        """
        get match for ticker
        """
        PERCENT_CUTOFF = self.search_settings.get("percent_cutoff", 0.35)
        DAY_CUTOFF = self.search_settings.get("day_cutoff", 5)
        ticker_data = self.get_data(ticker, DAY_CUTOFF)
        d = self.find_anomaly(ticker_data, PERCENT_CUTOFF)
        if d.get("MaxPercentDiff") or d.get("MinPercentDiff"):
            d["Ticker"] = ticker
            d["Max % Diff"] = round(d["MaxPercentDiff"], 2)
            d["Min % Diff"] = round(d["MinPercentDiff"], 2)
            d["Diff"] = round(d["Diff"], 2)
            return d

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
        post_webhook(f"Length: **{len(list_of_values)}**")
        content_df = pd.DataFrame(list_of_values).reindex(
            columns=[
                "Ticker",
                "Min",
                "Max",
                "Diff",
                "MaxPercentDiff",
                "MinPercentDiff",
                "Direction",
            ]
        )
        if content_df.empty == True:
            post_webhook(f"**{title}**")
            return
        content_str = content_df.to_string(index=False)
        # move later, just return df
        for chunk in [
            content_str[i : i + 1994] for i in range(0, len(content_str), 1994)
        ]:
            post_webhook(f"```{chunk}```")
        return content_df


if __name__ == "__main__":
    test_tickers = ["IP.CN", "NTAR.CN", "API.CN", "IGN.CN"]
    cfg = {}
    scanner = Scanner(test_tickers, cfg)
    ip = scanner.main_func()
