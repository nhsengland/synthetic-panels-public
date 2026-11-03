import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

data_dir = ""

num_repeats = len(list(pd.io.common.Path(data_dir).glob("repeat_*")))
repeats = [pd.read_csv(f"{data_dir}/repeat_{i}/results.csv") for i in range(num_repeats)]

prompts = [
    "Ownership w/ Narrow Link",
    "Ownership w/ Broad Link",
    "RCT1 Doctor Recommendation Only",
    "Doctor Recommendation & Ownership w/ Narrow Link",
    "Doctor Recommendation & Ownership w/ Broad Link",
]
threshold = 4

experiment_results = pd.read_csv(f"{data_dir}/experiment_results.csv", index_col=0)
real_results = experiment_results.loc["real"].to_dict()

fig, ax = plt.subplots(figsize=(12, 7))

for prompt in prompts:
    n = np.arange(1, len(repeats[0]) + 1)
    cumulative_pcts = []
    for df in repeats:
        yes_cumulative = (df[prompt] >= threshold).cumsum()
        cumulative_pcts.append(yes_cumulative / n * 100)

    pcts = np.array(cumulative_pcts)
    mean_pct = pcts.mean(axis=0)
    std_pct = pcts.std(axis=0)

    line, = ax.plot(n, mean_pct, label=prompt)
    if num_repeats > 1:
        ax.fill_between(n, mean_pct - std_pct, mean_pct + std_pct, alpha=0.2, color=line.get_color())
        ax.fill_between(n, mean_pct - 2 * std_pct, mean_pct + 2 * std_pct, alpha=0.1, color=line.get_color())

    ax.axhline(real_results[prompt] * 100, linestyle="--", color=line.get_color(), alpha=1.0, linewidth=2)

ax.set_xlabel("Number of patients in sample")
ax.set_ylabel("% saying YES (score >= 4)")
ax.set_title(f"Convergence of YES % as sample size increases ({num_repeats} repeat{'s' if num_repeats > 1 else ''})")
ax.legend(loc="upper right", fontsize=9)
ax.set_xlim(1, len(repeats[0]))
ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f"{data_dir}/convergence_plot.png", dpi=150)
plt.show()
print("Plot saved.")
