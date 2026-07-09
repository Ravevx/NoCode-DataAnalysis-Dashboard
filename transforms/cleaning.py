"""Pure pandas cleaning functions. No Streamlit imports allowed here."""
import pandas as pd


def drop_na(df: pd.DataFrame, cols=None, how="any", thresh=None) -> pd.DataFrame:
    """Drop rows with missing values.

    how: 'any' or 'all'. Ignored if thresh is set.
    thresh: minimum number of non-NA values required to keep the row.
    cols: subset of columns to check; None = check all columns.
    """
    if thresh is not None:
        return df.dropna(axis=0, thresh=thresh, subset=cols)
    return df.dropna(axis=0, how=how, subset=cols)


def drop_na_columns(df: pd.DataFrame, how="any", thresh=None) -> pd.DataFrame:
    """Drop columns with missing values."""
    if thresh is not None:
        return df.dropna(axis=1, thresh=thresh)
    return df.dropna(axis=1, how=how)


def fill_na(df: pd.DataFrame, cols, strategy="mean", value=None) -> pd.DataFrame:
    """Fill missing values in given columns.

    strategy: 'mean' | 'median' | 'mode' | 'constant' | 'ffill' | 'bfill'
    value: required if strategy == 'constant'
    """
    df = df.copy()
    for c in cols:
        if strategy == "mean":
            df[c] = df[c].fillna(df[c].mean())
        elif strategy == "median":
            df[c] = df[c].fillna(df[c].median())
        elif strategy == "mode":
            mode_val = df[c].mode()
            if not mode_val.empty:
                df[c] = df[c].fillna(mode_val.iloc[0])
        elif strategy == "constant":
            df[c] = df[c].fillna(value)
        elif strategy == "ffill":
            df[c] = df[c].ffill()
        elif strategy == "bfill":
            df[c] = df[c].bfill()
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    return df


def drop_duplicates(df: pd.DataFrame, cols=None, keep="first") -> pd.DataFrame:
    """Drop duplicate rows, optionally based on a subset of columns."""
    return df.drop_duplicates(subset=cols, keep=keep)


def change_dtype(df: pd.DataFrame, col: str, dtype: str) -> pd.DataFrame:
    """Cast a column to a new dtype.

    dtype: 'str' | 'int' | 'float' | 'datetime' | 'category'
    """
    df = df.copy()
    if dtype == "datetime":
        df[col] = pd.to_datetime(df[col], errors="coerce")
    elif dtype == "category":
        df[col] = df[col].astype("category")
    elif dtype == "int":
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    elif dtype == "float":
        df[col] = pd.to_numeric(df[col], errors="coerce")
    elif dtype == "str":
        df[col] = df[col].astype(str)
    else:
        raise ValueError(f"Unknown dtype: {dtype}")
    return df

