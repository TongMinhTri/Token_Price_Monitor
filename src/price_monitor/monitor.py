import time
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from src.price_monitor.block_processor import process_block
from src.db.mongo import get_token_price_collection


def monitor_token_prices(config: dict, from_block: int | None, to_block: int | None, pair_names: list[str], logger):
    w3 = Web3(Web3.HTTPProvider(config["rpc_url"]))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    collection = get_token_price_collection(config)

    if from_block is None:
        from_block = w3.eth.block_number

    if to_block:
        for block_num in range(from_block - 1, to_block):
            process_block(w3, block_num, config, collection, logger)
        logger.info(f"Reached target block {to_block}. Monitoring complete.")
    else:
        current_block = from_block
        while True:
            latest_block = w3.eth.block_number
            while current_block <= latest_block:
                process_block(w3, current_block, config, collection, logger)
                current_block += 1
            time.sleep(3)
