import numpy as np
from scipy import stats
from itertools import combinations
from collections import Counter


def compare_to_real(synthetic_rates: dict, real_results: dict) -> dict:
    common_keys = [k for k in real_results if k in synthetic_rates
                   and not np.isnan(synthetic_rates[k]) and not np.isnan(real_results[k])]
    if len(common_keys) < 2:
        return None

    real_vals = [real_results[k] for k in common_keys]
    synth_vals = [synthetic_rates[k] for k in common_keys]

    real_ranks = stats.rankdata([-v for v in real_vals])
    synth_ranks = stats.rankdata([-v for v in synth_vals])

    spearman_corr, spearman_p = stats.spearmanr(real_vals, synth_vals)
    kendall_corr, kendall_p = stats.kendalltau(real_vals, synth_vals)

    pairs_correct = 0
    pairs_total = 0
    pairs_tied_real = 0
    for i, j in combinations(range(len(common_keys)), 2):
        if real_vals[i] == real_vals[j]:
            pairs_tied_real += 1
            continue
        pairs_total += 1
        real_order = real_vals[i] > real_vals[j]
        synth_order = synth_vals[i] > synth_vals[j]
        if real_order == synth_order:
            pairs_correct += 1

    pairwise_accuracy = pairs_correct / pairs_total if pairs_total > 0 else None

    diffs = [synth_vals[i] - real_vals[i] for i in range(len(common_keys))]
    abs_diffs = [abs(d) for d in diffs]
    mae = np.mean(abs_diffs)
    rmse = np.sqrt(np.mean([d ** 2 for d in diffs]))

    per_variant = []
    for i, k in enumerate(common_keys):
        per_variant.append({
            "variant": k,
            "real_rate": real_vals[i],
            "synthetic_rate": synth_vals[i],
            "difference": diffs[i],
            "real_rank": int(real_ranks[i]),
            "synthetic_rank": int(synth_ranks[i]),
        })
    per_variant.sort(key=lambda x: x["real_rank"])

    return {
        "n_variants": len(common_keys),
        "spearman_correlation": spearman_corr,
        "spearman_p_value": spearman_p,
        "kendall_tau": kendall_corr,
        "kendall_p_value": kendall_p,
        "pairwise_accuracy": pairwise_accuracy,
        "pairs_correct": pairs_correct,
        "pairs_total": pairs_total,
        "pairs_tied_real": pairs_tied_real,
        "mae": mae,
        "rmse": rmse,
        "per_variant": per_variant,
    }


def format_comparison_report(comparison: dict, scenario_label: str = "") -> str:
    if comparison is None:
        return ""

    lines = []
    header = "## Comparison to Real Results"
    if scenario_label:
        header += f" ({scenario_label})"
    lines.append(header)
    lines.append("")

    lines.append("### Ordering Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(
        f"| Spearman rank correlation | {comparison['spearman_correlation']:.3f}"
        f" (p={comparison['spearman_p_value']:.3f}) |"
    )
    lines.append(
        f"| Kendall's tau | {comparison['kendall_tau']:.3f}"
        f" (p={comparison['kendall_p_value']:.3f}) |"
    )
    if comparison["pairwise_accuracy"] is not None:
        lines.append(
            f"| Pairwise accuracy | {comparison['pairwise_accuracy']:.1%}"
            f" ({comparison['pairs_correct']}/{comparison['pairs_total']} pairs correct) |"
        )
    if comparison["pairs_tied_real"] > 0:
        lines.append(
            f"| Tied pairs in real data (excluded) | {comparison['pairs_tied_real']} |"
        )
    lines.append("")

    lines.append("### Closeness Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Mean Absolute Error (MAE) | {comparison['mae']:.3f} |")
    lines.append(f"| Root Mean Square Error (RMSE) | {comparison['rmse']:.3f} |")
    lines.append("")

    lines.append("### Per-Variant Comparison")
    lines.append("")
    lines.append(
        "| Rank (Real) | Rank (Synthetic) | Variant | Real Rate | Synthetic Rate | Difference |"
    )
    lines.append("|-------------|-----------------|---------|-----------|----------------|------------|")
    for v in comparison["per_variant"]:
        lines.append(
            f"| {v['real_rank']} | {v['synthetic_rank']} | {v['variant']}"
            f" | {v['real_rate']:.3f} | {v['synthetic_rate']:.3f}"
            f" | {v['difference']:+.3f} |"
        )
    lines.append("")

    return "\n".join(lines)


def aggregate_comparisons(comparisons: list[dict], real_results: dict) -> dict:
    valid = [c for c in comparisons if c is not None]
    if not valid:
        return None

    n_runs = len(valid)

    spearman_vals = [c["spearman_correlation"] for c in valid if not np.isnan(c["spearman_correlation"])]
    kendall_vals = [c["kendall_tau"] for c in valid if not np.isnan(c["kendall_tau"])]
    pairwise_vals = [c["pairwise_accuracy"] for c in valid if c["pairwise_accuracy"] is not None]
    mae_vals = [c["mae"] for c in valid]
    rmse_vals = [c["rmse"] for c in valid]

    real_top_variant = max(real_results, key=real_results.get)
    correct_top_count = 0
    for c in valid:
        synth_top = max(
            c["per_variant"], key=lambda v: v["synthetic_rate"]
        )["variant"]
        if synth_top == real_top_variant:
            correct_top_count += 1

    variants = [v["variant"] for v in valid[0]["per_variant"]]
    variant_rates = {v: [] for v in variants}
    variant_ranks = {v: [] for v in variants}
    for c in valid:
        for pv in c["per_variant"]:
            variant_rates[pv["variant"]].append(pv["synthetic_rate"])
            variant_ranks[pv["variant"]].append(pv["synthetic_rank"])

    per_variant_stability = []
    for v in variants:
        rank_counts = Counter(variant_ranks[v])
        per_variant_stability.append({
            "variant": v,
            "real_rate": real_results[v],
            "mean_synthetic_rate": float(np.mean(variant_rates[v])),
            "std_synthetic_rate": float(np.std(variant_rates[v])),
            "rank_distribution": dict(sorted(rank_counts.items())),
        })
    per_variant_stability.sort(key=lambda x: x["real_rate"], reverse=True)

    return {
        "n_runs": n_runs,
        "correct_top_variant": correct_top_count,
        "correct_top_rate": correct_top_count / n_runs,
        "real_top_variant": real_top_variant,
        "spearman_mean": float(np.mean(spearman_vals)) if spearman_vals else None,
        "spearman_std": float(np.std(spearman_vals)) if spearman_vals else None,
        "kendall_mean": float(np.mean(kendall_vals)) if kendall_vals else None,
        "kendall_std": float(np.std(kendall_vals)) if kendall_vals else None,
        "pairwise_accuracy_mean": float(np.mean(pairwise_vals)) if pairwise_vals else None,
        "pairwise_accuracy_std": float(np.std(pairwise_vals)) if pairwise_vals else None,
        "mae_mean": float(np.mean(mae_vals)),
        "mae_std": float(np.std(mae_vals)),
        "rmse_mean": float(np.mean(rmse_vals)),
        "rmse_std": float(np.std(rmse_vals)),
        "per_variant_stability": per_variant_stability,
        "per_run_metrics": [
            {
                "spearman": c["spearman_correlation"],
                "kendall": c["kendall_tau"],
                "pairwise_accuracy": c["pairwise_accuracy"],
                "mae": c["mae"],
                "rmse": c["rmse"],
            }
            for c in valid
        ],
    }


def format_experiment_report(agg: dict, scenario_label: str = "") -> str:
    if agg is None:
        return ""

    lines = []
    header = "# Experiment Summary"
    if scenario_label:
        header += f" — {scenario_label}"
    lines.append(header)
    lines.append("")
    lines.append(f"**{agg['n_runs']} independent runs**")
    lines.append("")

    lines.append("## Top Variant Identification")
    lines.append("")
    lines.append(
        f"Real best variant: **{agg['real_top_variant']}** — "
        f"correctly identified in **{agg['correct_top_variant']}/{agg['n_runs']}** "
        f"runs ({agg['correct_top_rate']:.0%})"
    )
    lines.append("")

    lines.append("## Aggregate Ordering Metrics")
    lines.append("")
    lines.append("| Metric | Mean | Std |")
    lines.append("|--------|------|-----|")
    if agg["spearman_mean"] is not None:
        lines.append(f"| Spearman correlation | {agg['spearman_mean']:.3f} | {agg['spearman_std']:.3f} |")
    if agg["kendall_mean"] is not None:
        lines.append(f"| Kendall's tau | {agg['kendall_mean']:.3f} | {agg['kendall_std']:.3f} |")
    if agg["pairwise_accuracy_mean"] is not None:
        lines.append(f"| Pairwise accuracy | {agg['pairwise_accuracy_mean']:.1%} | {agg['pairwise_accuracy_std']:.1%} |")
    lines.append("")

    lines.append("## Aggregate Closeness Metrics")
    lines.append("")
    lines.append("| Metric | Mean | Std |")
    lines.append("|--------|------|-----|")
    lines.append(f"| MAE | {agg['mae_mean']:.3f} | {agg['mae_std']:.3f} |")
    lines.append(f"| RMSE | {agg['rmse_mean']:.3f} | {agg['rmse_std']:.3f} |")
    lines.append("")

    lines.append("## Per-Variant Stability")
    lines.append("")
    lines.append("| Variant | Real Rate | Synthetic Mean | Synthetic Std | Rank Distribution |")
    lines.append("|---------|-----------|----------------|---------------|-------------------|")
    for v in agg["per_variant_stability"]:
        rank_str = ", ".join(f"#{k}: {cnt}x" for k, cnt in v["rank_distribution"].items())
        lines.append(
            f"| {v['variant']} | {v['real_rate']:.3f} "
            f"| {v['mean_synthetic_rate']:.3f} | {v['std_synthetic_rate']:.3f} "
            f"| {rank_str} |"
        )
    lines.append("")

    lines.append("## Per-Run Metrics")
    lines.append("")
    lines.append("| Run | Spearman | Kendall | Pairwise Acc | MAE | RMSE |")
    lines.append("|-----|----------|---------|--------------|-----|------|")
    for i, m in enumerate(agg["per_run_metrics"]):
        sp = f"{m['spearman']:.3f}" if not np.isnan(m['spearman']) else "N/A"
        kt = f"{m['kendall']:.3f}" if not np.isnan(m['kendall']) else "N/A"
        pa = f"{m['pairwise_accuracy']:.1%}" if m['pairwise_accuracy'] is not None else "N/A"
        lines.append(f"| {i} | {sp} | {kt} | {pa} | {m['mae']:.3f} | {m['rmse']:.3f} |")
    lines.append("")

    return "\n".join(lines)
