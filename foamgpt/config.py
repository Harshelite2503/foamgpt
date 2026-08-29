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
OPENALEX_MAILTO = os.getenv("OPENALEX_MAILTO", "")
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
