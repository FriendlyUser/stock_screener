# Canadian stock screener

Inspired by [UnusualVolumeDetector](https://github.com/SamPom100/UnusualVolumeDetector/blob/master/market_scanner.py)

## Project Goals
Scan the canadian stock market for unusual behaviour


### V2

* Make into pip package (should be easy with poetry)
* Add Sphinx Docs (again not too hard)
* Set cfg flag to skip in development or prod

### V1

* Test run to limit runs in development
* Scrap Stock Tickers from all exchanges in canada
* Quickly scan for unusual stock tickers
* Notification System (cron jobs run daily, output to discord) 
* summarize which config and tickers with link to site)

### Modules


* Stock list (grabs list of stocks) from cad_tickers and transformers then for yfinance