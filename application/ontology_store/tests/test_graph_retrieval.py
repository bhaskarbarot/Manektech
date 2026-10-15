import pytest

from ontology_store.service.competency_service import CompetencyService

from .conftest import ANALYTICAL, DATA_ANALYSIS, DATA_SCIENTIST, RELATED_TO, REQUIRES, SOFTWARE_DEVELOPER


def test_query_by_subject(store):
    rels = store.query_relationships({"subject_uri": SOFTWARE_DEVELOPER})
    assert len(rels) == 4
    assert {r["predicate_uri"] for r in rels} == {REQUIRES}


def test_query_by_predicate(store):
    assert len(store.query_relationships({"predicate_uri": RELATED_TO})) == 5


def test_query_by_object(store):
    subjects = {r["subject_uri"] for r in store.query_relationships({"object_uri": ANALYTICAL})}
    assert DATA_SCIENTIST in subjects and DATA_ANALYSIS in subjects
    assert len(subjects) == 3


def test_query_limit(store):
    assert len(store.query_relationships({"predicate_uri": REQUIRES}, limit=2)) == 2


def test_relationship_metadata_is_kept(store):
    rel = store.query_relationships({"subject_uri": SOFTWARE_DEVELOPER, "object_uri": "http://example.org/esco/skill/sql-gebruiken"})
    assert rel[0]["metadata"] == {"relevance": "optional", "source": "seed"}


def test_neighbours_in_both_directions(store):
    found = {(n["direction"], n["label"]) for n in store.get_neighbours(DATA_ANALYSIS)}
    assert found == {("out", "analytisch vermogen"), ("in", "data scientist")}


def test_neighbours_filtered_by_predicate(store):
    found = store.get_neighbours(DATA_ANALYSIS, predicates=[RELATED_TO])
    assert [n["label"] for n in found] == ["analytisch vermogen"]


def test_neighbours_bad_direction(store):
    with pytest.raises(ValueError):
        store.get_neighbours(DATA_ANALYSIS, direction="sideways")


def test_competencies_required_by_occupation(store):
    required = CompetencyService(store).required_competencies(DATA_SCIENTIST)
    assert {r["label"] for r in required} == {
        "programmeren in Python",
        "machine learning toepassen",
        "data analyseren",
        "analytisch vermogen",
        "communicatieve vaardigheden",
    }
    optional = [r["label"] for r in required if r["relationship_metadata"]["relevance"] == "optional"]
    assert optional == ["communicatieve vaardigheden"]


def test_linked_entities_incoming(store):
    occupations = store.get_linked_entities(ANALYTICAL, [REQUIRES], direction="in")
    assert [o["label"] for o in occupations] == ["data scientist"]
