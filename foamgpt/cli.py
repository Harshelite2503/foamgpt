"""FoamGPT command-line pipeline.

    foamgpt harvest            # OpenAlex -> data/raw/papers.jsonl
    foamgpt download           # OA PDFs -> data/pdfs/
    foamgpt parse              # PDFs -> data/text/
    foamgpt extract --limit 5  # Claude structured extraction (sync)
    foamgpt batch-submit / batch-collect <id>
    foamgpt curate             # -> data/curated/foam_psp.csv
    foamgpt bench-ml           # classical ML baselines
    foamgpt bench-llm          # LLM zero-shot / RAG baseline
    foamgpt stats              # corpus + dataset summary
"""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="FoamGPT: LLM-extracted PSP dataset for syntactic foams", no_args_is_help=True)
console = Console()


@app.command()
def harvest(max_pages: int = 10):
    from foamgpt.harvest.openalex import harvest as _h
    _h(max_pages=max_pages)


@app.command()
def download(limit: int = typer.Option(None), min_relevance: int = 2):
    from foamgpt.harvest.download import download_all
    download_all(limit=limit, min_relevance=min_relevance)


@app.command()
def parse(force: bool = False):
    from foamgpt.parse.pdf import parse_all
    console.print(f"parsed {parse_all(force=force)} new PDFs")


@app.command()
def extract(limit: int = typer.Option(3, help="papers to extract synchronously")):
    from foamgpt.extract.extractor import extract_sync
    console.print(f"extracted {extract_sync(limit=limit)} papers")


@app.command("batch-submit")
def batch_submit(limit: int = typer.Option(None)):
    from foamgpt.extract.extractor import submit_batch
    submit_batch(limit=limit)


@app.command("batch-collect")
def batch_collect(batch_id: str):
    from foamgpt.extract.extractor import collect_batch
    collect_batch(batch_id)


@app.command()
def curate():
    from foamgpt.curate.normalize import curate as _c
    from foamgpt.curate.normalize import summary
    df = _c()
    console.print_json(json.dumps(summary(df)))


@app.command("bench-ml")
def bench_ml():
    import pandas as pd

    from foamgpt.benchmark.ml_baselines import run
    from foamgpt.curate.normalize import CURATED
    res = run(pd.read_csv(CURATED))
    console.print(res.to_string())


@app.command("bench-llm")
def bench_llm(target: str = "strength_mpa", n: int = 60, k: int = 5):
    import pandas as pd

    from foamgpt.benchmark.llm_baseline import run
    from foamgpt.curate.normalize import CURATED
    console.print(run(pd.read_csv(CURATED), target=target, n=n, k=k).to_string())


@app.command()
def stats():
    from foamgpt.config import PDF_DIR, TEXT_DIR
    from foamgpt.harvest.openalex import load_papers
    papers = load_papers()
    t = Table(title="FoamGPT corpus")
    t.add_column("metric"); t.add_column("value", justify="right")
    t.add_row("papers (metadata)", str(len(papers)))
    t.add_row("with OA pdf link", str(sum(1 for p in papers if p["oa_pdf_url"])))
    for lvl, name in ((2, "strong"), (1, "weak"), (0, "off-topic")):
        t.add_row(f"relevance={name}", str(sum(1 for p in papers if p.get("relevance", 0) == lvl)))
    t.add_row("strong + OA pdf", str(sum(1 for p in papers if p.get("relevance") == 2 and p["oa_pdf_url"])))
    t.add_row("pdfs on disk", str(len(list(PDF_DIR.glob("*.pdf")))))
    t.add_row("parsed texts", str(len(list(TEXT_DIR.glob("*.txt")))))
    years = [p["year"] for p in papers if p.get("year")]
    if years:
        t.add_row("year range", f"{min(years)}-{max(years)}")
    console.print(t)


if __name__ == "__main__":
    app()
