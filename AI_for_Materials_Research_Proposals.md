# AI/LLM Research Directions for Collaboration with Prof. Nikhil Gupta (NYU Tandon)

Prepared: Aug 2026

## 1. What Prof. Gupta actually works on (from Scholar + recent papers)

| Thread | Evidence (recent) |
|---|---|
| **Syntactic foams / hollow-particle composites** (polymer & metal matrix, HDPE-HGM, µCT porosity analysis) | *Automated segmentation of voids and particles in HDPE-HGM syntactic foams using µCT imaging and K-means clustering*, Materials & Design 2026 |
| **Vat photopolymerization / DLP printing of particle-filled resins** | *Rheological Measurement Dataset of Resin and Composite Mixtures for DLP AM*, Scientific Data 2026 (explicitly says the data is "good candidates for machine learning") |
| **Architected metamaterials / lattices** | Book *Architected Metamaterials: Design Principles and Properties* (Springer 2025) with chapters on ML-driven design and "Current Limitations and Future Directions" |
| **Dynamic / rate- and temperature-dependent characterization of foams** | *ML-aided accelerated characterization of temperature and strain-rate-dependent dynamic properties of closed-cell polymer foams*, J. Cellular Plastics 2025 |
| **Additive-manufacturing cybersecurity** (with Ramesh Karri, N. Tsoutsos): CAD/STL obfuscation, embedding security features, defect-based anti-counterfeiting, reverse-engineering attacks | Long-running thread with NYU Center for Cybersecurity |
| **Biomaterials / implants** (with Paulo Coelho) | Co-author list |

Key observation: his group is already doing "classical" ML (K-means, regression, surrogate models). What is **missing** is LLM / foundation-model / agentic work, and that is exactly where a CS+Econ person adds value.

## 2. Top open problems in the field (AI × materials/manufacturing), 2025–26

Drawn from the major reviews (Jiang et al., npj Comput. Mater. 2025; Van et al., ACM CSUR 2026; Zimmermann et al., "32 examples of LLM applications in materials", MLST 2025; Schilling-Wilhelmi et al., Chem. Soc. Rev. 2025; MatSciBench 2026):

1. **Data scarcity & fragmentation** – experimental composites/AM data is small, heterogeneous, and buried in PDFs, tables and figures. Structured extraction from literature is still unsolved for *mechanical/processing* data (most LLM extraction work is on chemistry/synthesis, not composites).
2. **Process–structure–property (PSP) linkage** – especially for AM, where process parameters (exposure, layer time, viscosity, particle loading) → microstructure (porosity, particle distribution) → properties (modulus, strength, damping).
3. **Inverse design** – given a target property set, propose a material/lattice/process recipe. Generative models exist for crystals & molecules; almost nothing for filled resins, foams, or architected lattices with manufacturability constraints.
4. **Multimodal data** – µCT scans, SEM images, stress–strain curves, rheology curves, G-code/CAD. Vision-language models have barely been applied to these.
5. **Reasoning & reliability** – MatSciBench shows LLMs still fail at multi-step materials reasoning; hallucinated properties are dangerous. Verification, uncertainty, and "physics-aware" checking are open.
6. **Autonomous / self-driving labs** – LLM agents planning experiments, but almost all demos are in chemistry, not mechanical testing or 3D printing.
7. **Security & provenance of digital manufacturing** – AI both as attacker (reconstructing designs from side channels, defeating obfuscation) and defender (anomaly detection, watermark verification). Very few people sit at the intersection of AM security and LLMs — Gupta + Karri do.
8. **Economics of AI-enabled materials** – cost of data, value of a prediction, technology adoption, supply-chain decisions. Practically no rigorous work (your Econ angle).

## 3. Proposed paper topics (ranked by fit × feasibility)

### Tier A — high fit, can start now with his existing data

**A1. "FoamGPT": an LLM-extracted, structured database of syntactic-foam properties + a benchmark**
- Use an LLM pipeline (PDF → tables/figures → schema) over the ~2,000 syntactic-foam papers (many are his own) to build the first open PSP dataset: matrix, particle type, wall thickness ratio, volume fraction, processing route, density, modulus, strength, strain rate.
- Deliverables: dataset paper (Scientific Data, like his 2026 rheology dataset), plus a benchmark of how well LLMs/ML predict properties from it.
- Why it works: he is the world authority on the topic, so validation and curation are credible. Sets up everything below.

**A2. Physics-constrained LLM surrogate for DLP printability of particle-filled resins**
- Input: his rheology dataset (Sci. Data 2026) + print outcomes. Train/finetune a model that, given resin + filler + loading + temperature, predicts viscosity, cure depth, printability window, and suggests parameters.
- LLM angle: a natural-language "print assistant" that reasons over the dataset + rheology physics (Krieger–Dougherty, Jacobs equation) and flags out-of-distribution requests.
- Paper: Additive Manufacturing or Materials & Design.

**A3. Vision-language models for µCT/SEM microstructure interpretation of foams**
- Extends the K-means segmentation paper: use foundation segmentation models (SAM-family) + VLM captioning to produce quantitative void/particle statistics *and* natural-language defect reports, then link to measured properties.
- Paper: Materials Characterization / Composites Part B.

### Tier B — high novelty, needs some new experiments

**B1. LLM agent for inverse design of architected metamaterials with manufacturability constraints**
- Agent loop: target property → propose lattice family/parameters → run FE surrogate → check DLP printability (from A2) → iterate. Directly extends the "future directions" chapter of his 2025 Springer book.
- Paper: Advanced Engineering Materials / Extreme Mechanics Letters.

**B2. LLM-accelerated dynamic characterization (extends his J. Cellular Plastics 2025 paper)**
- Use active-learning + LLM-based experiment planning to choose the minimal set of strain-rate/temperature tests needed to fit a master curve. Report test-count reduction. Very practical, industry-friendly.

**B3. AI-native AM security (with Karri)**
- (a) Attack side: can multimodal LLMs reverse-engineer obfuscated STL/G-code or infer geometry from printer acoustic/power side channels? (b) Defense side: LLM-based anomaly detection on G-code and embedded "security feature" verification from µCT.
- Paper: IEEE Security & Privacy / ACM TOMPECS / Additive Manufacturing. Strong CS venue potential.

### Tier C — your Econ differentiator

**C1. Economics of AI-enabled materials data: value of information, data-sharing incentives, and adoption of AI in AM shops**
- Model when a lab/firm should run an experiment vs. trust a prediction (VOI framework), and how open datasets (like his Sci. Data papers) shift incentives. Could be a perspective piece in *Matter*, *Nature Reviews Materials*, or *Research Policy*.

**C2. Techno-economic assessment of AI-optimized lightweight composites** (e.g., syntactic foams for marine/aerospace) — cost/weight/CO₂ trade-offs with AI-designed vs. conventional recipes.

## 4. Suggested pitch to Prof. Gupta (3 topics to lead with)

1. **A1 (FoamGPT dataset + benchmark)** — low risk, high visibility, builds the asset for everything else.
2. **A2 (DLP printability assistant)** — uses data he just published; quick paper.
3. **B3 (AI-native AM security)** — most novel, pulls in Karri, fundable (NSF SaTC, DoD).

Offer C1 as a "perspective" paper you can mostly write yourself.

## 5. Key references to read first
- Jiang et al., *Applications of NLP and LLMs in materials discovery*, npj Comput. Mater. 2025
- Van et al., *A survey of AI for materials science: foundation models, LLM agents, datasets, and tools*, ACM CSUR 2026
- Zimmermann et al., *32 examples of LLM applications in materials science and chemistry*, MLST 2025
- Schilling-Wilhelmi et al., *From text to insight: LLMs for chemical data extraction*, Chem. Soc. Rev. 2025
- Zhang et al., *MatSciBench*, 2026
- Shangguan et al., *AI-driven material development for AM: a critical review*, IJAMD 2025
- Beckwith & Gupta, *Rheological Measurement Dataset… DLP AM*, Sci. Data 2026
- Vasan, Gupta et al., *Automated segmentation of voids… µCT + K-means*, Mater. Des. 2026
- Gupta & Beckwith, *Architected Metamaterials* (Springer 2025), chs. 5–6
