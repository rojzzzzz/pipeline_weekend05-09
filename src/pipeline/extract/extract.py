from pipeline.config import RAW_PATH, data_contract
from pathlib import Path
import logging
import pandas as pd
import time

logger = logging.getLogger(__name__)
completeness_contract = data_contract['completeness']

def extract(path: Path | str) -> pd.DataFrame:
    start = time.perf_counter()
    logger.info("Starting to extract data")
    try:
        df = pd.read_parquet(path)
    except FileNotFoundError:
        logger.error("Raw File not found: %s", path)
        raise
    except Exception:
        logger.exception(f"Failed to extract parquet file {path}")
        raise

    if df.empty:
        logger.error("Raw data is empty, %s", path)
        raise ValueError(f"Extracted dataset contains no rows: {path}")

    duration = time.perf_counter() - start

    logger.info(
        "Successfully extracted raw data: path=%s rows=%d columns=%d duration=%.2fs",
        path,
        len(df),
        len(df.columns),
        duration,
    )

    return df





