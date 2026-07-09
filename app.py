"""No-code pandas dashboard. Streamlit UI only — all logic lives in transforms/."""
import io

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from transforms import cleaning, editing, encoding, scaling

st.set_page_config(page_title="No-Code Data Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    .block-container {padding-top: 3rem;}
    div[data-testid="stButton"] button {width: 100%;}
    </style>
    """,
    unsafe_allow_html=True,
)

PANEL_HEIGHT = 700

if "original_df" not in st.session_state:
    st.session_state.original_df = None
if "steps" not in st.session_state:
    st.session_state.steps = []
if "editor_key_version" not in st.session_state:
    st.session_state.editor_key_version = 0


def apply_step(df, step):
    name, params = step["name"], step["params"]
    fn_map = {
        "drop_na": cleaning.drop_na,
        "drop_na_columns": cleaning.drop_na_columns,
        "fill_na": cleaning.fill_na,
        "drop_duplicates": cleaning.drop_duplicates,
        "change_dtype": cleaning.change_dtype,
        "select_columns": editing.select_columns,
        "drop_columns": editing.drop_columns,
        "rename_columns": editing.rename_columns,
        "filter_rows": editing.filter_rows,
        "scale": scaling.scale,
        "one_hot_encode": encoding.one_hot_encode,
        "label_encode": encoding.label_encode,
    }
    if name == "manual_edit":
        return editing.apply_manual_edits(df, params["edited_df"])
    if name not in fn_map:
        raise ValueError(f"Unknown step: {name}")
    return fn_map[name](df, **params)


def replay(original_df, steps):
    df = original_df.copy()
    for step in steps:
        df = apply_step(df, step)
    return df


def add_step(name, params):
    st.session_state.steps.append({"name": name, "params": params})
    st.session_state.editor_key_version += 1


def get_current_df():
    if st.session_state.original_df is None:
        return None
    return replay(st.session_state.original_df, st.session_state.steps)


def dfs_differ(df_a: pd.DataFrame, df_b: pd.DataFrame) -> bool:
    """Robust comparison that doesn't blow up on dtype/index mismatches."""
    try:
        if df_a.shape != df_b.shape:
            return True
        if list(df_a.columns) != list(df_b.columns):
            return True
        a = df_a.reset_index(drop=True)
        b = df_b.reset_index(drop=True)
        return not a.astype(str).equals(b.astype(str))
    except Exception:
        return True


def step_to_code(step):
    name, p = step["name"], step["params"]
    templates = {
        "drop_na": lambda: f"df = df.dropna(subset={p.get('cols')}, how='{p.get('how','any')}')",
        "drop_na_columns": lambda: f"df = df.dropna(axis=1, how='{p.get('how','any')}')",
        "fill_na": lambda: f"df[{p['cols']}] = df[{p['cols']}].fillna(strategy='{p['strategy']}')",
        "drop_duplicates": lambda: f"df = df.drop_duplicates(subset={p.get('cols')})",
        "change_dtype": lambda: f"df['{p['col']}'] = df['{p['col']}'].astype('{p['dtype']}')",
        "select_columns": lambda: f"df = df[{p['cols']}]",
        "drop_columns": lambda: f"df = df.drop(columns={p['cols']})",
        "rename_columns": lambda: f"df = df.rename(columns={p['mapping']})",
        "filter_rows": lambda: f"df = df[df['{p['col']}'] {p['op']} {p['value']!r}]",
        "manual_edit": lambda: "df = <manual cell edits applied via data editor>",
        "scale": lambda: f"df[{p['cols']}] = {p['method']}_scaler.fit_transform(df[{p['cols']}])",
        "one_hot_encode": lambda: f"df = pd.get_dummies(df, columns={p['cols']})",
        "label_encode": lambda: f"df['{p['col']}'] = LabelEncoder().fit_transform(df['{p['col']}'])",
    }
    return templates.get(name, lambda: f"# unknown step: {name}")()


with st.sidebar:
    st.markdown("### 📁 Data Source")
    upload = st.file_uploader("Upload file", type=["csv", "xlsx", "xls", "json"], label_visibility="collapsed")
    url = st.text_input("...or paste a URL", placeholder="https://...")

    if st.button("Load data", type="primary"):
        try:
            if upload is not None:
                if upload.name.endswith(".csv"):
                    df = pd.read_csv(upload)
                elif upload.name.endswith((".xlsx", ".xls")):
                    df = pd.read_excel(upload)
                else:
                    df = pd.read_json(upload)
            elif url:
                df = pd.read_json(url) if url.endswith(".json") else pd.read_csv(url)
            else:
                df = None
            if df is not None:
                st.session_state.original_df = df
                st.session_state.steps = []
                st.session_state.editor_key_version += 1
                st.success(f"Loaded {df.shape[0]} rows x {df.shape[1]} cols")
        except Exception as e:
            st.error(f"Failed to load: {e}")

    st.divider()
    st.markdown("### 🕒 Step History")

    if st.session_state.steps:
        for i, step in enumerate(st.session_state.steps):
            c1, c2 = st.columns([4, 1])
            c1.caption(f"{i+1}. **{step['name']}**")
            if c2.button("✕", key=f"rm_{i}", help="Remove this step"):
                st.session_state.steps.pop(i)
                st.session_state.editor_key_version += 1
                st.rerun()
        if st.button("🗑️ Reset all steps"):
            st.session_state.steps = []
            st.session_state.editor_key_version += 1
            st.rerun()
    else:
        st.caption("No steps applied yet.")

if st.session_state.original_df is None:
    st.title("📊 No-Code Pandas Dashboard")
    st.info("👆 Upload a dataset from the sidebar to get started.")
    st.stop()

current_df = get_current_df()
numeric_cols = current_df.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = current_df.select_dtypes(exclude=[np.number]).columns.tolist()
all_cols = list(current_df.columns)

with st.sidebar:
    st.divider()
    st.markdown("### ⬇️ Downloads")

    csv_bytes = current_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv_bytes, file_name="cleaned_data.csv", mime="text/csv", key="dl_csv")

    json_bytes = current_df.to_json(orient="records").encode("utf-8")
    st.download_button("Download JSON", data=json_bytes, file_name="cleaned_data.json", mime="application/json", key="dl_json")

    excel_buffer = io.BytesIO()
    current_df.to_excel(excel_buffer, index=False, engine="openpyxl")
    st.download_button(
        "Download Excel",
        data=excel_buffer.getvalue(),
        file_name="cleaned_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_excel",
    )

    code_lines = ["import pandas as pd", "", "df = pd.read_csv('your_file.csv')", ""]
    for step in st.session_state.steps:
        code_lines.append(step_to_code(step))
    code_str = "\n".join(code_lines)
    st.download_button("Download pandas code (.py)", data=code_str.encode("utf-8"), file_name="pipeline.py", mime="text/x-python", key="dl_code")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Rows", current_df.shape[0])
m2.metric("Columns", current_df.shape[1])
m3.metric("Missing", int(current_df.isna().sum().sum()))
m4.metric("Memory (KB)", f"{current_df.memory_usage(deep=True).sum() / 1024:.1f}")

left, right = st.columns([1, 1], gap="medium")

with left:
    st.markdown("#### ✏️ Dataset (live)")
    left_container = st.container(height=PANEL_HEIGHT, border=True)
    with left_container:
        edited = st.data_editor(
            current_df,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{st.session_state.editor_key_version}",
        )
    ac1, ac2 = st.columns([1, 2])
    with ac1:
        apply_clicked = st.button("💾 Apply manual edits", type="primary")
    if apply_clicked:
        if dfs_differ(edited, current_df):
            add_step("manual_edit", {"edited_df": edited})
            st.rerun()
        else:
            ac2.info("No changes detected — edit a cell, add/delete a row, then click Apply.")

with right:
    st.markdown("#### ⚙️ Operations")
    right_container = st.container(height=PANEL_HEIGHT, border=True)
    with right_container:
        sec_clean, sec_cols, sec_transform, sec_stats, sec_viz, sec_code = st.tabs(
            ["🧹 Clean", "🔧 Columns", "🔬 Scale/Encode", "📉 Stats", "📈 Chart", "🐍 Code"]
        )

        with sec_clean:
            na_counts = current_df.isna().sum()
            na_counts = na_counts[na_counts > 0]
            if not na_counts.empty:
                st.dataframe(na_counts.rename("NA count"), use_container_width=True, height=100)
            else:
                st.caption("No missing values ✅")

            st.markdown("**Drop NA rows**")
            drop_cols = st.multiselect("Subset (optional)", options=all_cols, key="drop_na_cols")
            drop_how = st.radio("How", ["any", "all"], key="drop_na_how", horizontal=True)
            if st.button("Drop NA rows", key="btn_drop_na"):
                add_step("drop_na", {"cols": drop_cols or None, "how": drop_how})
                st.rerun()

            st.markdown("**Fill NA**")
            fill_cols = st.multiselect("Columns", options=all_cols, key="fill_na_cols")
            fill_strategy = st.selectbox("Strategy", ["mean", "median", "mode", "constant", "ffill", "bfill"], key="fill_strategy")
            fill_value = st.text_input("Constant value", key="fill_value") if fill_strategy == "constant" else None
            if st.button("Fill NA", key="btn_fill_na"):
                add_step("fill_na", {"cols": fill_cols, "strategy": fill_strategy, "value": fill_value})
                st.rerun()

            st.markdown("**Other**")
            cd1, cd2 = st.columns(2)
            if cd1.button("Drop duplicates"):
                add_step("drop_duplicates", {"cols": None})
                st.rerun()
            dtype_col = cd2.selectbox("Col", options=all_cols, key="dtype_col", label_visibility="collapsed")
            dtype_target = st.selectbox("New dtype", ["str", "int", "float", "datetime", "category"], key="dtype_target")
            if st.button("Change dtype"):
                add_step("change_dtype", {"col": dtype_col, "dtype": dtype_target})
                st.rerun()

        with sec_cols:
            cols_to_drop = st.multiselect("Drop columns", options=all_cols, key="cols_to_drop")
            if st.button("Drop selected columns"):
                add_step("drop_columns", {"cols": cols_to_drop})
                st.rerun()

            st.markdown("**Rename**")
            rc1, rc2 = st.columns(2)
            old_name = rc1.selectbox("Column", options=all_cols, key="rename_old")
            new_name = rc2.text_input("New name", key="rename_new")
            if st.button("Rename column"):
                if new_name:
                    add_step("rename_columns", {"mapping": {old_name: new_name}})
                    st.rerun()

            st.markdown("**Filter rows**")
            fc1, fc2 = st.columns(2)
            filter_col = fc1.selectbox("Column", options=all_cols, key="filter_col")
            filter_op = fc2.selectbox("Op", ["==", "!=", ">", "<", ">=", "<=", "contains"], key="filter_op")
            filter_val = st.text_input("Value", key="filter_val")
            if st.button("Apply filter"):
                val = filter_val
                try:
                    val = float(filter_val)
                except ValueError:
                    pass
                add_step("filter_rows", {"col": filter_col, "op": filter_op, "value": val})
                st.rerun()

        with sec_transform:
            st.markdown("**Scaling**")
            scale_cols = st.multiselect("Numeric columns", options=numeric_cols, key="scale_cols")
            scale_method = st.selectbox("Method", ["standard", "minmax", "robust"], key="scale_method")
            if st.button("Apply scaling"):
                add_step("scale", {"cols": scale_cols, "method": scale_method})
                st.rerun()

            st.markdown("**Encoding**")
            onehot_cols = st.multiselect("One-hot encode", options=cat_cols, key="onehot_cols")
            if st.button("Apply one-hot"):
                add_step("one_hot_encode", {"cols": onehot_cols, "drop_first": False})
                st.rerun()

            label_col = st.selectbox("Label encode", options=cat_cols if cat_cols else ["-"], key="label_col")
            if st.button("Apply label encode"):
                if cat_cols:
                    add_step("label_encode", {"col": label_col})
                    st.rerun()

        with sec_stats:
            st.dataframe(current_df.describe(include="all").transpose(), use_container_width=True, height=220)
            if len(numeric_cols) >= 2:
                corr = current_df[numeric_cols].corr()
                fig = px.imshow(corr, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r")
                st.plotly_chart(fig, use_container_width=True)
            vc_col = st.selectbox("Value counts for", options=all_cols, key="vc_col")
            st.dataframe(current_df[vc_col].value_counts().rename("count"), use_container_width=True, height=150)

        with sec_viz:
            vc1, vc2, vc3 = st.columns(3)
            chart_type = vc1.selectbox("Chart", ["Histogram", "Box", "Scatter", "Bar", "Line", "Pie"])
            x_col = vc2.selectbox("X / value", options=all_cols)
            y_col = None
            if chart_type in ("Scatter", "Bar", "Line"):
                y_col = vc3.selectbox("Y", options=all_cols)
            try:
                if chart_type == "Histogram":
                    fig = px.histogram(current_df, x=x_col)
                elif chart_type == "Box":
                    fig = px.box(current_df, y=x_col)
                elif chart_type == "Pie":
                    fig = px.pie(current_df, names=x_col)
                elif chart_type == "Scatter":
                    fig = px.scatter(current_df, x=x_col, y=y_col)
                elif chart_type == "Bar":
                    fig = px.bar(current_df, x=x_col, y=y_col)
                elif chart_type == "Line":
                    fig = px.line(current_df, x=x_col, y=y_col)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not render chart: {e}")

        with sec_code:
            lines = ["import pandas as pd", "", "df = pd.read_csv('your_file.csv')", ""]
            for step in st.session_state.steps:
                lines.append(step_to_code(step))
            st.code("\n".join(lines), language="python")