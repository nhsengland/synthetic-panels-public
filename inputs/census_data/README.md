# Census Data

Source files used to generate location-specific demographic distributions via
`src/prepare_census_data.py`.

## How it works

The user selects an **LTLA name** (Lower Tier Local Authority, e.g. `"Merton"`) in
`config/params.py`. Rather than filtering each dataset by that name, the pipeline:

1. Resolves the LTLA name to its set of **2021 LSOA codes** using `lsoa_ltla_lookup.csv`.
2. Pulls age/sex, ethnicity and deprivation data by **LSOA code**.

LSOA (Lower layer Super Output Area) boundaries are stable, whereas LTLAs are periodically
renamed or reorganised. Keying on LSOA codes makes the pipeline robust to those changes, and to
the same authority being spelled or coded differently across files.

The pipeline is **England-only** because the IMD file covers England alone. Non-English LSOAs
(Wales `W01`, Scotland `S01`, NI `N`) are dropped by `prepare_census_data.py` using the
configured `england_lsoa_prefix` (`"E01"` in `config/params.py`). Selecting a Welsh or Scottish
authority therefore resolves to no LSOAs and raises an error.

### Warnings you may see

`load_census_distributions` warns (via the `warnings` module) when:

- An LTLA name is not found in the lookup — it suggests close matches. (If *none* of the
  requested names resolve, it raises `ValueError`.)
- Some of the selected LSOAs are absent from a dataset and were dropped (coverage gap).
- The same LSOA's LAD is named differently between the lookup and the age/IMD files — i.e. the
  authority was renamed/recoded between data vintages. Joins are unaffected (they key on LSOA
  code); the warning just flags the discrepancy.

## Data Sources

All four CSVs are gitignored (`*.csv`) — they are **not committed** and must be downloaded
locally into this folder.

| File | Description | Source |
|------|-------------|--------|
| `lsoa_ltla_lookup.csv` | Postcode → OA → LSOA → MSOA → LAD best-fit lookup (Feb 2025) | [ONS Open Geography Portal](https://open-geography-portalx-ons.hub.arcgis.com/datasets/ons::postcode-to-oa-2021-to-lsoa-to-msoa-to-lad-february-2025-best-fit-lookup-in-the-uk/about) |
| `lsoa_age_sex.csv` | Single year of age × sex population estimates by LSOA, mid-2024 | [ONS LSOA mid-year population estimates](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/lowersuperoutputareamidyearpopulationestimates) |
| `lsoa_ethnicity.csv` | Ethnic group (20 categories) by LSOA, Census 2021 | [ONS TS021](https://www.ons.gov.uk/datasets/TS021/editions/2021/versions/3/filter-outputs/a9d54b5f-ecaf-479b-8225-4ca70f85c247#get-data) |
| `lsoa_index_of_multiple_deprivation.csv` | IMD decile by LSOA, 2025 | [English Indices of Deprivation 2025](https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025) |

## Download Instructions

### Lookup (`lsoa_ltla_lookup.csv`)

1. Go to the [ONS Open Geography Portal lookup](https://open-geography-portalx-ons.hub.arcgis.com/datasets/ons::postcode-to-oa-2021-to-lsoa-to-msoa-to-lad-february-2025-best-fit-lookup-in-the-uk/about)
   and download the full CSV.
2. Save it to `inputs/census_data/lsoa_ltla_lookup.csv`.

> ⚠️ **Do not open or save this file in Excel.** It has ~2.7 million rows (one per postcode),
> which exceeds Excel's 1,048,575-row limit. Excel silently truncates it, dropping ~63% of
> England's LSOAs (and entire local authorities). Keep it as the raw downloaded CSV. The code
> only reads the `lsoa21cd` and `ladnm` columns, so the file size is not a performance concern.

### Age/sex (`lsoa_age_sex.csv`)

1. From the [ONS LSOA mid-year population estimates](https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/lowersuperoutputareamidyearpopulationestimates),
   download the single-year-of-age by sex dataset and export the relevant sheet to CSV.
2. Save it to `inputs/census_data/lsoa_age_sex.csv`.

> The ONS export has three preamble rows above the column headers (handled in code via
> `header=3`), a comma-formatted `Total` column, and age columns `F0..F90` / `M0..M90` where
> `90` means 90 and over. Covers England and Wales (Welsh rows are dropped as above).

### Ethnicity (`lsoa_ethnicity.csv`)

1. From [ONS TS021](https://www.ons.gov.uk/datasets/TS021/editions/2021/versions/3/filter-outputs/a9d54b5f-ecaf-479b-8225-4ca70f85c247#get-data),
   get the data (ethnic group, 20 categories, by LSOA) and download the CSV.
2. Save it to `inputs/census_data/lsoa_ethnicity.csv`.

### Deprivation (`lsoa_index_of_multiple_deprivation.csv`)

1. From [English Indices of Deprivation 2025](https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025),
   download the file containing the IMD decile by LSOA and export it to CSV.
2. Save it to `inputs/census_data/lsoa_index_of_multiple_deprivation.csv`.

## Configuration

Filenames and key column names are configured in `config/params.py` under the `"census_data"`
key. If you download a different version of any file, update the corresponding `"file"` and
column entries to match:

Everything is config-driven — `prepare_census_data.py` holds no hard-coded filenames, column
names or mappings. The full block (see `config/params.py` for the complete value):

```python
"census_data": {
    "lookup": {
        "file": "lsoa_ltla_lookup.csv",
        "lsoa_col": "lsoa21cd",              # LSOA 2021 code column
        "ltla_name_col": "ladnm",            # LAD/LTLA name column
        "england_lsoa_prefix": "E01",        # England-only: drop Wales/Scotland/NI LSOAs
    },
    "age": {
        "file": "lsoa_age_sex.csv",
        "lsoa_col": "LSOA 2021 Code",
        "lad_name_col": "LAD 2023 Name",     # used only for the rename-mismatch warning
        "header_row": 3,                     # preamble rows above the column headers
        "max_age_band": 90,                  # top single-year band; "90" means 90+
        "sex_prefixes": {"female": "F", "male": "M"},  # wide cols "F0".."F90" / "M0".."M90"
    },
    "ethnicity": {
        "file": "lsoa_ethnicity.csv",
        "lsoa_col": "Lower layer Super Output Areas Code",
        "value_col": "Ethnic group (20 categories)",
        "weight_col": "Observation",
        "exclude_value": "Does not apply",
        "broad_mapping": { ... },            # 20 census labels -> broad ethnicity groups
    },
    "deprivation": {
        "file": "lsoa_index_of_multiple_deprivation.csv",
        "lsoa_col": "LSOA code (2021)",
        "value_col": "Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOA",
        "lad_name_col": "Local Authority District name (2024)",
        "decile_to_level": { ... },          # IMD decile (1 = most deprived) -> deprivation level
    },
}
```

Set `ltla` to a specific LTLA name (e.g. `"Merton"`), a list of LTLAs (e.g.
`["Merton", "Sutton"]`), or `"England"` to aggregate across all England LSOAs.
