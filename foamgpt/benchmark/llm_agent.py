"""Agent-lane LLM benchmark (no API calls).

`make_tasks` samples held-out records and writes self-contained prediction tasks
(zero-shot and retrieval-augmented with k neighbours from OTHER papers). Claude
Code subagents answer each task from the task text alone - they must NOT open the
dataset or any paper (leakage). `score` compares answers with the true values.

    python -m foamgpt.benchmark.llm_agent make
    python -m foamgpt.benchmark.llm_agent score
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from foamgpt.benchmark.llm_baseline import DESC_COLS, _neighbours
from foamgpt.config import BENCH_DIR
from foamgpt.curate.normalize import CURATED

TASK_DIR = BENCH_DIR / "llm_tasks"; ANS_DIR = BENCH_DIR / "llm_answers"
TASK_DIR.mkdir(exist_ok=True); ANS_DIR.mkdir(exist_ok=True)


def _desc(row, exclude: str) -> str:
    return "\n".join(f"{c}: {row[c]}" for c in DESC_COLS if c != exclude and pd.notna(row.get(c)))


def make_all(n_per: dict[str, int], k: int = 5, seed: int = 0) -> int:
    """Sample held-out rows for every target first, then build tasks whose retrieval pool
    excludes ALL benchmark rows (no cross-task leakage) and whose description omits the target."""
    df = pd.read_csv(CURATED)
    base = df[(df["flags"].fillna("") == "") & (df["data_origin"] == "primary")]
    samples = {}
    for target, n in n_per.items():
        d = base[base[target].notna() & (base[target] > 0) & base["matrix_class"].notna() & base["particle_type"].notna()]
        if "density" not in target:
            d = d[d["test_type"] == "compression"]
        samples[target] = d.sample(min(n, len(d)), random_state=seed)
    bench_ids = set().union(*[set(s.record_id) for s in samples.values()])
    pool = base[~base.record_id.isin(bench_ids)]
    for f in TASK_DIR.glob("*"):
        f.unlink()
    total = 0
    for target, sample in samples.items():
        unit = "g/cm^3" if "density" in target else "MPa"
        truth, tasks = {}, []
        for _, row in sample.iterrows():
            desc = _desc(row, exclude=target)
            for cond in ("zero_shot", f"rag_{k}"):
                ctx = ""
                if cond.startswith("rag"):
                    nb = _neighbours(pool, row, target, k)
                    ctx = "\n\nReference measurements from OTHER papers (may be a different lab/grade):\n" + "\n---\n".join(
                        _desc(r, exclude=target) + f"\n{target}: {r[target]}" for _, r in nb.iterrows())
                tid = f"{row.record_id}__{target}__{cond}"
                tasks.append({"task_id": tid, "target": target, "unit": unit, "condition": cond,
                              "prompt": f"Material and test:\n{desc}{ctx}\n\nPredict {target} in {unit}."})
                truth[tid] = float(row[target])
        (TASK_DIR / f"{target}.jsonl").write_text("".join(json.dumps(t) + "\n" for t in tasks))
        (TASK_DIR / f"{target}.truth.json").write_text(json.dumps(truth))
        total += len(tasks); print(f"{len(tasks)} tasks for {target}")
    # chunks: zero-shot tasks and rag tasks never share a chunk
    import random
    allt = [json.loads(l) for f in TASK_DIR.glob("*.jsonl") for l in f.read_text().splitlines() if l.strip()]
    zs = [t for t in allt if t["condition"] == "zero_shot"]; rg = [t for t in allt if t["condition"] != "zero_shot"]
    random.Random(seed).shuffle(zs); random.Random(seed + 1).shuffle(rg)
    chunks = [zs[i::4] for i in range(4)] + [rg[i::4] for i in range(4)]
    for i, c in enumerate(chunks):
        (TASK_DIR / f"chunk_{i}.json").write_text(json.dumps(c, indent=1))
    print(total, "tasks in", len(chunks), "chunks")
    return total


def score() -> pd.DataFrame:
    """Score answers. Exclusions (reported): unfilled-matrix controls (particle fraction 0), and
    density tasks whose record also appears as a strength/modulus task (its density is visible there)."""
    df = pd.read_csv(CURATED).set_index("record_id")
    all_tasks = [json.loads(l) for f in TASK_DIR.glob("*.jsonl") for l in f.read_text().splitlines() if l.strip()]
    rec_of = lambda tid: tid.split("__")[0]
    mech_recs = {rec_of(t["task_id"]) for t in all_tasks if t["target"] != "measured_density_g_cc"}
    excluded = {"control_rows": 0, "density_visible_in_sibling": 0}
    rows = []
    for tf in TASK_DIR.glob("*.jsonl"):
        target = tf.stem; truth = json.loads((TASK_DIR / f"{target}.truth.json").read_text())
        for t in (json.loads(l) for l in tf.read_text().splitlines() if l.strip()):
            af = ANS_DIR / f"{t['task_id']}.json"
            if not af.exists():
                continue
            rec = rec_of(t["task_id"]); r = df.loc[rec]
            vf = r.get("particle_volume_fraction"); wf = r.get("particle_weight_fraction")
            if (pd.notna(vf) and vf == 0) or (pd.notna(wf) and wf == 0 and pd.isna(vf)):
                excluded["control_rows"] += 1; continue
            if target == "measured_density_g_cc" and rec in mech_recs:
                excluded["density_visible_in_sibling"] += 1; continue
            try:
                a = json.loads(af.read_text())
                est, lo, hi = float(a["estimate"]), float(a["low_90"]), float(a["high_90"])
            except Exception as e:  # noqa: BLE001
                print("bad answer file", af.name, str(e)[:80]); continue
            y = truth[t["task_id"]]
            rows.append({"task_id": t["task_id"], "target": target, "condition": t["condition"], "true": y,
                         "pred": est, "low": lo, "high": hi, "covered": lo <= y <= hi,
                         "ape": abs(y - est) / y, "log_err": np.log10(max(est, 1e-6)) - np.log10(y)})
    out = pd.DataFrame(rows)
    out.to_csv(BENCH_DIR / "llm_agent_predictions.csv", index=False)
    print("excluded:", excluded); (BENCH_DIR / "llm_agent_exclusions.json").write_text(json.dumps(excluded))
    if out.empty:
        print("no answers yet"); return out
    def summ(g):
        yt = np.log10(g["true"]); yp = np.log10(g["pred"].clip(1e-6))
        return pd.Series({"n": len(g), "mape_pct": g["ape"].mean() * 100, "median_ape_pct": g["ape"].median() * 100,
                          "coverage_90": g["covered"].mean(),
                          "r2_log": 1 - ((yt - yp) ** 2).sum() / ((yt - yt.mean()) ** 2).sum()})
    s = out.groupby(["target", "condition"]).apply(summ).round(3)
    s.to_csv(BENCH_DIR / "llm_agent_summary.csv"); print(s.to_string())
    _plot(out)
    return s


def _plot(out: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    targets = [t for t in ("measured_density_g_cc", "modulus_mpa", "strength_mpa") if t in set(out.target)]
    fig, axes = plt.subplots(1, len(targets), figsize=(4.2 * len(targets), 4))
    axes = np.atleast_1d(axes)
    for ax, t in zip(axes, targets):
        d = out[out.target == t]
        for cond, col, mk in (("zero_shot", "tab:red", "o"), ("rag_5", "tab:blue", "s")):
            g = d[d.condition == cond]
            ax.errorbar(g["true"], g["pred"], yerr=[np.clip(g["pred"] - g["low"], 0, None), np.clip(g["high"] - g["pred"], 0, None)],
                        fmt=mk, color=col, alpha=.55, ms=4, lw=.6, label=f"{cond} (n={len(g)})")
        lo, hi = d["true"].min() * .6, d["true"].max() * 1.6
        ax.plot([lo, hi], [lo, hi], "k--", lw=.8); ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel(f"measured {t}"); ax.set_ylabel("LLM prediction"); ax.legend(fontsize=7); ax.set_title(t)
    fig.tight_layout(); fig.savefig(BENCH_DIR / "llm_vs_ml.png", dpi=200)


if __name__ == "__main__":
    if sys.argv[1] == "make":
        make_all({"strength_mpa": 40, "measured_density_g_cc": 40, "modulus_mpa": 30})
    else:
        score()
