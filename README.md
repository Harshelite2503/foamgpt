# FoamGPT

**An LLM-extracted, literature-scale Process–Structure–Property (PSP) dataset and benchmark for syntactic foams.**

Syntactic foams (hollow-particle-filled composites) have ~30 years of literature, but the quantitative
results live in tables and figures inside thousands of PDFs. FoamGPT turns that literature into a
machine-readable dataset and asks: *how well can classical ML and frontier LLMs predict foam properties,
and where do LLMs hallucinate?*

```
OpenAlex ──▶ OA PDFs ──▶ text+tables ──▶ Claude structured extraction ──▶ curated PSP table ──▶ benchmarks
 harvest      download      parse            extract / batch                  curate           bench-ml / bench-llm
```

## Quickstart

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env            # add ANTHROPIC_API_KEY

foamgpt harvest                 # ~1-2 min, free, no key needed
foamgpt download                # open-access PDFs only
foamgpt parse                   # PyMuPDF text + Markdown tables
foamgpt extract --limit 3       # spot-check extraction quality
foamgpt batch-submit            # whole corpus via Message Batches (50% cheaper)
foamgpt batch-collect <batch_id>
foamgpt curate                  # -> data/curated/foam_psp.csv
foamgpt bench-ml                # by-paper GroupKFold: ridge / RF / GBR
foamgpt bench-llm --target strength_mpa   # zero-shot vs RAG LLM prediction
foamgpt stats
```

## Schema

One record = one composition × one test condition. See [`foamgpt/schema.py`](foamgpt/schema.py) and
[`docs/schema.md`](docs/schema.md). Every record carries verbatim `evidence` quotes so any number can be audited
back to the source paper.

| block | example fields |
|---|---|
| Processing | matrix class/name, particle type/grade, true density, diameter, wall-thickness ratio η, volume/weight fraction, process route, cure temp |
| Structure | measured & theoretical density, matrix porosity, particle breakage |
| Test | test type, strain rate, temperature, standard |
| Properties | modulus, strength, failure strain, energy absorption, plateau stress, DMA, thermal, moisture |

## Design decisions

* **Provenance first** – extractions keep model, prompt version, token usage, and quotes.
* **No hallucinated numbers** – prompt forbids guessing; curation flags out-of-range values, %-vs-fraction and GPa-vs-MPa slips instead of silently fixing them.
* **Honest splits** – ML baselines use `GroupKFold` by paper.
* **OA only** – the downloader fetches only open-access links from OpenAlex. Paywalled PDFs obtained via institutional access can be dropped into `data/pdfs/<OpenAlexID>.pdf`.

## Repo layout

```
foamgpt/
  schema.py            PSP pydantic schema + flattening
  harvest/             OpenAlex search, OA PDF download
  parse/               PDF -> text with Markdown tables
  extract/             prompts + Claude structured-output extraction (sync & batch)
  curate/              range checks, derived fields, dedupe -> CSV/parquet
  benchmark/           ML baselines, LLM zero-shot/RAG baseline
  cli.py               typer CLI
docs/                  paper outline, schema notes
data/                  raw/ pdfs/ text/ extracted/ curated/ benchmarks/
```

## Status

- [x] harvest (4,912 papers; 1,329 strongly relevant; 279 with OA links) / download (93 real PDFs — 177 OA links resolve to HTML landing pages) / parse (93 texts, tables as Markdown)
- [x] pilot corpus manifest: `data/raw/pilot_corpus_manifest.json`
- [x] extraction pipeline (sync + batch) with strict schema
- [x] curation + ML baselines + LLM baseline code
- [ ] run full extraction (needs API key + budget)
- [ ] expert validation sample (target: 100 records, 2 annotators)
- [ ] paper draft — see `docs/paper_outline.md`

## Citation

Pre-print in preparation (Gupta K., Gupta N.). MIT licensed code; dataset license TBD after curation.
