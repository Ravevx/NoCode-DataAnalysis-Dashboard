import pandas as pd
import numpy as np
import pytest
from transforms import cleaning


def make_df():
    return pd.DataFrame({
        "a": [1, 2, np.nan, 4],
        "b": [10, 20, 30, np.nan],
        "c": ["x", "y", "x", "x"],
    })


def test_drop_na_rows():
    df = make_df()
    out = cleaning.drop_na(df, cols=["a"])
    assert out["a"].isna().sum() == 0
    assert len(out) == 3


def test_drop_na_columns():
    df = make_df()
    out = cleaning.drop_na_columns(df, how="any")
    assert "a" not in out.columns
    assert "b" not in out.columns
    assert "c" in out.columns


def test_fill_na_mean():
    df = make_df()
    out = cleaning.fill_na(df, cols=["a"], strategy="mean")
    assert out["a"].isna().sum() == 0
    assert out["a"].iloc[2] == pytest.approx((1 + 2 + 4) / 3)


def test_fill_na_constant():
    df = make_df()
    out = cleaning.fill_na(df, cols=["b"], strategy="constant", value=0)
    assert out["b"].iloc[3] == 0


def test_fill_na_ffill():
    df = make_df()
    out = cleaning.fill_na(df, cols=["a"], strategy="ffill")
    assert out["a"].iloc[2] == 2


def test_drop_duplicates():
    df = pd.DataFrame({"a": [1, 1, 2], "b": [1, 1, 2]})
    out = cleaning.drop_duplicates(df)
    assert len(out) == 2


def test_change_dtype_int():
    df = pd.DataFrame({"a": ["1", "2", "3"]})
    out = cleaning.change_dtype(df, "a", "int")
    assert str(out["a"].dtype) == "Int64"


def test_change_dtype_datetime():
    df = pd.DataFrame({"a": ["2024-01-01", "2024-02-01"]})
    out = cleaning.change_dtype(df, "a", "datetime")
    assert pd.api.types.is_datetime64_any_dtype(out["a"])


def test_change_dtype_category():
    df = pd.DataFrame({"a": ["x", "y", "x"]})
    out = cleaning.change_dtype(df, "a", "category")
    assert str(out["a"].dtype) == "category"
