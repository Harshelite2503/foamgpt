"""Download open-access PDFs listed in papers.jsonl.

Only OA links returned by OpenAlex are fetched - we never bypass paywalls. For
paywalled papers the user's institutional access is used manually: drop the PDF in
`data/pdfs/<openalex_id>.pdf` and the rest of the pipeline picks it up.
"""

from __future__ import annotations

import time
from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import track

from foamgpt.config import PDF_DIR
from foamgpt.harvest.openalex import load_papers

console = Console()
HEADERS = {"User-Agent": "Mozilla/5.0 (research; foamgpt/0.1)", "Accept": "application/pdf,*/*"}


def _is_pdf(content: bytes) -> bool:
    return content[:5] == b"%PDF-"


def download_all(limit: int | None = None, sleep: float = 0.5, min_relevance: int = 2) -> dict[str, int]:
    papers = [p for p in load_papers() if p.get("oa_pdf_url") and p.get("relevance", 0) >= min_relevance]
    papers.sort(key=lambda p: -p.get("cited_by", 0))  # most-cited first
    if limit:
        papers = papers[:limit]
    stats = {"ok": 0, "exists": 0, "fail": 0, "not_pdf": 0}
    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=20) as client:
        for p in track(papers, description="Downloading OA PDFs"):
            dest: Path = PDF_DIR / f"{p['id']}.pdf"
            if dest.exists():
                stats["exists"] += 1
                continue
            try:
                r = client.get(p["oa_pdf_url"])
                if r.status_code == 200 and _is_pdf(r.content):
                    dest.write_bytes(r.content)
                    stats["ok"] += 1
                else:
                    stats["not_pdf"] += 1
            except Exception:  # noqa: BLE001 - network noise is expected
                stats["fail"] += 1
            time.sleep(sleep)
    console.print(stats)
    return stats
