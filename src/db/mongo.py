from pymongo import MongoClient


def get_token_price_collection(config: dict):
    db = MongoClient(config["mongo_url"])
    database = db[config["database_name"]]
    return database[config["collection_name"]]
