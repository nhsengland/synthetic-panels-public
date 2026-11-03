import json
import os
import string
from datetime import datetime

import pandas as pd

from src.generate_samples import GeneratePatients, GeneratePrompt, RunLLM, BiasJudge
from src.evaluate import generate_evaluation_report
from src.power_analyzer import PowerAnalyzer
from src.prompts import prompts, ANSWER_INSTRUCTIONS, build_behavioural_fields
from src.prepare_census_data import load_census_distributions
from src.semantic_similarity import score_semantic_similarity
from inputs.demographic_distributions import get_demographic_distributions
from inputs.behavoural_traits import get_behavioural_dimensions


def run_pipeline(params, texts, question, scale, behaviours=None, demographics=None, enabled_demographic_dims=None, hide_demographics_from_prompt=None, status_callback=None, run_name=None, real_results=None, seed_override=None, output_dir_override=None):
    """Run the full pipeline and return all outputs.

    Args:
        params: dict matching config/params.py structure
        texts: dict of text_id -> text content
        question: str scenario question
        scale: str scale description
        behaviours: optional {trait: weights} dict of enabled behavioural traits (the
            app supplies its edited/toggled set); when None, falls back to the
            include=True traits in inputs/behavoural_traits.py
        demographics: optional {dimension: weights} dict; when provided it is used
            directly so the app's edited distributions win over census/defaults
        enabled_demographic_dims: optional list of dimension names to include;
            when provided, census/default distributions are filtered to only
            these dimensions
        hide_demographics_from_prompt: optional list of dimension names that should
            be generated (e.g. for name generation) but NOT included in the
            patient prompt or evaluation report
        status_callback: optional fn(message) called at each stage

    Returns:
        dict with keys: patients_df, results_df, bias_df, report_md, run_dir
    """
    def status(msg):
        if status_callback:
            status_callback(msg)

    if hide_demographics_from_prompt is None:
        hide_demographics_from_prompt = []
        if not params.get("census_data", {}).get("ethnicity", {}).get("use", True):
            hide_demographics_from_prompt.append("ethnicity")

    answer_type = params["answer_type"]
    scale_min, scale_max = answer_type["scale"]

    if params["use_semantic_similarity"]:
        system_template = prompts["generate_patient_semantic_scaling"]["system"]
        user_template = string.Template(prompts["generate_patient_semantic_scaling"]["user"]).safe_substitute(
            ANSWER_INSTRUCTION=ANSWER_INSTRUCTIONS["semantic_scale"],
        )
        scale_template = string.Template(prompts["generate_scale"]).safe_substitute(
            QUESTION = question,
            REFERENCE_SET = scale,
            N = 6,
            SCALE_MIN = scale_min,
            SCALE_MAX = scale_max
        )
    else:
        answer_instruction = string.Template(ANSWER_INSTRUCTIONS["scale"]).safe_substitute(
            SCALE_MIN=scale_min, SCALE_MAX=scale_max,
        )
        system_template = prompts["generate_patient"]["system"]
        user_template = string.Template(prompts["generate_patient"]["user"]).safe_substitute(
            ANSWER_INSTRUCTION=answer_instruction,
            SCALE=scale,
        )

    seed = seed_override if seed_override is not None else params["random_seed"]

    run_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if output_dir_override:
        run_dir = output_dir_override
    else:
        if run_name!=None:
            run_name = run_name
        else:
            run_name = params.get("run_name", "run")
        run_dir = os.path.join("data", f"{run_name}_{run_timestamp}")
    os.makedirs(run_dir, exist_ok=True)

    with open(os.path.join(run_dir, "params.json"), "w") as f:
        json.dump(params, f, indent=2)

    status("Generating patients...")

    # Resolve demographic distributions
    if params.get("use_census_data"):
        # Load census data then filter to only enabled dimensions
        ltla = params.get("ltla")
        if not ltla:
            raise ValueError("'ltla' must be set in params when use_census_data is True")
        demographic_distributions = load_census_distributions(ltla, min_age=params["min_age"], max_age=params["max_age"], census_data=params["census_data"])
        if enabled_demographic_dims is not None:
            demographic_distributions = {
                k: v for k, v in demographic_distributions.items()
                if k in enabled_demographic_dims
            }
    elif demographics is not None:
        # Explicit distributions from the app (already filtered to enabled dims)
        demographic_distributions = demographics
    else:
        # Fallback to default distributions
        demographic_distributions = get_demographic_distributions(min_age=params["min_age"], max_age=params["max_age"])
        if enabled_demographic_dims is not None:
            demographic_distributions = {
                k: v for k, v in demographic_distributions.items()
                if k in enabled_demographic_dims
            }

    # Ethnicity is always needed for culturally appropriate name generation.
    # Re-add it from defaults if it was filtered out.
    if "ethnicity" not in demographic_distributions:
        fallback = get_demographic_distributions(
            min_age=params["min_age"], max_age=params["max_age"]
        )
        if "ethnicity" in fallback:
            demographic_distributions["ethnicity"] = fallback["ethnicity"]

    behavioural_dimensions = behaviours if behaviours is not None else get_behavioural_dimensions()

    if params["enable_power_analysis"]:
        status("Calculating sample size from power analysis...")
        binary_threshold = params["binary_threshold"]
        outcome_type = "binary" if binary_threshold is not None or scale_max - scale_min <= 1 else "continuous"
        analyzer = PowerAnalyzer(
            outcome_type=outcome_type,
            significance_level=params["significance_level"],
            target_power=params["target_power"],
            p1=params.get("p1"),
            p2=params.get("p2"),
            mean_control=params.get("mean_control"),
            mean_treatment=params.get("mean_treatment"),
            std_dev=params.get("std_dev"),
        )
        n = analyzer.calculate_required_n()
        params["N"] = n
        status(f"Power analysis complete — N={n} per prompt")
    else:
        print(f"Power analysis disabled, using N={params['N']}")

    status(f"Generating {params['N']} patients...")
    generator = GeneratePatients(
        n=params["N"],
        behavioural_dimensions=behavioural_dimensions,
        demographic_distributions=demographic_distributions,
        seed=seed
    )
    patients_df = generator.generate(output_dir=run_dir)
    status(f"{len(patients_df)} patients generated")

    status("Building prompts...")
    # Filter DEMOGRAPHIC_FIELDS to only include dimensions present in the distributions
    # and not hidden from the prompt (hidden dims are still generated for name generation etc.)
    from src.prompts import DEMOGRAPHIC_FIELDS
    hidden_dims = set(hide_demographics_from_prompt or [])
    active_demo_fields = [
        (col, label) for col, label in DEMOGRAPHIC_FIELDS
        if col in demographic_distributions and col not in hidden_dims
    ]
    prompt_generator = GeneratePrompt(
        question=question,
        prompt_template=user_template,
        system_template=system_template,
        input_texts=texts,
        patients_csv_path=os.path.join(run_dir, "patients.csv"),
        behavioural_fields=build_behavioural_fields(behavioural_dimensions.keys()),
        demographic_fields=active_demo_fields,
        shuffle_prompt=params.get("shuffle_prompt", True),
    )
    prompt_generator.generate(output_dir=run_dir)
    status("Prompts built")

    status("Running LLM (this is the slow part)...")
    llm_runner = RunLLM(
        model=params["model"],
        prompts_csv_path=os.path.join(run_dir, "prompts.csv"),
        answer_type=answer_type,
        temperature=params["temperature"],
        use_semantic_similarity=params["use_semantic_similarity"],
    )
    results_df = llm_runner.generate(output_dir=run_dir)
    status("LLM responses received")

    if params["use_semantic_similarity"]:
        status("Running semantic similarity...")
        results_df = score_semantic_similarity(
            scale_prompt = scale_template,
            scale = scale,
            results_csv_path=os.path.join(run_dir, "results.csv"),
            output_dir = run_dir
        )

    if params["enable_bias_analysis"]:
        status("Running bias judge...")
        bias_judge = BiasJudge(
            results_csv_path=os.path.join(run_dir, "results.csv"),
            patients_csv_path=os.path.join(run_dir, "patients.csv"),
            model=params["model"],
            verbose=params.get("verbose", False),
            temperature=params["judge_temperature"]
        )
        bias_df = bias_judge.generate(output_dir=run_dir)
        status("Bias judge complete")
    else:
        bias_df = pd.DataFrame()

    status("Generating evaluation report...")
    visible_demo_keys = [k for k in demographic_distributions.keys() if k not in hidden_dims]
    generate_evaluation_report(
        results_df=results_df,
        patients_csv_path=os.path.join(run_dir, "patients.csv"),
        demographic_keys=visible_demo_keys,
        behavioural_keys=list(behavioural_dimensions.keys()),
        input_texts=texts,
        output_dir=run_dir,
        run_name=run_name,
        run_timestamp=run_timestamp,
        question=question,
        scale=scale,
        bias_df=bias_df,
        report_sections=params["report_sections"],
        answer_type=answer_type,
        binary_threshold=params.get("binary_threshold"),
        real_results=real_results,
    )

    report_path = os.path.join(run_dir, "evaluation_report.md")
    report_md = ""
    if os.path.exists(report_path):
        with open(report_path) as f:
            report_md = f.read()

    return {
        "patients_df": patients_df,
        "results_df": results_df,
        "bias_df": bias_df,
        "report_md": report_md,
        "run_dir": run_dir,
    }
