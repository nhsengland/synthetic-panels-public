"""Compare synthetic panel results to real RCT results.

Usage (single run):
    python scripts/compare_to_real.py data/<run_folder> --scenario 111_repeat_prescription
    python scripts/compare_to_real.py data/<run_folder> --real '{"control": 0.17, "social": 0.18, "easy": 0.29}'

Usage (multiple runs / experiment folder):
    python scripts/compare_to_real.py data/<experiment_folder> --scenario 111_repeat_prescription
    python scripts/compare_to_real.py data/run/repeat_0 data/run/repeat_1 data/run/repeat_2 --scenario 111_repeat_prescription
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from inputs.scenario_presets import scenario_presets
from src.compare_to_real import (
    compare_to_real, format_comparison_report,
    aggregate_comparisons, format_experiment_report,
)


def compute_synthetic_rates(results_path: Path, binary_threshold=None) -> dict:
    df = pd.read_csv(results_path)
    text_cols = [c for c in df.columns if not c.endswith("_reasoning") and c != "patient_id"]
    rates = {}
    for col in text_cols:
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if binary_threshold is not None:
            rates[col] = float((vals >= binary_threshold).mean())
        else:
            rates[col] = float(vals.mean())
    return rates


def resolve_run_dirs(paths: list[Path]) -> list[Path]:
    """Resolve input paths to a list of run directories with results.csv.

    If a single directory is given that contains repeat_* sub-folders, expand it.
    """
    if len(paths) == 1:
        p = paths[0]
        repeat_dirs = sorted(p.glob("repeat_*"))
        if repeat_dirs and all((d / "results.csv").exists() for d in repeat_dirs):
            return repeat_dirs
        if (p / "results.csv").exists():
            return [p]
        print(f"Error: {p} has no results.csv and no repeat_* sub-folders")
        sys.exit(1)
    return paths


def resolve_real_results(args, first_results_path):
    if args.real:
        return json.loads(args.real), "custom"
    if args.scenario:
        preset = scenario_presets.get(args.scenario)
        if not preset:
            print(f"Error: scenario '{args.scenario}' not found in presets")
            print(f"Available: {list(scenario_presets.keys())}")
            sys.exit(1)
        real_results = preset.get("real_results")
        if not real_results:
            print(f"Error: scenario '{args.scenario}' has no real_results defined")
            sys.exit(1)
        return real_results, preset.get("label", args.scenario)

    results_df = pd.read_csv(first_results_path)
    text_cols = [c for c in results_df.columns if not c.endswith("_reasoning") and c != "patient_id"]
    for key, preset in scenario_presets.items():
        if set(preset.get("texts", {}).keys()) == set(text_cols):
            if preset.get("real_results"):
                return preset["real_results"], preset.get("label", key)
    print("Error: could not auto-detect scenario. Use --scenario or --real")
    sys.exit(1)


def get_threshold(args, run_dir):
    if args.threshold is not None:
        return args.threshold
    params_path = run_dir / "params.json"
    if params_path.exists():
        with open(params_path) as f:
            params = json.load(f)
        return params.get("binary_threshold") or None
    return None


def main():
    parser = argparse.ArgumentParser(description="Compare synthetic results to real RCT results")
    parser.add_argument("run_dirs", type=Path, nargs="+", help="Path(s) to run output directory or experiment folder")
    parser.add_argument("--scenario", type=str, help="Scenario preset key (e.g. 111_repeat_prescription)")
    parser.add_argument("--real", type=str, help="Real results as JSON dict (overrides scenario preset)")
    parser.add_argument("--threshold", type=float, help="Binary threshold override (>= threshold = YES)")
    args = parser.parse_args()

    run_dirs = resolve_run_dirs(args.run_dirs)
    first_results = run_dirs[0] / "results.csv"
    real_results, scenario_label = resolve_real_results(args, first_results)

    if len(run_dirs) == 1:
        binary_threshold = get_threshold(args, run_dirs[0])
        synthetic_rates = compute_synthetic_rates(run_dirs[0] / "results.csv", binary_threshold)
        comparison = compare_to_real(synthetic_rates, real_results)
        if comparison is None:
            print("Error: fewer than 2 common variants between synthetic and real results")
            sys.exit(1)
        print(format_comparison_report(comparison, scenario_label))
    else:
        comparisons = []
        for rd in run_dirs:
            binary_threshold = get_threshold(args, rd)
            rates = compute_synthetic_rates(rd / "results.csv", binary_threshold)
            comparisons.append(compare_to_real(rates, real_results))

        agg = aggregate_comparisons(comparisons, real_results)
        if agg is None:
            print("Error: no valid comparisons across runs")
            sys.exit(1)
        print(format_experiment_report(agg, scenario_label))


if __name__ == "__main__":
    main()
