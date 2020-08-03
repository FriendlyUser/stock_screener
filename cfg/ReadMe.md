Schema for config, consider using concepts from mlfinlab https://mlfinlab.readthedocs.io/en/latest/

```json

{
  "name": "Unusual TSX Volume",
  "tsx": {
    "tickers_config": {
      "exchanges": "TSXV",
      "sectors": "technology"
    }
  },
  "type": "UnusualVolume",
  "settings": {
    "month_cutoff": 5,
    "day_cutoff": 3,
    "std_cutoff": 1.1
  }
}

```