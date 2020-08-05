"""
  Grab stocks from cad tickers 
"""
import pandas as pd
from cad_tickers.exchanges.tsx import dl_tsx_xlsx, add_descriptions_to_df_pp
from cad_tickers.exchanges.cse import get_cse_tickers_df
class TickerController:
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
    # update tsx tickers
    tsx_cfg = cfg.get('tsx')

    if tsx_cfg is not None:
      tsx_ticker_cfg = tsx_cfg.get('tickers_config')
      if tsx_ticker_cfg is not None:
        tsx_df = dl_tsx_xlsx(**tsx_ticker_cfg)
        tsx_df = tsx_df[['Ex.', 'Ticker']]
        ytickers_series = tsx_df.apply(self.tsx_ticker_to_yahoo, axis=1)
        ytickers_series = ytickers_series.drop_duplicates(keep='last')
        ytickers = ytickers_series.tolist()
        self.yf_tickers = [*self.yf_tickers, *ytickers]
    
    # DO cse listings
    cse_cfg = cfg.get('cse')
    if cse_cfg is not None:
      # ticker_cfg, not going to check if atm
      cse_ticker_cfg = cse_cfg.get('tickers_config')
      cse_df = get_cse_tickers_df()
      cse_df = cse_df[['Symbol']]
      ytickers_series = cse_df.apply(self.cse_ticker_to_yahoo, axis=1)
      ytickers_series = ytickers_series.drop_duplicates(keep='last')
      ytickers = ytickers_series.tolist()
      self.yf_tickers = [*self.yf_tickers, *ytickers]

  def get_ytickers(self)-> list:
    return self.yf_tickers

  @staticmethod
  def cse_ticker_to_yahoo(row: pd.Series)-> str:
    ticker = row['Symbol']
    return f"{ticker}.CN"

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
  import json
  with open('cfg/tsx_technology.json') as file_:
    cfg = json.load(file_)
    ticker_controller = TickerController(cfg)
