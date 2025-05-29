from decimal import Decimal


def calculate_price_v2(contract, block_number: int, normal_coin_address: str) -> Decimal:
    reserves = contract.functions.getReserves().call(block_identifier=block_number)
    reserve0, reserve1, _ = reserves
    token0 = contract.functions.token0().call()

    if token0.lower() == normal_coin_address.lower():
        return Decimal(reserve1) / Decimal(reserve0)
    else:
        return Decimal(reserve0) / Decimal(reserve1)


def calculate_price_v3(contract, block_number: int, normal_coin_address: str) -> Decimal:
    slot0 = contract.functions.slot0().call(block_identifier=block_number)
    sqrt_price_x96 = slot0[0]
    token0 = contract.functions.token0().call()

    if token0.lower() == normal_coin_address.lower():
        return (Decimal(sqrt_price_x96) ** 2) / (2 ** 192)
    else:
        return (2 ** 192) / (Decimal(sqrt_price_x96) ** 2)
