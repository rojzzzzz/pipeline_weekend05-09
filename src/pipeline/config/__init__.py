from dotenv import load_dotenv
import os
from pathlib import Path
import logging
from .logging_config import setup_logging

setup_logging()
load_dotenv()
logger = logging.getLogger(__name__)

def get_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    raise ValueError(f"Environment variable {name} not set")

DB_CREDENTIALS = {}

try:
    DB_CREDENTIALS['db_user'] = get_env('DB_USER')
    DB_CREDENTIALS['db_password'] = get_env('DB_PASSWORD')
    DB_CREDENTIALS['db_name'] = get_env('DB_NAME')
    DB_CREDENTIALS['db_host'] = get_env('DB_HOST')
    DB_CREDENTIALS['db_port'] = get_env('DB_PORT')
    logger.info("Environment variables have been successfully loaded")
except ValueError as e:
    print("Missing required environment variables, check example")
    raise e
except Exception as e:
    logger.exception(f"Unexpected error while loading environment variables: {e}")
    raise e



RAW_PATH = Path(__file__).parents[3] / "data" / "raw" / "yellow_tripdata_2026-03.parquet"

data_contract = {}
data_contract['completeness'] = {"OK_THRESHOLD": 90, "WARNING_THRESHOLD": 80,
                                 "HEALTHY_COLUMNS_THRESHOLD": 85, "HEALTHY_COLUMNS_LIMIT": 60}

data_contract['uniqueness'] = {'OK_THRESHOLD': 95, 'WARNING_THRESHOLD': 90}
data_contract['quality_score'] = {'HEALTHY_THRESHOLD': 95, 'WARNING_THRESHOLD': 85}
