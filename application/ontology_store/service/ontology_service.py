from typing import Any

from pydantic import ValidationError

from ontology_service.data_models import (
    AddEntityResponse,
    BrowseEntitiesRequest,
    BrowseEntitiesResponse,
    BrowseEntityCompact,
    BrowseEntityFull,
    DeleteByMetadataRequest,
    DeleteResponse,
    EntityResponse,
    GetEntityRequest,
    QueryEntitiesRequest,
    QueryEntitiesResponse,
    QueryRelationshipsRequest,
    TripleIngestManyRequest,
    TripleIngestManyResponse,
)

from ..store.errors import OntologyStoreError
from ..store.interface import OntologyStore
from ..store.models import CanonicalEntity, CanonicalRelationship

INTERNAL_KEYS = ("dataset_id", "score")


def public(record: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k not in INTERNAL_KEYS}


class OntologyService:
    def __init__(self, store: OntologyStore):
        self.store = store

    def get_entity(self, request: GetEntityRequest) -> EntityResponse:
        record = self.store.get_entity(request.uri)
        return EntityResponse(entity=public(record) if record else None)

    def browse_entities(self, request: BrowseEntitiesRequest) -> BrowseEntitiesResponse:
        page_size = request.page_size or 25
        records = self.store.browse_entities(request.page_number, page_size, request.filters)
        item_type = BrowseEntityFull if request.response_format == "full" else BrowseEntityCompact
        items = [item_type.model_validate(r) for r in records]
        return BrowseEntitiesResponse(page_number=request.page_number, page_size=page_size, returned=len(items), items=items)

    def query_entities(self, request: QueryEntitiesRequest) -> QueryEntitiesResponse:
        items = [public(r) for r in self.store.query_entities(request.filters, request.limit)]
        return QueryEntitiesResponse(items=items, total=self.store.count_entities(request.filters))

    def query_relationships(self, request: QueryRelationshipsRequest) -> QueryEntitiesResponse:
        items = [public(r) for r in self.store.query_relationships(request.filters, request.limit)]
        return QueryEntitiesResponse(items=items, total=self.store.count_relationships(request.filters))

    def add_entity(self, entity: dict[str, Any]) -> AddEntityResponse:
        try:
            record = CanonicalEntity.model_validate(entity)
        except ValidationError:
            return AddEntityResponse(success=False, metadata=None)
        self.store.import_entities([record])
        self.store.rebuild_embeddings([record.uri])
        return AddEntityResponse(success=True, metadata={"embedded_text": self.store.embedded_text(record.uri)})

    def add_relationships(self, request: TripleIngestManyRequest) -> TripleIngestManyResponse:
        records = [
            CanonicalRelationship(
                subject_uri=item.subject_uri,
                predicate_uri=item.predicate_uri,
                object_uri=item.object_uri,
                metadata=item.metadata or {},
            )
            for item in request.items
        ]
        result = self.store.import_relationships(records, check_entities_exist=request.check_entities_exist)
        return TripleIngestManyResponse(
            success=result.failed == 0, inserted=result.inserted, failed=result.failed, errors=result.errors
        )

    def delete_by_metadata(self, request: DeleteByMetadataRequest) -> DeleteResponse:
        try:
            deleted = self.store.delete_by_metadata(request.filters)
        except OntologyStoreError as exc:
            return DeleteResponse(success=False, deleted=0, error=str(exc))
        return DeleteResponse(success=True, deleted=deleted)
