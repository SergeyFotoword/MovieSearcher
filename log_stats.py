from log_writer import collection
from pymongo.errors import PyMongoError
from handler_error import log_error

def get_top_queries(limit=5):
   try:
        pipeline = [
            {"$group": {"_id": {"type": "$search_type", "params": "$params"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        return list(collection.aggregate(pipeline))

   except PyMongoError as e:
       print(f"MongoDB error in get_top_queries: {e}")
       log_error("get_top_queries", e)
       return []


def get_recent_queries(limit=5):
    try:
        return list(collection.find().sort("timestamp", -1).limit(limit))

    except PyMongoError as e:
        print(f"MongoDB error in get_recent_queries: {e}")
        log_error("get_recent_queries", e)
        return []


