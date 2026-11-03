"""
Combine two (or more) runs with the same texts into a single merged dataset
and produce a combined evaluation report.

Usage:
    python combine_runs.py <folder1> <folder2> [folder3 ...]

Example:
    python combine_runs.py data/baseline_2026-04-29_15-29-12 data/baseline_2026-05-01_10-00-00

The combined output is written to data/combined_<timestamp>/
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inputs.behavoural_traits import get_behavioural_dimensions
from inputs.demographic_distributions import get_demographic_distributions
from inputs.input_texts import question, texts
from config.params import params
from src.evaluate import generate_evaluation_report


def combine_runs(run_dirs: list[str], output_dir: str = None):
    """
    Combine multiple run folders into a single merged dataset and report.

    Parameters
    ----------
    run_dirs : list[str]
        Paths to the run folders to combine (e.g. ["data/run_a", "data/run_b"])
    output_dir : str, optional
        Where to write the combined output. Defaults to data/combined_<timestamp>
    """
    if len(run_dirs) < 2:
        print("Error: Please provide at least two run folders to combine.")
        sys.exit(1)

    # Validate all folders exist
    for d in run_dirs:
        if not os.path.isdir(d):
            print(f"Error: Folder not found: {d}")
            sys.exit(1)
        for required_file in ["patients.csv", "results.csv"]:
            if not os.path.isfile(os.path.join(d, required_file)):
                print(f"Error: {required_file} not found in {d}")
                sys.exit(1)

    # Create output folder
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if output_dir is None:
        output_dir = os.path.join("data", f"combined_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    print(f"=== Combining {len(run_dirs)} runs ===")
    for d in run_dirs:
        print(f"  - {d}")
    print()

    # --- Combine patients (re-index to avoid ID collisions) ---
    all_patients = []
    all_results = []
    all_bias = []
    patient_counter = 0

    for run_idx, run_dir in enumerate(run_dirs):
        patients_df = pd.read_csv(os.path.join(run_dir, "patients.csv"))
        results_df = pd.read_csv(os.path.join(run_dir, "results.csv"))

        # Create a mapping from old patient_id to new unique patient_id
        id_map = {}
        for _, row in patients_df.iterrows():
            old_id = row["patient_id"]
            new_id = f"patient_{patient_counter}"
            id_map[old_id] = new_id
            patient_counter += 1

        # Re-map patient IDs
        patients_df["patient_id"] = patients_df["patient_id"].map(id_map)
        patients_df["source_run"] = os.path.basename(run_dir)
        all_patients.append(patients_df)

        results_df["patient_id"] = results_df["patient_id"].map(id_map)
        all_results.append(results_df)

        # Combine bias judgements if available
        bias_path = os.path.join(run_dir, "bias_judgements.csv")
        if os.path.isfile(bias_path):
            bias_df = pd.read_csv(bias_path)
            bias_df["patient_id"] = bias_df["patient_id"].map(id_map)
            all_bias.append(bias_df)

    # Concatenate all
    combined_patients = pd.concat(all_patients, ignore_index=True)
    combined_results = pd.concat(all_results, ignore_index=True)
    combined_bias = pd.concat(all_bias, ignore_index=True) if all_bias else None

    # Save combined CSVs
    combined_patients.to_csv(os.path.join(output_dir, "patients.csv"), index=False)
    combined_results.to_csv(os.path.join(output_dir, "results.csv"), index=False)
    if combined_bias is not None:
        combined_bias.to_csv(os.path.join(output_dir, "bias_judgements.csv"), index=False)

    print(f"Combined patients: {len(combined_patients)}")
    print(f"Combined results:  {len(combined_results)}")
    if combined_bias is not None:
        print(f"Combined bias judgements: {len(combined_bias)}")
    print()

    # Save metadata about which runs were combined
    meta = {
        "combined_at": timestamp,
        "source_runs": run_dirs,
        "total_patients": len(combined_patients),
        "patients_per_run": [len(pd.read_csv(os.path.join(d, "patients.csv"))) for d in run_dirs],
    }
    with open(os.path.join(output_dir, "combine_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    # --- Generate combined evaluation report ---
    run_name = "combined"
    generate_evaluation_report(
        results_df=combined_results,
        patients_csv_path=os.path.join(output_dir, "patients.csv"),
        demographic_keys=list(get_demographic_distributions(
            min_age=params["min_age"], max_age=params["max_age"]
        ).keys()),
        behavioural_keys=list(get_behavioural_dimensions().keys()),
        input_texts=texts,
        output_dir=output_dir,
        run_name=run_name,
        run_timestamp=timestamp,
        question=question,
        bias_df=combined_bias,
        report_sections=params.get("report_sections"),
        answer_type=params["answer_type"],
        binary_threshold=params.get("binary_threshold"),
    )

    print(f"\nCombined output saved to: {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python combine_runs.py <folder1> <folder2> [folder3 ...]")
        print("Example: python combine_runs.py data/baseline_2026-04-29_15-29-12 data/baseline_2026-05-01_10-00-00")
        sys.exit(1)

    run_folders = sys.argv[1:]
    combine_runs(run_folders)
