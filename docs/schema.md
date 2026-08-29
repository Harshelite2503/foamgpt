# Schema notes

* `particle_wall_thickness_ratio` is η = r_inner / r_outer. Commercial glass microballoons: η ≈ 0.90–0.98.
  It is the key structural variable in Gupta's work – it controls particle density and crush strength.
* Volume fraction is a **fraction** (0.30), never percent. Curation flags values > 1.
* Modulus/strength are **MPa**. Polymer syntactic foams: modulus ≈ 1–5 GPa (1000–5000 MPa), strength 20–120 MPa.
  Metal-matrix: modulus 10–70 GPa, strength 50–300 MPa. Curation flags polymer moduli < 20 MPa as "maybe GPa".
* `strain_rate_per_s`: quasi-static tests are typically 1e-3 /s; SHPB ~1e3 /s.
* Records from the same paper with identical numbers are deduplicated; near-duplicates (rounding) are kept and
  will be handled in the validation phase.

## Validation protocol (planned)

1. Stratified sample of 100 records (by matrix class, year, venue).
2. Two annotators (one domain expert) independently check every field against the PDF.
3. Report per-field precision/recall, Cohen's κ, and an error taxonomy (unit slips, wrong row, figure misreads).
