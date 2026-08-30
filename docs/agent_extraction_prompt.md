# Agent extraction instructions (FoamGPT, prompt v1.1 — agent lane)

You are extracting quantitative Process–Structure–Property data from ONE syntactic-foam paper.

## Procedure
1. Read the paper text at `data/text/<PAPER_ID>.txt` (page-marked; tables appear between `[TABLE ...]` and `[/TABLE]`).
   Read the WHOLE file; tables near the end matter.
2. Write a single JSON object to `data/extracted/agent/<PAPER_ID>.json` that validates against the schema below.
3. Run `source .venv/bin/activate && python -m foamgpt.extract.agent_collect --check data/extracted/agent/<PAPER_ID>.json`
   and fix any reported problem until it prints `OK`.
4. Return a one-line summary: paper id, is_syntactic_foam_paper, number of records.

## Rules
You are an expert in composite materials, specifically syntactic foams
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

8. data_origin: "primary" only for values the authors measured themselves. Values quoted from other papers
   (review tables, comparison rows) are "secondary" — include the cited reference in sample_label.
   Simulation/analytical results are "model".
9. Leave record_id and paper_id null (the pipeline fills them). Do NOT call any API. Do not read other papers.
10. If the paper is off-topic (no hollow-particle composite data), set is_syntactic_foam_paper=false, records=[].

## Units (schema units — convert!)
modulus/strength: MPa (GPa × 1000) · density: g/cm³ (kg/m³ ÷ 1000) · fractions 0–1 (not %) · strain rate: 1/s · temperature: °C

## JSON Schema
```json
{
 "$defs": {
  "DataOrigin": {
   "enum": [
    "primary",
    "secondary",
    "model"
   ],
   "title": "DataOrigin",
   "type": "string"
  },
  "Evidence": {
   "properties": {
    "quote": {
     "description": "Verbatim snippet (<=300 chars) supporting the values.",
     "title": "Quote",
     "type": "string"
    },
    "location": {
     "description": "Where in the paper, e.g. 'Table 2', 'Fig. 5', 'Sec. 3.2 para 2'.",
     "title": "Location",
     "type": "string"
    }
   },
   "required": [
    "quote",
    "location"
   ],
   "title": "Evidence",
   "type": "object"
  },
  "FoamRecord": {
   "description": "One composition x one test condition.",
   "properties": {
    "record_id": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Filled in by pipeline.",
     "title": "Record Id"
    },
    "paper_id": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "OpenAlex ID, filled in by pipeline.",
     "title": "Paper Id"
    },
    "sample_label": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Label used in the paper, e.g. 'E-K46-40'.",
     "title": "Sample Label"
    },
    "data_origin": {
     "$ref": "#/$defs/DataOrigin",
     "default": "primary",
     "description": "primary = measured in this paper; secondary = quoted from another paper (cite it in sample_label); model = simulation/analytical result."
    },
    "processing": {
     "$ref": "#/$defs/Processing"
    },
    "structure": {
     "$ref": "#/$defs/Structure"
    },
    "test": {
     "$ref": "#/$defs/TestCondition"
    },
    "properties": {
     "$ref": "#/$defs/Properties"
    },
    "evidence": {
     "items": {
      "$ref": "#/$defs/Evidence"
     },
     "title": "Evidence",
     "type": "array"
    },
    "extractor_confidence": {
     "default": 0.5,
     "description": "Extractor's own confidence that all values are correct.",
     "maximum": 1,
     "minimum": 0,
     "title": "Extractor Confidence",
     "type": "number"
    }
   },
   "required": [
    "processing",
    "structure",
    "test",
    "properties"
   ],
   "title": "FoamRecord",
   "type": "object"
  },
  "MatrixClass": {
   "enum": [
    "epoxy",
    "vinyl_ester",
    "polyester",
    "polyurethane",
    "hdpe",
    "pp",
    "pla",
    "other_thermoplastic",
    "other_thermoset",
    "aluminum",
    "magnesium",
    "iron_steel",
    "titanium",
    "zinc",
    "other_metal",
    "cement",
    "other"
   ],
   "title": "MatrixClass",
   "type": "string"
  },
  "ParticleType": {
   "enum": [
    "glass_microballoon",
    "fly_ash_cenosphere",
    "ceramic_hollow",
    "polymer_hollow",
    "carbon_hollow",
    "metal_hollow",
    "other"
   ],
   "title": "ParticleType",
   "type": "string"
  },
  "ProcessRoute": {
   "enum": [
    "mechanical_mixing_cast",
    "vacuum_assisted",
    "compression_molding",
    "injection_molding",
    "extrusion",
    "stir_casting",
    "pressure_infiltration",
    "powder_metallurgy",
    "additive_fdm",
    "additive_dlp_sla",
    "additive_other",
    "other"
   ],
   "title": "ProcessRoute",
   "type": "string"
  },
  "Processing": {
   "properties": {
    "matrix_class": {
     "$ref": "#/$defs/MatrixClass"
    },
    "matrix_name": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Trade name / grade, e.g. 'DGEBA epoxy, EPON 828'.",
     "title": "Matrix Name"
    },
    "particle_type": {
     "$ref": "#/$defs/ParticleType"
    },
    "particle_grade": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Manufacturer grade, e.g. '3M K46', 'S38'.",
     "title": "Particle Grade"
    },
    "particle_true_density_g_cc": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Particle true density, g/cm^3.",
     "title": "Particle True Density G Cc"
    },
    "particle_mean_diameter_um": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Mean diameter, micrometres.",
     "title": "Particle Mean Diameter Um"
    },
    "particle_wall_thickness_ratio": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Radius ratio eta = inner/outer radius (0-1), if reported.",
     "title": "Particle Wall Thickness Ratio"
    },
    "particle_volume_fraction": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Particle volume fraction as a fraction (0-1), NOT percent.",
     "title": "Particle Volume Fraction"
    },
    "particle_weight_fraction": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Weight fraction (0-1), if reported instead.",
     "title": "Particle Weight Fraction"
    },
    "process_route": {
     "$ref": "#/$defs/ProcessRoute"
    },
    "cure_or_process_temperature_c": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Cure / processing temperature, C.",
     "title": "Cure Or Process Temperature C"
    },
    "additional_fillers": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Fibres, nanoclay, rubber, etc.",
     "title": "Additional Fillers"
    }
   },
   "required": [
    "matrix_class",
    "particle_type",
    "process_route"
   ],
   "title": "Processing",
   "type": "object"
  },
  "Properties": {
   "properties": {
    "modulus_mpa": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Elastic modulus for the test type, MPa.",
     "title": "Modulus Mpa"
    },
    "strength_mpa": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Peak / yield strength, MPa.",
     "title": "Strength Mpa"
    },
    "strain_at_failure": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Strain at failure or peak (fraction, 0-1 typical).",
     "title": "Strain At Failure"
    },
    "energy_absorption_mj_m3": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Energy absorbed up to densification or failure, MJ/m^3.",
     "title": "Energy Absorption Mj M3"
    },
    "plateau_stress_mpa": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Plateau Stress Mpa"
    },
    "densification_strain": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Densification Strain"
    },
    "specific_modulus_mpa_per_g_cc": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "modulus / density if reported.",
     "title": "Specific Modulus Mpa Per G Cc"
    },
    "specific_strength_mpa_per_g_cc": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Specific Strength Mpa Per G Cc"
    },
    "storage_modulus_mpa": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "DMA storage modulus, MPa.",
     "title": "Storage Modulus Mpa"
    },
    "loss_tangent": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Loss Tangent"
    },
    "thermal_conductivity_w_mk": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Thermal Conductivity W Mk"
    },
    "cte_per_k": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Coefficient of thermal expansion, 1/K.",
     "title": "Cte Per K"
    },
    "moisture_uptake_pct": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Moisture Uptake Pct"
    }
   },
   "title": "Properties",
   "type": "object"
  },
  "Structure": {
   "properties": {
    "measured_density_g_cc": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Measured bulk density, g/cm^3.",
     "title": "Measured Density G Cc"
    },
    "theoretical_density_g_cc": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Theoretical Density G Cc"
    },
    "matrix_porosity_fraction": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Void (unintended porosity) fraction in matrix (0-1).",
     "title": "Matrix Porosity Fraction"
    },
    "particle_breakage_fraction": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Fraction of particles broken during processing (0-1).",
     "title": "Particle Breakage Fraction"
    },
    "microstructure_notes": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Microstructure Notes"
    }
   },
   "title": "Structure",
   "type": "object"
  },
  "TestCondition": {
   "properties": {
    "test_type": {
     "$ref": "#/$defs/TestType"
    },
    "strain_rate_per_s": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Strain rate, 1/s. Quasi-static ~1e-3.",
     "title": "Strain Rate Per S"
    },
    "temperature_c": {
     "anyOf": [
      {
       "type": "number"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "Test temperature, C. Room temp = 25.",
     "title": "Temperature C"
    },
    "standard": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "description": "e.g. 'ASTM D695'.",
     "title": "Standard"
    },
    "specimen_notes": {
     "anyOf": [
      {
       "type": "string"
      },
      {
       "type": "null"
      }
     ],
     "default": null,
     "title": "Specimen Notes"
    }
   },
   "required": [
    "test_type"
   ],
   "title": "TestCondition",
   "type": "object"
  },
  "TestType": {
   "enum": [
    "compression",
    "tension",
    "flexure",
    "shear",
    "impact",
    "dma",
    "fatigue",
    "hydrostatic",
    "other"
   ],
   "title": "TestType",
   "type": "string"
  }
 },
 "description": "Everything extracted from one paper.",
 "properties": {
  "is_syntactic_foam_paper": {
   "description": "False if the paper is off-topic (then records is empty).",
   "title": "Is Syntactic Foam Paper",
   "type": "boolean"
  },
  "paper_summary": {
   "description": "2-3 sentence summary of materials and findings.",
   "title": "Paper Summary",
   "type": "string"
  },
  "records": {
   "items": {
    "$ref": "#/$defs/FoamRecord"
   },
   "title": "Records",
   "type": "array"
  },
  "extraction_notes": {
   "anyOf": [
    {
     "type": "string"
    },
    {
     "type": "null"
    }
   ],
   "default": null,
   "description": "Ambiguities, assumptions, unit conversions made.",
   "title": "Extraction Notes"
  }
 },
 "required": [
  "is_syntactic_foam_paper",
  "paper_summary",
  "records"
 ],
 "title": "PaperExtraction",
 "type": "object"
}
```
