import json


def load_config(path: str) -> dict:
    with open(path, "r") as config_file:
        config = json.load(config_file)

    required_keys = ["mongo_url", "database_name",
                     "collection_name", "rpc_url", "token_pairs", "stable_coins"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")

    return config
