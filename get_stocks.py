"""
  Grab stocks from cad tickers 
"""
import pandas as pd
from cad_tickers.exchanges.tsx import dl_tsx_xlsx, add_descriptions_to_df_pp
class TickerController:
  """
    Grabs cad_tickers dataframes and normalized them
  """
  def __init__(self, update=True):
    """
      Extract yahoo finance tickers from website

      Consider using hardcoded csvs sheets for the tickers to
      increase speed, no need to grab all data dynamically.
    """
    self.yf_tickers = []
    # update tsx tickers
    tsx_df = dl_tsx_xlsx(sectors='technology')
    tsx_df = tsx_df[['Ex.', 'Ticker']]
    ytickers_series = tsx_df.apply(self.tsx_ticker_to_yahoo, axis=1)
    ytickers = ytickers_series.tolist()
    self.tsx_df = tsx_df
    self.ytickers = ytickers

  def get_ytickers(self)-> list:
    return self.ytickers

  @staticmethod
  def tsx_ticker_to_yahoo(row: pd.Series)-> str:
    """
      Parameters:
        ticker: ticker from pandas dataframe from cad_tickers
        exchange: what exchange the ticker is for
      Returns:

    """
    ticker = row['Ticker']
    exchange = row['Ex.']
    # 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
    switcher = {
      "TSXV":   "V",
      "TSX":     "TO"
    }
    yahoo_ex = switcher.get(exchange, "TSXV")
    return f"{ticker}.{yahoo_ex}"

if __name__ == "__main__":
  ticker_controller = TickerController()