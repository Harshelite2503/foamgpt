# FoamGPT: A Literature-Scale Process–Structure–Property Dataset for Syntactic Foams Extracted with Large Language Models, and What Machine Learning and LLMs Can Predict From It

Harsh Vardhan Gupta¹, Nikhil Gupta¹
¹ Department of Mechanical and Aerospace Engineering, NYU Tandon School of Engineering, Brooklyn, NY, USA

DRAFT v0.1 — August 2026 — for internal discussion

# Abstract

Syntactic foams — hollow-particle-filled composites — have a three-decade experimental literature whose quantitative results remain locked in PDF tables and figures. We present FoamGPT, an open pipeline and dataset that converts that literature into a machine-readable process–structure–property (PSP) table with per-value provenance. From 1,329 relevant papers identified in OpenAlex (1990–2026) we processed the 93 open-access papers, of which 80 were confirmed on-topic, and extracted 951 records (738 primary measurements, 152 literature-quoted values, 61 model results) using a large language model constrained by a 40-field schema, a no-guessing rule, and mandatory verbatim evidence quotes. Automated physical-range checks flag 51 records for expert review. The extracted data reproduce known structure–property trends without post-processing. Using paper-level cross-validation, a random forest predicts foam density from processing descriptors alone (R² = 0.80) but cannot yet predict modulus or strength across laboratories (R² < 0), quantifying how far recipe-level features are from transferable mechanical prediction at this data scale. We release the dataset, extraction prompts, and benchmark code, and describe a validation protocol and the remaining barriers — figure-only reporting, paywalled corpora, and unit/definition heterogeneity — to a complete literature-scale dataset.

# 1. Introduction

Syntactic foams are particulate composites in which hollow microspheres (glass, ceramic, fly-ash cenosphere, polymer, or metal) are dispersed in a polymer or metal matrix. Their combination of low density, high specific compressive strength, damage tolerance, and low moisture uptake makes them the material of choice for deep-submergence buoyancy, marine and aerospace sandwich cores, and energy-absorbing structures. Because properties depend on the full processing chain — matrix chemistry, microsphere grade and wall-thickness ratio, volume fraction, mixing and curing route — the field has produced a large empirical literature: we identify 1,329 relevant papers since 1990, growing every decade.

Almost none of this knowledge is usable computationally. Each paper reports its own compositions in its own tables, with inconsistent units (MPa vs. GPa; kg/m³ vs. g/cm³; vol% vs. wt%), paper-specific sample labels, and results that are often shown only graphically. Consequently, materials selection is performed by manual literature review, and machine-learning studies in the field are trained on a few dozen in-house samples that do not generalise across laboratories.

Large language models (LLMs) now extract structured data from scientific text with near-expert accuracy when the schema is explicit and outputs are validated [Schilling-Wilhelmi 2025; Zimmermann 2025]. Nearly all demonstrations target chemistry and crystalline materials; mechanical and processing data for composites is a recognised gap [Van 2026]. At the same time, LLMs are increasingly consulted for materials questions, and whether their numerical answers reflect knowledge or plausible fabrication has not been measured for composite properties [Zhang 2026].

This paper makes three contributions. (1) An open, provenance-carrying PSP dataset for syntactic foams built from the open-access literature with an LLM extraction pipeline that refuses to guess. (2) A quantitative characterisation of what the literature actually contains — how much is tabulated versus figure-only, how coverage varies by matrix class and era, and what internal inconsistencies occur. (3) A benchmark of classical ML and a frontier LLM on cross-laboratory property prediction, with calibration analysis for the LLM.

# 2. Related Work

Syntactic foam mechanics. The roles of microballoon wall-thickness ratio, volume fraction, matrix modulus, strain rate and temperature have been mapped in polymer-matrix foams and, with pressure-infiltration processing, in aluminium and magnesium matrix foams [Gupta & Rohatgi; Orbulov; Szlancsik]. Micromechanical models (Bardella–Genna, Porfiri–Gupta) predict elastic moduli from constituent properties, but strength and energy absorption remain empirical.

LLM-based scientific data extraction. Structured extraction with schema constraints and validation has been demonstrated for reaction conditions, MOF synthesis, and polymer properties. Reviews [Jiang 2025; Van 2026] identify composites/manufacturing as under-served and highlight provenance and hallucination control as open problems.

Benchmarks of LLM materials knowledge. MatSciBench [Zhang 2026] evaluates reasoning on textbook-style problems; van Herck et al. [2025] compare fine-tuned LLMs with ML on tabular property prediction. No prior work measures calibration of LLM numerical predictions for a composite class against literature ground truth.

# 3. Methods

## 3.1 Corpus construction

Seven queries ("syntactic foam(s)", "hollow glass microspheres", "glass microballoons", "cenosphere composite", "hollow particle composite", "metal matrix syntactic foam") were run against the OpenAlex works index restricted to 1990–2026, returning 4,912 works. A title/abstract relevance score labelled 1,329 as strongly relevant (syntactic foam or microballoon explicitly named) and 662 as weakly relevant. Only 279 of the strongly relevant papers (21%) expose an open-access PDF; 93 of those resolved to a real PDF (the remainder are HTML landing pages) and form the pilot corpus. Figure 1 shows the corpus by year.

![](data/benchmarks/corpus_by_year.png)
Figure 1. Strongly relevant syntactic-foam papers per year in the OpenAlex-derived corpus.

## 3.2 Parsing

PDFs were converted with PyMuPDF; detected tables were rendered as Markdown so that rows and columns survive. Full-length documents were retained (an initial 40-page cap silently truncated ten theses and was removed; the truncated papers were re-extracted). Image-only scans (one in the corpus) and bitmap tables yield only captions and are recorded as such.

## 3.3 Schema

One record is one composition tested under one condition. Fields are grouped as Processing (matrix class and name; particle type, grade, true density, mean diameter, wall-thickness ratio η; volume and weight fraction; process route; cure temperature; additional fillers), Structure (measured and theoretical density, matrix porosity, particle breakage), Test (type, strain rate, temperature, standard), and Properties (modulus, strength, failure strain, energy absorption, plateau stress, densification strain, DMA storage modulus and tan δ, thermal conductivity, CTE, moisture uptake). Every numeric field is optional. Each record carries a data-origin tag (primary measurement, secondary literature quotation with citation, or model result), at least one verbatim evidence quote with location, and an extractor confidence.

## 3.4 Extraction

Extraction is performed by Claude (Anthropic) with the schema inlined in the system prompt and a fixed rule set: one record per composition × condition; never invent a value — leave it null if it is not stated numerically; convert to schema units; do not read values off plots; tag literature-quoted values as secondary. Outputs are validated against the Pydantic schema with one self-repair turn, then passed through range and unit checks. Two execution lanes share the same prompt, schema and validator: an API lane (Claude Opus 5 via the Messages API; three papers, ≈US$1) and an agent lane in which Claude Code subagents (Claude Opus 5) read the paper text and write the JSON, used for the remaining papers to avoid per-token cost. Prompt version and lane are recorded per paper.

## 3.5 Curation

Records are flattened, deduplicated on all fields, and checked against physical ranges (density 0.1–8 g/cm³; volume fraction ≤ 0.8; modulus 1–300,000 MPa; strength 0.1–3,000 MPa; wall-thickness ratio 0.3–1). Percent-not-fraction and GPa-not-MPa slips are flagged, not silently corrected. Specific modulus and strength are derived where density is present.

## 3.6 Validation protocol

A stratified sample of 91 primary records (41 papers), balanced across matrix classes and across records with and without numeric properties, is provided with the source quote for each value. Two annotators, one a domain expert, will verify value, unit and row correctness; per-field precision, inter-annotator agreement (Cohen's κ) and an error taxonomy will be reported. This step is pending at the time of this draft.

## 3.7 Benchmarks

ML. Targets: compressive modulus, compressive strength (compression tests only) and measured density. Features: matrix class, particle type, process route, test type, particle true density and diameter, wall-thickness ratio, volume and weight fraction, measured density (except when it is the target), strain rate and temperature. Only unflagged primary records are used. Ridge regression, random forest and gradient boosting are evaluated with 5-fold GroupKFold by paper so that no paper contributes to both training and test. Modulus and strength are modelled in log10.

LLM. From the same pool, held-out records are sampled (40 strength, 40 density, 30 modulus). For each, the model receives the record's processing and test descriptors and is asked for a point estimate and a 90% credible interval, (a) zero-shot and (b) with the five nearest primary records from other papers (matched on matrix class, particle type and volume fraction) supplied as context. The model under test is Claude Opus 5 acting through Claude Code with file access restricted to the task text, so it cannot see the dataset or the source papers. Metrics: median and mean absolute percentage error, log-R², and empirical coverage of the 90% interval.

# 4. Results

## 4.1 What the literature contains

Of 93 processed papers, 80 were confirmed on-topic; the 13 rejected papers were keyword false positives (conservation reports using microballoon putty, an economics working paper, an antenna design, a radome FEA study) and produced no records. The on-topic papers yielded 951 records: 738 primary, 152 secondary and 61 model. The median paper contributes 6 records; theses contribute the most (up to 185).

Table 1. Dataset composition.

| Quantity | Value |
|---|---|
| Records with strength / modulus / measured density | 413 / 314 / 386 |
| Records with particle volume fraction | 604 (0–0.92) |
| Records at strain rate ≥ 100 s⁻¹ | 52 |
| Matrix classes | epoxy 381, aluminum 229, other_thermoset 126, pp 62, vinyl_ester 50, polyurethane 43, other 29 |
| Particle types | glass_microballoon 563, ceramic_hollow 143, fly_ash_cenosphere 91, other 75, polymer_hollow 66 |
| Process routes | mechanical_mixing_cast 427, pressure_infiltration 166, other 144, vacuum_assisted 77, injection_molding 58 |
| Test types | compression 328, tension 179, other 146, flexure 88, dma 81, impact 57 |
| Records flagged by range checks | 51 |

A central finding is how much of the literature is figure-only. Only 64 of 80 on-topic papers state at least one numeric strength, modulus or density value in text or tables; the share rises from 59% for papers before 2010 to 86% after (Figure 2). Records from figure-only papers carry composition and test conditions with null properties, which the extractor reports rather than digitising plots. Fire, tribological, acoustic and fracture-toughness results — present in several papers — have no schema field and are preserved in notes, indicating natural schema extensions.

![](data/benchmarks/records_year_coverage.png)
Figure 2. Left: records per publication year. Right: fraction of records carrying strength, modulus and density, by matrix class.

## 4.2 Extracted data reproduce known structure–property relations

Figure 3 plots density against compressive modulus and strength for unflagged primary compression records. Metal-matrix foams occupy the high-density, high-strength region (aluminium: 1.07–2.39 g/cm³, 18–272 MPa); polymer foams cluster at 0.3–0.95 g/cm³. Within aluminium foams, strength correlates with density (r = 0.28, n = 50) despite spanning different matrices (Al99.5, AlSi12, A356, 7075), particle chemistries and strain rates; within a single study the correlation is near-perfect (r = 0.98 for the six quasi-static Al7075 compositions of one paper). The split-Hopkinson series in the dataset show the expected 2–3× strain-rate strengthening of Al-matrix foams.

![](data/benchmarks/pilot_density_strength.png)
Figure 3. Density versus compressive modulus (left) and strength (right), unflagged primary records, coloured by matrix class.

## 4.3 Cross-laboratory machine-learning baselines

Table 2. Paper-level GroupKFold results.

| Target | Model | n rows / papers | R² (log for E, σ) | MAPE % |
|---|---|---|---|---|
| modulus_mpa | ridge | 87 / 15 | -0.09 | 116 |
| modulus_mpa | random_forest | 87 / 15 | 0.09 | 100 |
| modulus_mpa | gbr | 87 / 15 | 0.18 | 87 |
| strength_mpa | ridge | 138 / 23 | -0.99 | 292 |
| strength_mpa | random_forest | 138 / 23 | 0.01 | 114 |
| strength_mpa | gbr | 138 / 23 | -0.04 | 110 |
| measured_density_g_cc | ridge | 254 / 37 | 0.61 | 26 |
| measured_density_g_cc | random_forest | 254 / 37 | 0.80 | 20 |
| measured_density_g_cc | gbr | 254 / 37 | 0.74 | 22 |

Density is predictable from processing descriptors across laboratories (random forest R² = 0.80, MAPE ≈ 20%), as expected from the rule of mixtures. Modulus and strength are barely predictable: the best log-R² values are 0.18 and 0.01, with MAPE around 90–110%. The rows mix metal and polymer matrices, quasi-static and dynamic loading, and heterogeneous particle grades, and most papers report a single matrix with one to six compositions, so the paper-level split forces extrapolation to unseen matrix/particle combinations. This is the quantitative statement of the data-scarcity problem: at ~140 usable strength rows from 23 papers, recipe-level features do not transfer. Data quality matters as much as quantity: before a curation rule flagged metal-matrix moduli reported in GPa under an MPa label (ISO 13314 'structural stiffness' in several papers), the modulus log-R² was −0.89; removing those 17 rows raised it to 0.18.

## 4.4 LLM prediction and calibration

[LLM benchmark running — table and figure inserted automatically when data/benchmarks/llm_agent_summary.csv exists.]

# 5. Discussion

- Provenance is the enabling design choice. Because every value carries a quote and location, the expert audit reduces to checking quotes, and internal inconsistencies found by the extractor (table vs. text values, unit labels contradicting magnitudes, negative porosities from sign conventions) become a curated list rather than silent errors.
- Refusing to guess is measurable. Null properties in on-topic papers are a feature of the literature, not the extractor; the pre/post-2010 contrast (59% vs 86% of papers with numeric values) quantifies the return on a figure-digitisation stage.
- Secondary data must be tagged. Review tables and comparison rows contribute 16% of records; without the data-origin tag they would double-count originals and leak between train and test.
- Cross-laboratory prediction is the right target and it is hard. Density transfers; mechanical properties do not at ~10² rows. The dataset therefore serves less as a training set today than as a benchmark and a map of where measurements are missing.
- Cost. The entire pilot required ≈US$1 of API spend plus subagent compute; the full 1,329-paper corpus is estimated at US$400–500 via batch API, dominated by input tokens for long theses.

# 6. Limitations

- Open-access bias: only 21% of relevant papers are open access; institutional access is required for the remainder and may shift the composition of the dataset toward journals with different reporting norms.
- Figure-only data are not captured; a plot-digitisation stage with uncertainty is future work.
- Field mapping strain: some papers report properties the schema lacks (fracture toughness, hardness, acoustic, fire), and some values were mapped to the nearest field with a note (e.g., ISO 13314 structural stiffness recorded as modulus).
- Validation is pending; extraction accuracy is currently supported only by spot checks and automated range flags.
- The LLM under test also performed extraction (different sessions, no file access during prediction); an independent model family should be added.

# 7. Data and Code Availability

Dataset (CSV/Parquet), per-paper extractions with evidence (JSONL), prompts, schema, curation and benchmark code: https://github.com/Harshelite2503/foamgpt (MIT). A Zenodo DOI will accompany the validated release.

# References

- Jiang X. et al. Applications of natural language processing and large language models in materials discovery. npj Comput. Mater. 2025.
- Van M.H. et al. A survey of AI for materials science: foundation models, LLM agents, datasets, and tools. ACM Comput. Surv. 2026.
- Zimmermann Y. et al. 32 examples of LLM applications in materials science and chemistry. Mach. Learn.: Sci. Technol. 2025.
- Schilling-Wilhelmi M. et al. From text to insight: large language models for chemical data extraction. Chem. Soc. Rev. 2025.
- Zhang J. et al. MatSciBench: benchmarking the reasoning ability of LLMs in materials science. 2026.
- van Herck J. et al. Assessment of fine-tuned LLMs for real-world chemistry and material science applications. Chem. Sci. 2025.
- Gupta N., Rohatgi P.K. (eds). Metal Matrix Syntactic Foams. DEStech, 2014.
- Orbulov I.N., Dobránszky J. Producing metal matrix syntactic foams by pressure infiltration. Period. Polytech. Mech. Eng. 2008.
- Porfiri M., Gupta N. Effect of volume fraction and wall thickness on the elastic properties of hollow particle filled composites. Compos. B 2009.
- Beckwith C., Gupta N. Rheological measurement dataset of resin and composite mixtures for DLP additive manufacturing. Sci. Data 2026.
