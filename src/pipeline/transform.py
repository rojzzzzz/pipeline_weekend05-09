import pandas as pd
import logging

logger = logging.getLogger(__name__)
TIMESTAMP_COLUMNS = ("tpep_pickup_datetime", "tpep_dropoff_datetime")
SOURCE_TIMEZONE = "America/New_York"


def _to_utc(series: pd.Series, column_name: str) -> pd.Series:
    original_null_count = int(series.isna().sum())
    converted = pd.to_datetime(series, errors="coerce")

    if converted.dt.tz is None:
        converted = converted.dt.tz_localize(
            SOURCE_TIMEZONE,
            ambiguous="NaT",
            nonexistent="NaT",
        ).dt.tz_convert("UTC")
    else:
        converted = converted.dt.tz_convert("UTC")

    invalid_count = int(converted.isna().sum()) - original_null_count
    if invalid_count:
        logger.warning(
            "Timestamp normalization produced null values: column=%s invalid_rows=%d",
            column_name,
            invalid_count,
        )

    return converted


def transform(df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = set(TIMESTAMP_COLUMNS) - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Cannot transform data: missing required columns {sorted(missing_columns)}"
        )

    logger.info("Starting timestamp transformation: rows=%d", len(df))
    transformed_df = df.copy()

    for column_name in TIMESTAMP_COLUMNS:
        transformed_df[column_name] = _to_utc(transformed_df[column_name], column_name)

    logger.info("Finished timestamp transformation: rows=%d", len(transformed_df))
    return transformed_df   
