# src/price_monitor/block_processor.py

from web3 import Web3
from datetime import datetime
from .token_utils import get_token_symbol
from .price_calculator import calculate_price_v2, calculate_price_v3
from .abis import POOL_V2_ABI, POOL_V3_ABI
from .prometheus_exporter import PRICE_GAUGE, DEVIATION_GAUGE

def process_block(w3: Web3, block_num: int, config: dict, collection, logger):
    try:
        block = w3.eth.get_block(block_num)
    except Exception as e:
        logger.warning(f"Could not fetch block {block_num}: {e}")
        return

    logger.info(f"Processing block {block_num}")

    tracked_pairs = set(config["token_pairs"].keys())

    prices = {}

    for pair_name in tracked_pairs:
        token_pair = config["token_pairs"][pair_name]
        pool_address = token_pair["pool_address"]
        pool_type = token_pair["pool_type"]

        contract = w3.eth.contract(
            address=Web3.to_checksum_address(pool_address),
            abi=POOL_V2_ABI if pool_type == "v2" else POOL_V3_ABI
        )

        token0 = contract.functions.token0().call()
        token1 = contract.functions.token1().call()

        token0_symbol = get_token_symbol(w3, token0)
        token1_symbol = get_token_symbol(w3, token1)

        if token0_symbol in config["stable_coins"]:
            normal_coin, stable_coin = token1_symbol, token0_symbol
            normal_coin_address = token1
        else:
            normal_coin, stable_coin = token0_symbol, token1_symbol
            normal_coin_address = token0

        price = calculate_price_v2(contract, block_num, normal_coin_address) \
            if pool_type == "v2" else \
            calculate_price_v3(contract, block_num, normal_coin_address)

        PRICE_GAUGE.labels(pair_name=pair_name).set(float(price))
        logger.info(f"Pair: {pair_name}, {normal_coin} in {stable_coin}: {price}")

        collection.insert_one({
            "block_number": block_num,
            "pool_address": pool_address,
            "pool_type": pool_type,
            "pair_name": pair_name,
            "price_token0_in_token1": float(price),
            "token0_symbol": normal_coin,
            "token1_symbol": stable_coin,
            "timestamp": datetime.fromtimestamp(block["timestamp"]).strftime('%Y-%m-%d %H:%M:%S') #type: ignore
        })

        prices[pair_name] = float(price)

    for pair_a in tracked_pairs:
        for pair_b in tracked_pairs:
            if pair_a >= pair_b:
                continue
            if pair_a in prices and pair_b in prices:
                p1, p2 = prices[pair_a], prices[pair_b]
                deviation = abs(p1 - p2) / ((p1 + p2) / 2) * 100
                DEVIATION_GAUGE.labels(pair=f"{pair_a}_{pair_b}").set(deviation)
                logger.info(f"Deviation for {pair_a}_{pair_b} at block {block_num}: {deviation:.4f}%")
