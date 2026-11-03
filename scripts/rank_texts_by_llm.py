"""
For each scenario in scenario_presets and each of the 3 LLMs,
ask the LLM to rank the message texts by likely effectiveness,
then write a summary markdown table to data/llm_text_rankings.md.
"""

import re
import sys
import os
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from scipy import stats
from itertools import combinations
from inputs.scenario_presets import scenario_presets
from src.llm_utils import call_llm

N_SAMPLES = 10

EXCLUDED_SCENARIOS = {"sleepio", "Wayfinder", "melanoma", "covid_vaccine_RCT_3", "milkman_vaccine_study"}

MODELS = [
    "ri.language-model-service..language-model.gpt-5-1",
    "ri.language-model-service..language-model.anthropic-claude-4-6-sonnet",
    "ri.language-model-service..language-model.anthropic-claude-4-6-opus",
    "ri.language-model-service..language-model.gpt-oss-120b",
]

MODEL_LABELS = {
    "ri.language-model-service..language-model.gpt-5-1": "GPT-5.1",
    "ri.language-model-service..language-model.anthropic-claude-4-6-sonnet": "Claude 4.6 Sonnet",
    "ri.language-model-service..language-model.anthropic-claude-4-6-opus ": "Claude 4.6 Opus",
    "ri.language-model-service..language-model.gpt-oss-120b": "GPT-OSS-120B",
}


def build_prompt(question: str, texts: dict[str, str]) -> str:
    text_names = list(texts.keys())
    text_list = "\n".join(
        f"- **{name}**: \"{text}\"" for name, text in texts.items()
    )
    return (
        f"You are designing an experiment to determine which healthcare message "
        f"performs best at influencing patient behaviour.\n\n"
        f"The question patients are asked is:\n\"{question}\"\n\n"
        f"Here are the candidate messages:\n{text_list}\n\n"
        f"Rank these messages from most to least effective at encouraging "
        f"the desired behaviour. Return ONLY a numbered list using the exact "
        f"message names ({', '.join(text_names)}), one per line, e.g.:\n"
        f"1. message_name\n"
        f"2. message_name\n"
    )


def parse_ranking(response: str, valid_names: list[str]) -> list[str]:
    """Extract ordered message names from a numbered list response."""
    ranked = []
    for line in response.strip().splitlines():
        line = line.strip()
        match = re.match(r"^\d+[\.\)]\s*\**(.+?)\**\s*$", line)
        if not match:
            match = re.match(r"^\d+[\.\)]\s*\**(.+?)\**\s*[—\-–:]", line)
        if match:
            name = match.group(1).strip().strip("*").strip()
            for valid in valid_names:
                if valid.lower() == name.lower() or valid.lower().replace("_", " ") == name.lower():
                    ranked.append(valid)
                    break
    if len(ranked) != len(valid_names):
        return [f"(parse error — got {len(ranked)}/{len(valid_names)})"]
    return ranked


def compute_ranking_metrics(llm_ranking: list[str], real_results: dict) -> dict | None:
    """Compute Spearman, Kendall, and pairwise accuracy of an LLM ranking vs real results."""
    common = [k for k in llm_ranking if k in real_results]
    if len(common) < 2:
        return None

    llm_rank_vals = [llm_ranking.index(k) + 1 for k in common]
    real_sorted = sorted(common, key=lambda k: real_results[k], reverse=True)
    real_rank_vals = [real_sorted.index(k) + 1 for k in common]

    spearman, spearman_p = stats.spearmanr(real_rank_vals, llm_rank_vals)
    kendall, kendall_p = stats.kendalltau(real_rank_vals, llm_rank_vals)

    pairs_correct = 0
    pairs_total = 0
    for i, j in combinations(range(len(common)), 2):
        if real_results[common[i]] == real_results[common[j]]:
            continue
        pairs_total += 1
        real_order = real_results[common[i]] > real_results[common[j]]
        llm_order = llm_ranking.index(common[i]) < llm_ranking.index(common[j])
        if real_order == llm_order:
            pairs_correct += 1

    pairwise_acc = pairs_correct / pairs_total if pairs_total > 0 else None

    return {
        "spearman": spearman,
        "spearman_p": spearman_p,
        "kendall": kendall,
        "kendall_p": kendall_p,
        "pairwise_accuracy": pairwise_acc,
        "pairs_correct": pairs_correct,
        "pairs_total": pairs_total,
    }


def consensus_ranking(all_rankings: list[list[str]], text_names: list[str]) -> list[str]:
    """Compute consensus ranking by average rank position across N samples."""
    rank_sums = {name: 0.0 for name in text_names}
    valid_count = 0
    for ranking in all_rankings:
        if len(ranking) != len(text_names):
            continue
        valid_count += 1
        for pos, name in enumerate(ranking):
            rank_sums[name] += pos
    if valid_count == 0:
        return text_names
    return sorted(text_names, key=lambda n: rank_sums[n] / valid_count)


def rank_stability(all_rankings: list[list[str]], text_names: list[str]) -> dict[str, dict[int, int]]:
    """For each text, count how often it appeared at each rank position."""
    position_counts = {name: Counter() for name in text_names}
    for ranking in all_rankings:
        if len(ranking) != len(text_names):
            continue
        for pos, name in enumerate(ranking):
            position_counts[name][pos + 1] += 1
    return position_counts


def main():
    # results[scenario_key][model] = list of N rankings
    results: dict[str, dict[str, list[list[str]]]] = {}

    scenarios = {k: v for k, v in scenario_presets.items() if k not in EXCLUDED_SCENARIOS}
    total = len(scenarios) * len(MODELS) * N_SAMPLES
    done = 0

    for scenario_key, scenario in scenarios.items():
        label = scenario["label"]
        question = scenario["question"]
        texts = scenario["texts"]
        text_names = list(texts.keys())
        results[scenario_key] = {}

        prompt = build_prompt(question, texts)

        for model in MODELS:
            model_label = MODEL_LABELS[model]
            all_rankings = []

            for n in range(N_SAMPLES):
                done += 1
                print(f"[{done}/{total}] {label} — {model_label} (sample {n+1}/{N_SAMPLES})...")

                response = call_llm(prompt, model=model, temp=1.0)
                if response:
                    ranked = parse_ranking(response, text_names)
                else:
                    ranked = ["(no response)"]
                all_rankings.append(ranked)
                print(f"         → {ranked}")

            results[scenario_key][model] = all_rankings

    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "llm_text_rankings.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# LLM Text Rankings (best of {N_SAMPLES}, temp=1)\n\n")

        for scenario_key, scenario in scenarios.items():
            label = scenario["label"]
            real = scenario.get("real_results", {})
            text_names = list(scenario["texts"].keys())
            true_ranking = sorted(real, key=lambda k: real[k], reverse=True) if real else []

            model_consensus = {}
            model_stability = {}
            for model in MODELS:
                all_rankings = results[scenario_key][model]
                model_consensus[model] = consensus_ranking(all_rankings, text_names)
                model_stability[model] = rank_stability(all_rankings, text_names)

            all_cols = [true_ranking] + [model_consensus[m] for m in MODELS]
            max_rows = max(len(r) for r in all_cols)

            headers = ["Ranking", "True"] + [MODEL_LABELS[m] for m in MODELS]
            f.write(f"## {label}\n\n")
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("| " + " | ".join("---" for _ in headers) + " |\n")

            for i in range(max_rows):
                row = [str(i + 1)]
                row.append(true_ranking[i] if i < len(true_ranking) else "")
                for model in MODELS:
                    ranking = model_consensus[model]
                    name = ranking[i] if i < len(ranking) else ""
                    stability = model_stability[model]
                    if name and name in stability:
                        count = stability[name].get(i + 1, 0)
                        row.append(f"{name} ({count}/{N_SAMPLES})")
                    else:
                        row.append(name)
                f.write("| " + " | ".join(row) + " |\n")

            if real:
                f.write("\n")
                metrics_headers = ["Metric"] + [MODEL_LABELS[m] for m in MODELS]
                f.write("| " + " | ".join(metrics_headers) + " |\n")
                f.write("| " + " | ".join("---" for _ in metrics_headers) + " |\n")

                for metric_name, metric_key in [
                    ("Spearman (mean)", "spearman"),
                    ("Kendall's tau (mean)", "kendall"),
                    ("Pairwise accuracy (mean)", "pairwise_accuracy"),
                ]:
                    row = [metric_name]
                    for model in MODELS:
                        all_rankings = results[scenario_key][model]
                        values = []
                        for ranking in all_rankings:
                            m = compute_ranking_metrics(ranking, real)
                            if m is not None and m[metric_key] is not None:
                                values.append(m[metric_key])
                        if not values:
                            row.append("N/A")
                        elif metric_key == "pairwise_accuracy":
                            row.append(f"{np.mean(values):.0%} ± {np.std(values):.0%}")
                        else:
                            row.append(f"{np.mean(values):.3f} ± {np.std(values):.3f}")
                    f.write("| " + " | ".join(row) + " |\n")

            f.write("\n")

    print(f"\nDone! Results written to {os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
