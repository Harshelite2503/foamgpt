from foamgpt.harvest.openalex import _reconstruct_abstract, _slim


def test_reconstruct_abstract():
    inv = {"foam": [1], "Syntactic": [0], "rocks": [2]}
    assert _reconstruct_abstract(inv) == "Syntactic foam rocks"


def test_slim():
    w = {"id": "https://openalex.org/W1", "doi": "x", "title": "t", "publication_year": 2020,
         "cited_by_count": 3, "type": "article", "open_access": {"is_oa": True},
         "best_oa_location": {"pdf_url": "u"}, "primary_location": {"source": {"display_name": "J"}},
         "authorships": [{"author": {"display_name": "N Gupta"}}], "abstract": "a", "concepts": []}
    s = _slim(w)
    assert s["id"] == "W1" and s["oa_pdf_url"] == "u" and s["venue"] == "J"
