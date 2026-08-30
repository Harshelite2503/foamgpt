"""Curation: flatten extractions, sanity-check physical ranges, derive fields, dedupe.

Physics checks (each flags a row, does not drop it):
  * density must lie between particle density*Vf and matrix-ish bounds (0.1-8 g/cc)
  * volume fraction in (0, 0.8]  (random close packing ~0.64; >0.8 is suspicious)
  * modulus 1-300,000 MPa; strength 0.1-3,000 MPa (covers polymers and metals)
  * specific values recomputed if density and modulus/strength present
"""

from __future__ import annotations

import pandas as pd

from foamgpt.config import CURATED_DIR
from foamgpt.extract.extractor import load_extractions
from foamgpt.schema import FLAT_COLUMNS, FoamRecord, flatten

CURATED = CURATED_DIR / "foam_psp.csv"

RANGES = {
    "measured_density_g_cc": (0.1, 8.0),
    "particle_volume_fraction": (0.0, 0.8),
    "particle_weight_fraction": (0.0, 0.9),
    "matrix_porosity_fraction": (0.0, 0.6),
    "modulus_mpa": (1.0, 300_000.0),
    "strength_mpa": (0.1, 3_000.0),
    "strain_at_failure": (0.0, 1.0),
    "particle_mean_diameter_um": (1.0, 5_000.0),
    "particle_true_density_g_cc": (0.05, 5.0),
    "particle_wall_thickness_ratio": (0.3, 1.0),
    "temperature_c": (-273.0, 1_500.0),
}


def _flags(row: pd.Series) -> str:
    flags = []
    for col, (lo, hi) in RANGES.items():
        v = row.get(col)
        if pd.notna(v) and not (lo <= v <= hi):
            flags.append(f"{col}_out_of_range")
    # percent-not-fraction detector
    for col in ("particle_volume_fraction", "particle_weight_fraction", "strain_at_failure"):
        v = row.get(col)
        if pd.notna(v) and v > 1.0:
            flags.append(f"{col}_looks_like_percent")
    # GPa-not-MPa detector for polymer foams
    if pd.notna(row.get("modulus_mpa")) and row["modulus_mpa"] < 20 and row.get("matrix_class") in (
        "epoxy", "vinyl_ester", "polyester", "hdpe", "pp", "pla"):
        flags.append("modulus_maybe_gpa")
    if pd.notna(row.get("modulus_mpa")) and row["modulus_mpa"] < 200 and row.get("matrix_class") in (
        "aluminum", "magnesium", "iron_steel", "titanium", "zinc", "other_metal"):
        flags.append("modulus_maybe_gpa")
    return ";".join(flags)


def build_table() -> pd.DataFrame:
    rows = []
    papers_meta = {}
    for ex in load_extractions():
        papers_meta[ex["paper_id"]] = ex
        if not ex["extraction"]["is_syntactic_foam_paper"]:
            continue
        for r in ex["extraction"]["records"]:
            rec = FoamRecord.model_validate(r)
            rows.append(flatten(rec))
    if not rows:
        return pd.DataFrame(columns=FLAT_COLUMNS + ["flags"])
    df = pd.DataFrame(rows).reindex(columns=FLAT_COLUMNS)

    # Derived fields
    m = df["specific_modulus_mpa_per_g_cc"].isna() & df["modulus_mpa"].notna() & df["measured_density_g_cc"].notna()
    df.loc[m, "specific_modulus_mpa_per_g_cc"] = df.loc[m, "modulus_mpa"] / df.loc[m, "measured_density_g_cc"]
    s = df["specific_strength_mpa_per_g_cc"].isna() & df["strength_mpa"].notna() & df["measured_density_g_cc"].notna()
    df.loc[s, "specific_strength_mpa_per_g_cc"] = df.loc[s, "strength_mpa"] / df.loc[s, "measured_density_g_cc"]

    df["flags"] = df.apply(_flags, axis=1)

    # Dedupe exact duplicates (same paper, same composition, same test, same numbers)
    key_cols = [c for c in FLAT_COLUMNS if c not in ("record_id", "sample_label", "extractor_confidence")]
    df = df.drop_duplicates(subset=key_cols).reset_index(drop=True)
    return df


def curate() -> pd.DataFrame:
    df = build_table()
    df.to_csv(CURATED, index=False)
    df.to_parquet(CURATED.with_suffix(".parquet"), index=False)
    return df


def summary(df: pd.DataFrame) -> dict:
    return {
        "records": len(df),
        "primary_records": int((df["data_origin"] == "primary").sum()),
        "papers": df["paper_id"].nunique(),
        "flagged": int((df["flags"] != "").sum()),
        "with_modulus": int(df["modulus_mpa"].notna().sum()),
        "with_strength": int(df["strength_mpa"].notna().sum()),
        "with_density": int(df["measured_density_g_cc"].notna().sum()),
        "matrix_classes": df["matrix_class"].value_counts().to_dict(),
        "test_types": df["test_type"].value_counts().to_dict(),
    }
