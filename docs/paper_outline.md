# Paper outline — FoamGPT

**Working title:** FoamGPT: A literature-scale Process–Structure–Property dataset for syntactic foams extracted
with large language models, and a benchmark of what LLMs actually know about them.

**Target venues:** Scientific Data (dataset descriptor) + companion benchmark at NeurIPS Datasets & Benchmarks /
AI4Mat workshop, or Composites Part B / Materials & Design (single combined paper).

## 1. Introduction
* Syntactic foams: lightweight, damage-tolerant; 30+ years of literature; no consolidated dataset.
* Materials-science LLM work concentrates on crystals/molecules; composites & AM lag (cite npj CM 2025 review, ACM CSUR 2026).
* Contributions: (i) open PSP dataset with provenance; (ii) extraction methodology + validation; (iii) ML vs LLM benchmark; (iv) findings on LLM calibration / hallucination.

## 2. Related work
LLM data extraction (Schilling-Wilhelmi 2025), MatSciBench, "32 examples" survey, prior syntactic-foam reviews (Gupta et al.).

## 3. Corpus construction
OpenAlex queries → N papers → OA subset → institutional subset. Year/venue distribution figure.

## 4. Extraction pipeline
Schema design (why one record per composition×condition), prompt rules, structured outputs, batch runs, cost.

## 5. Validation
100-record expert audit; per-field accuracy; error taxonomy; inter-annotator agreement.

## 6. Dataset statistics
Coverage by matrix, particle, process; density–modulus and density–strength maps; comparison to Gibson–Ashby / Bardella–Genna model predictions.

## 7. Benchmarks
7.1 Classical ML by-paper CV. 7.2 LLM zero-shot vs RAG: MAPE, 90% interval coverage. 7.3 Where LLMs fail (metal matrices, high strain rate, unusual particles).

## 8. Discussion & limitations
OA bias, figure-only data, unit ambiguity, inverse-design outlook (link to DLP printability, metamaterials).

## 9. Data availability
CSV/parquet + JSONL extractions with evidence; code on GitHub.
