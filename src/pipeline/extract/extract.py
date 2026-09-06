from pipeline.config import RAW_PATH
import logging
import pandas as pd
import time

path = RAW_PATH
logger = logging.getLogger(__name__)

def extract(path) -> dict:
    start = time.time()
    logger.info("Starting to extract data")
    try:
        df = pd.read_parquet(path)
    except FileNotFoundError as e:
        logger.error("Raw File Not Found")
        raise e
    except Exception as e:
        logger.exception(e)
        print(type(e).__name__)
        raise e

    completeness_df = measure_completeness(df)
    duration = time.time() - start

    logger.info(f"Succesfully extracted raw data. Duration: {duration} seconds")
    return {"data": df, "completeness_df": completeness_df}


def measure_completeness(df: pd.DataFrame) -> pd.DataFrame:
    df_sub = df.copy()
    df_sub = df_sub.replace(r'^\s*$', pd.NA, regex=True)

    result = pd.DataFrame({
        'column': df_sub.columns,
        'total': len(df_sub),
        'no_null': df_sub.notna().sum().values,
        'null': df_sub.isna().sum().values
    })

    result['completeness%'] = round(result['no_null'] / result['total'] * 100, 2)
    result['state'] = result['completeness%'].apply(lambda x: '[OK]' if x>= 90 else (
        '[WARNING]' if x > 80 else '[EXCEEDED THRESHOLD]'
    ))

    ok_count = (result['state'] == '[OK]').sum()
    total_columns = len(result)
    ok_percentage = round(ok_count / total_columns * 100, 2)

    if ok_count > 85:
        logger.info(
            f"Completeness quality is adequate: "
            f"{ok_count}/{total_columns} columns are [OK] "
            f"({ok_percentage}%).")
    else:
        logger.warning(
            f"Completeness quality degradation detected: "
            f"only {ok_count}/{total_columns} columns are [OK] "
            f"({ok_percentage:.2f}%)."
        )

    return result

my_dict = extract(path)


