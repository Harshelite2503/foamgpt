"""Process-Structure-Property (PSP) schema for syntactic-foam records.

One `FoamRecord` = one material composition tested under one condition, as reported
in one paper. A paper typically yields 3-20 records (one per volume fraction /
particle grade / strain rate).

Design rules:
  * Every numeric field is Optional - missing is allowed, hallucinating is not.
  * Units are fixed per field (documented in Field descriptions) so the extractor
    must convert; a later normalisation pass double-checks ranges.
  * `evidence` carries a verbatim snippet + location so every value is auditable.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class MatrixClass(str, Enum):
    epoxy = "epoxy"
    vinyl_ester = "vinyl_ester"
    polyester = "polyester"
    polyurethane = "polyurethane"
    hdpe = "hdpe"
    pp = "pp"
    pla = "pla"
    other_thermoplastic = "other_thermoplastic"
    other_thermoset = "other_thermoset"
    aluminum = "aluminum"
    magnesium = "magnesium"
    iron_steel = "iron_steel"
    titanium = "titanium"
    zinc = "zinc"
    other_metal = "other_metal"
    cement = "cement"
    other = "other"


class ParticleType(str, Enum):
    glass_microballoon = "glass_microballoon"
    fly_ash_cenosphere = "fly_ash_cenosphere"
    ceramic_hollow = "ceramic_hollow"
    polymer_hollow = "polymer_hollow"
    carbon_hollow = "carbon_hollow"
    metal_hollow = "metal_hollow"
    other = "other"


class ProcessRoute(str, Enum):
    mechanical_mixing_cast = "mechanical_mixing_cast"
    vacuum_assisted = "vacuum_assisted"
    compression_molding = "compression_molding"
    injection_molding = "injection_molding"
    extrusion = "extrusion"
    stir_casting = "stir_casting"
    pressure_infiltration = "pressure_infiltration"
    powder_metallurgy = "powder_metallurgy"
    additive_fdm = "additive_fdm"
    additive_dlp_sla = "additive_dlp_sla"
    additive_other = "additive_other"
    other = "other"


class TestType(str, Enum):
    compression = "compression"
    tension = "tension"
    flexure = "flexure"
    shear = "shear"
    impact = "impact"
    dma = "dma"
    fatigue = "fatigue"
    hydrostatic = "hydrostatic"
    other = "other"


class DataOrigin(str, Enum):
    primary = "primary"        # measured by the paper's authors
    secondary = "secondary"    # compiled from other papers (reviews, comparison tables)
    model = "model"            # simulated / analytical, not measured


class Evidence(BaseModel):
    quote: str = Field(description="Verbatim snippet (<=300 chars) supporting the values.")
    location: str = Field(
        description="Where in the paper, e.g. 'Table 2', 'Fig. 5', 'Sec. 3.2 para 2'."
    )


class Processing(BaseModel):
    matrix_class: MatrixClass
    matrix_name: str | None = Field(None, description="Trade name / grade, e.g. 'DGEBA epoxy, EPON 828'.")
    particle_type: ParticleType
    particle_grade: str | None = Field(None, description="Manufacturer grade, e.g. '3M K46', 'S38'.")
    particle_true_density_g_cc: float | None = Field(None, description="Particle true density, g/cm^3.")
    particle_mean_diameter_um: float | None = Field(None, description="Mean diameter, micrometres.")
    particle_wall_thickness_ratio: float | None = Field(
        None, description="Radius ratio eta = inner/outer radius (0-1), if reported."
    )
    particle_volume_fraction: float | None = Field(
        None, description="Particle volume fraction as a fraction (0-1), NOT percent."
    )
    particle_weight_fraction: float | None = Field(None, description="Weight fraction (0-1), if reported instead.")
    process_route: ProcessRoute
    cure_or_process_temperature_c: float | None = Field(None, description="Cure / processing temperature, C.")
    additional_fillers: str | None = Field(None, description="Fibres, nanoclay, rubber, etc.")


class Structure(BaseModel):
    measured_density_g_cc: float | None = Field(None, description="Measured bulk density, g/cm^3.")
    theoretical_density_g_cc: float | None = None
    matrix_porosity_fraction: float | None = Field(
        None, description="Void (unintended porosity) fraction in matrix (0-1)."
    )
    particle_breakage_fraction: float | None = Field(None, description="Fraction of particles broken during processing (0-1).")
    microstructure_notes: str | None = None


class TestCondition(BaseModel):
    test_type: TestType
    strain_rate_per_s: float | None = Field(None, description="Strain rate, 1/s. Quasi-static ~1e-3.")
    temperature_c: float | None = Field(None, description="Test temperature, C. Room temp = 25.")
    standard: str | None = Field(None, description="e.g. 'ASTM D695'.")
    specimen_notes: str | None = None


class Properties(BaseModel):
    modulus_mpa: float | None = Field(None, description="Elastic modulus for the test type, MPa.")
    strength_mpa: float | None = Field(None, description="Peak / yield strength, MPa.")
    strain_at_failure: float | None = Field(None, description="Strain at failure or peak (fraction, 0-1 typical).")
    energy_absorption_mj_m3: float | None = Field(None, description="Energy absorbed up to densification or failure, MJ/m^3.")
    plateau_stress_mpa: float | None = None
    densification_strain: float | None = None
    specific_modulus_mpa_per_g_cc: float | None = Field(None, description="modulus / density if reported.")
    specific_strength_mpa_per_g_cc: float | None = None
    storage_modulus_mpa: float | None = Field(None, description="DMA storage modulus, MPa.")
    loss_tangent: float | None = None
    thermal_conductivity_w_mk: float | None = None
    cte_per_k: float | None = Field(None, description="Coefficient of thermal expansion, 1/K.")
    moisture_uptake_pct: float | None = None


class FoamRecord(BaseModel):
    """One composition x one test condition."""

    record_id: str | None = Field(None, description="Filled in by pipeline.")
    paper_id: str | None = Field(None, description="OpenAlex ID, filled in by pipeline.")
    sample_label: str | None = Field(None, description="Label used in the paper, e.g. 'E-K46-40'.")
    data_origin: DataOrigin = Field(
        DataOrigin.primary,
        description="primary = measured in this paper; secondary = quoted from another paper (cite it in "
        "sample_label); model = simulation/analytical result.",
    )
    processing: Processing
    structure: Structure
    test: TestCondition
    properties: Properties
    evidence: list[Evidence] = Field(default_factory=list)
    extractor_confidence: float = Field(
        0.5, ge=0, le=1, description="Extractor's own confidence that all values are correct."
    )


class PaperExtraction(BaseModel):
    """Everything extracted from one paper."""

    is_syntactic_foam_paper: bool = Field(description="False if the paper is off-topic (then records is empty).")
    paper_summary: str = Field(description="2-3 sentence summary of materials and findings.")
    records: list[FoamRecord]
    extraction_notes: str | None = Field(None, description="Ambiguities, assumptions, unit conversions made.")


# Flat column order for the curated table.
FLAT_COLUMNS: list[str] = [
    "record_id", "paper_id", "sample_label", "data_origin",
    "matrix_class", "matrix_name", "particle_type", "particle_grade",
    "particle_true_density_g_cc", "particle_mean_diameter_um", "particle_wall_thickness_ratio",
    "particle_volume_fraction", "particle_weight_fraction", "process_route",
    "cure_or_process_temperature_c", "additional_fillers",
    "measured_density_g_cc", "theoretical_density_g_cc", "matrix_porosity_fraction",
    "particle_breakage_fraction",
    "test_type", "strain_rate_per_s", "temperature_c", "standard",
    "modulus_mpa", "strength_mpa", "strain_at_failure", "energy_absorption_mj_m3",
    "plateau_stress_mpa", "densification_strain", "specific_modulus_mpa_per_g_cc",
    "specific_strength_mpa_per_g_cc", "storage_modulus_mpa", "loss_tangent",
    "thermal_conductivity_w_mk", "cte_per_k", "moisture_uptake_pct",
    "extractor_confidence",
]


def flatten(rec: FoamRecord) -> dict:
    d: dict = {"record_id": rec.record_id, "paper_id": rec.paper_id, "sample_label": rec.sample_label,
               "data_origin": rec.data_origin.value}
    for part in (rec.processing, rec.structure, rec.test, rec.properties):
        for k, v in part.model_dump().items():
            if k in FLAT_COLUMNS:
                d[k] = v.value if isinstance(v, Enum) else v
    d["extractor_confidence"] = rec.extractor_confidence
    return d
