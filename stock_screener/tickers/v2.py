"""
  Grab stocks from cad tickers 
"""
import pandas as pd


class TickerControllerV2:
    """
    Grabs cad_tickers dataframes and normalized them
    """

    def __init__(self, cfg: dict):
        """
        Extract yahoo finance tickers from website

        Consider using hardcoded csvs sheets for the tickers to
        increase speed, no need to grab all data dynamically.
        """
        self.yf_tickers = []
        # import csv from github
        ticker_df = pd.read_csv(
            "https://raw.githubusercontent.com/FriendlyUser/cad_tickers_list/main/static/latest/stocks.csv"
        )
        tickers_config = cfg.get("tickers_config")
        us_df = None
        if tickers_config != None:
            industries = tickers_config.get("industries")
            if industries != None:
                ticker_df = ticker_df[ticker_df["industry"].isin(industries)]

            us_tickers_url = tickers_config.get("us_tickers_url")
            if us_tickers_url != None:
                # same format as above
                us_df =  pd.read_csv(us_tickers_url)

        # get symbols from tickers
        ytickers_series = ticker_df.apply(self.ex_to_yahoo_ex, axis=1)
        ytickers = ytickers_series.tolist()
        if us_df != None:
            us_ytickers_series = us_df.apply(self.ex_to_yahoo_ex, axis=1)
            us_ytickers = us_ytickers_series.tolist()
            ytickers = [*ytickers, us_ytickers]
        self.yf_tickers = ytickers

    def get_ytickers(self) -> list:
        return self.yf_tickers

    @staticmethod
    def ex_to_yahoo_ex(row: pd.Series) -> str:
        """
        Parameters:
          ticker: ticker from pandas dataframe from cad_tickers
          exchange: what exchange the ticker is for
        Returns:

        """
        ticker = row["symbol"]
        exchange = row["exShortName"]
        if exchange == "CSE":
            # strip :CNX from symbol
            ticker = ticker.replace(":CNX", "")
        
        if exchange in ["OTCPK", "NYSE", "NASDAQ", "NYE", "NCM", "NSM", "NGS"]:
            ticker = ticker.replace(":US", "")
        # 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        switcher = {"TSXV": "V", "TSX": "TO", "CSE": "CN"}
        yahoo_ex = switcher.get(exchange, None)
        if yahoo_ex != None:
            return f"{ticker}.{yahoo_ex}"
        return ticker


if __name__ == "__main__":
    import json

    with open("cfg/penny_stocks.json") as file_:
        cfg = json.load(file_)
        ticker_controller = TickerControllerV2(cfg)
        ticker_list = ticker_controller.get_ytickers()
        print(ticker_list)
