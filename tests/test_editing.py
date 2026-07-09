
import pandas as pd
import pytest
from transforms import editing


def make_df():
    return pd.DataFrame({"a": [1, 2, 3, 4], "b": [10, 20, 30, 40], "c": ["x", "y", "x", "z"]})


def test_select_columns():
    df = make_df()
    out = editing.select_columns(df, ["a", "c"])
    assert list(out.columns) == ["a", "c"]


def test_drop_columns():
    df = make_df()
    out = editing.drop_columns(df, ["b"])
    assert "b" not in out.columns


def test_rename_columns():
    df = make_df()
    out = editing.rename_columns(df, {"a": "alpha"})
    assert "alpha" in out.columns
    assert "a" not in out.columns


def test_filter_rows_gt():
    df = make_df()
    out = editing.filter_rows(df, "a", ">", 2)
    assert out["a"].min() > 2


def test_filter_rows_contains():
    df = make_df()
    out = editing.filter_rows(df, "c", "contains", "x")
    assert set(out["c"].unique()) == {"x"}


def test_filter_rows_invalid_op():
    df = make_df()
    with pytest.raises(ValueError):
        editing.filter_rows(df, "a", "bogus", 1)


def test_apply_manual_edits():
    df = make_df()
    edited = df.copy()
    edited.loc[0, "a"] = 99
    out = editing.apply_manual_edits(df, edited)

import pandas as pd
import pytest
from transforms import editing


def make_df():
    return pd.DataFrame({"a": [1, 2, 3, 4], "b": [10, 20, 30, 40], "c": ["x", "y", "x", "z"]})


def test_select_columns():
    df = make_df()
    out = editing.select_columns(df, ["a", "c"])
    assert list(out.columns) == ["a", "c"]


def test_drop_columns():
    df = make_df()
    out = editing.drop_columns(df, ["b"])
    assert "b" not in out.columns


def test_rename_columns():
    df = make_df()
    out = editing.rename_columns(df, {"a": "alpha"})
    assert "alpha" in out.columns
    assert "a" not in out.columns


def test_filter_rows_gt():
    df = make_df()
    out = editing.filter_rows(df, "a", ">", 2)
    assert out["a"].min() > 2


def test_filter_rows_contains():
    df = make_df()
    out = editing.filter_rows(df, "c", "contains", "x")
    assert set(out["c"].unique()) == {"x"}


def test_filter_rows_invalid_op():
    df = make_df()
    with pytest.raises(ValueError):
        editing.filter_rows(df, "a", "bogus", 1)


def test_apply_manual_edits():
    df = make_df()
    edited = df.copy()
    edited.loc[0, "a"] = 99
    out = editing.apply_manual_edits(df, edited)
    assert out.loc[0, "a"] == 99