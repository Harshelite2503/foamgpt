"""Collect extractions written by Claude Code subagents (no API calls).

Agents read data/text/<paper_id>.txt and write data/extracted/agent/<paper_id>.json
following docs/agent_extraction_prompt.md. This module validates each file against
PaperExtraction and appends it to extractions.jsonl with mode="claude_code_agent".

    python -m foamgpt.extract.agent_collect --check data/extracted/agent/W123.json   # validate one
    python -m foamgpt.extract.agent_collect                                          # collect all
"""
from __future__ import annotations

import sys
from pathlib import Path

from foamgpt.config import EXTRACTED_DIR
from foamgpt.extract.extractor import OUT, _already_done, _append
from foamgpt.extract.prompts import PROMPT_VERSION
from foamgpt.schema import PaperExtraction

AGENT_DIR = EXTRACTED_DIR / "agent"
AGENT_DIR.mkdir(exist_ok=True)


def check(path: Path) -> tuple[bool, str]:
    try:
        ex = PaperExtraction.model_validate_json(path.read_text())
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:2000]
    problems = []
    for i, r in enumerate(ex.records):
        if not r.evidence:
            problems.append(f"record {i}: no evidence")
        for f in ("particle_volume_fraction", "particle_weight_fraction"):
            v = getattr(r.processing, f)
            if v is not None and v > 1:
                problems.append(f"record {i}: {f}={v} looks like percent, must be fraction")
        if r.properties.strain_at_failure is not None and r.properties.strain_at_failure > 1.5:
            problems.append(f"record {i}: strain_at_failure={r.properties.strain_at_failure} looks like percent")
        if r.structure.measured_density_g_cc is not None and r.structure.measured_density_g_cc > 20:
            problems.append(f"record {i}: density {r.structure.measured_density_g_cc} looks like kg/m3")
    if ex.is_syntactic_foam_paper and not ex.records:
        problems.append("on-topic paper but zero records - confirm no quantitative data")
    return (not problems), ("OK" if not problems else "\n".join(problems))


def collect() -> int:
    done = _already_done(); n = 0
    for p in sorted(AGENT_DIR.glob("*.json")):
        pid = p.stem
        if pid in done:
            continue
        ok, msg = check(p)
        if not ok:
            print(f"SKIP {pid}: {msg}")
            continue
        ex = PaperExtraction.model_validate_json(p.read_text())
        _append(pid, ex, {"mode": "claude_code_agent", "model_note": "claude-fable-5 via Claude Code subagent",
                          "usage": None, "prompt_version": PROMPT_VERSION})
        n += 1; print(f"OK   {pid}: {len(ex.records)} records")
    print(f"collected {n} -> {OUT}")
    return n


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--check":
        ok, msg = check(Path(sys.argv[2])); print(msg); sys.exit(0 if ok else 1)
    collect()
