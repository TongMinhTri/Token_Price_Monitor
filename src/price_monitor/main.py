from decimal import Decimal
import logging
from pymongo import MongoClient
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import json
from datetime import datetime
import time
import argparse


# Load configuration from config.json
with open("src/config.json", "r") as config_file:
    config = json.load(config_file)

# Update MongoDB and Web3 initialization to use config values
db = MongoClient(config["mongo_url"])
collection = db[config["database_name"]]
token_price_collection = collection[config["collection_name"]]

w3 = Web3(Web3.HTTPProvider(config["rpc_url"]))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("price_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


POOL_V2_ABI = [
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    }
]

POOL_V3_ABI = [
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16",
                "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16",
                "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint32", "name": "feeProtocol", "type": "uint32"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


def calculate_price_v2(pool_contract, block_number, token0_address, token1_address):
    reserves = pool_contract.functions.getReserves().call(block_identifier=block_number)
    reserve0, reserve1, _ = reserves

    # Determine the order of reserves based on token addresses
    pool_token0 = pool_contract.functions.token0().call()
    if pool_token0.lower() == token0_address.lower():
        price_token0_in_token1 = Decimal(reserve0) / Decimal(reserve1)
        price_token1_in_token0 = Decimal(reserve1) / Decimal(reserve0)
    else:
        price_token0_in_token1 = Decimal(reserve1) / Decimal(reserve0)
        price_token1_in_token0 = Decimal(reserve0) / Decimal(reserve1)

    return price_token0_in_token1, price_token1_in_token0


def calculate_price_v3(pool_contract, block_number, token0_address, token1_address):

    slot0 = pool_contract.functions.slot0().call(block_identifier=block_number)
    sqrt_price_x96 = slot0[0]

    # Determine the order of tokens based on token addresses
    pool_token0 = pool_contract.functions.token0().call()
    if pool_token0.lower() == token0_address.lower():
        price_token0_in_token1 = (Decimal(sqrt_price_x96) ** 2) / (2 ** 192)
        price_token1_in_token0 = (2 ** 192) / (Decimal(sqrt_price_x96) ** 2)
    else:
        price_token0_in_token1 = (2 ** 192) / (Decimal(sqrt_price_x96) ** 2)
        price_token1_in_token0 = (Decimal(sqrt_price_x96) ** 2) / (2 ** 192)

    return price_token0_in_token1, price_token1_in_token0


def get_token_symbol(token_address):
    token_contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=[
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ])
    return token_contract.functions.symbol().call()


def monitor_token_prices(from_block, to_block, pair_names: list[str]):

    current_block = w3.eth.block_number

    while True:

        if to_block is not None and current_block == to_block:
            logger.info(
                f"Reached target block {to_block}. Monitoring complete.")
            break
        if from_block is None:
            from_block = current_block

        for block_num in range(from_block - 1, current_block + 1):
            block = w3.eth.get_block(block_num)
            logger.info(f"Processing block {block_num}")
            for pair_name in pair_names:
                token_pair = config["token_pairs"][pair_name]

                pool_address = token_pair["pool_address"]
                pool_type = token_pair["pool_type"]
                token0_address = token_pair["token0_address"]
                token1_address = token_pair["token1_address"]

                contract = w3.eth.contract(
                    address=Web3.to_checksum_address(pool_address),
                    abi=POOL_V2_ABI if pool_type == "v2" else POOL_V3_ABI
                )
                pool_token0 = contract.functions.token0().call()
                token0_symbol = get_token_symbol(pool_token0)
                token1_symbol = get_token_symbol(token1_address if pool_token0.lower(
                ) == token0_address.lower() else token0_address)

                if pool_type == "v2":
                    price_token0_in_token1, price_token1_in_token0 = calculate_price_v2(
                        contract, block_num, token0_address, token1_address)
                else:
                    price_token0_in_token1, price_token1_in_token0 = calculate_price_v3(
                        contract, block_num, token0_address, token1_address)

                logger.info(
                    f"Pair: {pair_name}, {token0_symbol} in {token1_symbol}: {price_token0_in_token1}, "
                    f"{token1_symbol} in {token0_symbol}: {price_token1_in_token0}"
                )

                token_price_collection.insert_one({
                    "block_number": block_num,
                    "pool_address": pool_address,
                    "pool_type": pool_type,
                    "pair_name": pair_name,
                    "price_token0_in_token1": float(price_token0_in_token1),
                    "price_token1_in_token0": float(price_token1_in_token0),
                    "token0_symbol": token0_symbol,
                    "token1_symbol": token1_symbol,
                    "timestamp": datetime.fromtimestamp(block["timestamp"]).strftime('%Y-%m-%d %H:%M:%S') #type: ignore
                })
        if to_block is None:
            time.sleep(3)


def main():
    parser = argparse.ArgumentParser(
        description="Monitor token prices per block.")
    parser.add_argument("--pair", required=True, nargs='+',
                        help="One or more token pair names")
    parser.add_argument("--from_block", type=int, help="Starting block number")
    parser.add_argument("--to_block", type=int, help="Ending block number")
    args = parser.parse_args()

    try:
        monitor_token_prices(args.from_block, args.to_block, args.pair)

    except Exception as e:
        print("An error occurred while monitoring token prices")


if __name__ == "__main__":
    main()
