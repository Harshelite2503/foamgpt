"""LLM zero-shot / few-shot property prediction baseline.

Question the paper asks: "Does a frontier LLM already 'know' syntactic-foam
properties, or does it hallucinate plausible-looking numbers?" We give the model the
processing/structure description of a held-out record and ask for a point estimate
plus a 90% interval, then score against the measured value.

Two conditions:
  * zero_shot  - no data shown
  * rag_k      - k nearest records from OTHER papers (by simple feature similarity)
                 shown as context. Tests whether retrieval over the dataset helps.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from rich.progress import track

from foamgpt.config import BENCH_DIR, MODEL, anthropic_client

DESC_COLS = [
    "matrix_class", "matrix_name", "particle_type", "particle_grade", "particle_true_density_g_cc",
    "particle_mean_diameter_um", "particle_volume_fraction", "particle_weight_fraction",
    "process_route", "measured_density_g_cc", "test_type", "strain_rate_per_s", "temperature_c",
]


class Prediction(BaseModel):
    estimate: float = Field(description="Point estimate in the requested unit.")
    low_90: float = Field(description="Lower bound of a 90% credible interval.")
    high_90: float = Field(description="Upper bound of a 90% credible interval.")
    reasoning: str = Field(description="One or two sentences.")


SYSTEM = """You are a materials scientist specialising in syntactic foams. Given a
description of a hollow-particle composite and a test condition, estimate the requested
mechanical property. Be calibrated: your 90% interval should contain the true value ~90%
of the time. Answer with the schema only."""


def _describe(row: pd.Series) -> str:
    parts = [f"{c}: {row[c]}" for c in DESC_COLS if pd.notna(row.get(c))]
    return "\n".join(parts)


def _neighbours(df: pd.DataFrame, row: pd.Series, target: str, k: int) -> pd.DataFrame:
    other = df[(df["paper_id"] != row["paper_id"]) & df[target].notna()]
    same = other[(other["matrix_class"] == row["matrix_class"]) & (other["particle_type"] == row["particle_type"])]
    pool = same if len(same) >= k else other
    vf = pool["particle_volume_fraction"].fillna(pool["particle_weight_fraction"]).fillna(0.3)
    rv = row.get("particle_volume_fraction") or row.get("particle_weight_fraction") or 0.3
    return pool.iloc[np.argsort(np.abs(vf.values - rv))[:k]]


def run(df: pd.DataFrame, target: str = "strength_mpa", n: int = 60, k: int = 5, seed: int = 0) -> pd.DataFrame:
    client = anthropic_client()
    unit = "g/cm^3" if "density" in target else "MPa"
    d = df[df[target].notna() & (df["flags"].fillna("") == "")]
    d = d[d["test_type"] == "compression"] if "density" not in target else d
    sample = d.sample(min(n, len(d)), random_state=seed)
    rows = []
    for _, row in track(list(sample.iterrows()), description=f"LLM baseline: {target}"):
        for cond in ("zero_shot", f"rag_{k}"):
            ctx = ""
            if cond.startswith("rag"):
                nb = _neighbours(df, row, target, k)
                ctx = "\n\nReference measurements from other papers:\n" + "\n---\n".join(
                    _describe(r) + f"\n{target}: {r[target]}" for _, r in nb.iterrows())
            resp = client.messages.parse(
                model=MODEL, max_tokens=4000, thinking={"type": "adaptive"}, system=SYSTEM,
                messages=[{"role": "user", "content":
                           f"Material and test:\n{_describe(row)}{ctx}\n\nPredict {target} in {unit}."}],
                output_format=Prediction,
            )
            p = resp.parsed_output
            if p is None:
                continue
            rows.append({"record_id": row["record_id"], "target": target, "condition": cond,
                         "true": row[target], "pred": p.estimate, "low": p.low_90, "high": p.high_90,
                         "covered": p.low_90 <= row[target] <= p.high_90})
    out = pd.DataFrame(rows)
    out.to_csv(BENCH_DIR / f"llm_baseline_{target}.csv", index=False)
    summ = out.groupby("condition").apply(lambda g: pd.Series({
        "n": len(g),
        "mape_pct": float(np.mean(np.abs(g["true"] - g["pred"]) / g["true"]) * 100),
        "coverage_90": float(g["covered"].mean()),
        "r2_log": float(1 - np.sum((np.log10(g["true"]) - np.log10(g["pred"].clip(1e-6))) ** 2)
                        / np.sum((np.log10(g["true"]) - np.log10(g["true"]).mean()) ** 2)),
    }))
    summ.to_csv(BENCH_DIR / f"llm_baseline_{target}_summary.csv")
    (BENCH_DIR / f"llm_baseline_{target}_summary.json").write_text(json.dumps(summ.to_dict(), indent=2))
    return summ
