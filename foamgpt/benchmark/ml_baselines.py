"""Classical ML baselines for property prediction on the curated PSP table.

Tasks (each = predict a property from processing + structure features):
  * compressive modulus (MPa)
  * compressive strength (MPa)
  * density (g/cc)

Splits are BY PAPER (GroupKFold) so a model can't memorise a paper's other rows -
this is the honest setting for "can we predict a new lab's foam".
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from foamgpt.config import BENCH_DIR

CAT = ["matrix_class", "particle_type", "process_route", "test_type"]
NUM = [
    "particle_true_density_g_cc", "particle_mean_diameter_um", "particle_wall_thickness_ratio",
    "particle_volume_fraction", "particle_weight_fraction", "measured_density_g_cc",
    "strain_rate_per_s", "temperature_c",
]
TARGETS = {
    "modulus_mpa": {"log": True},
    "strength_mpa": {"log": True},
    "measured_density_g_cc": {"log": False},
}


def _pipeline(model, num_feats: list[str]) -> Pipeline:
    pre = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
            ("num", Pipeline([("imp", SimpleImputer(strategy="median", keep_empty_features=True)), ("sc", StandardScaler())]), num_feats),
        ]
    )
    return Pipeline([("pre", pre), ("model", model)])


MODELS = {
    "ridge": lambda: Ridge(alpha=1.0),
    "random_forest": lambda: RandomForestRegressor(n_estimators=400, min_samples_leaf=2, random_state=0, n_jobs=-1),
    "gbr": lambda: GradientBoostingRegressor(n_estimators=400, learning_rate=0.05, max_depth=3, random_state=0),
}


def run(df: pd.DataFrame, n_splits: int = 5, test_type: str | None = "compression") -> pd.DataFrame:
    results = []
    for target, cfg in TARGETS.items():
        d = df[df[target].notna()].copy()
        if test_type and target != "measured_density_g_cc":
            d = d[d["test_type"] == test_type]
        feats = [c for c in NUM if c != target]
        d = d[(d["flags"].fillna("") == "") & (d["data_origin"] == "primary")]  # sane, primary rows
        d = d[d[target] > 0]  # log-scale targets must be positive
        d = d.replace([np.inf, -np.inf], np.nan)
        if d["paper_id"].nunique() < n_splits or len(d) < 30:
            results.append({"target": target, "model": "-", "n": len(d), "note": "too few rows/papers"})
            continue
        y = np.log10(d[target].values) if cfg["log"] else d[target].values
        groups = d["paper_id"].values
        X = d[CAT + feats]
        for name, make in MODELS.items():
            preds = np.zeros_like(y, dtype=float)
            for tr, te in GroupKFold(n_splits=n_splits).split(X, y, groups):
                pipe = _pipeline(make(), feats)
                pipe.fit(X.iloc[tr], y[tr])
                preds[te] = pipe.predict(X.iloc[te])
            preds = np.clip(preds, y.min() - 1, y.max() + 1)  # guard against wild extrapolation
            y_true = 10 ** y if cfg["log"] else y
            y_pred = 10 ** preds if cfg["log"] else preds
            results.append({
                "target": target, "model": name, "n": len(d), "papers": d["paper_id"].nunique(),
                "r2_log" if cfg["log"] else "r2": round(r2_score(y, preds), 3),
                "mae": round(mean_absolute_error(y_true, y_pred), 3),
                "mape_pct": round(float(np.mean(np.abs(y_true - y_pred) / np.maximum(np.abs(y_true), 1e-9)) * 100), 1),
            })
    res = pd.DataFrame(results)
    res.to_csv(BENCH_DIR / "ml_baselines.csv", index=False)
    (BENCH_DIR / "ml_baselines.json").write_text(json.dumps(results, indent=2))
    return res
