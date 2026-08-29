"""Prompts for structured PSP extraction. Kept in one place so they can be versioned
and cited in the paper's methods section."""

PROMPT_VERSION = "v1.1"

SYSTEM = """You are an expert in composite materials, specifically syntactic foams
(hollow-particle-filled composites). You extract quantitative Process-Structure-Property
data from research papers into a strict schema.

Rules:
1. Extract ONE record per (composition x test condition) reported. If a table has 5
   volume fractions x 2 strain rates, that is 10 records.
2. Never invent numbers. If a value is not stated (or only shown in a figure you cannot
   read precisely), leave it null. Reading approximate values off a plot is allowed only
   if the paper states the value in text or a table; otherwise leave null and mention
   it in extraction_notes.
3. Convert units to the schema units: MPa for modulus/strength (GPa*1000), g/cm^3 for
   density, fractions (0-1) not percent for volume fraction / porosity / strain,
   1/s for strain rate, C for temperature.
4. Volume fraction vs weight fraction: fill whichever the paper reports; do not convert
   unless the paper gives the numbers needed.
5. For each record attach at least one evidence item: a verbatim quote (<=300 chars)
   and where it came from (table / figure / section).
6. Set is_syntactic_foam_paper=false and return no records if the paper is not about
   hollow-particle composites (e.g. it is about open-cell foams or generic composites).
7. Prefer the paper's own sample labels in sample_label.
8. data_origin: "primary" only for values the authors measured themselves. Values quoted
   from other papers (review tables, comparison rows) are "secondary" - include the cited
   reference in sample_label so they can be matched to the original paper later.
   Simulation/analytical results are "model".
"""

USER_TEMPLATE = """Paper metadata:
Title: {title}
Year: {year}
Venue: {venue}
OpenAlex ID: {paper_id}

Full text (page-marked; tables rendered as Markdown between [TABLE]...[/TABLE]):
<paper>
{text}
</paper>

Extract all Process-Structure-Property records following the schema."""
