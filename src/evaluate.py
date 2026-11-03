import os
import pandas as pd
import numpy as np
from scipy import stats
from src.compare_to_real import compare_to_real, format_comparison_report


DEFAULT_REPORT_SECTIONS = {
    "overall_results": True,
    "text_ranking": True,
    "cross_text_agreement": True,
    "demographic_breakdown": True,
    "demographic_disparity": True,
    "sample_size_warnings": True,
    "behavioural_traits": True,
    "bias_judge": True,
    "comparison_to_real": True,
}

def prepare_chart_data(results_df: pd.DataFrame, text_cols: list[str], binary_threshold=None):
    """Return chart-ready numeric data, converting scale answers to YES rates when a binary threshold is configured."""
    chart_df = results_df.copy()
    for col in text_cols:
        raw_num = pd.to_numeric(chart_df[col], errors="coerce")
        if binary_threshold is not None:
            chart_df[col] = (raw_num >= binary_threshold).astype("float").mask(raw_num.isna())
        else:
            chart_df[col] = raw_num
    return chart_df

def generate_evaluation_report(
    results_df: pd.DataFrame,
    patients_csv_path: str,
    demographic_keys: list[str],
    behavioural_keys: list[str],
    input_texts: dict[str, str],
    output_dir: str,
    run_name: str,
    run_timestamp: str,
    question: str = "",
    scale: str = "",
    top_n: int = 10,
    bias_df: pd.DataFrame = None,
    report_sections: dict = None,
    answer_type={"scale": [0, 1]},
    binary_threshold=None,
    real_results: dict = None,
):
    sections = {**DEFAULT_REPORT_SECTIONS, **(report_sections or {})}
    is_scale = isinstance(answer_type, dict) and "scale" in answer_type
    # If binary_threshold is set on a scale, evaluate as binary (>= threshold = YES)
    treat_as_binary = is_scale and binary_threshold is not None

    patients_df = pd.read_csv(patients_csv_path)
    text_names = list(input_texts.keys())
    text_cols = [name for name in text_names if name in results_df.columns]

    # Merge patient demographics + behaviours into results
    merge_cols = ["patient_id"] + demographic_keys + behavioural_keys
    merged = results_df.merge(patients_df[merge_cols], on="patient_id")

    # Convert answers to numeric. Missing/invalid answers stay NaN (never imputed),
    # so they are excluded from every statistic rather than counted as a neutral value.
    for col in text_cols:
        raw_num = pd.to_numeric(merged[col], errors="coerce")
        if treat_as_binary:
            # (raw_num >= threshold) would turn NaN into a false "NO"; mask it back to NaN.
            merged[f"{col}_num"] = (raw_num >= binary_threshold).astype("float").mask(raw_num.isna())
        else:
            merged[f"{col}_num"] = raw_num
    num_cols = [f"{col}_num" for col in text_cols]

    # For reporting purposes, treat_as_binary uses the binary report style
    is_scale_report = is_scale and not treat_as_binary

    lines = []
    lines.append("# Evaluation Report")
    lines.append("")
    lines.append(f"- **Run name:** {run_name}")
    lines.append(f"- **Timestamp:** {run_timestamp}")
    lines.append(f"- **N patients:** {len(patients_df)}")
    lines.append(f"- **N texts:** {len(input_texts)}")
    lines.append("")
    lines.append(f"- **Question:** {question or 'No question asked'}")
    lines.append(f"- **Scale:** {scale or 'No scale provided'}")

    if is_scale:
        scale_min, scale_max = answer_type["scale"]
        if treat_as_binary:
            lines.append("- **Answer type:** Binary (derived from scale)")
            lines.append(f"- **Binary threshold:** >= {binary_threshold} is YES, < {binary_threshold} is NO")
        else:
            lines.append(f"- **Answer type:** Scale ({scale_min} to {scale_max})")
    else:
        lines.append("- **Answer type:** Scale (unknown)")

    lines.append("")

    # --- Text reference (always shown) ---
    lines.append("## Texts Used")
    lines.append("")
    for text_name, text_content in input_texts.items():
        lines.append(f"- **{text_name}:** {text_content}")
    lines.append("")

    # --- Data quality (missing / unparsed responses) ---
    lines.append("## Data Quality")
    lines.append("")
    lines.append(
        "Missing or invalid LLM answers are recorded as missing (not imputed) and "
        "excluded from all statistics below. This section reports how much data is missing."
    )
    lines.append("")
    lines.append("| Text | Answered | Missing | Missing Rate |")
    lines.append("|------|----------|---------|--------------|")
    total_answers = len(merged) * len(num_cols)
    total_missing = 0
    for col, num_col in zip(text_cols, num_cols):
        answered = int(merged[num_col].count())
        missing = len(merged) - answered
        total_missing += missing
        rate = missing / len(merged) if len(merged) > 0 else 0.0
        lines.append(f"| {col} | {answered} | {missing} | {rate:.3f} |")
    lines.append("")

    # Judge parse failures, if a bias judgement frame was provided.
    n_judge_unparsed = 0
    if bias_df is not None and not bias_df.empty and "judge_parsed" in bias_df.columns:
        judge_parsed_flag = bias_df["judge_parsed"].apply(
            lambda x: x if isinstance(x, bool) else str(x).strip().lower() == "true"
        )
        n_judge_unparsed = int((~judge_parsed_flag).sum())
        lines.append(
            f"- **Bias judgements:** {len(bias_df)} total, "
            f"{int(judge_parsed_flag.sum())} parsed, {n_judge_unparsed} unparsed (excluded)."
        )
        lines.append("")

    if total_missing > 0 or n_judge_unparsed > 0:
        lines.append(
            f"> **Warning:** {total_missing} of {total_answers} answers were missing/invalid "
            f"and {n_judge_unparsed} judge responses were unparsed. See `missing_answers.csv` "
            "for the affected prompts."
        )
        lines.append("")

    # --- Overall summary per text ---
    if sections["overall_results"]:
        lines.append("## Overall Results")
        lines.append("")
        if is_scale_report:
            lines.append("| Text | Text Content | Mean Score | 95% CI | N | Missing |")
            lines.append("|------|-------------|------------|--------|---|---------|")
            for col, num_col in zip(text_cols, num_cols):
                text_content = input_texts.get(col, "")
                text_preview = (text_content[:50] + "...") if len(text_content) > 50 else text_content
                n = int(merged[num_col].count())
                missing = len(merged) - n
                mean = merged[num_col].mean()
                if n > 1:
                    se = merged[num_col].std() / np.sqrt(n)
                    t_crit = stats.t.ppf(0.975, df=n - 1)
                    ci_str = f"[{mean - t_crit * se:.3f}, {mean + t_crit * se:.3f}]"
                else:
                    ci_str = "N/A"
                lines.append(f"| {col} | {text_preview} | {mean:.3f} | {ci_str} | {n} | {missing} |")
        else:
            lines.append("| Text | Text Content | YES Count | N | Missing | Mean (YES rate) | 95% CI |")
            lines.append("|------|-------------|-----------|---|---------|-----------------|--------|")
            for col, num_col in zip(text_cols, num_cols):
                text_content = input_texts.get(col, "")
                text_preview = (text_content[:50] + "...") if len(text_content) > 50 else text_content
                yes_count = int(merged[num_col].sum())
                n = int(merged[num_col].count())
                missing = len(merged) - n
                mean = merged[num_col].mean()
                if n > 1:
                    se = np.sqrt(mean * (1 - mean) / n)
                    z_crit = stats.norm.ppf(0.975)
                    ci_str = f"[{max(0, mean - z_crit * se):.3f}, {min(1, mean + z_crit * se):.3f}]"
                else:
                    ci_str = "N/A"
                lines.append(f"| {col} | {text_preview} | {yes_count} | {n} | {missing} | {mean:.3f} | {ci_str} |")
        lines.append("")

    # --- Text ranking ---
    if sections["text_ranking"]:
        if is_scale_report:
            lines.append("## Text Ranking (by mean score)")
            lines.append("")
            lines.append("Texts ranked from highest to lowest mean score.")
        else:
            lines.append("## Text Ranking (by YES rate)")
            lines.append("")
            lines.append("Texts ranked from most to least effective at eliciting a YES response.")
        lines.append("")
        text_rankings = []
        for col, num_col in zip(text_cols, num_cols):
            text_content = input_texts.get(col, "")
            text_preview = (text_content[:60] + "...") if len(text_content) > 60 else text_content
            mean = merged[num_col].mean()
            text_rankings.append({"col": col, "preview": text_preview, "mean": mean})
        text_rankings.sort(key=lambda x: x["mean"], reverse=True)
        score_label = "Mean Score" if is_scale_report else "YES Rate"
        lines.append(f"| Rank | Text | Text Content | {score_label} |")
        lines.append("|------|------|-------------|----------|")
        for rank, entry in enumerate(text_rankings, start=1):
            lines.append(f"| {rank} | {entry['col']} | {entry['preview']} | {entry['mean']:.3f} |")
        lines.append("")

    # --- Cross-text agreement ---
    if sections["cross_text_agreement"]:
        lines.append("## Cross-Text Agreement")
        lines.append("")
        if len(text_cols) > 1:
            # Only patients who answered every text can be compared across texts.
            complete = merged[["patient_id"] + num_cols].dropna(subset=num_cols)
            n_excluded = len(merged) - len(complete)
            n_total = len(complete)
            if n_total == 0:
                lines.append("_No patient answered every text — cross-text agreement is not applicable._")
            elif is_scale_report:
                lines.append(
                    "How consistently does each patient respond across all texts? "
                    "Unanimous means the patient gave the exact same score for every text. "
                    f"Restricted to the {n_total} patients who answered every text "
                    f"({n_excluded} excluded for missing answers)."
                )
                lines.append("")
                patient_answers = complete.copy()
                patient_answers["unanimous"] = patient_answers[num_cols].nunique(axis=1) == 1
                n_unanimous = patient_answers["unanimous"].sum()
                n_mixed = n_total - n_unanimous
                lines.append("| Metric | Count | Proportion |")
                lines.append("|--------|-------|------------|")
                lines.append(f"| Unanimous (same score for all texts) | {n_unanimous} | {n_unanimous / n_total:.3f} |")
                lines.append(f"| Mixed (score varies by text) | {n_mixed} | {n_mixed / n_total:.3f} |")
            else:
                lines.append(
                    "How consistently does each patient respond across all texts? "
                    "High agreement means the patient profile dominates the response; "
                    "low agreement means the text wording has more influence. "
                    f"Restricted to the {n_total} patients who answered every text "
                    f"({n_excluded} excluded for missing answers)."
                )
                lines.append("")
                patient_answers = complete.copy()
                patient_answers["all_yes"] = patient_answers[num_cols].sum(axis=1) == len(num_cols)
                patient_answers["all_no"] = patient_answers[num_cols].sum(axis=1) == 0
                patient_answers["unanimous"] = patient_answers["all_yes"] | patient_answers["all_no"]
                n_unanimous = patient_answers["unanimous"].sum()
                n_all_yes = patient_answers["all_yes"].sum()
                n_all_no = patient_answers["all_no"].sum()
                n_mixed = n_total - n_unanimous
                lines.append("| Metric | Count | Proportion |")
                lines.append("|--------|-------|------------|")
                lines.append(f"| All YES (across every text) | {n_all_yes} | {n_all_yes / n_total:.3f} |")
                lines.append(f"| All NO (across every text) | {n_all_no} | {n_all_no / n_total:.3f} |")
                lines.append(f"| Unanimous (same answer for all) | {n_unanimous} | {n_unanimous / n_total:.3f} |")
                lines.append(f"| Mixed (answer varies by text) | {n_mixed} | {n_mixed / n_total:.3f} |")
        else:
            lines.append("_Only one text — cross-text agreement is not applicable._")
        lines.append("")

    # --- Breakdown per demographic group ---
    if sections["demographic_breakdown"]:
        for demo_key in demographic_keys:
            lines.append(f"## Breakdown by `{demo_key}`")
            lines.append("")
            groups = sorted(merged[demo_key].dropna().unique())
            for col, num_col in zip(text_cols, num_cols):
                lines.append(f"### {col}")
                lines.append("")
                if is_scale_report:
                    lines.append(f"| {demo_key} | Mean Score | 95% CI | N |")
                    lines.append(f"|{'-' * (len(demo_key) + 2)}|------------|--------|---|")
                    for group in groups:
                        subset = merged[merged[demo_key] == group]
                        n = int(subset[num_col].count())
                        mean = subset[num_col].mean() if n > 0 else 0.0
                        if n > 1:
                            se = subset[num_col].std() / np.sqrt(n)
                            t_crit = stats.t.ppf(0.975, df=n - 1)
                            ci_str = f"[{mean - t_crit * se:.3f}, {mean + t_crit * se:.3f}]"
                        else:
                            ci_str = "N/A"
                        lines.append(f"| {group} | {mean:.3f} | {ci_str} | {n} |")
                else:
                    lines.append(f"| {demo_key} | YES Count | N | Mean (YES rate) | 95% CI |")
                    lines.append(f"|{'-' * (len(demo_key) + 2)}|-----------|---|-----------------|--------|")
                    for group in groups:
                        subset = merged[merged[demo_key] == group]
                        yes_count = int(subset[num_col].sum())
                        n = int(subset[num_col].count())
                        mean = subset[num_col].mean() if n > 0 else 0.0
                        if n > 1:
                            se = np.sqrt(mean * (1 - mean) / n)
                            z_crit = stats.norm.ppf(0.975)
                            ci_str = f"[{max(0, mean - z_crit * se):.3f}, {min(1, mean + z_crit * se):.3f}]"
                        else:
                            ci_str = "N/A"
                        lines.append(f"| {group} | {yes_count} | {n} | {mean:.3f} | {ci_str} |")
                lines.append("")

    # --- Demographic disparity score ---
    if sections["demographic_disparity"]:
        lines.append("## Demographic Disparity")
        lines.append("")
        score_label = "Mean Score" if is_scale_report else "YES Rate"
        lines.append(
            f"For each demographic dimension and text, the disparity score is the difference between the "
            f"highest and lowest {score_label.lower()} across groups within that dimension."
        )
        lines.append("")
        lines.append(f"| Demographic | Text | Min Group | Min {score_label} | Max Group | Max {score_label} | Disparity |")
        lines.append("|-------------|------|-----------|--------------|-----------|--------------|-----------|")
        for demo_key in demographic_keys:
            groups = sorted(merged[demo_key].dropna().unique())
            for col, num_col in zip(text_cols, num_cols):
                group_rates = {}
                for group in groups:
                    subset = merged[merged[demo_key] == group]
                    if subset[num_col].count() > 0:
                        group_rates[group] = subset[num_col].mean()
                if group_rates:
                    min_group = min(group_rates, key=group_rates.get)
                    max_group = max(group_rates, key=group_rates.get)
                    disparity = group_rates[max_group] - group_rates[min_group]
                    lines.append(
                        f"| {demo_key} | {col} | {min_group} | {group_rates[min_group]:.3f} "
                        f"| {max_group} | {group_rates[max_group]:.3f} | {disparity:.3f} |"
                    )
        lines.append("")

    # --- Sample size warnings ---
    if sections["sample_size_warnings"]:
        small_sample_threshold = 5
        warnings = []
        for demo_key in demographic_keys:
            for group in merged[demo_key].dropna().unique():
                n = len(merged[merged[demo_key] == group])
                if n < small_sample_threshold:
                    warnings.append({"type": "demographic", "dimension": demo_key, "group": group, "n": n})
        for beh_key in behavioural_keys:
            for trait_value in merged[beh_key].dropna().unique():
                n = len(merged[merged[beh_key] == trait_value])
                if n < small_sample_threshold:
                    warnings.append({"type": "behavioural", "dimension": beh_key, "group": trait_value, "n": n})
        lines.append("## Sample Size Warnings")
        lines.append("")
        if warnings:
            lines.append(
                f"The following groups have fewer than **{small_sample_threshold} patients**. "
                "Statistics for these groups may be unreliable."
            )
            lines.append("")
            lines.append("| Type | Dimension | Group | N |")
            lines.append("|------|-----------|-------|---|")
            for w in sorted(warnings, key=lambda x: x["n"]):
                lines.append(f"| {w['type']} | {w['dimension']} | {w['group']} | {w['n']} |")
        else:
            lines.append(f"All groups have at least {small_sample_threshold} patients. No warnings.")
        lines.append("")

        # --- Missing data warnings ---
        missing_rate_threshold = 0.20
        missing_warnings = []
        for kind, keys in (("demographic", demographic_keys), ("behavioural", behavioural_keys)):
            for dimension in keys:
                for group in merged[dimension].dropna().unique():
                    subset = merged[merged[dimension] == group]
                    total = len(subset) * len(num_cols)
                    if total == 0:
                        continue
                    missing = total - int(subset[num_cols].count().sum())
                    rate = missing / total
                    if rate > missing_rate_threshold:
                        missing_warnings.append(
                            {"type": kind, "dimension": dimension, "group": group,
                             "missing": missing, "total": total, "rate": rate}
                        )
        lines.append("### Missing Data Warnings")
        lines.append("")
        if missing_warnings:
            lines.append(
                f"The following groups have more than **{missing_rate_threshold:.0%}** missing/invalid "
                "answers. Statistics for these groups may be unreliable due to missing data."
            )
            lines.append("")
            lines.append("| Type | Dimension | Group | Missing | Total | Missing Rate |")
            lines.append("|------|-----------|-------|---------|-------|--------------|")
            for w in sorted(missing_warnings, key=lambda x: x["rate"], reverse=True):
                lines.append(
                    f"| {w['type']} | {w['dimension']} | {w['group']} | {w['missing']} "
                    f"| {w['total']} | {w['rate']:.3f} |"
                )
        else:
            lines.append(
                f"No group exceeds {missing_rate_threshold:.0%} missing answers."
            )
        lines.append("")

    # --- Behavioural trait analysis ---
    if sections["behavioural_traits"]:
        lines.append("## Behavioural Trait Analysis")
        lines.append("")
        score_label = "Mean Score" if is_scale_report else "YES Rate"
        lines.append(
            f"For each text, traits are ranked by their {score_label.lower()} among patients who hold that trait."
        )
        lines.append("")
        for col, num_col in zip(text_cols, num_cols):
            lines.append(f"### {col}")
            lines.append("")
            trait_rates = []
            for beh_key in behavioural_keys:
                for trait_value in merged[beh_key].dropna().unique():
                    subset = merged[merged[beh_key] == trait_value]
                    n = int(subset[num_col].count())
                    if n == 0:
                        continue
                    rate = subset[num_col].mean()
                    trait_rates.append(
                        {
                            "dimension": beh_key,
                            "trait": trait_value,
                            "rate": rate,
                            "n": n,
                        }
                    )
            trait_rates.sort(key=lambda x: x["rate"], reverse=True)
            lines.append(f"**Top {top_n} traits with highest {score_label.lower()}:**")
            lines.append("")
            lines.append(f"| Rank | Dimension | Trait | {score_label} | N |")
            lines.append("|------|-----------|-------|----------|---|")
            for rank, entry in enumerate(trait_rates[:top_n], start=1):
                lines.append(
                    f"| {rank} | {entry['dimension']} | {entry['trait']} | {entry['rate']:.3f} | {entry['n']} |"
                )
            lines.append("")
            lines.append(f"**Top {top_n} traits with lowest {score_label.lower()}:**")
            lines.append("")
            lines.append(f"| Rank | Dimension | Trait | {score_label} | N |")
            lines.append("|------|-----------|-------|----------|---|")
            for rank, entry in enumerate(reversed(trait_rates[-top_n:]), start=1):
                lines.append(
                    f"| {rank} | {entry['dimension']} | {entry['trait']} | {entry['rate']:.3f} | {entry['n']} |"
                )
            lines.append("")

    # --- Bias Judge Analysis ---
    if sections["bias_judge"] and bias_df is not None and not bias_df.empty:
        bias_merged = bias_df.merge(patients_df[["patient_id"] + demographic_keys], on="patient_id")
        # Exclude unparsed judge responses so they aren't counted as "not biased".
        n_judge_total = len(bias_merged)
        if "judge_parsed" in bias_merged.columns:
            parsed_flag = bias_merged["judge_parsed"].apply(
                lambda x: x if isinstance(x, bool) else str(x).strip().lower() == "true"
            )
            bias_merged = bias_merged[parsed_flag]
        n_judge_unparsed = n_judge_total - len(bias_merged)
        bias_merged["bias_flag"] = bias_merged["dangerous_bias_present"].apply(
            lambda x: x if isinstance(x, bool) else str(x).strip().lower() == "true"
        )
        total_judgements = len(bias_merged)
        total_biased = bias_merged["bias_flag"].sum()

        lines.append("## Bias Judge Analysis")
        lines.append("")
        lines.append(
            "An LLM judge reviewed every patient reasoning for dangerous ethical bias. "
            "This section reports the results."
        )
        lines.append("")

        # Overall bias summary
        lines.append("### Overall Bias Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total reasonings judged (parsed) | {total_judgements} |")
        lines.append(f"| Unparsed judge responses (excluded) | {n_judge_unparsed} |")
        lines.append(f"| Dangerous bias detected | {total_biased} |")
        bias_rate = total_biased / total_judgements if total_judgements > 0 else 0.0
        lines.append(f"| Bias rate | {bias_rate:.3f} |")
        if total_biased > 0:
            avg_severity = bias_merged.loc[bias_merged["bias_flag"], "bias_severity"].mean()
            lines.append(f"| Mean severity (biased only) | {avg_severity:.2f} / 4 |")
        lines.append("")

        # Bias rate per text
        lines.append("### Bias Rate by Text")
        lines.append("")
        lines.append("| Text | Biased | Total | Bias Rate |")
        lines.append("|------|--------|-------|-----------|")
        for text_id in sorted(bias_merged["text_id"].unique()):
            subset = bias_merged[bias_merged["text_id"] == text_id]
            n_biased = subset["bias_flag"].sum()
            n_total = len(subset)
            rate = n_biased / n_total if n_total > 0 else 0.0
            lines.append(f"| {text_id} | {n_biased} | {n_total} | {rate:.3f} |")
        lines.append("")

        # Bias rate per demographic subgroup
        lines.append("### Bias Rate by Demographic Subgroup")
        lines.append("")
        lines.append("Proportion of reasonings flagged as biased, broken down by demographic group.")
        lines.append("")
        lines.append("| Demographic | Group | Biased | Total | Bias Rate |")
        lines.append("|-------------|-------|--------|-------|-----------|")
        for demo_key in demographic_keys:
            for group in sorted(bias_merged[demo_key].dropna().unique()):
                subset = bias_merged[bias_merged[demo_key] == group]
                n_biased = subset["bias_flag"].sum()
                n_total = len(subset)
                rate = n_biased / n_total if n_total > 0 else 0.0
                lines.append(f"| {demo_key} | {group} | {n_biased} | {n_total} | {rate:.3f} |")
        lines.append("")

        # Flagged cases with reasoning
        flagged = bias_merged[bias_merged["bias_flag"]].copy()
        if not flagged.empty:
            flagged_sorted = flagged.sort_values("bias_severity", ascending=False)
            lines.append("### Flagged Cases — Dangerous Bias Detected")
            lines.append("")
            lines.append(
                "The following patient reasonings were flagged by the bias judge. Sorted by severity (highest first)."
            )
            lines.append("")
            for _, row in flagged_sorted.iterrows():
                lines.append("---")
                lines.append("")
                lines.append(
                    f"**Patient:** `{row['patient_id']}` | **Text:** `{row['text_id']}` "
                    f"| **Severity:** {row['bias_severity']}/4 "
                    f"| **Harm likelihood:** {row['harm_likelihood']}/3"
                )
                lines.append("")
                bias_types = row.get("bias_types", [])
                if isinstance(bias_types, str):
                    bias_types = bias_types.strip("[]").replace("'", "").split(", ") if bias_types else []
                if bias_types:
                    lines.append(f"**Bias types:** {', '.join(bias_types)}")
                    lines.append("")
                groups_affected = row.get("protected_groups_affected", [])
                if isinstance(groups_affected, str):
                    groups_affected = (
                        groups_affected.strip("[]").replace("'", "").split(", ") if groups_affected else []
                    )
                if groups_affected:
                    lines.append(f"**Protected groups affected:** {', '.join(groups_affected)}")
                    lines.append("")
                lines.append(f"**Judge justification:** {row.get('justification', 'N/A')}")
                lines.append("")
                lines.append("**Original reasoning:**")
                lines.append(f"> {row.get('reasoning', 'N/A')}")
                lines.append("")
        else:
            lines.append("### Flagged Cases")
            lines.append("")
            lines.append("_No dangerous bias was detected in any reasoning._")
            lines.append("")

    # --- Comparison to real results ---
    if real_results and sections.get("comparison_to_real", True):
        synthetic_rates = {}
        for col, num_col in zip(text_cols, num_cols):
            vals = merged[num_col].dropna()
            if treat_as_binary:
                synthetic_rates[col] = float(vals.mean())
            else:
                synthetic_rates[col] = float(vals.mean())
        comparison = compare_to_real(synthetic_rates, real_results)
        if comparison:
            lines.append(format_comparison_report(comparison))

    # --- Write report ---
    report_text = "\n".join(lines)

    report_path = os.path.join(output_dir, "evaluation_report.md")
    with open(report_path, "w") as f:
        f.write(report_text)

    # Also print a summary to terminal
    print(f"\n--- Evaluation (run: {run_name}_{run_timestamp}) ---")
    for col, num_col in zip(text_cols, num_cols):
        n = int(merged[num_col].count())
        if is_scale_report:
            mean = merged[num_col].mean()
            if n > 1:
                se = merged[num_col].std() / np.sqrt(n)
                t_crit = stats.t.ppf(0.975, df=n - 1)
                ci_lo, ci_hi = mean - t_crit * se, mean + t_crit * se
                print(f"  {col}: mean={mean:.2f}, 95% CI=[{ci_lo:.2f}, {ci_hi:.2f}] (n={n})")
            else:
                print(f"  {col}: mean={mean:.2f}, 95% CI=N/A (n={n})")
        else:
            yes_count = int(merged[num_col].sum())
            mean = merged[num_col].mean()
            print(f"  {col}: {yes_count}/{n} responded YES ({mean:.1%})")
    print(f"\nFull report saved to: {report_path}")
