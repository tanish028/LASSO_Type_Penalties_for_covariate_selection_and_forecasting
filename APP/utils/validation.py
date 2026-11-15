"""Small checks on the saved result files. A failed check raises DataProblem; pages show it as a message and never invent values."""
import pandas as pd


class DataProblem(Exception):
    pass


def require_columns(df, cols, name):
    miss = [c for c in cols if c not in df.columns]
    if miss:
        raise DataProblem(f"{name}: missing columns {miss}")
    return df


def require_numeric(df, cols, name):
    for c in cols:
        if not pd.api.types.is_numeric_dtype(df[c]):
            raise DataProblem(f"{name}: column '{c}' is not numeric")
    return df


def require_nonempty(df, name):
    if df is None or len(df) == 0:
        raise DataProblem(f"{name}: no rows")
    return df
