import asyncio
import json
import os
import random
import re
import string
import pandas as pd
from faker import Faker
from faker.config import AVAILABLE_LOCALES
from unidecode import unidecode
from src.llm_utils import call_llm_async
from src.prompts import prompts as prompt_templates, DEMOGRAPHIC_FIELDS
from inputs.demographic_distributions import ethnicity_name_mapper, ArabicNameGenerator


class GeneratePatients:
    def __init__(self, n: int, behavioural_dimensions: dict, demographic_distributions: dict, seed: int):
        self.n = n
        self.behavioural_dimensions = behavioural_dimensions
        self.demographic_distributions = demographic_distributions
        self.seed = seed
        self.rng = random.Random(seed)

    def sample_from_distribution(self, distribution: dict):
        categories = list(distribution.keys())
        weights = list(distribution.values())
        return self.rng.choices(categories, weights=weights, k=1)[0]

    def _generate_behaviours(self) -> dict:
        return {key: self.sample_from_distribution(dist) for key, dist in self.behavioural_dimensions.items()}

    def _generate_demographics(self) -> dict:
        return {key: self.sample_from_distribution(dist) for key, dist in self.demographic_distributions.items()}
        
    def generate_patient_name(self, ethnicity, gender)-> str:
        """
        Given a random ethnicity, generate a name, convert to latin alphabet 
        """
        chosen_locale = self.rng.choice(ethnicity_name_mapper[ethnicity])
        fake = Faker([chosen_locale, 'en_GB'])
        fake.seed_instance(self.rng.randrange(2**32))

        if gender=='female':
            original_name = fake.name_female()
        else:
            original_name = fake.name_male()
        latin_name = unidecode(original_name)

        if ethnicity=='arab':
            generator = ArabicNameGenerator()
            if gender=='female':
                return generator.generate(include_father=True, gender="female")
            else:
                return generator.generate(include_father=True, gender="male")

        return latin_name
    
    def generate(self, output_dir: str) -> pd.DataFrame:
        print(f"Generating {self.n} patients...")
        self.rng = random.Random(self.seed)
        people = []

        for i in range(self.n):
            demographics = self._generate_demographics()
            name = self.generate_patient_name(demographics['ethnicity'], demographics['gender'])
            behaviours = self._generate_behaviours()
            person = {
                "patient_id": f"patient_{i}",
                "name":name,
                **demographics,
                **behaviours,
            }
            people.append(person)

        df = pd.DataFrame(people)
        df.to_csv(os.path.join(output_dir, "patients.csv"), index=False)
        print(f"  Done. {len(df)} patients saved.")
        return df


class GeneratePrompt:
    def __init__(
        self,
        question: str,
        prompt_template: str,
        system_template: str,
        input_texts: dict[str, str],
        patients_csv_path: str,
        behavioural_fields: list[tuple[str, str]],
        demographic_fields: list[tuple[str, str]] | None = None,
        shuffle_prompt: bool = True,
    ):
        self.patients_df = pd.read_csv(patients_csv_path)
        self.question = question
        self.prompt_template = prompt_template
        self.system_template = system_template
        self.input_texts = input_texts
        self.behavioural_fields = behavioural_fields
        self.demographic_fields = demographic_fields if demographic_fields is not None else DEMOGRAPHIC_FIELDS
        self.shuffle_prompt = shuffle_prompt

    @staticmethod
    def _render_sentence(
        fields: list,
        patient_row: pd.Series,
        chunk_size: int = 3,
    ) -> str:
        """Render (col, template) fields as one or more natural sentences describing the patient/persona."""
        rng = random.Random()

        _CONNECTIVES = [
            "In addition",
            "Also",
            "On top of this",
            "Alongside this",
            "Furthermore",
        ]

        parts = [
            label.format(value=patient_row.get(col, ''))
            for col, label in fields
        ]
        if not parts:
            return ""

        def _join_clause(clause_parts: list) -> str:
            if len(clause_parts) == 1:
                return clause_parts[0]
            return ", ".join(clause_parts[:-1]) + " and " + clause_parts[-1]

        def _capitalise(s: str) -> str:
            return s[0].upper() + s[1:]

        chunks = [parts[i:i + chunk_size] for i in range(0, len(parts), chunk_size)]

        sentences = []
        for i, chunk in enumerate(chunks):
            clause = _join_clause(chunk)
            if i == 0:
                sentence = _capitalise(clause)
            else:
                connective = rng.choice(_CONNECTIVES)
                sentence = f"{connective}, {clause[0].lower() + clause[1:]}"
            sentences.append(sentence.rstrip('.') + ".")

        return " ".join(sentences)

    def _build_prompt(self, patient_row: pd.Series, text: str) -> dict:
        """Return {"system_prompt": ..., "user_prompt": ...} for this patient/text."""
        demo_fields = self.demographic_fields[:]
        behav_fields = self.behavioural_fields[:]

        if self.shuffle_prompt:
            seed = int(patient_row["patient_id"].split("_")[1])
            rng = random.Random(seed)
            rng.shuffle(demo_fields)
            rng.shuffle(behav_fields)

        demo_sentence = self._render_sentence(demo_fields, patient_row)
        behav_sentence = self._render_sentence(behav_fields, patient_row)

        name = patient_row.get("name", "")
        name = name if pd.notna(name) else "Patient"

        system_prompt = string.Template(self.system_template).safe_substitute(
            NAME=name,
            DEMOGRAPHIC_SENTENCE=demo_sentence,
            BEHAVIOURAL_SENTENCE=behav_sentence,
        )

        user_prompt = string.Template(self.prompt_template).safe_substitute(
            QUESTION=self.question,
            TEXT=text,
        )

        return {"system_prompt": system_prompt, "user_prompt": user_prompt}

    def generate(self, output_dir: str) -> pd.DataFrame:
        n_texts = len(self.input_texts)
        n_patients = len(self.patients_df)
        print(f"Building prompts ({n_patients} patients x {n_texts} texts = {n_patients * n_texts} prompts)...")
        rows = []

        for text_name, text in self.input_texts.items():
            for _, patient_row in self.patients_df.iterrows():

                name = patient_row["name"]
                name = name if pd.notna(name) else "Patient"
                personalised_text = string.Template(text).safe_substitute(
                    NAME=name
                )

                built = self._build_prompt(patient_row, personalised_text)
                rows.append(
                    {
                        "patient_id": patient_row["patient_id"],
                        "text_id": text_name,
                        "text": personalised_text,
                        "system_prompt": built["system_prompt"],
                        "prompt": built["user_prompt"],
                    }
                )

        prompts_df = pd.DataFrame(rows)
        prompts_df.to_csv(os.path.join(output_dir, "prompts.csv"), index=False)
        print(f"  Done. {len(prompts_df)} prompts saved.")
        return prompts_df


class RunLLM:
    def __init__(
        self,
        model: str,
        prompts_csv_path: str = "data/prompts.csv",
        verbose: bool = False,
        answer_type={"scale": [0, 1]},
        temperature: float = 0.0,
        use_semantic_similarity: bool = False,
    ):
        self.prompts_df = pd.read_csv(prompts_csv_path)
        self.model = model
        self.verbose = verbose
        self.answer_type = answer_type
        self.temperature = temperature
        self.use_semantic_similarity = use_semantic_similarity

    @staticmethod
    def _parse_response_scale(response: str, scale_min: int, scale_max: int) -> dict:
        """Parse a numeric scale response from the LLM.

        Returns ``answer=None`` for any missing or invalid response (empty,
        unparseable, non-numeric, or out-of-range). Invalid answers are recorded
        as missing rather than imputed as a neutral value.
        """
        if not response:
            return {"reasoning": "", "answer": None}

        def _validate(val):
            if isinstance(val, bool):
                return None
            try:
                n = float(val)
            except (ValueError, TypeError):
                return None
            if n < scale_min or n > scale_max:
                return None
            return n

        text = response.strip()

        # Trust only structured output: parse JSON, or an embedded JSON object.
        parsed = None
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except (json.JSONDecodeError, ValueError):
                    parsed = None

        if isinstance(parsed, dict):
            return {
                "reasoning": parsed.get("reasoning", ""),
                "answer": _validate(parsed.get("answer")),
            }
        if isinstance(parsed, (int, float)) and not isinstance(parsed, bool):
            return {"reasoning": "", "answer": _validate(parsed)}

        # Could not extract a structured answer — record as missing.
        return {"reasoning": text, "answer": None}

    @staticmethod
    def _parse_response_semantic(response: str) -> dict:
        """Parse a semantic-similarity response from the LLM.

        In semantic-similarity mode the LLM is instructed to return only
        ``{"reasoning": "..."}``.  No numeric "answer" is expected — that will
        be computed later via embedding similarity.

        This parser handles:
        - Valid JSON: ``{"reasoning": "..."}``
        - Valid JSON with an unexpected "answer" key (answer is discarded)
        - Malformed JSON missing the colon: ``{"reasoning" "..."}``
        - Plain text (treated as the reasoning itself)

        Returns ``{"reasoning": <extracted text>, "answer": None}`` in all cases.
        """
        if not response:
            return {"reasoning": "", "answer": None}

        text = response.strip()

        # Attempt standard JSON parse first.
        parsed = None
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            # Try to find an embedded JSON object.
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except (json.JSONDecodeError, ValueError):
                    parsed = None

        if isinstance(parsed, dict):
            return {"reasoning": parsed.get("reasoning", ""), "answer": None}

        # Handle malformed JSON like {"reasoning" "..."} (missing colon).
        # Try to extract the value associated with "reasoning" using a regex.
        malformed_match = re.search(
            r'["\']reasoning["\']\s*[:\s]*\s*["\'](.*?)["\']?\s*\}',
            text,
            re.DOTALL,
        )
        if malformed_match:
            return {"reasoning": malformed_match.group(1), "answer": None}

        # Fall back: treat the entire response as the reasoning.
        return {"reasoning": text, "answer": None}

    async def _run_all(self, output_dir: str = None, batch_size: int = 500) -> list[dict]:
        if not self.use_semantic_similarity:
            is_scale = isinstance(self.answer_type, dict) and "scale" in self.answer_type
            if not is_scale:
                raise ValueError("answer_type must be a dict with a 'scale' key, e.g. {'scale': [1,5]}")
            scale_min, scale_max = self.answer_type["scale"]

        rows = list(self.prompts_df.iterrows())
        n = len(rows)
        results = []

        for batch_start in range(0, n, batch_size):
            batch_rows = rows[batch_start:batch_start + batch_size]
            batch_num = batch_start // batch_size + 1
            total_batches = (n + batch_size - 1) // batch_size
            print(f"  Batch {batch_num}/{total_batches}: running {len(batch_rows)} prompts...")

            tasks = [
                call_llm_async(
                    row["prompt"], model=self.model, temp=self.temperature,
                    verbose=self.verbose,
                    system_message=row.get("system_prompt") or None,
                )
                for _, row in batch_rows
            ]
            raw_responses = await asyncio.gather(*tasks)

            for (_, row), raw in zip(batch_rows, raw_responses):
                if self.use_semantic_similarity:
                    parsed = self._parse_response_semantic(raw)
                else:
                    parsed = self._parse_response_scale(raw, scale_min, scale_max)
                results.append(
                    {
                        "patient_id": row["patient_id"],
                        "text_id": row["text_id"],
                        "answer": parsed["answer"],
                        "reasoning": parsed["reasoning"],
                        "raw_response": raw,
                    }
                )

            print(f"  Batch {batch_num}/{total_batches} complete. {len(results)}/{n} total responses.")
            if output_dir:
                checkpoint_path = os.path.join(output_dir, "checkpoint_results.csv")
                pd.DataFrame(results).to_csv(checkpoint_path, index=False)
                print(f"  Checkpoint saved to {checkpoint_path}")

        return results

    def generate(self, output_dir: str) -> pd.DataFrame:
        n = len(self.prompts_df)
        print(f"Running LLM on {n} prompts (model: {self.model})...")
        results = asyncio.run(self._run_all(output_dir=output_dir))
        print(f"  Done. {len(results)} responses received.")
        results_df = pd.DataFrame(results)

        # Record and surface missing/invalid answers rather than imputing them.
        # In semantic-similarity mode all answers are expected to be None.
        if not self.use_semantic_similarity:
            missing = results_df[results_df["answer"].isna()]
            if not missing.empty:
                print(f"  WARNING: {len(missing)}/{len(results_df)} answers were missing or invalid "
                      "(recorded as blank, not imputed).")
                missing[["patient_id", "text_id", "raw_response"]].to_csv(
                    os.path.join(output_dir, "missing_answers.csv"), index=False
                )

        results_df = results_df.drop(columns=["raw_response"])

        # Pivot answers: rows = patients, columns = text_0, text_1, ...
        answer_pivot = results_df.pivot(index="patient_id", columns="text_id", values="answer")
        answer_pivot.columns.name = None
        answer_pivot = answer_pivot.reset_index()

        # Pivot reasoning: rows = patients, columns = text_0_reasoning, text_1_reasoning, ...
        reasoning_pivot = results_df.pivot(index="patient_id", columns="text_id", values="reasoning")
        reasoning_pivot.columns = [f"{c}_reasoning" for c in reasoning_pivot.columns]
        reasoning_pivot = reasoning_pivot.reset_index()

        # Merge answers and reasoning side by side
        merged_df = answer_pivot.merge(reasoning_pivot, on="patient_id")
        merged_df.to_csv(os.path.join(output_dir, "results.csv"), index=False)
        return merged_df


class BiasJudge:
    """Sends each reasoning to an LLM judge to assess for dangerous bias."""

    def __init__(
        self,
        results_csv_path: str,
        patients_csv_path: str,
        model: str,
        verbose: bool = False,
        temperature: float = 0.0,
    ):
        self.results_df = pd.read_csv(results_csv_path)
        self.patients_df = pd.read_csv(patients_csv_path)
        self.model = model
        self.verbose = verbose
        self.temperature = temperature
        self.judge_template = string.Template(prompt_templates["bias_judge"])

    @staticmethod
    def _parse_judge_response(response: str) -> dict:
        """Parse the JSON bias judgement from the LLM judge.

        A failed or partial response is recorded as unparsed (``judge_parsed=False``,
        numeric fields ``pd.NA``) rather than a clean "no bias" negative, so judge
        failures are not silently counted as non-biased.
        """
        missing = {
            "judge_parsed": False,
            "dangerous_bias_present": pd.NA,
            "bias_severity": pd.NA,
            "bias_types": [],
            "protected_groups_affected": [],
            "harm_likelihood": pd.NA,
            "confidence": pd.NA,
            "justification": "",
        }
        if not response:
            return missing

        parsed = None
        try:
            parsed = json.loads(response.strip())
        except (json.JSONDecodeError, AttributeError):
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except (json.JSONDecodeError, AttributeError):
                    parsed = None

        # Require the key that determines the verdict; without it, treat as unparsed.
        if not isinstance(parsed, dict) or "dangerous_bias_present" not in parsed:
            return missing

        # Overlay parsed values; absent optional fields stay NA/empty (never 0/False).
        template = {**missing, "judge_parsed": True}
        return {**template, **parsed}

    @staticmethod
    def _build_patient_profile(patient_row: pd.Series) -> str:
        """Format a patient row into a readable profile string for the judge."""
        skip_cols = {"patient_id"}
        lines = []
        for col, val in patient_row.items():
            if col not in skip_cols:
                lines.append(f"- {col}: {val}")
        return "\n".join(lines)

    async def _judge_all(self) -> list[dict]:
        """Build judge prompts for every (patient, text) reasoning and run them."""
        reasoning_cols = sorted([c for c in self.results_df.columns if c.endswith("_reasoning")])
        text_cols = [c.replace("_reasoning", "") for c in reasoning_cols]

        # Index patients by patient_id for fast lookup
        patients_indexed = self.patients_df.set_index("patient_id")

        tasks = []
        task_keys = []

        for _, row in self.results_df.iterrows():
            patient_id = row["patient_id"]
            patient_row = patients_indexed.loc[patient_id] if patient_id in patients_indexed.index else pd.Series()
            patient_profile = self._build_patient_profile(patient_row)

            for text_col, r_col in zip(text_cols, reasoning_cols):
                reasoning = str(row.get(r_col, ""))
                if not reasoning.strip() or reasoning == "nan":
                    continue
                prompt = self.judge_template.safe_substitute(
                    PATIENT_PROFILE=patient_profile,
                    REASONING=reasoning,
                )
                tasks.append(call_llm_async(prompt, model=self.model, temp=self.temperature, verbose=self.verbose))
                task_keys.append(
                    {
                        "patient_id": patient_id,
                        "text_id": text_col,
                        "reasoning": reasoning,
                    }
                )

        raw_responses = await asyncio.gather(*tasks)

        results = []
        for key, raw in zip(task_keys, raw_responses):
            parsed = self._parse_judge_response(raw)
            results.append({**key, **parsed})

        return results

    def generate(self, output_dir: str) -> pd.DataFrame:
        n = len(self.results_df)
        reasoning_cols = [c for c in self.results_df.columns if c.endswith("_reasoning")]
        total = sum(
            1
            for _, row in self.results_df.iterrows()
            for c in reasoning_cols
            if str(row.get(c, "")).strip() and str(row.get(c, "")) != "nan"
        )
        print(f"Running bias judge on {total} reasonings across {n} patients (model: {self.model})...")
        def _is_biased(value) -> bool:
            return value if isinstance(value, bool) else str(value).strip().lower() == "true"

        results = asyncio.run(self._judge_all())
        n_unparsed = sum(1 for r in results if not r.get("judge_parsed", False))
        n_flagged = sum(
            1 for r in results
            if r.get("judge_parsed", False) and _is_biased(r.get("dangerous_bias_present"))
        )
        print(f"  Done. {len(results)} judged, {n_flagged} flagged for dangerous bias.")
        if n_unparsed:
            print(f"  WARNING: {n_unparsed}/{len(results)} judge responses were unparsed "
                  "(recorded as missing, not counted as 'no bias').")
        judge_df = pd.DataFrame(results)
        judge_df.to_csv(os.path.join(output_dir, "bias_judgements.csv"), index=False)
        return judge_df
