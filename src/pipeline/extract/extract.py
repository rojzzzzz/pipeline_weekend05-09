from pipeline.config import RAW_PATH, data_contract
from pathlib import Path
import logging
import pandas as pd
import time

path = RAW_PATH
logger = logging.getLogger(__name__)
completeness_contract = data_contract['completeness']

def extract(path: Path | str) -> dict:
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

    completeness = measure_completeness(df)
    duration = time.perf_counter() - start

    logger.info(
        "Successfully extracted raw data: path=%s rows=%d columns=%d duration=%.2fs",
        path,
        len(df),
        len(df.columns),
        duration,
    )

    return {'data': df, 'completeness_df': completeness}


def measure_completeness(df: pd.DataFrame) -> pd.DataFrame:
    if df.shape[1] == 0:
        raise ValueError("Cannot measure completeness: dataframe has no columns.")

    df_sub = df.copy()
    df_sub = df_sub.replace(r'^\s*$', pd.NA, regex=True)

    result = pd.DataFrame({
        'column': df_sub.columns,
        'total': len(df_sub),
        'no_null': df_sub.notna().sum().values,
        'null': df_sub.isna().sum().values
    })

    result['completeness%'] = round(result['no_null'] / result['total'] * 100, 2)
    result['state'] = result['completeness%'].apply(lambda x: 'OK' if x>= completeness_contract['OK_THRESHOLD']
    else ('WARNING' if x >= completeness_contract['WARNING_THRESHOLD'] else 'EXCEEDED THRESHOLD'))

    ok_count = (result['state'] == 'OK').sum()
    total_columns = len(result)
    ok_percentage = round(ok_count / total_columns * 100, 2)

    if ok_percentage >= completeness_contract['HEALTHY_COLUMNS_THRESHOLD']:
        logger.info(
            f"Completeness quality is adequate: "
            f"{ok_count}/{total_columns} columns are [OK] "
            f"({ok_percentage}%).")
    elif ok_percentage >= completeness_contract['HEALTHY_COLUMNS_LIMIT']:
        logger.warning(
            f"Completeness quality degradation detected: "
            f"only {ok_count}/{total_columns} columns are [OK] "
            f"({ok_percentage:.2f}%)."
        )
    else:
        raise ValueError(
            f"Completeness validation failed: "
            f"{ok_percentage:.2f}% healthy columns"
        )

    return result

my_dict = extract(path)


