import os
from datetime import datetime

import numpy as np
import pandas as pd

from src.pipeline_runner import run_pipeline
from src.compare_to_real import compare_to_real, aggregate_comparisons, format_experiment_report
from src.evaluate import generate_evaluation_report
from inputs.demographic_distributions import get_demographic_distributions
from inputs.behavoural_traits import get_behavioural_dimensions


def compute_rates_from_df(results_df, text_cols, binary_threshold):
    rates = {}
    for col in text_cols:
        vals = pd.to_numeric(results_df[col], errors="coerce").dropna()
        if binary_threshold is not None:
            rates[col] = float((vals >= binary_threshold).mean())
        else:
            rates[col] = float(vals.mean())
    return rates


def run_experiment(params, texts, question, scale, real_results=None,
                   behaviours=None, demographics=None, enabled_demographic_dims=None,
                   status_callback=None, run_name=None):
    def status(msg):
        if status_callback:
            status_callback(msg)

    n_repeats = params.get("n_repeats", 5)
    vary_patients = params.get("vary_patients", True)
    base_seed = params["random_seed"]
    binary_threshold = params.get("binary_threshold")

    run_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if run_name is None:
        run_name = params.get("run_name", "run")
    experiment_dir = os.path.join("data", f"{run_name}_{run_timestamp}")
    os.makedirs(experiment_dir, exist_ok=True)

    text_cols = list(texts.keys())
    comparisons = []
    run_dirs = []
    all_rates = []
    all_results_dfs = []
    all_patients_dfs = []

    for i in range(n_repeats):
        status(f"Running repeat {i + 1}/{n_repeats}...")
        repeat_dir = os.path.join(experiment_dir, f"repeat_{i}")

        seed = base_seed + i if vary_patients else base_seed

        result = run_pipeline(
            params=params,
            texts=texts,
            question=question,
            scale=scale,
            behaviours=behaviours,
            demographics=demographics,
            enabled_demographic_dims=enabled_demographic_dims,
            status_callback=status_callback,
            run_name=run_name,
            real_results=real_results,
            seed_override=seed,
            output_dir_override=repeat_dir,
        )
        run_dirs.append(repeat_dir)
        result["results_df"]["patient_id"] = f"run{i}_" + result["results_df"]["patient_id"]
        result["patients_df"]["patient_id"] = f"run{i}_" + result["patients_df"]["patient_id"]
        all_results_dfs.append(result["results_df"])
        all_patients_dfs.append(result["patients_df"])

        rates = compute_rates_from_df(result["results_df"], text_cols, binary_threshold)
        all_rates.append(rates)

        if real_results:
            comparison = compare_to_real(rates, real_results)
            comparisons.append(comparison)

    rates_df = build_experiment_results_csv(text_cols, all_rates, real_results)
    rates_csv_path = os.path.join(experiment_dir, "experiment_results.csv")
    rates_df.to_csv(rates_csv_path, index=False)
    status(f"Experiment results CSV saved to {rates_csv_path}")

    agg = None
    experiment_report = ""
    if real_results and comparisons:
        agg = aggregate_comparisons(comparisons, real_results)
        scenario_label = run_name
        experiment_report = format_experiment_report(agg, scenario_label)

        report_path = os.path.join(experiment_dir, "experiment_summary.md")
        with open(report_path, "w") as f:
            f.write(experiment_report)
        status(f"Experiment summary saved to {report_path}")

    # Generate combined evaluation report across all repeats
    status("Generating combined evaluation report across all repeats...")
    combined_results_df = pd.concat(all_results_dfs, ignore_index=True)
    combined_patients_df = pd.concat(all_patients_dfs, ignore_index=True)
    combined_patients_path = os.path.join(experiment_dir, "combined_patients.csv")
    combined_patients_df.to_csv(combined_patients_path, index=False)

    demographic_keys = list((demographics or get_demographic_distributions(params.get("min_age", 18), params.get("max_age", 100))).keys())
    behavioural_keys = list((behaviours or get_behavioural_dimensions()).keys())

    generate_evaluation_report(
        results_df=combined_results_df,
        patients_csv_path=combined_patients_path,
        demographic_keys=demographic_keys,
        behavioural_keys=behavioural_keys,
        input_texts=texts,
        output_dir=experiment_dir,
        run_name=run_name,
        run_timestamp=run_timestamp,
        question=question,
        scale=scale,
        bias_df=pd.DataFrame(),
        report_sections=params["report_sections"],
        answer_type=params["answer_type"],
        binary_threshold=binary_threshold,
        real_results=real_results,
    )
    status(f"Combined evaluation report saved to {experiment_dir}/evaluation_report.md")

    return {
        "experiment_dir": experiment_dir,
        "run_dirs": run_dirs,
        "comparisons": comparisons,
        "aggregate": agg,
        "experiment_report": experiment_report,
        "rates_df": rates_df,
    }


def build_experiment_results_csv(text_cols, all_rates, real_results=None):
    rows = []
    for i, rates in enumerate(all_rates):
        row = {"run": f"repeat_{i}"}
        for col in text_cols:
            row[col] = rates.get(col)
        rows.append(row)

    means = {"run": "mean"}
    stds = {"run": "std"}
    ci_lo = {"run": "ci_95_low"}
    ci_hi = {"run": "ci_95_high"}
    for col in text_cols:
        vals = [r[col] for r in all_rates if r.get(col) is not None]
        m = np.mean(vals)
        s = np.std(vals, ddof=1) if len(vals) > 1 else 0.0
        se = s / np.sqrt(len(vals)) if len(vals) > 1 else 0.0
        means[col] = m
        stds[col] = s
        ci_lo[col] = m - 1.96 * se
        ci_hi[col] = m + 1.96 * se
    rows.extend([means, stds, ci_lo, ci_hi])

    if real_results:
        real_row = {"run": "real"}
        for col in text_cols:
            real_row[col] = real_results.get(col)
        rows.append(real_row)

    return pd.DataFrame(rows)
