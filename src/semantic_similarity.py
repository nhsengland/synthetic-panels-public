# How this works:
# This module scores free-text survey responses on a Likert scale using
# semantic similarity. First, an LLM generates multiple sets of reference
# statements—one per scale level. These references and the respondent's
# text are embedded into vector space. Cosine similarity between the
# response embedding and each reference embedding is computed, then
# converted into a probability mass function (PMF) over scale levels
# (with optional temperature smoothing). PMFs from multiple reference
# sets are averaged for robustness, and the expected value of the final
# PMF yields the numeric score assigned to the response.

# For more information read this paper: https://arxiv.org/abs/2510.08338

from src.llm_utils import call_llm, call_llm_async, get_embeddings
import json
import numpy as np
import pandas as pd
import os
from sklearn.metrics.pairwise import cosine_similarity

def response_to_pmf_single_set(response_vector, reference_set_vectors, epsilon=0.0, temperature=1.0):
    """
    Map a response embedding to a probability mass function (pmf) using ONE complete reference set
    (exactly one reference vector per level).

    Args:
        response_vector: embedding of the free-text response
        reference_set_vectors: dict {level: ref_vector} for a single set
        epsilon: offset to avoid zero-probability levels
        temperature: pmf smearing parameter

    Returns:
        dict {level: probability}
    """
    levels = sorted(reference_set_vectors.keys(), key=lambda x: int(x))

    # Cosine similarity to this set's single reference statement per level
    similarities = {
        level: cosine_similarity([response_vector], [reference_set_vectors[level]])[0][0]
        for level in levels
    }

    # Subtract the minimum similarity across levels, add epsilon
    min_sim = min(similarities.values())
    adjusted = {lvl: (sim - min_sim) + epsilon for lvl, sim in similarities.items()}

    total = sum(adjusted.values())
    pmf = ({lvl: 1.0 / len(levels) for lvl in levels} if total == 0
           else {lvl: v / total for lvl, v in adjusted.items()})

    # Temperature
    if temperature != 1.0:
        pmf = {lvl: p ** (1.0 / temperature) for lvl, p in pmf.items()}
        t_total = sum(pmf.values())
        pmf = {lvl: p / t_total for lvl, p in pmf.items()}

    return pmf


def response_to_pmf(response_vector, all_sets_vectors, epsilon=0.0, temperature=1.0):
    """
    Map a response embedding to a pmf by building one pmf PER reference set
    (each normalized independently) and averaging the resulting pmfs.
    Matches the paper's multi-set averaging approach.

    Args:
        response_vector: embedding of the free-text response
        all_sets_vectors: dict {set_id: {level: ref_vector}}
        epsilon, temperature: passed through to each single-set pmf

    Returns:
        dict {level: probability}  (averaged across sets)
    """
    per_set_pmfs = [
        response_to_pmf_single_set(response_vector, set_vectors, epsilon, temperature)
        for set_vectors in all_sets_vectors.values()
    ]

    levels = per_set_pmfs[0].keys()
    n_sets = len(per_set_pmfs)
    averaged = {
        level: sum(pmf[level] for pmf in per_set_pmfs) / n_sets
        for level in levels
    }
    return averaged


def pmf_to_mean(pmf):
    """
    Compute the expected value (weighted mean) of a discrete probability mass function.

    Multiplies each scale level by its associated probability and sums
    the results, yielding a single continuous score that summarizes the
    distribution across Likert-scale levels.

    Args:
        pmf: dict {level (str): probability (float)} where levels are
             numeric strings (e.g. "1" through "5") and probabilities sum to 1.

    Returns:
        float: The expected scale value.
    """
    return sum(int(level) * prob for level, prob in pmf.items())


def embed_reference_sets(all_sets):
    """
    Embed every reference statement in every set.

    Input:  {set_id: {level: "phrasing"}}
    Output: {set_id: {level: embedding_vector}}

    Batches all statements into a single get_embeddings call, then
    reassembles into the nested structure (order preserved).
    """
    keys = []
    texts = []
    for set_id, level_map in all_sets.items():
        for level, phrasing in level_map.items():
            keys.append((set_id, level))
            texts.append(phrasing)

    vectors = get_embeddings(texts)  # list in, list out (same order)

    all_sets_vectors = {set_id: {} for set_id in all_sets}
    for (set_id, level), vec in zip(keys, vectors):
        all_sets_vectors[set_id][level] = vec

    return all_sets_vectors


def score_semantic_similarity(
    scale_prompt,
    scale,
    results_csv_path,
    output_dir,
    epsilon=0.0,
    temperature=1.0,
):
    # Build reference sets: {set_id: {"1": phrasing, ..., "5": phrasing}}
    all_sets = json.loads(call_llm(scale_prompt))

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "reference_sets.json"), "w") as f:
        json.dump(all_sets, f, indent=2)

    all_sets_vectors = embed_reference_sets(all_sets)

    results_df = pd.read_csv(results_csv_path)

    # Pair each "text_*_reasoning" column with its target "text_*" column.
    reasoning_cols = [c for c in results_df.columns if c.endswith("_reasoning")]

    for reasoning_col in reasoning_cols:
        target_col = reasoning_col[: -len("_reasoning")]  # "text_1_reasoning" -> "text_1"

        if target_col not in results_df.columns:
            continue

        texts = results_df[reasoning_col].fillna("").astype(str).tolist()
        embeddings = get_embeddings(texts)  # takes a list, returns a list

        scores = [
            pmf_to_mean(response_to_pmf(vec, all_sets_vectors, epsilon, temperature))
            for vec in embeddings
        ]

        results_df[target_col] = scores

    # Save scored results to output_dir
    output_path = os.path.join(output_dir, "scored_results.csv")
    results_df.to_csv(output_path, index=False)

    return results_df