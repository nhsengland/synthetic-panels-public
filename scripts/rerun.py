"""Re-run evaluation report on an existing pipeline output without re-running the full pipeline."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from src.evaluate import generate_evaluation_report
from inputs.scenario_presets import scenario_presets

run_dir = "data/aib-111-repeat-prescription-change-q_2026-08-21_16-33-57"

scenario = scenario_presets["111_repeat_prescription"]
texts = scenario["texts"]
question = scenario["question"]
scale = scenario["scale"]

import os
output_dir = os.path.join(run_dir, "rerun")
os.makedirs(output_dir, exist_ok=True)

results_df = pd.read_csv(f"{run_dir}/results.csv")
bias_df = pd.read_csv(f"{run_dir}/bias_judgements.csv")

generate_evaluation_report(
    results_df=results_df,
    patients_csv_path=f"{run_dir}/patients.csv",
    demographic_keys=["gender", "ethnicity", "deprivation_level"],
    behavioural_keys=["health_literacy", "trust_in_healthcare", "digital_literacy", "health_engagement", "response_to_authority", "prosocial_orientation"],
    input_texts=texts,
    output_dir=output_dir,
    run_name="aib-111-repeat-prescription-changed-q",
    run_timestamp="2026-08-21_16-33-57",
    question=question,
    scale=scale,
    bias_df=bias_df,
    report_sections={
        "overall_results": True,
        "text_ranking": True,
        "cross_text_agreement": True,
        "demographic_breakdown": True,
        "demographic_disparity": True,
        "sample_size_warnings": True,
        "behavioural_traits": True,
        "bias_judge": True,
    },
    answer_type={"scale": [1, 2]},
    binary_threshold=2,
)

print(f"Evaluation report regenerated in: {output_dir}/evaluation_report.md")
 