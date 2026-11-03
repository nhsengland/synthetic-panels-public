# Synthetic Panels

A tool for understanding which healthcare communication will be most effective using LLM-simulated patient panels. It generates synthetic patients with realistic demographic and behavioural profiles, sends them healthcare messages via an LLM, and evaluates which messages lead to the most people responding with desired behaviour. This is a proof-of-concept, as yet unfinished tool, which is in the process of being tested and does not reflect NHS England policy or processes. 

## How It Works

1. **Generate patients** — Synthetic patients are sampled from configurable demographic and behavioural distributions (age, gender, ethnicity, deprivation, health engagement, trust, etc.).
2. **Build prompts** — Each patient is paired with one or more candidate message texts. The LLM is prompted to role-play as that patient and answer a scale-based question (e.g., 1–5) about the message. For YES/No questions you can use a scale of 0-1.
3. **Run LLM** — All prompts are sent concurrently to the configured model. Responses are parsed into structured numeric scale answers with reasoning.
4. **Bias judge** — A second LLM pass reviews each reasoning for dangerous ethical bias (stereotyping, essentialism, paternalism, etc.).
5. **Evaluate** — A markdown report is generated with mean score breakdowns by demographic, behavioural trait analysis, cross-text agreement, disparity scores, and flagged bias cases.

## Setup

### Prerequisites

- Python 3.11+
- Access to a Foundry-hosted LLM endpoint (or modify `src/llm_utils.py` for your provider)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd synthetic_panels

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```bash
FOUNDRY_HOSTNAME=<your-foundry-hostname>
FOUNDRY_TOKEN=<your-token>
```

## Usage

### Streamlit UI

The project includes a multi-page Streamlit app for configuring parameters, editing input texts and distributions, running the pipeline, and exploring results:

```bash
streamlit run app.py
```

For some reason when doing a preview in FDP, the normal streamlit run command doesn't load it up correctly, run this instead:

```
streamlit run app2.py --server.port 8501 --server.address 0.0.0.0
```


Pages:

1. **Configuration** — Edit run parameters (model, N, power analysis settings, etc.)
2. **Input Texts** — View and edit candidate message texts
3. **Distributions** — Inspect demographic and behavioural distributions
4. **Run** — Launch the pipeline from the UI
5. **Results** — Browse and explore past run outputs

### Running via CLI

Configure your run in `config/params.py` then execute:

```bash
python scripts/run.py
```

This will create a timestamped folder under `data/` containing:

- `params.json` — the parameters used for this run
- `patients.csv` — all generated patient panels
- `prompts.csv` — all prompts sent to the LLM
- `results.csv` — parsed numeric scale answers and reasoning
- `bias_judgements.csv` — bias judge output for each reasoning
- `evaluation_report.md` — the full evaluation report

#### Power Analysis

When enabled, the pipeline calculates the required sample size **upfront** from your specified assumptions, then runs once with that N. If disabled, it uses the `N` set directly in `config/params.py`.

**How it works:**

1. You specify the effect you want to detect (`p1`, `p2` for binary; `mean_control`, `mean_treatment`, `std_dev` for continuous)
2. The pipeline solves for the N needed to detect that effect at your target power and significance level
3. The pipeline runs once with that N

**How N is calculated:**

- **Binary outcomes** (YES/NO responses): uses a chi-square test of homogeneity comparing response rates across all prompts simultaneously. Effect size (Cohen's w) is derived from `p1` (baseline proportion) and `p2` (minimum proportion to detect in at least one prompt).

- **Continuous outcomes**: uses an independent-samples t-test. Cohen's d is derived from `mean_control`, `mean_treatment`, and `std_dev`.

**Configuration** (in `config/params.py`):

| Parameter               | Default | Description                                                   |
| ----------------------- | ------- | ------------------------------------------------------------- |
| `enable_power_analysis` | `True`  | If `False`, use `N` directly without calculating sample size  |
| `N`                     | `50`    | Sample size to use when power analysis is disabled            |
| `outcome_type`          | `"binary"` | `"binary"` or `"continuous"`                               |
| `p1`                    | `0.5`   | Baseline YES proportion *(binary only)*                       |
| `p2`                    | `0.7`   | Minimum detectable YES proportion in at least one prompt *(binary only)* |
| `mean_control`          | `20`    | Average for control group *(continuous only)*                 |
| `mean_treatment`        | `25`    | Average for treatment group *(continuous only)*               |
| `std_dev`               | `120`   | Standard deviation of control group at baseline *(continuous only)* |
| `significance_level`    | `0.05`  | Alpha level (false positive rate)                             |
| `target_power`          | `0.80`  | Target statistical power                                      |

**Example configuration (binary):**

```python
params = {
    "run_name": "bias_test_v2",
    "N": 50,                        # used only if enable_power_analysis is False
    "enable_power_analysis": True,
    "outcome_type": "binary",
    "p1": 0.5,                      # baseline YES rate
    "p2": 0.7,                      # minimum difference to detect in one prompt
    "significance_level": 0.05,
    "target_power": 0.80,
    # ... other config ...
}
```

**Console output example:**

```
Power analysis: N=123 per prompt required to detect effect (outcome_type=binary, power=0.8, alpha=0.05)
```

### Configuration

Edit `config/params.py` to control:

| Parameter               | Description                                                          |
| ----------------------- | -------------------------------------------------------------------- |
| `run_name`              | Label for the run (used in folder naming)                            |
| `N`                     | Number of synthetic patients to generate when power analysis is disabled|
| `question`              | The question patients are asked; responses are expected on a numeric scale (e.g., 1–5). |
| `verbose`               | Whether to print LLM responses during execution                      |
| `report_sections`       | Toggle individual sections of the evaluation report                  |
| `enable_power_analysis` | If `True`, calculate N from power assumptions; otherwise use `N`     |
| `outcome_type`          | `"binary"` or `"continuous"`                                         |
| `p1` / `p2`             | Baseline and target YES proportions (binary only)                    |
| `mean_control` / `mean_treatment` / `std_dev` | Mean and SD params for sample size calculation (continuous only) |
| `significance_level`    | Alpha level (default 0.05)                                           |
| `target_power`          | Target statistical power (default 0.80)                              |


### Customising inputs

- **Message texts** — Edit `inputs/input_texts.py` to define the candidate messages being tested.
- **Demographics** — Edit `inputs/demographic_distributions.py` to change population distributions, or set `use_census_data: True` and an `ltla` in `config/params.py` to draw real distributions for a chosen Local Authority from census data (see `inputs/census_data/README.md`).
- **Behavioural traits** — Edit `inputs/behavoural_traits.py` to add or modify behavioural dimensions.
- **Names** — Edit `inputs/names.py` to update the name pools per ethnicity/gender.

### Combining runs

To merge multiple runs into a single dataset with a combined report:

```bash
python scripts/combine_runs.py data/<run_folder_1> data/<run_folder_2>
```

### Evaluating the bias judge

To test the bias judge against a curated set of labelled examples and produce precision/recall metrics:

```bash
python scripts/evaluate_judge.py
```

## Project Structure

```text
synthetic_panels/
├── config/
│   └── params.py              # Run configuration
├── inputs/
│   ├── behavoural_traits.py   # Behavioural dimension distributions
│   ├── demographic_distributions.py  # Demographic distributions
│   ├── input_texts.py         # Candidate message texts
│   └── names.py               # Name pools by ethnicity/gender
├── scripts/
│   ├── run.py                 # Main entry point
│   ├── combine_runs.py        # Merge multiple runs
│   └── evaluate_judge.py      # Bias judge evaluation
├── src/
│   ├── evaluate.py            # Report generation
│   ├── generate_samples.py    # Patient/prompt generation and LLM execution
│   ├── llm_utils.py           # LLM client (Foundry/OpenAI-compatible)
│   ├── power_analyzer.py      # Sample size calculation from power assumptions
│   └── prompts.py             # Prompt templates
├── requirements.txt
└── .env                       # (not committed) API credentials
```

## Contact

This project is maintained by the NHS England Data Science & Applied AI team.

- **Will Poulett** — [william.poulett1@nhs.net](mailto:william.poulett1@nhs.net)
- **Amaia Imaz Blanco** — [amaia.imazblanco1@nhs.net](mailto:amaia.imazblanco1@nhs.net)
- **Team inbox** — [datascience@nhs.net](mailto:datascience@nhs.net)

For security issues, see [SECURITY.md](SECURITY.md).
