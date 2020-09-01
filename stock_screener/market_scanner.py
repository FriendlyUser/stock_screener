import glob
import json
import importlib
import os
from datetime import datetime, date
from stock_screener.get_stocks import TickerController
from stock_screener.util import post_webhook
from typing import Union


def perform_scan(cfg_path):
    with open(cfg_path) as file_:
        cfg = json.load(file_)
    scan_type = cfg.get("type", "unusual_volume")
    ticker_controller = TickerController(cfg)
    tickers = ticker_controller.get_ytickers()
    scanner_lib_name = f"stock_screener.{scan_type}.logic"
    scanner_lib = importlib.import_module(scanner_lib_name)
    Scanner = scanner_lib.Scanner(tickers, cfg)
    Scanner.main_func()


def scan_markets(config_path: Union[None, str] = None):
    start_time = datetime.now()

    if config_path is None:
        # every json file has settings controlling what tickers will be "found"
        for cfg_path in glob.glob("cfg/*.json"):
            perform_scan(cfg_path)
    else:
        perform_scan(config_path)

    end_time = datetime.now()
    print(end_time - start_time)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="parse the config file")
    parser.add_argument(
        "-f", "--files", nargs="+", help="<Required> List of config files"
    )
    args = parser.parse_args()
    files = args.files
    valid_files = []
    # check for valid files, todo check format
    for file_path in args.files:
        valid_file = os.path.isfile(file_path)
        if valid_file is True:
            valid_files.append(valid_file)
        else:
            print(f"File path {file_path} invalid")
    if len(valid_files) > 0:
        # TODO validate files exist
        for config_file in args.files:
            scan_markets(config_file)
    else:
        scan_markets()
