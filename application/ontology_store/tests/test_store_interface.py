import pytest

from ontology_store.store.errors import InvalidFilterError

from .conftest import PYTHON


def test_get_entity_returns_full_record(store):
    entity = store.get_entity(PYTHON)
    assert entity["label"] == "programmeren in Python"
    assert entity["class"] == "skill"
    assert entity["framework"] == "ESCO"
    assert entity["id"] == "esco:skill:python-programmeren"
    assert entity["metadata"]["skillType"] == "skill/competence"


def test_get_entity_unknown_uri(store):
    assert store.get_entity("http://example.org/nothing") is None


def test_query_by_class(store):
    assert len(store.query_entities({"class": "occupation"})) == 4


def test_query_by_framework_and_language(store):
    labels = {e["label"] for e in store.query_entities({"framework": "ESCO", "language": "en"})}
    assert labels == {"data engineer"}


def test_query_by_list_value(store):
    assert len(store.query_entities({"class": ["skill", "competency"]})) == 12


def test_query_by_metadata(store):
    assert len(store.query_entities({"metadata": {"skillType": "skill/competence"}})) == 8


def test_query_by_group(store):
    assert {e["label"] for e in store.query_entities({"group": "Denken"})} == {"probleemoplossend vermogen", "analytisch vermogen"}


def test_query_limit_and_count(store):
    assert len(store.query_entities({"class": "skill"}, limit=3)) == 3
    assert store.count_entities({"class": "skill"}) == 8


def test_unknown_filter_is_rejected(store):
    with pytest.raises(InvalidFilterError, match="unknown filter 'colour'"):
        store.query_entities({"colour": "blue"})


def test_metadata_filter_must_be_object(store):
    with pytest.raises(InvalidFilterError):
        store.query_entities({"metadata": "seed"})


def test_browse_pages_cover_everything_once(store):
    pages = [store.browse_entities(page, 5) for page in range(1, 5)]
    assert [len(p) for p in pages] == [5, 5, 5, 1]
    uris = [e["uri"] for page in pages for e in page]
    assert len(set(uris)) == 16


def test_browse_with_filter(store):
    page = store.browse_entities(1, 25, {"framework": "FGR"})
    assert {e["framework"] for e in page} == {"FGR"}


def test_browse_rejects_bad_page(store):
    with pytest.raises(ValueError):
        store.browse_entities(0, 10)
    with pytest.raises(ValueError):
        store.browse_entities(1, 10_000)
