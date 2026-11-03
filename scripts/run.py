import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

#modify to add presets
from inputs.scenario_presets import scenario_presets
#from inputs.input_texts import question, scale, texts
from config.params import params
from src.pipeline_runner import run_pipeline
from src.experiment_runner import run_experiment

selected_scenario_preset = scenario_presets['covid_vaccine_RCT_1']

question = selected_scenario_preset['question']
scale = selected_scenario_preset['scale']
texts = selected_scenario_preset['texts']
real_results = selected_scenario_preset.get('real_results')

if params.get("experiment_mode"):
    results = run_experiment(
        params=params,
        texts=texts,
        question=question,
        scale=scale,
        real_results=real_results,
    )
    print(f"\nExperiment outputs saved to: {results['experiment_dir']}")
    if results["experiment_report"]:
        print("\n" + results["experiment_report"])
else:
    results = run_pipeline(
        params=params,
        texts=texts,
        question=question,
        scale=scale,
        real_results=real_results,
    )
    print(f"\nOutputs saved to: {results['run_dir']}")
