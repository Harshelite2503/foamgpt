"""Central configuration (paths, model names, env)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW_DIR = DATA / "raw"
PDF_DIR = DATA / "pdfs"
TEXT_DIR = DATA / "text"
EXTRACTED_DIR = DATA / "extracted"
CURATED_DIR = DATA / "curated"
BENCH_DIR = DATA / "benchmarks"

for _d in (RAW_DIR, PDF_DIR, TEXT_DIR, EXTRACTED_DIR, CURATED_DIR, BENCH_DIR):
    _d.mkdir(parents=True, exist_ok=True)

MODEL = os.getenv("FOAMGPT_MODEL", "claude-opus-5")
# Accept a few env-var spellings so users' existing shell config works.
ANTHROPIC_API_KEY = (
    os.getenv("ANTHROPIC_API_KEY") or os.getenv("MATERIALS_API_KEY") or os.getenv("FOAMGPT_API_KEY")
)
if ANTHROPIC_API_KEY and not os.getenv("ANTHROPIC_API_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY  # so anthropic.Anthropic() finds it
# Identity-linked API keys must send the workspace id on every request.
ANTHROPIC_WORKSPACE_ID = os.getenv("ANTHROPIC_WORKSPACE_ID") or os.getenv("MATERIALS_WORKSPACE_ID") or ""


def anthropic_client():
    """Anthropic client honouring the env aliases above."""
    import anthropic

    headers = {"anthropic-workspace-id": ANTHROPIC_WORKSPACE_ID} if ANTHROPIC_WORKSPACE_ID else None
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, default_headers=headers)


OPENALEX_MAILTO = os.getenv("OPENALEX_MAILTO") or os.getenv("OPENALEX_MAIL_TO") or ""
OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY", "")
OPENALEX_BASE = "https://api.openalex.org"

# Search queries that define the corpus. Kept explicit so the corpus is reproducible.
CORPUS_QUERIES: list[str] = [
    '"syntactic foam"',
    '"syntactic foams"',
    '"hollow glass microspheres" composite mechanical',
    '"glass microballoons" composite',
    '"cenosphere" composite mechanical',
    '"hollow particle" composite compressive',
    '"metal matrix syntactic foam"',
]
