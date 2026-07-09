"""Pure scaling functions. No Streamlit imports."""
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler


def scale(df: pd.DataFrame, cols, method="standard") -> pd.DataFrame:
    """Scale numeric columns.

    method: 'standard' | 'minmax' | 'robust'
    """
    df = df.copy()
    scalers = {
        "standard": StandardScaler(),
        "minmax": MinMaxScaler(),
        "robust": RobustScaler(),
    }
    if method not in scalers:
        raise ValueError(f"Unknown scaling method: {method}")
    scaler = scalers[method]
    df[cols] = scaler.fit_transform(df[cols])
    return df
