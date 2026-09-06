from pipeline.config import data_contract, RAW_PATH
from pipeline.extract.extract import extract
import pandas as pd
import logging
import math
import time

logger = logging.getLogger(__name__)
completeness_contract = data_contract['completeness']
uniqueness_contract = data_contract['uniqueness']
quality_contract = data_contract['quality_score']


def measure_completeness(df: pd.DataFrame) -> dict:
    if df.shape[1] == 0 or len(df) == 0:
        raise ValueError("Cannot measure completeness: dataframe is incomplete.")

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
        status = 'OK'
        logger.info(
            f"Completeness quality is adequate: "
            f"{ok_percentage}% of the columns are OK")
    elif ok_percentage >= completeness_contract['HEALTHY_COLUMNS_LIMIT']:
        status = 'WARNING'
        logger.warning(
            f"Completeness quality degradation detected: "
            f"only {ok_percentage}% of the columns are OK ")
    else:
        status = 'CRITICAL'
        logger.error(
            f"Completeness validation failed: "
            f"{ok_percentage}% healthy columns")

    return {'score': result['completeness%'].mean(), 'healthy_columns_pct': ok_percentage , "status": status,
            'detail': result}


def measure_uniqueness(df: pd.DataFrame) -> dict:
    if df.shape[1] == 0 or len(df) == 0:
        raise ValueError("Cannot measure uniqueness: dataframe is incomplete.")

    total = len(df)
    n_duplicated = df.duplicated(keep=False).sum()
    non_duplicated = len(df) - n_duplicated
    uniqueness = round(non_duplicated / total * 100, 2)
    status = 'OK' if uniqueness >= uniqueness_contract['OK_THRESHOLD'] else (
                'WARNING' if uniqueness >= uniqueness_contract['WARNING_THRESHOLD'] else 'CRITICAL')

    if status == 'OK':
        logger.info(f"Uniqueness quality is adequate: {uniqueness}%. {n_duplicated}/{total} are duplicated.")
    elif status == 'WARNING':
        logger.warning(f"Uniqueness quality degradation detected: {uniqueness}%. {n_duplicated}/{total} are duplicated.")
    else:
        logger.error(
            f"Uniqueness validation failed: {uniqueness}%. {n_duplicated}/{total} are duplicated.")

    return {'score': uniqueness,
            'total_entries': total,
            'duplicated_entries': n_duplicated,
            'status': status}

def calculate_data_quality(
        completeness: float,
        uniqueness: float,
        weights: dict=None):

    if weights is None:
        weights = {
            'completeness': 0.60,
            'uniqueness': 0.40
        }

    if not math.isclose(sum(weights.values()), 1.0):
        raise ValueError("Data quality weights must sum to 1.0")


    dimensions = {'completeness': completeness, 'uniqueness': uniqueness}
    score = round(sum(dimensions[d] * weights[d] for d in dimensions), 2)
    return {
        "score": score,
        "dimensions": dimensions,
        'status': 'HEALTHY' if score >= quality_contract['HEALTHY_THRESHOLD'] else (
            'DEGRADED' if score >= quality_contract['WARNING_THRESHOLD'] else 'CRITICAL'
        )
    }

def validate(df: pd.DataFrame) -> dict:
    start = time.perf_counter()
    logger.info("Starting to validate data...")
    completeness = measure_completeness(df)
    uniqueness = measure_uniqueness(df)

    quality_results = calculate_data_quality(completeness['score'], uniqueness['score'])
    if quality_results["status"] == "CRITICAL":
        logger.error("Data quality validation failed. Status is CRITICAL. Can't proceed.")
        raise ValueError("Data with quality status: 'CRITICAL' can't proceed.")

    elif quality_results["status"] == "DEGRADED":
        logger.warning(
            "Data validation completed with degraded quality. "
            "Pipeline will proceed."
        )

    else:
        logger.info(
            "Data validation completed successfully. "
            "Data quality is healthy."
        )

    duration = time.perf_counter() - start
    logger.info(f"Finished validating data. Status is: {quality_results['status']} which is optimal to proceed. Data quality score: {quality_results['score']}\n"
                f"Mean completeness: {completeness['score']}. Uniqueness score: {uniqueness['score']}\n"
                f"Total duration: {duration} seconds.")

    return {"completeness": completeness, "uniqueness": uniqueness, "quality": quality_results}





