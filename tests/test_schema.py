from foamgpt.schema import FLAT_COLUMNS, FoamRecord, PaperExtraction, flatten


def _rec():
    return FoamRecord.model_validate({
        "sample_label": "E-K46-40",
        "processing": {"matrix_class": "epoxy", "particle_type": "glass_microballoon",
                       "particle_grade": "3M K46", "particle_volume_fraction": 0.4,
                       "process_route": "mechanical_mixing_cast"},
        "structure": {"measured_density_g_cc": 0.78},
        "test": {"test_type": "compression", "strain_rate_per_s": 1e-3},
        "properties": {"modulus_mpa": 2100, "strength_mpa": 62},
        "evidence": [{"quote": "K46/40 ... 62 MPa", "location": "Table 2"}],
        "extractor_confidence": 0.9,
    })


def test_flatten_columns():
    d = flatten(_rec())
    assert set(d) <= set(FLAT_COLUMNS)
    assert d["matrix_class"] == "epoxy"
    assert d["strength_mpa"] == 62


def test_paper_extraction_schema_is_json_schema():
    s = PaperExtraction.model_json_schema()
    assert "records" in s["properties"]


def test_curation_flags():
    import pandas as pd

    from foamgpt.curate.normalize import _flags
    row = pd.Series({"particle_volume_fraction": 40, "modulus_mpa": 2.1, "matrix_class": "epoxy"})
    f = _flags(row)
    assert "particle_volume_fraction_looks_like_percent" in f
    assert "modulus_maybe_gpa" in f
