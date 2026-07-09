"""No-code pandas dashboard. Streamlit UI only — all logic lives in transforms/."""
import io

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from transforms import cleaning, editing, encoding, scaling

st.set_page_config(page_title="No-Code Data Dashboard", layout="wide")

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "original_df" not in st.session_state:
    st.session_state.original_df = None
if "steps" not in st.session_state:
    st.session_state.steps = []  # list of {"name": str, "params": dict}
if "editor_key_version" not in st.session_state:
    st.session_state.editor_key_version = 0


# ---------------------------------------------------------------------------
# Step registry: maps step name -> function + how to call it
# ---------------------------------------------------------------------------
def apply_step(df: pd.DataFrame, step: dict) -> pd.DataFrame:
    name = step["name"]
    params = step["params"]

    if name == "drop_na":
        return cleaning.drop_na(df, **params)
    if name == "drop_na_columns":
        return cleaning.drop_na_columns(df, **params)
    if name == "fill_na":
        return cleaning.fill_na(df, **params)
    if name == "drop_duplicates":
        return cleaning.drop_duplicates(df, **params)
    if name == "change_dtype":
        return cleaning.change_dtype(df, **params)
    if name == "select_columns":
        return editing.select_columns(df, **params)
    if name == "drop_columns":
        return editing.drop_columns(df, **params)
    if name == "rename_columns":
        return editing.rename_columns(df, **params)
    if name == "filter_rows":
        return editing.filter_rows(df, **params)
    if name == "manual_edit":
        return editing.apply_manual_edits(df, params["edited_df"])
    if name == "scale":
        return scaling.scale(df, **params)
    if name == "one_hot_encode":
        return encoding.one_hot_encode(df, **params)
    if name == "label_encode":
        return encoding.label_encode(df, **params)

    raise ValueError(f"Unknown step: {name}")


def replay(original_df: pd.DataFrame, steps: list) -> pd.DataFrame:
    df = original_df.copy()
    for step in steps:
        df = apply_step(df, step)
    return df


def add_step(name: str, params: dict):
    st.session_state.steps.append({"name": name, "params": params})
    st.session_state.editor_key_version += 1


def get_current_df() -> pd.DataFrame:
    if st.session_state.original_df is None:
        return None
    return replay(st.session_state.original_df, st.session_state.steps)


def step_to_code(step: dict) -> str:
    name, p = step["name"], step["params"]
    if name == "drop_na":
        return f"df = df.dropna(subset={p.get('cols')}, how='{p.get('how','any')}')"
    if name == "drop_na_columns":
        return f"df = df.dropna(axis=1, how='{p.get('how','any')}')"
    if name == "fill_na":
        return f"df[{p['cols']}] = df[{p['cols']}].fillna(strategy='{p['strategy']}')"
    if name == "drop_duplicates":
        return f"df = df.drop_duplicates(subset={p.get('cols')})"
    if name == "change_dtype":
        return f"df['{p['col']}'] = df['{p['col']}'].astype('{p['dtype']}')"
    if name == "select_columns":
        return f"df = df[{p['cols']}]"
    if name == "drop_columns":
        return f"df = df.drop(columns={p['cols']})"
    if name == "rename_columns":
        return f"df = df.rename(columns={p['mapping']})"
    if name == "filter_rows":
        return f"df = df[df['{p['col']}'] {p['op']} {p['value']!r}]"
    if name == "manual_edit":
        return "df = <manual cell edits applied via data editor>"
    if name == "scale":
        return f"df[{p['cols']}] = {p['method']}_scaler.fit_transform(df[{p['cols']}])"
    if name == "one_hot_encode":
        return f"df = pd.get_dummies(df, columns={p['cols']})"
    if name == "label_encode":
        return f"df['{p['col']}'] = LabelEncoder().fit_transform(df['{p['col']}'])"
    return f"# unknown step: {name}"


# ---------------------------------------------------------------------------
# Sidebar: upload + step history
# ---------------------------------------------------------------------------
st.sidebar.title("📁 Data Source")
upload = st.sidebar.file_uploader("Upload CSV / Excel / JSON", type=["csv", "xlsx", "xls", "json"])
url = st.sidebar.text_input("...or load from URL")

if st.sidebar.button("Load data"):
    try:
        if upload is not None:
            if upload.name.endswith(".csv"):
                df = pd.read_csv(upload)
            elif upload.name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(upload)
            elif upload.name.endswith(".json"):
                df = pd.read_json(upload)
            st.session_state.original_df = df
            st.session_state.steps = []
            st.session_state.editor_key_version += 1
            st.sidebar.success(f"Loaded {df.shape[0]} rows x {df.shape[1]} cols")
        elif url:
            if url.endswith(".csv"):
                df = pd.read_csv(url)
            elif url.endswith(".json"):
                df = pd.read_json(url)
            else:
                df = pd.read_csv(url)
            st.session_state.original_df = df
            st.session_state.steps = []
            st.session_state.editor_key_version += 1
            st.sidebar.success(f"Loaded {df.shape[0]} rows x {df.shape[1]} cols")
    except Exception as e:
        st.sidebar.error(f"Failed to load: {e}")

st.sidebar.divider()
st.sidebar.title("🕒 Step History")

if st.session_state.steps:
    for i, step in enumerate(st.session_state.steps):
        col1, col2 = st.sidebar.columns([4, 1])
        col1.text(f"{i+1}. {step['name']}")
        if col2.button("✕", key=f"remove_step_{i}"):
            st.session_state.steps.pop(i)
            st.session_state.editor_key_version += 1
            st.rerun()
    if st.sidebar.button("Reset all steps"):
        st.session_state.steps = []
        st.session_state.editor_key_version += 1
        st.rerun()
else:
    st.sidebar.caption("No steps applied yet.")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("📊 No-Code Pandas Dashboard")

if st.session_state.original_df is None:
    st.info("Upload a dataset from the sidebar to get started.")
    st.stop()

current_df = get_current_df()

tab_edit, tab_clean, tab_transform, tab_stats, tab_viz, tab_code, tab_export = st.tabs(
    ["✏️ Edit", "🧹 Clean", "🔧 Transform", "📈 Stats", "📉 Visualize", "🐍 Code", "⬇️ Export"]
)

# --- Edit tab ---
with tab_edit:
    st.subheader("Live data editor")
    st.caption(f"Shape: {current_df.shape[0]} rows x {current_df.shape[1]} cols | Memory: {current_df.memory_usage(deep=True).sum() / 1024:.1f} KB")

    edited = st.data_editor(
        current_df,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{st.session_state.editor_key_version}",
    )

    if st.button("Apply manual edits as step"):
        if not edited.equals(current_df):
            add_step("manual_edit", {"edited_df": edited})
            st.rerun()
        else:
            st.info("No changes detected.")

    st.divider()
    st.subheader("Column / row operations")

    c1, c2 = st.columns(2)
    with c1:
        cols_to_keep = st.multiselect("Select columns to keep", options=list(current_df.columns), default=list(current_df.columns))
        if st.button("Apply column selection"):
            add_step("select_columns", {"cols": cols_to_keep})
            st.rerun()

    with c2:
        cols_to_drop = st.multiselect("Select columns to drop", options=list(current_df.columns))
        if st.button("Drop selected columns"):
            add_step("drop_columns", {"cols": cols_to_drop})
            st.rerun()

    st.markdown("**Rename a column**")
    rc1, rc2, rc3 = st.columns([2, 2, 1])
    old_name = rc1.selectbox("Column", options=list(current_df.columns), key="rename_old")
    new_name = rc2.text_input("New name", key="rename_new")
    if rc3.button("Rename"):
        if new_name:
            add_step("rename_columns", {"mapping": {old_name: new_name}})
            st.rerun()

    st.markdown("**Filter rows**")
    fc1, fc2, fc3, fc4 = st.columns([2, 1, 2, 1])
    filter_col = fc1.selectbox("Column", options=list(current_df.columns), key="filter_col")
    filter_op = fc2.selectbox("Op", options=["==", "!=", ">", "<", ">=", "<=", "contains"], key="filter_op")
    filter_val = fc3.text_input("Value", key="filter_val")
    if fc4.button("Filter"):
        val = filter_val
        try:
            val = float(filter_val)
        except ValueError:
            pass
        add_step("filter_rows", {"col": filter_col, "op": filter_op, "value": val})
        st.rerun()

# --- Clean tab ---
with tab_clean:
    st.subheader("Missing values")
    na_counts = current_df.isna().sum()
    st.dataframe(na_counts[na_counts > 0].rename("NA count"), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Drop NA rows**")
        drop_cols = st.multiselect("Subset columns (optional)", options=list(current_df.columns), key="drop_na_cols")
        drop_how = st.selectbox("How", options=["any", "all"], key="drop_na_how")
        if st.button("Drop NA rows"):
            add_step("drop_na", {"cols": drop_cols or None, "how": drop_how})
            st.rerun()

    with c2:
        st.markdown("**Fill NA**")
        fill_cols = st.multiselect("Columns", options=list(current_df.columns), key="fill_na_cols")
        fill_strategy = st.selectbox("Strategy", options=["mean", "median", "mode", "constant", "ffill", "bfill"], key="fill_strategy")
        fill_value = None
        if fill_strategy == "constant":
            fill_value = st.text_input("Constant value", key="fill_value")
        if st.button("Fill NA"):
            add_step("fill_na", {"cols": fill_cols, "strategy": fill_strategy, "value": fill_value})
            st.rerun()

    st.divider()
    c3, c4 = st.columns(2)
    with c3:
        if st.button("Drop duplicate rows"):
            add_step("drop_duplicates", {"cols": None})
            st.rerun()

    with c4:
        st.markdown("**Change dtype**")
        dtype_col = st.selectbox("Column", options=list(current_df.columns), key="dtype_col")
        dtype_target = st.selectbox("New dtype", options=["str", "int", "float", "datetime", "category"], key="dtype_target")
        if st.button("Change dtype"):
            add_step("change_dtype", {"col": dtype_col, "dtype": dtype_target})
            st.rerun()

# --- Transform tab ---
with tab_transform:
    numeric_cols = current_df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = current_df.select_dtypes(exclude=[np.number]).columns.tolist()

    st.subheader("Scaling")
    scale_cols = st.multiselect("Numeric columns", options=numeric_cols, key="scale_cols")
    scale_method = st.selectbox("Method", options=["standard", "minmax", "robust"], key="scale_method")
    if st.button("Apply scaling"):
        add_step("scale", {"cols": scale_cols, "method": scale_method})
        st.rerun()

    st.divider()
    st.subheader("Encoding")
    e1, e2 = st.columns(2)
    with e1:
        onehot_cols = st.multiselect("One-hot encode columns", options=cat_cols, key="onehot_cols")
        if st.button("Apply one-hot encoding"):
            add_step("one_hot_encode", {"cols": onehot_cols, "drop_first": False})
            st.rerun()
    with e2:
        label_col = st.selectbox("Label encode column", options=cat_cols if cat_cols else ["-"], key="label_col")
        if st.button("Apply label encoding"):
            if cat_cols:
                add_step("label_encode", {"col": label_col})
                st.rerun()

# --- Stats tab ---
with tab_stats:
    st.subheader("Summary statistics")
    st.dataframe(current_df.describe(include="all").transpose(), use_container_width=True)

    st.subheader("Correlation matrix")
    numeric_df = current_df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] >= 2:
        corr = numeric_df.corr()
        fig = px.imshow(corr, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Need at least 2 numeric columns for correlation.")

    st.subheader("Value counts")
    vc_col = st.selectbox("Column", options=list(current_df.columns), key="vc_col")
    st.dataframe(current_df[vc_col].value_counts().rename("count"), use_container_width=True)

# --- Visualize tab ---
with tab_viz:
    chart_type = st.selectbox("Chart type", options=["Histogram", "Box", "Scatter", "Bar", "Line", "Pie"])
    all_cols = list(current_df.columns)

    if chart_type == "Histogram":
        col = st.selectbox("Column", options=all_cols)
        fig = px.histogram(current_df, x=col)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Box":
        col = st.selectbox("Column", options=all_cols)
        fig = px.box(current_df, y=col)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Scatter":
        x = st.selectbox("X axis", options=all_cols, key="scatter_x")
        y = st.selectbox("Y axis", options=all_cols, key="scatter_y")
        fig = px.scatter(current_df, x=x, y=y)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Bar":
        x = st.selectbox("X axis", options=all_cols, key="bar_x")
        y = st.selectbox("Y axis", options=all_cols, key="bar_y")
        fig = px.bar(current_df, x=x, y=y)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Line":
        x = st.selectbox("X axis", options=all_cols, key="line_x")
        y = st.selectbox("Y axis", options=all_cols, key="line_y")
        fig = px.line(current_df, x=x, y=y)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Pie":
        names = st.selectbox("Category column", options=all_cols, key="pie_names")
        fig = px.pie(current_df, names=names)
        st.plotly_chart(fig, use_container_width=True)

# --- Code tab ---
with tab_code:
    st.subheader("Generated pandas code")
    lines = ["import pandas as pd", "", "df = pd.read_csv('your_file.csv')", ""]
    for step in st.session_state.steps:
        lines.append(step_to_code(step))
    st.code("\n".join(lines), language="python")

# --- Export tab ---
with tab_export:
    st.subheader("Download cleaned dataset")
    csv_bytes = current_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download as CSV", data=csv_bytes, file_name="cleaned_data.csv", mime="text/csv")

    excel_buffer = io.BytesIO()
    current_df.to_excel(excel_buffer, index=False, engine="openpyxl")
    st.download_button(
        "Download as Excel",
        data=excel_buffer.getvalue(),
        file_name="cleaned_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

