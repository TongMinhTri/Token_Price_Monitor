from web3 import Web3


def get_token_symbol(w3: Web3, token_address: str) -> str:
    token_contract = w3.eth.contract(
        address=Web3.to_checksum_address(token_address),
        abi=[{
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }]
    )
    return token_contract.functions.symbol().call()
