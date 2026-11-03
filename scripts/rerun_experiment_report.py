"""
Re-run the evaluation report for an existing run or experiment directory.

Works for both single pipeline runs and experiment-mode runs (with repeat_*
subdirectories).

Usage:
    python scripts/rerun_experiment_report.py data/my_run_2026-09-01_12-00-00
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inputs.scenario_presets import scenario_presets
from inputs.behavoural_traits import get_behavioural_dimensions
from inputs.demographic_distributions import get_demographic_distributions
from src.evaluate import generate_evaluation_report

# --- Change this to match the scenario you ran ---
selected_scenario_preset = scenario_presets['covid_vaccine_RCT_1']

question = selected_scenario_preset['question']
scale = selected_scenario_preset['scale']
texts = selected_scenario_preset['texts']
real_results = selected_scenario_preset.get('real_results')

# --- Point this at your run / experiment directory ---
run_dir = sys.argv[1]

repeat_dirs = sorted(
    d for d in Path(run_dir).iterdir()
    if d.is_dir() and d.name.startswith("repeat_")
)

is_experiment = len(repeat_dirs) > 0

if is_experiment:
    with open(os.path.join(repeat_dirs[0], "params.json")) as f:
        run_params = json.load(f)

    all_results, all_patients = [], []
    for i, rd in enumerate(repeat_dirs):
        results_df = pd.read_csv(rd / "results.csv")
        patients_df = pd.read_csv(rd / "patients.csv")
        results_df["patient_id"] = f"run{i}_" + results_df["patient_id"]
        patients_df["patient_id"] = f"run{i}_" + patients_df["patient_id"]
        all_results.append(results_df)
        all_patients.append(patients_df)

    combined_results = pd.concat(all_results, ignore_index=True)
    combined_patients = pd.concat(all_patients, ignore_index=True)
    patients_csv_path = os.path.join(run_dir, "combined_patients.csv")
    combined_patients.to_csv(patients_csv_path, index=False)
else:
    with open(os.path.join(run_dir, "params.json")) as f:
        run_params = json.load(f)

    combined_results = pd.read_csv(os.path.join(run_dir, "results.csv"))
    patients_csv_path = os.path.join(run_dir, "patients.csv")

bias_path = os.path.join(run_dir, "bias_judgements.csv")
bias_df = pd.read_csv(bias_path) if os.path.exists(bias_path) else pd.DataFrame()

generate_evaluation_report(
    results_df=combined_results,
    patients_csv_path=patients_csv_path,
    demographic_keys=list(get_demographic_distributions(
        run_params.get("min_age", 18), run_params.get("max_age", 100)
    ).keys()),
    behavioural_keys=list(get_behavioural_dimensions().keys()),
    input_texts=texts,
    output_dir=run_dir,
    run_name=run_params.get("run_name", "rerun"),
    run_timestamp="rerun",
    question=question,
    scale=scale,
    bias_df=bias_df,
    report_sections=run_params.get("report_sections", {}),
    answer_type=run_params.get("answer_type", {"scale": [0, 1]}),
    binary_threshold=run_params.get("binary_threshold"),
    real_results=real_results,
)

print(f"Report regenerated: {run_dir}/evaluation_report.md")
