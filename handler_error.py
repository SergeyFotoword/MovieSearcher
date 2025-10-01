import traceback
from datetime import datetime, timezone
from pathlib import Path
from log_writer import mongo_db
from pymongo.errors import PyMongoError

collection_errors = mongo_db["errors_Movie_Searcher_Galushka"]

LOG_FILE = Path("handler_error.log")

def log_error(source: str, error: Exception):
    error_info = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "error_type": type(error).__name__,
        "message": str(error),
        "traceback": traceback.format_exc()
    }

    try:
        collection_errors.insert_one(error_info)
    except PyMongoError as mongo_error:
        print(f"Mongo log failure: {mongo_error} — writing to file instead")
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as file:
                file.write(
                    f"[{error_info['timestamp']}] SOURCE: {error_info['source']}\n"
                    f"ERROR_TYPE: {error_info['error_type']}\n"
                    f"MESSAGE: {error_info['message']}\n"
                    f"TRACEBACK:\n{error_info['traceback']}\n"
                    f"{'-'*80}\n"
                )
        except OSError as file_error:
            print(f"Critical log failure: {file_error}")