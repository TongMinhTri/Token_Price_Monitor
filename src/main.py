from config import load_config
from logger import setup_logger
from price_monitor.monitor import monitor_token_prices
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", required=True, nargs='+')
    parser.add_argument("--from_block", type=int)
    parser.add_argument("--to_block", type=int)
    args = parser.parse_args()

    config = load_config("src/config.json")
    logger = setup_logger("price_monitor.log")

    try:
        monitor_token_prices(config, args.from_block,
                             args.to_block, args.pair, logger)
    except Exception as e:
        logger.exception("Monitoring failed")


if __name__ == "__main__":
    main()
