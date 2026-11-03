"""Plot synthetic experiment results vs real results.

Usage:
    python scripts/plot_comparison.py data/<experiment_folder>
    python scripts/plot_comparison.py data/<experiment_folder> --output plot.png
    python scripts/plot_comparison.py experiment_results.csv --real '{"control": 0.17, "social": 0.18, "easy": 0.29}'
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def load_experiment_data(path: Path, real_override=None):
    if path.suffix == ".csv":
        df = pd.read_csv(path)
    else:
        csv_path = path / "experiment_results.csv"
        if not csv_path.exists():
            print(f"Error: {csv_path} not found")
            sys.exit(1)
        df = pd.read_csv(csv_path)

    text_cols = [c for c in df.columns if c != "run"]

    mean_row = df[df["run"] == "mean"].iloc[0]
    ci_lo_row = df[df["run"] == "ci_95_low"].iloc[0]
    ci_hi_row = df[df["run"] == "ci_95_high"].iloc[0]

    synthetic_means = {col: mean_row[col] for col in text_cols}
    synthetic_ci_lo = {col: ci_lo_row[col] for col in text_cols}
    synthetic_ci_hi = {col: ci_hi_row[col] for col in text_cols}

    if real_override:
        real_results = real_override
    elif "real" in df["run"].values:
        real_row = df[df["run"] == "real"].iloc[0]
        real_results = {col: real_row[col] for col in text_cols if pd.notna(real_row[col])}
    else:
        print("Error: no real results found. Use --real or ensure experiment was run with real_results.")
        sys.exit(1)

    per_run = df[~df["run"].isin(["mean", "std", "ci_95_low", "ci_95_high", "real"])]
    per_run_rates = {}
    for col in text_cols:
        per_run_rates[col] = per_run[col].dropna().values

    return text_cols, synthetic_means, synthetic_ci_lo, synthetic_ci_hi, real_results, per_run_rates


def plot_comparison(text_cols, synthetic_means, synthetic_ci_lo, synthetic_ci_hi,
                    real_results, per_run_rates, output_path=None):
    variants = sorted(real_results.keys(), key=lambda k: real_results[k], reverse=True)

    real_vals = [real_results[v] for v in variants]
    synth_vals = [synthetic_means[v] for v in variants]
    errors_lo = [synthetic_means[v] - synthetic_ci_lo[v] for v in variants]
    errors_hi = [synthetic_ci_hi[v] - synthetic_means[v] for v in variants]

    x = np.arange(len(variants))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    bars_real = ax.bar(x - width / 2, real_vals, width, label="Real Results",
                       color="#005EB8", alpha=0.8)
    bars_synth = ax.bar(x + width / 2, synth_vals, width, label="Synthetic (mean)",
                        color="#41B6E6", alpha=0.8,
                        yerr=[errors_lo, errors_hi], capsize=5, ecolor="#333")

    for v_idx, variant in enumerate(variants):
        runs = per_run_rates.get(variant, [])
        if len(runs) > 0:
            jitter = np.random.default_rng(42).uniform(-0.05, 0.05, len(runs))
            ax.scatter(x[v_idx] + width / 2 + jitter, runs,
                       color="#333", alpha=0.4, s=20, zorder=3)

    ax.set_xlabel("Text Variant")
    ax.set_ylabel("Response Rate")
    ax.set_title("Real vs Synthetic Results")
    ax.set_xticks(x)
    ax.set_xticklabels(variants, rotation=15, ha="right")
    ax.legend()
    ax.set_ylim(0, None)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Plot saved to {output_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot real vs synthetic experiment results")
    parser.add_argument("path", type=Path, help="Experiment folder or experiment_results.csv")
    parser.add_argument("--real", type=str, help="Real results as JSON dict (override)")
    parser.add_argument("--output", "-o", type=Path, help="Output file path (png/pdf/svg)")
    args = parser.parse_args()

    real_override = json.loads(args.real) if args.real else None
    text_cols, synth_means, ci_lo, ci_hi, real_results, per_run_rates = load_experiment_data(
        args.path, real_override
    )

    output_path = args.output
    if output_path is None and args.path.is_dir():
        output_path = args.path / "comparison_plot.png"

    plot_comparison(text_cols, synth_means, ci_lo, ci_hi, real_results, per_run_rates, output_path)


if __name__ == "__main__":
    main()
