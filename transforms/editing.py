"""Pure row/column editing functions. No Streamlit imports."""
import pandas as pd


def select_columns(df: pd.DataFrame, cols) -> pd.DataFrame:
    """Keep only the given columns, in the given order."""
    return df[cols]


def drop_columns(df: pd.DataFrame, cols) -> pd.DataFrame:
    """Drop the given columns."""
    return df.drop(columns=cols)


def rename_columns(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Rename columns using a {old_name: new_name} mapping."""
    return df.rename(columns=mapping)


def filter_rows(df: pd.DataFrame, col: str, op: str, value) -> pd.DataFrame:
    """Filter rows on a single column condition.

    op: '==' | '!=' | '>' | '<' | '>=' | '<=' | 'contains'
    """
    if op == "==":
        return df[df[col] == value]
    elif op == "!=":
        return df[df[col] != value]
    elif op == ">":
        return df[df[col] > value]
    elif op == "<":
        return df[df[col] < value]
    elif op == ">=":
        return df[df[col] >= value]
    elif op == "<=":
        return df[df[col] <= value]
    elif op == "contains":
        return df[df[col].astype(str).str.contains(str(value), na=False)]
    else:
        raise ValueError(f"Unknown operator: {op}")


def apply_manual_edits(df: pd.DataFrame, edited_df: pd.DataFrame) -> pd.DataFrame:
    """Accept edits made directly in st.data_editor as a full replacement."""

    return edited_df.copy()


