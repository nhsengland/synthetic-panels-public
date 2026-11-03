import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zipfile
import io
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from style import apply_nhs_style
from src.evaluate import prepare_chart_data

apply_nhs_style()
st.markdown("<style>.block-container { max-width: 1100px !important; }</style>", unsafe_allow_html=True)
st.header("Results")


def load_run_from_dir(run_dir):
    """Load results from a past run directory."""
    results_path = os.path.join(run_dir, "results.csv")
    patients_path = os.path.join(run_dir, "patients.csv")
    bias_path = os.path.join(run_dir, "bias_judgements.csv")
    report_path = os.path.join(run_dir, "evaluation_report.md")
    params_path = os.path.join(run_dir, "params.json")

    if not os.path.exists(results_path):
        return None

    results_df = pd.read_csv(results_path)
    patients_df = pd.read_csv(patients_path) if os.path.exists(patients_path) else pd.DataFrame()
    bias_df = pd.read_csv(bias_path) if os.path.exists(bias_path) else pd.DataFrame()
    params = {}
    if os.path.exists(params_path):
        with open(params_path) as f:
            params = json.load(f)
    report_md = ""
    if os.path.exists(report_path):
        with open(report_path) as f:
            report_md = f.read()

    return {
        "results_df": results_df,
        "patients_df": patients_df,
        "bias_df": bias_df,
        "report_md": report_md,
        "run_dir": run_dir,
        "params": params,
    }


# --- Source selection: current session or past run ---
data_dir = os.path.join(Path(__file__).resolve().parent.parent, "data")
past_runs = []
if os.path.isdir(data_dir):
    past_runs = sorted(
        [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))],
        reverse=True,
    )

has_session_results = "results" in st.session_state and st.session_state.results is not None

if not has_session_results and not past_runs:
    st.info("No results yet. Run the pipeline first, or place past runs in the `data/` folder.")
    st.stop()

source_options = []
if has_session_results:
    source_options.append("Current session")
source_options.extend(past_runs)

default_run = "scale_test_2_2026-06-29_13-40-45"
default_index = 0
if not has_session_results and default_run in source_options:
    default_index = source_options.index(default_run)
    st.info(f"No run completed this session. Showing default run: **{default_run}**")

selected_source = st.selectbox("Select run", source_options, index=default_index)

if selected_source == "Current session":
    results = st.session_state.results
else:
    results = load_run_from_dir(os.path.join(data_dir, selected_source))
    if results is None:
        st.error(f"Could not load results from `data/{selected_source}/` (no results.csv found).")
        st.stop()

results_df = results["results_df"]
patients_df = results["patients_df"]
bias_df = results["bias_df"]
report_md = results["report_md"]
run_dir = results["run_dir"]
run_params = results.get("params", {}) or st.session_state.get("params", {})

binary_threshold = run_params.get("binary_threshold")
if binary_threshold is None and isinstance(run_params.get("answer_type"), dict):
    scale = run_params.get("answer_type", {}).get("scale", [0, 1])
    if scale and len(scale) == 2 and scale[1] - scale[0] <= 1:
        binary_threshold = None

# --- Tabs ---
tab_report, tab_charts, tab_data, tab_download = st.tabs(["Report", "Charts", "Data Tables", "Download"])

# ============ REPORT TAB ============
with tab_report:
    if report_md:
        st.markdown(report_md)
    else:
        st.warning("No report generated.")

# ============ CHARTS TAB ============
with tab_charts:
    # Identify text columns (non-reasoning, non-patient_id)
    text_cols = [c for c in results_df.columns if not c.endswith("_reasoning") and c != "patient_id"]

    if not text_cols:
        st.warning("No result columns found.")
    else:
        numeric_df = prepare_chart_data(results_df, text_cols, binary_threshold=binary_threshold)

        # --- Overall Mean Scores ---
        if binary_threshold is not None:
            st.subheader("Yes Rate by Message Variant")
            means = numeric_df[text_cols].mean().reset_index()
            means.columns = ["Text", "Yes Rate"]
            fig = px.bar(means, x="Text", y="Yes Rate", color="Text", text_auto=".2%")
            fig.update_yaxes(tickformat=".0%")
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width='stretch')
        else:
            st.subheader("Mean Score by Message Variant")
            means = numeric_df[text_cols].mean().reset_index()
            means.columns = ["Text", "Mean Score"]
            fig = px.bar(means, x="Text", y="Mean Score", color="Text", text_auto=".2f")
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width='stretch')

        # --- Demographic Breakdown ---
        if binary_threshold is not None:
            st.subheader("Yes Rate by Demographic Group")
        else:
            st.subheader("Score by Demographic Group")
        merged = numeric_df.merge(patients_df, on="patient_id")
        demo_cols = [c for c in ["age_band", "gender", "ethnicity", "deprivation_level"] if c in merged.columns]

        if demo_cols:
            selected_demo = st.selectbox("Demographic dimension", demo_cols)
            melted = merged.melt(
                id_vars=["patient_id", selected_demo],
                value_vars=text_cols,
                var_name="Text",
                value_name="Score",
            )
            grouped = melted.groupby([selected_demo, "Text"])["Score"].mean().reset_index()
            if binary_threshold is not None:
                y_axis_label = "Yes Rate"
                text_format = ".0%"
            else:
                y_axis_label = "Score"
                text_format = ".2f"
            fig = px.bar(
                grouped, x="Text", y="Score", color=selected_demo,
                barmode="group", text_auto=text_format,
            )
            fig.update_yaxes(title=y_axis_label)
            if binary_threshold is not None:
                fig.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig, width='stretch')

            # --- Disparity Heatmap ---
            st.subheader("Disparity Heatmap")
            disparity_data = []
            for text_col in text_cols:
                group_means = merged.groupby(selected_demo)[text_col].mean()
                disparity = group_means.max() - group_means.min()
                disparity_data.append({"Text": text_col, "Disparity": disparity})
            disp_df = pd.DataFrame(disparity_data)
            fig = px.bar(disp_df, x="Text", y="Disparity", color="Text", text_auto=".3f")
            if binary_threshold is not None:
                fig.update_yaxes(title="Difference in Yes Rate")
                fig.update_traces(texttemplate='%{text:.3f}')
            fig.update_layout(showlegend=False, title=f"Max-Min Disparity by {selected_demo}")
            st.plotly_chart(fig, width='stretch')

        # --- Bias Analysis ---
        if bias_df is not None and not bias_df.empty:
            st.subheader("Bias Analysis")

            col1, col2 = st.columns(2)
            with col1:
                severity_counts = bias_df["bias_severity"].value_counts().sort_index().reset_index()
                severity_counts.columns = ["Severity", "Count"]
                fig = px.bar(severity_counts, x="Severity", y="Count", color="Severity",
                             title="Bias Severity Distribution")
                st.plotly_chart(fig, width='stretch')

            with col2:
                if "text_id" in bias_df.columns:
                    bias_rate = bias_df.groupby("text_id")["dangerous_bias_present"].mean().reset_index()
                    bias_rate.columns = ["Text", "Bias Rate"]
                    fig = px.bar(bias_rate, x="Text", y="Bias Rate", color="Text",
                                 title="Bias Rate by Text", text_auto=".2%")
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, width='stretch')

# ============ DATA TABLES TAB ============
with tab_data:
    st.subheader("Results")
    st.dataframe(results_df, width='stretch', height=400)

    st.subheader("Patients")
    st.dataframe(patients_df, width='stretch', height=400)

    if bias_df is not None and not bias_df.empty:
        st.subheader("Bias Judgements")
        st.dataframe(bias_df, width='stretch', height=400)

# ============ DOWNLOAD TAB ============
with tab_download:
    st.subheader("Download Outputs")

    col1, col2, col3 = st.columns(3)
    with col1:
        csv = results_df.to_csv(index=False)
        st.download_button("Download results.csv", csv, "results.csv", "text/csv")
    with col2:
        csv = patients_df.to_csv(index=False)
        st.download_button("Download patients.csv", csv, "patients.csv", "text/csv")
    with col3:
        if bias_df is not None and not bias_df.empty:
            csv = bias_df.to_csv(index=False)
            st.download_button("Download bias_judgements.csv", csv, "bias_judgements.csv", "text/csv")

    st.divider()

    if report_md:
        st.download_button("Download Report (Markdown)", report_md, "evaluation_report.md", "text/markdown")

    st.divider()
    st.subheader("Download All (ZIP)")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("results.csv", results_df.to_csv(index=False))
        zf.writestr("patients.csv", patients_df.to_csv(index=False))
        if bias_df is not None and not bias_df.empty:
            zf.writestr("bias_judgements.csv", bias_df.to_csv(index=False))
        if report_md:
            zf.writestr("evaluation_report.md", report_md)
    st.download_button("Download All as ZIP", zip_buffer.getvalue(), "synthetic_panels_results.zip", "application/zip")
