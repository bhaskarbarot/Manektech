from ontology_service.data_models import (
    BrowseEntitiesRequest,
    BrowseEntityFull,
    DeleteByMetadataRequest,
    GetEntityRequest,
    QueryEntitiesRequest,
    QueryRelationshipsRequest,
    SearchCompetencyRequest,
    SearchOccupationRequest,
    SearchResultCompact,
    SearchResultFull,
    TripleIngestItem,
    TripleIngestManyRequest,
)
from ontology_store.service.competency_service import CompetencyService

from .conftest import PYTHON, REQUIRES, SOFTWARE_DEVELOPER


def test_search_competency_only_returns_skills_and_competencies(store):
    response = CompetencyService(store).search_competency(SearchCompetencyRequest(query="data", limit=20))
    assert response.results
    assert all(isinstance(r, SearchResultCompact) for r in response.results)
    assert {r.class_ for r in response.results} <= {"skill", "competency"}
    assert all(r.similarity_score is not None for r in response.results)


def test_search_competency_keeps_caller_filters(store):
    request = SearchCompetencyRequest(query="vermogen", filters={"framework": "FGR"}, limit=10)
    response = CompetencyService(store).search_competency(request)
    assert {r.framework for r in response.results} == {"FGR"}


def test_search_occupation_full_format(store):
    request = SearchOccupationRequest(query="softwareontwikkelaar", response_format="full")
    response = CompetencyService(store).search_occupation(request)
    assert isinstance(response.results[0], SearchResultFull)
    assert response.results[0].uri == SOFTWARE_DEVELOPER
    assert {r.class_ for r in response.results} == {"occupation"}


def test_get_entity_response(store):
    service = CompetencyService(store)
    assert service.get_entity(GetEntityRequest(uri=PYTHON)).entity["label"] == "programmeren in Python"
    assert "dataset_id" not in service.get_entity(GetEntityRequest(uri=PYTHON)).entity
    assert service.get_entity(GetEntityRequest(uri="http://example.org/none")).entity is None


def test_browse_full_format(store):
    response = CompetencyService(store).browse_entities(BrowseEntitiesRequest(page_number=1, page_size=3, response_format="full"))
    assert (response.page_number, response.page_size, response.returned) == (1, 3, 3)
    assert all(isinstance(item, BrowseEntityFull) for item in response.items)


def test_query_entities_total(store):
    response = CompetencyService(store).query_entities(QueryEntitiesRequest(filters={"class": "skill"}, limit=2))
    assert len(response.items) == 2
    assert response.total == 8


def test_query_relationships_total_ignores_limit(store):
    request = QueryRelationshipsRequest(filters={"predicate_uri": REQUIRES}, limit=2)
    response = CompetencyService(store).query_relationships(request)
    assert len(response.items) == 2
    assert response.total == 14


def test_add_entity_returns_embedded_text(store):
    response = CompetencyService(store).add_entity(
        {"uri": "http://example.org/test/competency/x", "class": "competency", "framework": "TEST",
         "label": "test competency", "description": "Test skill for documentation examples."}
    )
    assert response.success
    assert response.metadata == {"embedded_text": "test competency Test skill for documentation examples."}
    assert store.vector_search("test competency", {"framework": "TEST"})[0]["label"] == "test competency"


def test_add_entity_rejects_invalid_record(store):
    assert CompetencyService(store).add_entity({"uri": "http://example.org/x"}).success is False


def test_add_relationships_reports_failures(store):
    request = TripleIngestManyRequest(items=[
        TripleIngestItem(subject_uri=SOFTWARE_DEVELOPER, predicate_uri=REQUIRES, object_uri=PYTHON, metadata={"source": "api"}),
        TripleIngestItem(subject_uri=SOFTWARE_DEVELOPER, predicate_uri=REQUIRES, object_uri="http://example.org/none"),
    ])
    response = CompetencyService(store).add_relationships(request)
    assert (response.success, response.inserted, response.failed) == (False, 1, 1)
    assert response.errors[0]["index"] == 1


def test_delete_by_metadata_response(store):
    service = CompetencyService(store)
    ok = service.delete_by_metadata(DeleteByMetadataRequest(filters={"metadata": {"mapping": "close"}}))
    assert (ok.success, ok.deleted) == (True, 2)
    bad = service.delete_by_metadata(DeleteByMetadataRequest(filters={"colour": "blue"}))
    assert bad.success is False and bad.deleted == 0 and bad.error
