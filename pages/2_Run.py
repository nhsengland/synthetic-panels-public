import streamlit as st
import pandas as pd

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from style import apply_nhs_style, require_configuration

apply_nhs_style()
require_configuration()
st.header("Run Pipeline")

# --- Check prerequisites ---
if "texts" not in st.session_state or not st.session_state.texts:
    st.warning("Please add at least one message variant on the Setup page.")
    st.stop()

if "demographics" not in st.session_state:
    st.warning("Please configure demographics on the Setup page.")
    st.stop()

# --- Initialize defaults for question/scale if not set ---
if "question" not in st.session_state:
    from inputs.input_texts import question as default_question, scale as default_scale
    st.session_state.question = default_question.strip()
    st.session_state.scale = default_scale.strip()

if "behaviours" not in st.session_state:
    from inputs.behavoural_traits import behavioural_dimensions
    st.session_state.behaviours = {k: dict(v["weights"]) for k, v in behavioural_dimensions.items()}
    st.session_state.behaviours_enabled = {k: v.get("include", True) for k, v in behavioural_dimensions.items()}

# --- Summary ---
st.subheader("Run Summary")
params = st.session_state.params

if params.get("outcome"):
    st.markdown(f"**Outcome:** {params['outcome']}")
if params.get("intervention_channel"):
    st.markdown(f"**Channel:** {params['intervention_channel']}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Run Name", params["run_name"])
    st.metric("Model", params["model"].split(".")[-1])
with col2:
    if params["enable_power_analysis"]:
        st.metric("Sample Size", "Auto (power analysis)")
    else:
        st.metric("Sample Size (N)", params["N"])
    scale_range = params["answer_type"]["scale"]
    st.metric("Scale", f"{scale_range[0]} - {scale_range[1]}")
with col3:
    st.metric("Message Variants", len(st.session_state.texts))
    if params["binary_threshold"] is not None:
        st.metric("Binary Threshold", f">= {params['binary_threshold']}")

st.subheader("Message Variants")
texts_display = pd.DataFrame(
    [{"Variant": k, "Content": v} for k, v in st.session_state.texts.items()]
)
st.dataframe(texts_display, width='stretch', hide_index=True)

# --- Population / traits that will be used ---
st.subheader("Population Used")
enabled_flags = st.session_state.get("behaviours_enabled", {})
enabled_traits = [t for t in st.session_state.behaviours if enabled_flags.get(t, True)]

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Demographics**")
    demo_enabled_flags = st.session_state.get("demographics_enabled", {})
    all_demo_dims = list(st.session_state.demographics.keys()) if not params.get("use_census_data") else ["age", "gender", "ethnicity", "deprivation_level"]
    enabled_demos = [d for d in all_demo_dims if demo_enabled_flags.get(d, True)]
    st.markdown(f"**{len(enabled_demos)}** demographic traits enabled:")
    st.write(", ".join(d.replace("_", " ").title() for d in enabled_demos) if enabled_demos else "_None enabled_")
    if params.get("use_census_data"):
        st.write(f"Census data — area: `{params.get('ltla', 'England')}`")

with col2:
    st.markdown(f"**Behavioural traits — {len(enabled_traits)} enabled**")
    st.write(", ".join(enabled_traits) if enabled_traits else "_None enabled_")

# Warn about any enabled trait / used demographic with no positive weight
zero_weight = [t for t in enabled_traits if sum(st.session_state.behaviours[t].values()) <= 0]
if not params.get("use_census_data"):
    zero_weight += [f"demographic:{d}" for d, cats in st.session_state.demographics.items()
                    if sum(cats.values()) <= 0]
if zero_weight:
    st.warning(f"These have no positive weight and will break sampling: {', '.join(zero_weight)}")

# --- Run ---
st.divider()

st.caption("This may take several minutes depending on sample size and number of message variants.")

if st.button("Run Pipeline", type="primary", width='stretch'):
    from src.pipeline_runner import run_pipeline

    status_text = st.empty()

    def status_callback(message):
        status_text.info(message)

    # Determine which demographic dimensions are enabled
    demo_enabled_flags = st.session_state.get("demographics_enabled", {})
    all_demo_dims = ["age", "gender", "ethnicity", "deprivation_level"] if params.get("use_census_data") else list(st.session_state.demographics.keys())
    enabled_demographic_dims = [d for d in all_demo_dims if demo_enabled_flags.get(d, True)]

    # Ethnicity must always be generated (needed for name generation) even when
    # hidden from the prompt.  If the user disabled ethnicity, keep it in the
    # generation list but add it to the "hide from prompt" list instead.
    hide_demographics_from_prompt = []
    if not demo_enabled_flags.get("ethnicity", True):
        if "ethnicity" not in enabled_demographic_dims:
            enabled_demographic_dims.append("ethnicity")
        hide_demographics_from_prompt.append("ethnicity")

    # Ensure ethnicity distributions are available for generation even when hidden
    demographics_for_pipeline = dict(st.session_state.demographics)
    if "ethnicity" not in demographics_for_pipeline and hide_demographics_from_prompt:
        from inputs.demographic_distributions import get_demographic_distributions
        default_dists = get_demographic_distributions()
        if "ethnicity" in default_dists:
            demographics_for_pipeline["ethnicity"] = default_dists["ethnicity"]

    try:
        with st.spinner("Running pipeline..."):
            results = run_pipeline(
                params=params,
                texts=st.session_state.texts,
                question=st.session_state.question,
                scale=st.session_state.scale,
                behaviours={k: v for k, v in st.session_state.behaviours.items()
                            if st.session_state.get("behaviours_enabled", {}).get(k, True)},
                demographics=demographics_for_pipeline,
                enabled_demographic_dims=enabled_demographic_dims,
                hide_demographics_from_prompt=hide_demographics_from_prompt,
                status_callback=status_callback,
            )
        status_text.empty()
        st.session_state.results = results
        st.success(f"Run complete! Results saved to: {results['run_dir']}")
        st.info("Navigate to the **Results** page to explore outputs.")
    except Exception as e:
        st.error(f"Pipeline failed: {e}")
        raise
