import pandas as pd
import pytest
from transforms import scaling


def make_df():
    return pd.DataFrame({"a": [1, 2, 3, 4], "b": [10, 20, 30, 40]})


def test_scale_standard():
    df = make_df()
    out = scaling.scale(df, ["a", "b"], method="standard")
    assert out["a"].mean() == pytest.approx(0, abs=1e-9)
    assert out["a"].std(ddof=0) == pytest.approx(1, abs=1e-6)


def test_scale_minmax():
    df = make_df()
    out = scaling.scale(df, ["a"], method="minmax")
    assert out["a"].min() == 0
    assert out["a"].max() == 1


def test_scale_robust():
    df = make_df()
    out = scaling.scale(df, ["a"], method="robust")
    assert out["a"].median() == pytest.approx(0, abs=1e-6)


def test_scale_invalid_method():
    df = make_df()
    with pytest.raises(ValueError):
        scaling.scale(df, ["a"], method="bogus")