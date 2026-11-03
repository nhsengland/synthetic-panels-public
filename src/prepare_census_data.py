import warnings
from difflib import get_close_matches
from pathlib import Path

import pandas as pd

def _resolve_ltla_to_lsoas(ltla, lookup_cfg) -> tuple[set[str], pd.DataFrame]:
    """Resolve an LTLA name (or list, or "England") to a set of England LSOA codes.

    Returns the selected LSOA codes and the England-only lookup (lsoa -> ladnm) so callers
    can cross-check LAD names against the other datasets.
    """
    lsoa_col = lookup_cfg["lsoa_col"]
    name_col = lookup_cfg["ltla_name_col"]

    lookup = (
        pd.read_csv(lookup_cfg["file"])
        [[lsoa_col, name_col]]     # replaces usecols=[...]
        .dropna()                  # drop nulls FIRST (see note)
        .astype(str)               # replaces dtype=str
        .drop_duplicates()
    )

    # England-only choke point: restrict to England before name resolution, so every
    # downstream LSOA set is England-only by construction and a Welsh/Scottish LTLA name
    # simply resolves to nothing here.
    lookup = lookup[lookup[lsoa_col].str.startswith(lookup_cfg["england_lsoa_prefix"])]

    if ltla == "England":
        return set(lookup[lsoa_col]), lookup

    requested = [ltla] if isinstance(ltla, str) else list(ltla)
    available = lookup[name_col].unique().tolist()

    selected: set[str] = set()
    for name in requested:
        codes = set(lookup.loc[lookup[name_col] == name, lsoa_col])
        if not codes:
            suggestions = get_close_matches(name, available, n=3)
            hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
            warnings.warn(
                f"LTLA '{name}' not found in the lookup (the pipeline is England-only, so "
                f"Welsh/Scottish authorities will not match).{hint}"
            )
            continue
        selected |= codes

    if not selected:
        raise ValueError(
            f"None of the requested LTLAs {requested} resolved to any England LSOA. "
            f"Set 'ltla' to a valid England LTLA name, a list of them, or 'England'."
        )

    return selected, lookup[lookup[lsoa_col].isin(selected)]


def _warn_missing_lsoas(dataset: str, selected: set[str], present: set[str]) -> None:
    missing = selected - present
    if missing:
        warnings.warn(
            f"{len(missing)} of {len(selected)} selected LSOAs are absent from the {dataset} "
            f"data and were dropped (e.g. {', '.join(sorted(missing)[:3])})."
        )


def _warn_name_mismatch(dataset: str, lookup_names: dict, other_names: dict) -> None:
    """Warn when the same LSOA's LAD is named differently across files (the rename hazard)."""
    examples = [
        f"{lsoa}: '{lookup_names.get(lsoa)}' vs '{name}'"
        for lsoa, name in other_names.items()
        if lookup_names.get(lsoa) is not None and name != lookup_names.get(lsoa)
    ]
    if examples:
        warnings.warn(
            f"LAD name for {len(examples)} selected LSOAs differs between the lookup and the "
            f"{dataset} data (LTLA renamed/recoded between vintages; joins are unaffected as "
            f"they key on LSOA code). e.g. {examples[0]}"
        )


def load_census_distributions(ltla: str | list[str], census_data: dict, min_age: int = 18, max_age: int = 100) -> dict:
    print("Preparing Census Data...")
    
    lookup_cfg = census_data["lookup"]
    age_sex_cfg = census_data["age_sex"]
    eth_cfg = census_data["ethnicity"]
    dep_cfg = census_data["deprivation"]

    use_age = age_sex_cfg.get("use_age", True)
    use_sex = age_sex_cfg.get("use_sex", True) # Flagging this is new for PR
    use_ethnicity = eth_cfg.get("use", True)
    use_deprivation = dep_cfg.get("use", True)

    selected_lsoas, lookup = _resolve_ltla_to_lsoas(ltla, lookup_cfg)
    lookup_names = lookup.set_index(lookup_cfg["lsoa_col"])[lookup_cfg["ltla_name_col"]].to_dict()

    distributions = {}

    # --- Age + sex (wide single-year-of-age x sex counts per LSOA) ---
    if use_age or use_sex:
        age_lsoa_col = age_sex_cfg["lsoa_col"]
        age_df = pd.read_csv(age_sex_cfg["file"])
        
        age_df = age_df[age_df[age_lsoa_col].isin(selected_lsoas)]
        _warn_missing_lsoas("age_sex", selected_lsoas, set(age_df[age_lsoa_col]))
        if ltla != "England":
            _warn_name_mismatch("age_sex", lookup_names, age_df.set_index(age_lsoa_col)[age_sex_cfg["lad_name_col"]].to_dict())

        # Sex/age counts are wide columns named "<prefix><age>" (e.g. "F0".."F90"). Coerce to numeric:
        # a stray non-numeric value elsewhere in the file leaves some columns as object dtype.
        female_prefix, male_prefix = age_sex_cfg["sex_prefixes"]["female"], age_sex_cfg["sex_prefixes"]["male"]
        ages = range(min_age, min(max_age, age_sex_cfg["max_age_band"]) + 1)
        f_cols = [f"{female_prefix}{a}" for a in ages]
        m_cols = [f"{male_prefix}{a}" for a in ages]
        counts = age_df[f_cols + m_cols].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)

        if use_age:
            age_weights = {a: int(counts[f"{female_prefix}{a}"].sum() + counts[f"{male_prefix}{a}"].sum()) for a in ages}
            distributions["age"] = age_weights

        if use_sex:
            female = int(counts[f_cols].to_numpy().sum())
            male = int(counts[m_cols].to_numpy().sum())
            distributions["gender"] = {"female": female, "male": male}
    else:
        print("  Skipping age/sex (use_age=False, use_sex=False)")

    # --- Ethnicity (long format) ---
    if use_ethnicity:
        eth_lsoa_col = eth_cfg["lsoa_col"]
        eth_value_col = eth_cfg["value_col"]
        eth_weight_col = eth_cfg["weight_col"]
        eth_df = pd.read_csv(eth_cfg["file"])[
            [eth_lsoa_col, eth_value_col, eth_weight_col]
        ]

        eth_df = eth_df.loc[
            eth_df[eth_lsoa_col].isin(selected_lsoas) &
            (eth_df[eth_value_col] != eth_cfg["exclude_value"])
        ].copy()
        _warn_missing_lsoas("ethnicity", selected_lsoas, set(eth_df[eth_lsoa_col]))
        eth_df["broad"] = eth_df[eth_value_col].map(eth_cfg["broad_mapping"])
        ethnicity_weights = (
            eth_df.dropna(subset=["broad"])
            .groupby("broad")[eth_weight_col]
            .sum()
            .to_dict()
        )
        distributions["ethnicity"] = ethnicity_weights
    else:
        print("  Skipping ethnicity (use=False)")

    # --- Deprivation (IMD decile per LSOA) ---
    if use_deprivation:
        dep_lsoa_col = dep_cfg["lsoa_col"]
        dep_df = pd.read_csv(dep_cfg["file"])
        dep_df = dep_df[dep_df[dep_lsoa_col].isin(selected_lsoas)].copy()
        _warn_missing_lsoas("deprivation", selected_lsoas, set(dep_df[dep_lsoa_col]))
        if ltla != "England":
            _warn_name_mismatch("deprivation", lookup_names, dep_df.set_index(dep_lsoa_col)[dep_cfg["lad_name_col"]].to_dict())
        dep_df["level"] = dep_df[dep_cfg["value_col"]].map(dep_cfg["decile_to_level"])
        deprivation_weights = dep_df.dropna(subset=["level"]).groupby("level").size().to_dict()
        distributions["deprivation_level"] = deprivation_weights
    else:
        print("  Skipping deprivation (use=False)")

    return distributions
