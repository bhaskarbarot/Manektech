from ontology_service.data_models import (
    SearchCompetencyRequest,
    SearchOccupationRequest,
    SearchRequest,
    SearchResponse,
    SearchResultCompact,
    SearchResultFull,
)

from .ontology_service import OntologyService, public

COMPETENCY_CLASSES = ["skill", "competency"]
OCCUPATION_CLASS = "occupation"
REQUIRES = "https://objectiveye.ai/oe-ontology/competencyframework/requires"


class CompetencyService(OntologyService):
    def search_competency(self, request: SearchCompetencyRequest) -> SearchResponse:
        return self._search(request, {"class": COMPETENCY_CLASSES} | (request.filters or {}))

    def search_occupation(self, request: SearchOccupationRequest) -> SearchResponse:
        return self._search(request, (request.filters or {}) | {"class": OCCUPATION_CLASS})

    def required_competencies(self, occupation_uri: str) -> list[dict]:
        return self.store.get_linked_entities(occupation_uri, [REQUIRES], "out", {"class": COMPETENCY_CLASSES})

    def _search(self, request: SearchRequest, filters: dict) -> SearchResponse:
        hits = self.store.vector_search(request.query, filters, request.limit or 10)
        result_type = SearchResultFull if request.response_format == "full" else SearchResultCompact
        return SearchResponse(
            results=[result_type.model_validate(public(hit) | {"similarity_score": hit["score"]}) for hit in hits]
        )
