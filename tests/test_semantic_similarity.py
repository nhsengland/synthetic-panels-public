"""
Unit tests for src/semantic_similarity.py
"""

import json
import string
import os
import tempfile
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

from src.semantic_similarity import (
    pmf_to_mean,
    response_to_pmf_single_set,
    response_to_pmf,
    embed_reference_sets,
    score_semantic_similarity,
    call_llm,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unit_vector(dim, index):
    """Create a unit vector with 1.0 at the given index and 0.0 elsewhere."""
    vec = np.zeros(dim)
    vec[index] = 1.0
    return vec


def _uniform_vector(dim):
    """Create a uniform vector (equal in all dimensions), normalized."""
    vec = np.ones(dim)
    return vec / np.linalg.norm(vec)


# ---------------------------------------------------------------------------
# Tests for pmf_to_mean
# ---------------------------------------------------------------------------

class TestPmfToMean:
    def test_uniform_pmf_returns_midpoint(self):
        """A uniform PMF over 1-5 should return 3.0."""
        pmf = {"1": 0.2, "2": 0.2, "3": 0.2, "4": 0.2, "5": 0.2}
        assert pmf_to_mean(pmf) == pytest.approx(3.0)

    def test_deterministic_pmf_level_1(self):
        """All probability on level 1 should return 1.0."""
        pmf = {"1": 1.0, "2": 0.0, "3": 0.0, "4": 0.0, "5": 0.0}
        assert pmf_to_mean(pmf) == pytest.approx(1.0)

    def test_deterministic_pmf_level_5(self):
        """All probability on level 5 should return 5.0."""
        pmf = {"1": 0.0, "2": 0.0, "3": 0.0, "4": 0.0, "5": 1.0}
        assert pmf_to_mean(pmf) == pytest.approx(5.0)

    def test_known_weighted_case(self):
        """Hand-computed expected value: 1*0.1 + 2*0.2 + 3*0.4 + 4*0.2 + 5*0.1 = 3.0."""
        pmf = {"1": 0.1, "2": 0.2, "3": 0.4, "4": 0.2, "5": 0.1}
        assert pmf_to_mean(pmf) == pytest.approx(3.0)

    def test_single_level_pmf(self):
        """A PMF with only one key should return that level."""
        pmf = {"3": 1.0}
        assert pmf_to_mean(pmf) == pytest.approx(3.0)

    def test_two_level_pmf(self):
        """PMF with probability split between two levels."""
        pmf = {"2": 0.5, "4": 0.5}
        assert pmf_to_mean(pmf) == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Tests for response_to_pmf_single_set
# ---------------------------------------------------------------------------

class TestResponseToPmfSingleSet:
    def test_identical_vector_gets_highest_probability(self):
        """When response equals a reference vector, that level gets max probability."""
        dim = 10
        set_vectors = {
            "1": _unit_vector(dim, 0),
            "2": _unit_vector(dim, 1),
            "3": _unit_vector(dim, 2),
            "4": _unit_vector(dim, 3),
            "5": _unit_vector(dim, 4),
        }
        response = _unit_vector(dim, 2)  # identical to level "3"

        pmf = response_to_pmf_single_set(response, set_vectors)

        assert pmf["3"] == max(pmf.values())

    def test_equidistant_vectors_give_uniform_pmf(self):
        """When response is equally similar to all references, PMF should be uniform."""
        dim = 10
        # All reference vectors are the same -> all similarities equal
        ref_vec = _uniform_vector(dim)
        set_vectors = {
            "1": ref_vec,
            "2": ref_vec,
            "3": ref_vec,
            "4": ref_vec,
            "5": ref_vec,
        }
        response = _uniform_vector(dim)

        pmf = response_to_pmf_single_set(response, set_vectors)

        for level in pmf:
            assert pmf[level] == pytest.approx(0.2, abs=1e-9)

    def test_probabilities_sum_to_one(self):
        """PMF values should always sum to 1.0."""
        dim = 50
        rng = np.random.default_rng(42)
        set_vectors = {str(i): rng.random(dim) for i in range(1, 6)}
        response = rng.random(dim)

        pmf = response_to_pmf_single_set(response, set_vectors)

        assert sum(pmf.values()) == pytest.approx(1.0)

    def test_epsilon_prevents_zero_probability(self):
        """With epsilon > 0, no level should have exactly zero probability."""
        dim = 10
        set_vectors = {
            "1": _unit_vector(dim, 0),
            "2": _unit_vector(dim, 1),
            "3": _unit_vector(dim, 2),
            "4": _unit_vector(dim, 3),
            "5": _unit_vector(dim, 4),
        }
        # Response identical to level "1" — without epsilon, others could be zero
        response = _unit_vector(dim, 0)

        pmf = response_to_pmf_single_set(response, set_vectors, epsilon=0.01)

        for level, prob in pmf.items():
            assert prob > 0.0

    def test_temperature_one_is_identity(self):
        """Temperature=1.0 should produce the same result as no temperature adjustment."""
        dim = 20
        rng = np.random.default_rng(123)
        set_vectors = {str(i): rng.random(dim) for i in range(1, 6)}
        response = rng.random(dim)

        pmf_default = response_to_pmf_single_set(response, set_vectors, temperature=1.0)
        pmf_no_temp = response_to_pmf_single_set(response, set_vectors)

        for level in pmf_default:
            assert pmf_default[level] == pytest.approx(pmf_no_temp[level])

    def test_high_temperature_more_uniform(self):
        """Higher temperature should make the PMF more uniform (higher entropy)."""
        dim = 10
        set_vectors = {
            "1": _unit_vector(dim, 0),
            "2": _unit_vector(dim, 1),
            "3": _unit_vector(dim, 2),
            "4": _unit_vector(dim, 3),
            "5": _unit_vector(dim, 4),
        }
        response = _unit_vector(dim, 0)  # close to level "1"

        pmf_low_t = response_to_pmf_single_set(response, set_vectors, epsilon=0.01, temperature=0.5)
        pmf_high_t = response_to_pmf_single_set(response, set_vectors, epsilon=0.01, temperature=5.0)

        # High temperature should flatten the distribution — max probability should be lower
        assert max(pmf_high_t.values()) < max(pmf_low_t.values())

    def test_low_temperature_more_peaked(self):
        """Lower temperature should make the PMF more peaked."""
        dim = 20
        rng = np.random.default_rng(99)
        set_vectors = {str(i): rng.random(dim) for i in range(1, 6)}
        response = rng.random(dim)

        pmf_t1 = response_to_pmf_single_set(response, set_vectors, epsilon=0.01, temperature=1.0)
        pmf_low = response_to_pmf_single_set(response, set_vectors, epsilon=0.01, temperature=0.1)

        assert max(pmf_low.values()) >= max(pmf_t1.values())

    def test_all_equal_similarities_fallback_to_uniform(self):
        """When all cosine similarities are equal, PMF should be uniform."""
        dim = 10
        ref_vec = np.ones(dim)
        set_vectors = {str(i): ref_vec.copy() for i in range(1, 6)}
        response = np.ones(dim) * 2  # same direction, different magnitude — cos sim still 1.0

        pmf = response_to_pmf_single_set(response, set_vectors)

        for level in pmf:
            assert pmf[level] == pytest.approx(0.2, abs=1e-9)


# ---------------------------------------------------------------------------
# Tests for response_to_pmf (multi-set averaging)
# ---------------------------------------------------------------------------

class TestResponseToPmf:
    def test_single_set_matches_single_set_function(self):
        """With one reference set, result should equal response_to_pmf_single_set."""
        dim = 20
        rng = np.random.default_rng(7)
        set_vectors = {str(i): rng.random(dim) for i in range(1, 6)}
        response = rng.random(dim)

        all_sets_vectors = {"set_0": set_vectors}

        pmf_multi = response_to_pmf(response, all_sets_vectors)
        pmf_single = response_to_pmf_single_set(response, set_vectors)

        for level in pmf_multi:
            assert pmf_multi[level] == pytest.approx(pmf_single[level])

    def test_multiple_sets_averaging(self):
        """Averaged PMF should be the mean of individual set PMFs."""
        dim = 20
        rng = np.random.default_rng(55)
        set_a = {str(i): rng.random(dim) for i in range(1, 6)}
        set_b = {str(i): rng.random(dim) for i in range(1, 6)}
        response = rng.random(dim)

        all_sets_vectors = {"set_a": set_a, "set_b": set_b}

        pmf_avg = response_to_pmf(response, all_sets_vectors)
        pmf_a = response_to_pmf_single_set(response, set_a)
        pmf_b = response_to_pmf_single_set(response, set_b)

        for level in pmf_avg:
            expected = (pmf_a[level] + pmf_b[level]) / 2.0
            assert pmf_avg[level] == pytest.approx(expected)

    def test_probabilities_sum_to_one(self):
        """Averaged PMF should still sum to 1.0."""
        dim = 30
        rng = np.random.default_rng(10)
        all_sets_vectors = {
            f"set_{s}": {str(i): rng.random(dim) for i in range(1, 6)}
            for s in range(4)
        }
        response = rng.random(dim)

        pmf = response_to_pmf(response, all_sets_vectors)

        assert sum(pmf.values()) == pytest.approx(1.0)

    def test_consistent_levels(self):
        """Output keys should match the levels in the reference sets."""
        dim = 10
        rng = np.random.default_rng(0)
        levels = ["1", "2", "3", "4", "5"]
        all_sets_vectors = {
            "s1": {lvl: rng.random(dim) for lvl in levels},
            "s2": {lvl: rng.random(dim) for lvl in levels},
        }
        response = rng.random(dim)

        pmf = response_to_pmf(response, all_sets_vectors)

        assert sorted(pmf.keys(), key=int) == levels


# ---------------------------------------------------------------------------
# Tests for embed_reference_sets (mocked)
# ---------------------------------------------------------------------------

class TestEmbedReferenceSets:
    @patch("src.semantic_similarity.get_embeddings")
    def test_structure_preservation(self, mock_get_embeddings):
        """Returned nested dict should have same set IDs and levels as input."""
        all_sets = {
            "set_1": {"1": "hate it", "2": "dislike it", "3": "neutral"},
            "set_2": {"1": "awful", "2": "bad", "3": "okay"},
        }
        # Return distinguishable fake vectors
        num_texts = sum(len(v) for v in all_sets.values())
        mock_get_embeddings.return_value = [np.array([i]) for i in range(num_texts)]

        result = embed_reference_sets(all_sets)

        assert set(result.keys()) == set(all_sets.keys())
        for set_id in all_sets:
            assert set(result[set_id].keys()) == set(all_sets[set_id].keys())

    @patch("src.semantic_similarity.get_embeddings")
    def test_correct_batching_order(self, mock_get_embeddings):
        """Each embedding should land under the correct (set_id, level) key."""
        all_sets = {
            "A": {"1": "text_A1", "2": "text_A2"},
            "B": {"1": "text_B1", "2": "text_B2"},
        }
        # Vectors are distinguishable by index
        mock_get_embeddings.return_value = [
            np.array([0.0]),  # A, "1"
            np.array([1.0]),  # A, "2"
            np.array([2.0]),  # B, "1"
            np.array([3.0]),  # B, "2"
        ]

        result = embed_reference_sets(all_sets)

        assert result["A"]["1"] == pytest.approx(np.array([0.0]))
        assert result["A"]["2"] == pytest.approx(np.array([1.0]))
        assert result["B"]["1"] == pytest.approx(np.array([2.0]))
        assert result["B"]["2"] == pytest.approx(np.array([3.0]))

    @patch("src.semantic_similarity.get_embeddings")
    def test_calls_get_embeddings_once(self, mock_get_embeddings):
        """All texts should be batched into a single get_embeddings call."""
        all_sets = {
            "s1": {"1": "a", "2": "b", "3": "c"},
            "s2": {"1": "d", "2": "e", "3": "f"},
        }
        mock_get_embeddings.return_value = [np.zeros(5) for _ in range(6)]

        embed_reference_sets(all_sets)

        mock_get_embeddings.assert_called_once()
        # Should pass 6 texts total
        assert len(mock_get_embeddings.call_args[0][0]) == 6


# ---------------------------------------------------------------------------
# Tests for score_semantic_similarity (integration-level, mocked)
# ---------------------------------------------------------------------------

class TestScoreSemanticSimilarity:
    @patch("src.semantic_similarity.get_embeddings")
    @patch("src.semantic_similarity.call_llm")
    def test_end_to_end_produces_scored_results(self, mock_call_llm, mock_get_embeddings):
        """End-to-end run should produce a DataFrame with numeric scores."""
        # Setup reference sets returned by LLM
        reference_sets = {
            "set_1": {"1": "hate it", "2": "dislike", "3": "neutral", "4": "like", "5": "love it"}
        }
        mock_call_llm.return_value = json.dumps(reference_sets)

        dim = 10
        rng = np.random.default_rng(42)

        # get_embeddings is called twice: once for reference sets, once for response texts
        ref_embeddings = [rng.random(dim) for _ in range(5)]
        response_embeddings = [rng.random(dim) for _ in range(3)]
        mock_get_embeddings.side_effect = [ref_embeddings, response_embeddings]

        # Create a temporary CSV with reasoning and target columns
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "results.csv")
            df = pd.DataFrame({
                "text_1": [0, 0, 0],
                "text_1_reasoning": ["I love this product", "It's okay", "Terrible experience"],
            })
            df.to_csv(csv_path, index=False)

            output_dir = os.path.join(tmpdir, "output")

            result_df = score_semantic_similarity(
                scale_prompt="Generate reference sets",
                scale=None,
                results_csv_path=csv_path,
                output_dir=output_dir,
            )

            # Scores should be numeric floats between 1 and 5
            assert all(1.0 <= v <= 5.0 for v in result_df["text_1"])
            # Output files should exist
            assert os.path.exists(os.path.join(output_dir, "scored_results.csv"))
            assert os.path.exists(os.path.join(output_dir, "reference_sets.json"))

    @patch("src.semantic_similarity.get_embeddings")
    @patch("src.semantic_similarity.call_llm")
    def test_missing_target_column_is_skipped(self, mock_call_llm, mock_get_embeddings):
        """A reasoning column without a matching target column should be skipped."""
        reference_sets = {
            "set_1": {"1": "a", "2": "b", "3": "c", "4": "d", "5": "e"}
        }
        mock_call_llm.return_value = json.dumps(reference_sets)

        dim = 5
        mock_get_embeddings.return_value = [np.random.random(dim) for _ in range(5)]

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "results.csv")
            # Has reasoning column but NO matching target column
            df = pd.DataFrame({
                "orphan_reasoning": ["some text", "more text"],
            })
            df.to_csv(csv_path, index=False)

            output_dir = os.path.join(tmpdir, "output")

            result_df = score_semantic_similarity(
                scale_prompt="prompt",
                scale=None,
                results_csv_path=csv_path,
                output_dir=output_dir,
            )

            # Should not crash and should not add an "orphan" column
            assert "orphan" not in result_df.columns

    @patch("src.semantic_similarity.get_embeddings")
    @patch("src.semantic_similarity.call_llm")
    def test_empty_responses_do_not_raise(self, mock_call_llm, mock_get_embeddings):
        """Rows with empty or NaN reasoning should not cause errors."""
        reference_sets = {
            "set_1": {"1": "a", "2": "b", "3": "c", "4": "d", "5": "e"}
        }
        mock_call_llm.return_value = json.dumps(reference_sets)

        dim = 5
        rng = np.random.default_rng(0)
        ref_embeddings = [rng.random(dim) for _ in range(5)]
        response_embeddings = [rng.random(dim) for _ in range(3)]
        mock_get_embeddings.side_effect = [ref_embeddings, response_embeddings]

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "results.csv")
            df = pd.DataFrame({
                "text_1": [0, 0, 0],
                "text_1_reasoning": ["", None, "   "],
            })
            df.to_csv(csv_path, index=False)

            output_dir = os.path.join(tmpdir, "output")

            # Should not raise
            result_df = score_semantic_similarity(
                scale_prompt="prompt",
                scale=None,
                results_csv_path=csv_path,
                output_dir=output_dir,
            )

            assert len(result_df) == 3

    @patch("src.semantic_similarity.get_embeddings")
    @patch("src.semantic_similarity.call_llm")
    def test_output_files_are_created(self, mock_call_llm, mock_get_embeddings):
        """Both reference_sets.json and scored_results.csv should be written."""
        reference_sets = {
            "set_1": {"1": "a", "2": "b", "3": "c", "4": "d", "5": "e"}
        }
        mock_call_llm.return_value = json.dumps(reference_sets)

        dim = 5
        rng = np.random.default_rng(1)
        ref_embeddings = [rng.random(dim) for _ in range(5)]
        response_embeddings = [rng.random(dim) for _ in range(2)]
        mock_get_embeddings.side_effect = [ref_embeddings, response_embeddings]

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "results.csv")
            df = pd.DataFrame({
                "text_1": [0, 0],
                "text_1_reasoning": ["good", "bad"],
            })
            df.to_csv(csv_path, index=False)

            output_dir = os.path.join(tmpdir, "output")

            score_semantic_similarity(
                scale_prompt="prompt",
                scale=None,
                results_csv_path=csv_path,
                output_dir=output_dir,
            )

            assert os.path.isfile(os.path.join(output_dir, "reference_sets.json"))
            assert os.path.isfile(os.path.join(output_dir, "scored_results.csv"))

            # Verify reference_sets.json content
            with open(os.path.join(output_dir, "reference_sets.json")) as f:
                saved_sets = json.load(f)
            assert saved_sets == reference_sets


# ---------------------------------------------------------------------------
# Integration test: LLM generates a valid ruler (reference sets)
# ---------------------------------------------------------------------------

class TestLLMGeneratesRuler:
    """
    Integration test that calls the real LLM to generate reference scale sets
    (the 'ruler') and validates the output is a correctly structured dict.

    Requires a live LLM connection — skip with:
        pytest -m "not integration"
    """

    @pytest.mark.integration
    def test_llm_generates_valid_reference_sets(self):
        """The LLM should return valid JSON with the expected ruler structure."""
        from src.prompts import prompts

        # Build a realistic scale prompt
        question = "How likely are you to book a GP appointment after reading this message?"
        reference_set = (
            '{"1": "I would definitely not book", "2": "I probably would not book", '
            '"3": "I am unsure whether I would book", "4": "I would probably book", '
            '"5": "I would definitely book"}'
        )
        n_sets = 4
        scale_min = 1
        scale_max = 5

        scale_prompt = string.Template(prompts["generate_scale"]).safe_substitute(
            QUESTION=question,
            REFERENCE_SET=reference_set,
            N=n_sets,
            SCALE_MIN=scale_min,
            SCALE_MAX=scale_max,
        )

        # Call the real LLM
        raw_response = call_llm(scale_prompt)
        all_sets = json.loads(raw_response)

        # --- Structural validations ---

        # Must be a dict with at least n_sets entries
        assert isinstance(all_sets, dict)
        assert len(all_sets) >= n_sets, f"Expected at least {n_sets} sets, got {len(all_sets)}"

        expected_levels = {str(i) for i in range(scale_min, scale_max + 1)}

        for set_id, level_map in all_sets.items():
            # Each set must be a dict
            assert isinstance(level_map, dict), f"{set_id} is not a dict"
            # Must contain exactly the expected levels
            assert set(level_map.keys()) == expected_levels, (
                f"{set_id} has keys {set(level_map.keys())}, expected {expected_levels}"
            )
            # Each statement must be a non-empty string
            for level, statement in level_map.items():
                assert isinstance(statement, str), f"{set_id}[{level}] is not a string"
                assert len(statement.strip()) > 0, f"{set_id}[{level}] is empty"
