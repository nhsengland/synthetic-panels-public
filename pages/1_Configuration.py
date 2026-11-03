import streamlit as st
import pandas as pd
import sys
import copy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from style import apply_nhs_style
from config.params import params as default_params
#from inputs.input_texts import question as default_question, scale as default_scale, texts as default_texts
from inputs.demographic_distributions import get_demographic_distributions
from inputs.behavoural_traits import behavioural_dimensions as default_behaviours
from inputs.scenario_presets import scenario_presets


apply_nhs_style()
st.header("Study Setup")


def _frame_to_dist(frame, key_col):
    """Convert an edited data_editor frame into a {name: weight} dict, skipping blanks."""
    dist = {}
    for _, row in frame.iterrows():
        name = str(row[key_col]).strip()
        weight = row["Weight"]
        if not name or pd.isna(weight):
            continue
        try:
            dist[name] = float(weight)
        except (ValueError, TypeError):
            continue
    return dist


# --- Initialize all defaults ---
if "params" not in st.session_state:
    st.session_state.params = copy.deepcopy(default_params)
    
if "demographic_tables" not in st.session_state:
    st.session_state.demographic_tables = {
        dim: pd.DataFrame([{"Category": k, "Weight": float(v)} for k, v in dist.items()])
        for dim, dist in get_demographic_distributions().items()
    }
if "demographics_enabled" not in st.session_state:
    # Derive enabled state from census_data "use" flags in params.
    # The census datasets map to demographic dimension names as follows:
    #   age_sex (use_age) -> "age"
    #   age_sex (use_sex) -> "gender"
    #   ethnicity (use) -> "ethnicity"
    #   deprivation (use) -> "deprivation_level"
    census_cfg = default_params.get("census_data", {})
    age_use = census_cfg.get("age_sex", {}).get("use_age", True)
    sex_use = census_cfg.get("age_sex", {}).get("use_sex", True)
    eth_use = census_cfg.get("ethnicity", {}).get("use", True)
    dep_use = census_cfg.get("deprivation", {}).get("use", True)
    st.session_state.demographics_enabled = {
        "age": age_use,
        "gender": sex_use,
        "ethnicity": eth_use,
        "deprivation_level": dep_use,
    }
if "behavioural_tables" not in st.session_state:
    st.session_state.behavioural_tables = {
        trait: pd.DataFrame([{"Level": k, "Weight": float(v)} for k, v in spec["weights"].items()])
        for trait, spec in default_behaviours.items()
    }
if "behaviours_enabled" not in st.session_state:
    st.session_state.behaviours_enabled = {
        trait: spec.get("include", True) for trait, spec in default_behaviours.items()
    }
if "demographics_enabled" not in st.session_state:
    st.session_state.demographics_enabled = {
        dim: True for dim in get_demographic_distributions().keys()
    }

params = st.session_state.params

# ============================================================
# SECTION A: Research Context
# ============================================================
st.subheader("Research Context")

params["run_name"] = st.text_input("Run name (Should be a label so you can find this run's data later)", value=params["run_name"])
st.divider()

# ============================================================
# SECTION B: Scenario & Response Scale
# ============================================================
# --- Scenario Preset ---
# Mia's logic for adding in preset experiments

st.subheader("Scenario Preset")
preset_options = {k: v["label"] for k, v in scenario_presets.items()}
preset_options["custom"] = "Custom"

if "scenario_preset" not in st.session_state:
    st.session_state.scenario_preset = '111_dental'

preset = scenario_presets[st.session_state.scenario_preset]
if "question" not in st.session_state:
    st.session_state.question = preset["question"]
if "scale" not in st.session_state:
    st.session_state.scale = preset["scale"]
if "texts" not in st.session_state:
    st.session_state.texts = {}
if "show_variants" not in st.session_state:
    st.session_state.show_variants = False


selected_preset = st.selectbox(
    "Choose a scenario preset",
    options=list(preset_options.keys()),
    format_func=lambda k: preset_options[k],
    index=list(preset_options.keys()).index(st.session_state.scenario_preset),
    help="Selecting a preset loads its question, scale, and message variants. Choose 'Custom' to define your own on the Input Texts page.",
)

if selected_preset != st.session_state.scenario_preset:
    st.session_state.scenario_preset = selected_preset
    if selected_preset != "custom":
        preset = scenario_presets[selected_preset]
        st.session_state.question = preset["question"]
        st.session_state.scale = preset["scale"]
        # Only replace the current message list when the user explicitly opts in
        # to loading the preset defaults.
        if st.session_state.get("show_variants"):
            st.session_state.texts = dict(preset["texts"])
    st.rerun()

if selected_preset != "custom":
    st.caption(f"Loaded: {preset_options[selected_preset]}")

st.subheader("Scenario & Response Scale")

st.session_state.question = st.text_area(
    "Question shown to the synthetic patient",
    value=st.session_state.question,
    height=100,
)
st.session_state.scale = st.text_area(
    "Scale description",
    value=st.session_state.scale,
    height=120,
)

col1, col2, col3 = st.columns(3)
with col1:
    scale_min = st.number_input("Scale Min", value=params["answer_type"]["scale"][0], step=1)
with col2:
    scale_max = st.number_input("Scale Max", value=params["answer_type"]["scale"][1], step=1)
with col3:
    use_threshold = st.checkbox("Use Binary Threshold", value=params["binary_threshold"] is not None)
    if use_threshold:
        params["binary_threshold"] = st.number_input(
            "Binary Threshold (>= is YES)",
            value=params["binary_threshold"] if params["binary_threshold"] is not None else 3,
            step=1,
        )
    else:
        params["binary_threshold"] = None

params["answer_type"] = {"scale": [int(scale_min), int(scale_max)]}
st.divider()

# ============================================================
# SECTION C: Message Variants
# ============================================================
st.subheader("Message Variants")
st.caption("Each variant is tested against the full patient panel.")

texts = st.session_state.get("texts", {})
keys_to_remove = []

if st.button("Use default message variants"):
    preset_texts = dict(scenario_presets[st.session_state.scenario_preset]["texts"])
    if st.session_state.scenario_preset == "custom":
        preset_texts = {}
    st.session_state.show_variants = True
    st.session_state.texts = dict(preset_texts)
    texts = st.session_state.texts
    st.rerun()

if st.session_state.get("show_variants"):
    for key in list(texts.keys()):
        with st.expander(f"**{texts[key]}**", expanded=False):
            new_content = st.text_area(
                f"Content for '{key}'",
                value=texts[key],
                height=100,
                key=f"text_content_{key}",
            )
            texts[key] = new_content
            if st.button(f"Remove '{key}'", key=f"remove_{key}"):
                keys_to_remove.append(key)

for key in keys_to_remove:
    del texts[key]

col1, col2 = st.columns([1, 3])
with col1:
    new_key = st.text_input("Variant Label (e.g. 'control', 'social')", key="new_text_key")
with col2:
    new_content = st.text_area("Content", key="new_text_content", height=80)

if st.button("Add Variant"):
    if new_key and new_key not in texts:
        texts[new_key] = new_content
        st.session_state.show_variants = True
        st.rerun()
    elif new_key in texts:
        st.error(f"Key '{new_key}' already exists.")
    else:
        st.error("Please provide a key.")

st.session_state.texts = texts
st.info(f"{len(texts)} message variant(s) configured.")
st.divider()

# ============================================================
# SECTION D: Sample Size & Power Analysis
# ============================================================
st.subheader("Sample Size & Power Analysis & Bias Analysis")

params["enable_bias_analysis"] = st.checkbox("Enable Bias Analysis", value=params["enable_bias_analysis"])
params["enable_power_analysis"] = st.checkbox("Enable Power Analysis", value=params["enable_power_analysis"])

if params["enable_power_analysis"]:
    binary_threshold = params["binary_threshold"]
    s_min, s_max = params["answer_type"]["scale"]
    is_binary = binary_threshold is not None or (s_max - s_min <= 1)

    if is_binary:
        st.caption("Binary outcome detected. Configure proportions:")
        col1, col2 = st.columns(2)
        with col1:
            params["p1"] = st.number_input("Baseline proportion (p1)", value=params["p1"], min_value=0.01, max_value=0.99, step=0.05)
        with col2:
            params["p2"] = st.number_input("Target proportion (p2)", value=params["p2"], min_value=0.01, max_value=0.99, step=0.05)
    else:
        st.caption("Continuous outcome detected. Configure means and std dev:")
        col1, col2, col3 = st.columns(3)
        with col1:
            params["mean_control"] = st.number_input("Mean Control", value=float(params["mean_control"]), step=1.0)
        with col2:
            params["mean_treatment"] = st.number_input("Mean Treatment", value=float(params["mean_treatment"]), step=1.0)
        with col3:
            params["std_dev"] = st.number_input("Std Dev", value=float(params["std_dev"]), min_value=0.1, step=1.0)

    col1, col2 = st.columns(2)
    with col1:
        params["significance_level"] = st.slider("Significance Level (alpha)", 0.01, 0.20, value=params["significance_level"], step=0.01)
    with col2:
        params["target_power"] = st.slider("Target Power", 0.50, 0.99, value=params["target_power"], step=0.01)
else:
    params["N"] = st.number_input("Sample Size (N)", value=params["N"], min_value=1, step=1)
st.divider()

# ============================================================
# SECTION E: Sample Demographics
# ============================================================
st.subheader("Sample Demographics")

params["use_census_data"] = st.checkbox(
    "Use census data for demographics",
    value=params.get("use_census_data", True),
    help="If ticked, demographics come from ONS census data for the area below. "
         "If unticked, you must submit demographic data below.",
)
if params["use_census_data"]:
    params["ltla"] = st.text_input(
        "Area (LTLA name, list of names, or 'England')",
        value=params.get("ltla") or "England",
    )
    st.caption("Toggle which demographic dimensions to include from census data:")
    demo_enabled = st.session_state.demographics_enabled
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        age_on = st.checkbox(
            "Age",
            value=demo_enabled.get("age", True),
            key="demo_enable_age",
        )
        demo_enabled["age"] = age_on
    with col2:
        sex_on = st.checkbox(
            "Sex",
            value=demo_enabled.get("gender", True),
            key="demo_enable_sex",
        )
        demo_enabled["gender"] = sex_on
    with col3:
        demo_enabled["ethnicity"] = st.checkbox(
            "Ethnicity",
            value=demo_enabled.get("ethnicity", True),
            key="demo_enable_ethnicity",
        )
    with col4:
        demo_enabled["deprivation_level"] = st.checkbox(
            "Deprivation Level",
            value=demo_enabled.get("deprivation_level", True),
            key="demo_enable_deprivation",
        )
    st.session_state.demographics_enabled = demo_enabled
    # Sync the "use" flags back into params so the census loader respects them
    params["census_data"]["age_sex"]["use_age"] = age_on
    params["census_data"]["age_sex"]["use_sex"] = sex_on
    params["census_data"]["ethnicity"]["use"] = demo_enabled["ethnicity"]
    params["census_data"]["deprivation"]["use"] = demo_enabled["deprivation_level"]
    st.info("Census data is enabled. Untick dimensions above to exclude them, or untick 'Use census data' for fully manual distributions.")

if not params["use_census_data"]:
    # --- Demographic trait toggles ---
    st.caption("Toggle demographic traits on/off to include or exclude them from patient generation.")
    demo_enabled = st.session_state.demographics_enabled
    demo_dim_names = list(st.session_state.demographic_tables.keys())

    cols_per_row_demo = 3
    for i in range(0, len(demo_dim_names), cols_per_row_demo):
        cols = st.columns(cols_per_row_demo)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(demo_dim_names):
                break
            dim_name = demo_dim_names[idx]
            with col:
                demo_enabled[dim_name] = st.checkbox(
                    dim_name.replace("_", " ").title(),
                    value=demo_enabled.get(dim_name, True),
                    key=f"demo_enable_{dim_name}",
                )

    st.session_state.demographics_enabled = demo_enabled
    n_demo_enabled = sum(1 for d in demo_dim_names if demo_enabled.get(d, True))
    st.markdown(f"**{n_demo_enabled}** of {len(demo_dim_names)} demographic traits enabled.")


if not params["use_census_data"]:
    st.caption("Weights are relative; they need not sum to 1.")
    demographics = {}
    for dim_name, base_df in st.session_state.demographic_tables.items():
        if not demo_enabled.get(dim_name, True):
            continue
        with st.expander(f"**{dim_name.replace('_', ' ').title()}**"):
            edited_df = st.data_editor(
                base_df,
                num_rows="dynamic",
                key=f"demo_{dim_name}",
                width='stretch',
            )
            st.session_state.demographic_tables[dim_name] = edited_df
            demographics[dim_name] = _frame_to_dist(edited_df, "Category")
else:
    demographics = {
        dim: _frame_to_dist(df, "Category")
        for dim, df in st.session_state.demographic_tables.items()
        if demo_enabled.get(dim, True)
    }

st.session_state.demographics = demographics
st.divider()

# ============================================================
# SECTION F: Behavioural Traits
# ============================================================
st.subheader("Behavioural Traits")


# --- Trait validation dialog ---
@st.dialog("New Trait Validation", width="large")
def _trait_validation_dialog():
    st.markdown("### Does the new trait pass these 5 tests?")
    st.markdown("Review each criterion below before adding your custom trait.")

    validation_data = pd.DataFrame([
        {
            "Test": "Theoretical relevance",
            "Question": "Is there a plausible causal or moderating path to the behaviour, stated in COM-B terms?",
        },
        {
            "Test": "Human-side effect size",
            "Question": "Does the trait explain real variance in the human behaviour?",
        },
        {
            "Test": "Steerability",
            "Question": "Does the model demonstrably behave differently when the trait is varied?",
        },
        {
            "Test": "Groundability",
            "Question": "Does a credible population distribution exist? If not, have the weights been carefully considered?",
        },
        {
            "Test": "Value",
            "Question": "Does adding this trait still tell us anything new, or is it a proxy for another trait?",
        },
    ])

    with st.expander("View the 5 validation tests", expanded=True):
        st.table(validation_data)

    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes", use_container_width=True, type="primary"):
            st.session_state["_trait_validation_passed"] = True
            st.rerun()
    with col_no:
        if st.button("No", use_container_width=True):
            st.session_state["_trait_validation_passed"] = False
            st.rerun()


# --- End dialog ---

st.caption("Toggle traits on/off. Disabled traits will not be included in patient generation.")

enabled = st.session_state.behaviours_enabled
trait_names = list(st.session_state.behavioural_tables.keys())

cols_per_row = 3
for i in range(0, len(trait_names), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, col in enumerate(cols):
        idx = i + j
        if idx >= len(trait_names):
            break
        dim_name = trait_names[idx]
        with col:
            enabled[dim_name] = st.checkbox(
                dim_name.replace("_", " ").title(),
                value=enabled[dim_name],
                key=f"enable_{dim_name}",
            )

n_enabled = sum(1 for t in trait_names if enabled[t])
st.markdown(f"**{n_enabled}** of {len(trait_names)} traits enabled.")

behaviours = {}

with st.expander("Edit trait distributions", expanded=False):
    for dim_name, base_df in st.session_state.behavioural_tables.items():
        if not enabled[dim_name]:
            continue
        with st.expander(f"**{dim_name.replace('_', ' ').title()}**"):
            edited_df = st.data_editor(
                base_df,
                num_rows="dynamic",
                key=f"behav_{dim_name}",
                width='stretch',
            )
            st.session_state.behavioural_tables[dim_name] = edited_df
            behaviours[dim_name] = _frame_to_dist(edited_df, "Level")

for dim_name, base_df in st.session_state.behavioural_tables.items():
    if dim_name not in behaviours:
        behaviours[dim_name] = _frame_to_dist(base_df, "Level")

st.session_state.behaviours = behaviours
st.session_state.behaviours_enabled = enabled

# --- Warning if more than 10 combined traits ---
n_demographic_traits = sum(1 for d in st.session_state.demographics_enabled if st.session_state.demographics_enabled[d])
n_behavioural_enabled = sum(1 for t in st.session_state.behaviours_enabled if st.session_state.behaviours_enabled[t])
total_traits = n_demographic_traits + n_behavioural_enabled

if total_traits > 10:
    st.warning("⚠️ Warning: We recommend using 10 total traits or fewer for simulations.")

with st.expander("Add Custom Trait", expanded=False):
    st.caption("""
    NOTE: If adding new traits, please make the `description` fit into the sentence\n
        "You `description`"\n
    This is how the description is injected into the prompt.""")
    col1, col2 = st.columns([1, 2])
    with col1:
        new_trait_name = st.text_input("Trait name (snake_case)", key="new_trait_name", placeholder="e.g. carer_responsibility")
    with col2:
        new_trait_levels = st.text_area(
            "Descriptions and Weights (one per line, format: `description`, weight)",
            key="new_trait_levels",
            height=100,
            placeholder="do not care for anyone, 0.4\nare a part-time carer, 0.3\nare a full-time carer, 0.2\nare the primary carer of child, 0.1",
        )

    # Handle the validation flow
    if st.button("Add Trait"):
        if not new_trait_name:
            st.error("Please provide a trait name.")
        elif new_trait_name in st.session_state.behavioural_tables:
            st.error(f"Trait '{new_trait_name}' already exists.")
        else:
            # Store pending trait info and open the dialog
            st.session_state["_pending_trait_name"] = new_trait_name
            st.session_state["_pending_trait_levels"] = new_trait_levels
            st.session_state["_trait_validation_passed"] = None
            _trait_validation_dialog()

    # Process the validation result
    if st.session_state.get("_trait_validation_passed") is True:
        pending_name = st.session_state.pop("_pending_trait_name", None)
        pending_levels = st.session_state.pop("_pending_trait_levels", "")
        st.session_state.pop("_trait_validation_passed", None)

        if pending_name:
            rows = []
            for line in pending_levels.strip().split("\n"):
                parts = line.rsplit(",", 1)
                if len(parts) == 2:
                    level = parts[0].strip()
                    try:
                        weight = float(parts[1].strip())
                    except ValueError:
                        weight = 1.0
                    if level:
                        rows.append({"Level": level, "Weight": weight})
            if rows:
                st.session_state.behavioural_tables[pending_name] = pd.DataFrame(rows)
                st.session_state.behaviours_enabled[pending_name] = True
                st.rerun()
            else:
                st.error("Please provide at least one level in the format: level_name, weight")

    elif st.session_state.get("_trait_validation_passed") is False:
        st.session_state.pop("_pending_trait_name", None)
        st.session_state.pop("_pending_trait_levels", None)
        st.session_state.pop("_trait_validation_passed", None)
        st.info("Trait was not added. Please ensure it passes all 5 validation tests before adding.")

st.divider()
# ============================================================
# SECTION G: Advanced Settings
# ============================================================
with st.expander("Advanced Settings", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        params["model"] = st.text_input("Model ID", value=params["model"])
    with col2:
        params["verbose"] = st.checkbox("Verbose", value=params["verbose"])
        params["use_semantic_similarity"] = st.checkbox("Use semantic similarity to calculate Likert value", value= params["use_semantic_similarity"])

    st.subheader("Report Sections")
    cols = st.columns(4)
    section_keys = list(params["report_sections"].keys())
    for i, key in enumerate(section_keys):
        with cols[i % 4]:
            params["report_sections"][key] = st.checkbox(
                key.replace("_", " ").title(),
                value=params["report_sections"][key],
                key=f"report_{key}",
            )

st.session_state.params = params
st.success("Configuration saved to session.")
