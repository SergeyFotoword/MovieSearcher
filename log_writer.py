from pymongo import MongoClient
from datetime import datetime
import dotenv
import os
from pathlib import Path

dotenv.load_dotenv(Path('.env'))

mongo_client = MongoClient(os.getenv("MONGO_URI"))
mongo_db = mongo_client[os.getenv("MONGO_DB")]
collection = mongo_db[os.getenv("MONGO_COLLECTION")]

def save_log(search_type, params, count):
    log = {
        "timestamp": datetime.now().isoformat(),
        "search_type": search_type,
        "params": params,
        "count": count
    }
    collection.insert_one(log)