"""Harvest paper metadata + open-access PDF links from OpenAlex.

OpenAlex is free, requires no key, and returns `best_oa_location.pdf_url` when an
open-access copy exists. We store the full metadata so the corpus is reproducible.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
from rich.console import Console
from tenacity import retry, stop_after_attempt, wait_exponential

from foamgpt.config import CORPUS_QUERIES, OPENALEX_BASE, OPENALEX_MAILTO, RAW_DIR

console = Console()

SELECT = (
    "id,doi,title,publication_year,cited_by_count,type,open_access,best_oa_location,"
    "primary_location,authorships,abstract_inverted_index,concepts"
)


def _reconstruct_abstract(inv: dict | None) -> str | None:
    if not inv:
        return None
    positions: list[tuple[int, str]] = []
    for word, idxs in inv.items():
        positions.extend((i, word) for i in idxs)
    return " ".join(w for _, w in sorted(positions))


@retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=30))
def _get(client: httpx.Client, params: dict) -> dict:
    r = client.get(f"{OPENALEX_BASE}/works", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def search(query: str, per_page: int = 200, max_pages: int = 10, min_year: int = 1990) -> Iterator[dict]:
    """Yield OpenAlex work objects matching a query (cursor-paginated)."""
    params = {
        "search": query,
        "filter": f"publication_year:>{min_year - 1},type:article|book-chapter|dissertation",
        "per-page": per_page,
        "cursor": "*",
        "select": SELECT,
    }
    if OPENALEX_MAILTO:
        params["mailto"] = OPENALEX_MAILTO
    with httpx.Client(headers={"User-Agent": "foamgpt/0.1 (research)"}) as client:
        for _ in range(max_pages):
            data = _get(client, params)
            for w in data.get("results", []):
                w["abstract"] = _reconstruct_abstract(w.pop("abstract_inverted_index", None))
                yield w
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor:
                break
            params["cursor"] = cursor
            time.sleep(0.2)  # be polite


STRONG = ("syntactic foam", "syntactic foams", "microballoon", "microballoons")
WEAK = ("hollow glass microsphere", "hollow microsphere", "cenosphere", "hollow particle",
        "hollow sphere", "glass bubble")


def relevance(title: str | None, abstract: str | None) -> int:
    """0 = off-topic, 1 = weak (hollow particles mentioned), 2 = strong (syntactic foam)."""
    t = f"{title or ''} {abstract or ''}".lower()
    if any(k in t for k in STRONG):
        return 2
    if any(k in t for k in WEAK) and any(k in t for k in ("composite", "foam", "compress", "mechanical")):
        return 1
    return 0


def _slim(w: dict) -> dict:
    loc = w.get("best_oa_location") or {}
    prim = w.get("primary_location") or {}
    return {
        "id": w["id"].rsplit("/", 1)[-1],
        "doi": w.get("doi"),
        "title": w.get("title"),
        "year": w.get("publication_year"),
        "cited_by": w.get("cited_by_count", 0),
        "type": w.get("type"),
        "venue": (prim.get("source") or {}).get("display_name"),
        "authors": [a.get("author", {}).get("display_name") for a in w.get("authorships", [])][:12],
        "is_oa": (w.get("open_access") or {}).get("is_oa", False),
        "oa_pdf_url": loc.get("pdf_url"),
        "oa_landing_url": loc.get("landing_page_url"),
        "abstract": w.get("abstract"),
        "concepts": [c.get("display_name") for c in w.get("concepts", [])[:8]],
        "relevance": relevance(w.get("title"), w.get("abstract")),
    }


def harvest(queries: list[str] | None = None, max_pages: int = 10, out: Path | None = None) -> Path:
    """Run all corpus queries, dedupe by OpenAlex id, write `data/raw/papers.jsonl`."""
    queries = queries or CORPUS_QUERIES
    out = out or RAW_DIR / "papers.jsonl"
    seen: dict[str, dict] = {}
    for q in queries:
        n = 0
        for w in search(q, max_pages=max_pages):
            s = _slim(w)
            s.setdefault("matched_queries", [])
            if s["id"] in seen:
                seen[s["id"]]["matched_queries"].append(q)
            else:
                s["matched_queries"] = [q]
                seen[s["id"]] = s
            n += 1
        console.print(f"[cyan]{q}[/] -> {n} hits (corpus now {len(seen)})")
    with out.open("w") as f:
        for s in seen.values():
            f.write(json.dumps(s) + "\n")
    n_oa = sum(1 for s in seen.values() if s["oa_pdf_url"])
    n_rel = sum(1 for s in seen.values() if s["relevance"] == 2)
    console.print(f"[green]Wrote {len(seen)} papers to {out}; {n_oa} have OA PDF links; "
                  f"{n_rel} strongly relevant[/]")
    return out


def load_papers(path: Path | None = None) -> list[dict]:
    path = path or RAW_DIR / "papers.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
