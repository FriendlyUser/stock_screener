# Canadian stock screener

Inspired by [UnusualVolumeDetector](https://github.com/SamPom100/UnusualVolumeDetector/blob/master/market_scanner.py)

## Project Goals
Scan the canadian stock market for unusual behaviour


### V2

* Make into pip package (should be easy with poetry)
* Add Sphinx Docs (again not too hard)

### V1

* Scrap Stock Tickers from all exchanges in canada
* Quickly scan for unusual stock tickers
* Report Generation, similar to yt_nlp where there is a html report to gh pages, but organized by content for month, day and year (either nuxt-content-theme with index in docs and the rest of the content elsewhere, links to static websites)

* Notification System (cron jobs run daily, output to discord, summarize which config and tickers with link to site)

### Modules


* Stock list (grabs list of stocks) from cad_tickers and transformers then for yfinance