"""PDF -> text (with page markers) using PyMuPDF.

Tables are the most valuable part of these papers. PyMuPDF's `find_tables` is used
to render detected tables as Markdown so the LLM sees clean rows instead of
scrambled column text.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # pymupdf
from rich.progress import track

from foamgpt.config import PDF_DIR, TEXT_DIR


def _table_to_md(tab) -> str:
    rows = tab.extract()
    if not rows:
        return ""
    clean = [[(c or "").replace("\n", " ").strip() for c in r] for r in rows]
    width = max(len(r) for r in clean)
    clean = [r + [""] * (width - len(r)) for r in clean]
    head = "| " + " | ".join(clean[0]) + " |"
    sep = "|" + "---|" * width
    body = "\n".join("| " + " | ".join(r) + " |" for r in clean[1:])
    return f"{head}\n{sep}\n{body}"


def pdf_to_text(pdf_path: Path, max_pages: int = 40) -> str:
    doc = fitz.open(pdf_path)
    parts: list[str] = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        parts.append(f"\n\n===== PAGE {i + 1} =====\n")
        parts.append(page.get_text("text"))
        try:
            tabs = page.find_tables()
            for j, tab in enumerate(tabs.tables):
                md = _table_to_md(tab)
                if md:
                    parts.append(f"\n[TABLE p{i + 1}-{j + 1}]\n{md}\n[/TABLE]\n")
        except Exception:  # noqa: BLE001, S112 - table detection is best-effort
            continue
    return "".join(parts)


def parse_all(force: bool = False) -> int:
    n = 0
    for pdf in track(sorted(PDF_DIR.glob("*.pdf")), description="Parsing PDFs"):
        out = TEXT_DIR / f"{pdf.stem}.txt"
        if out.exists() and not force:
            continue
        try:
            out.write_text(pdf_to_text(pdf))
            n += 1
        except Exception as e:  # noqa: BLE001
            (TEXT_DIR / f"{pdf.stem}.error").write_text(str(e))
    return n
