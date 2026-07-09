
import pandas as pd
from transforms import encoding


def make_df():
    return pd.DataFrame({"a": [1, 2, 3, 4], "cat": ["x", "y", "x", "z"]})


def test_one_hot_encode():
    df = make_df()
    out = encoding.one_hot_encode(df, ["cat"])
    assert "cat_x" in out.columns
    assert "cat_y" in out.columns
    assert "cat_z" in out.columns
    assert "cat" not in out.columns


def test_one_hot_encode_drop_first():
    df = make_df()
    out = encoding.one_hot_encode(df, ["cat"], drop_first=True)
    assert len(out.columns) == len(df.columns) - 1 + (df["cat"].nunique() - 1)


def test_label_encode():
    df = make_df()
    out = encoding.label_encode(df, "cat")
    assert out["cat"].dtype.kind in "iu"
