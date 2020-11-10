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

    def get_data(self, ticker: str, month_cutoff=5) -> pd.DataFrame:
        current_date = datetime.strptime(date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
        past_date = current_date - dateutil.relativedelta.relativedelta(
            months=month_cutoff
        )
        sys.stdout = open(os.devnull, "w")
        data = yf.download(ticker, past_date, current_date)
        sys.stdout = sys.__stdout__
        return data[["Volume"]]

    def find_anomalies(self, data: pd.DataFrame, STD_CUTOFF=1) -> dict:
        indexs = []
        outliers = []
        data_std = np.std(data["Volume"])
        data_mean = np.mean(data["Volume"])
        anomaly_cut_off = data_std * STD_CUTOFF
        upper_limit = data_mean + anomaly_cut_off
        data.reset_index(level=0, inplace=True)
        for i in range(len(data)):
            temp = data["Volume"].iloc[i]
            if temp > upper_limit:
                indexs.append(str(data["Date"].iloc[i])[:-9])
                outliers.append(temp)
        d = {"Dates": indexs, "Volume": outliers}
        return d

    def custom_print(self, d: pd.DataFrame, tick: str):
        print("\n\n\n*******  " + tick.upper() + "  *******")
        print("Ticker is: " + tick.upper())
        for i in range(len(d["Dates"])):
            str1 = str(d["Dates"][i])
            str2 = str(d["Volume"][i])
            print(str1 + " - " + str2)
        print("*********************\n\n\n")

    def days_between(self, d1: str, d2: str):
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    def get_match(self, ticker):
        """
        get match for ticker
        """
        MONTH_CUTOFF = self.search_settings.get("month_cutoff", 5)
        DAY_CUTOFF = self.search_settings.get("day_cutoff", 3)
        STD_CUTOFF = self.search_settings.get("std_cutoff", 0.75)
        currentDate = datetime.strptime(date.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
        ticker_data = self.get_data(ticker, MONTH_CUTOFF)
        d = self.find_anomalies(ticker_data, STD_CUTOFF)
        if d["Dates"]:
            for i in range(len(d["Dates"])):
                # Within current date
                if (
                    self.days_between(str(currentDate)[:-9], str(d["Dates"][i]))
                    <= DAY_CUTOFF
                ):
                    self.custom_print(d, ticker)
                    stonk = dict()
                    stonk["Ticker"] = ticker
                    stonk["TargetDate"] = d["Dates"][0]
                    stonk["TargetVolume"] = str("{:,.2f}".format(d["Volume"][0]))[:-3]
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
        post_webhook(f"Length: **{len(list_of_values)}**")
        content_df = pd.DataFrame(list_of_values).reindex(
            columns=["Ticker", "TargetDate", "TargetVolume"]
        )
        content_str = content_df.to_string(index=False)
        # move later, just return df
        for chunk in [
            content_str[i : i + 1994] for i in range(0, len(content_str), 1994)
        ]:
            post_webhook(f"```{chunk}```")
        return content_df
