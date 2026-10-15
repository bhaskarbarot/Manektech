from .search_dtos import (
    SearchRequest,
    SearchCompetencyRequest,
    SearchOccupationRequest,
    SearchResponse,
    SearchResultCompact,
    SearchResultFull,
    VacancyTextRequest,
    ExtractedCompetency,
    SkillExtractionResponse,
)

from .browse_dtos import (
    BrowseEntitiesRequest,
    BrowseEntitiesResponse,
    BrowseEntityCompact,
    BrowseEntityFull,
)

from .query_dtos import (
    GetEntityRequest,
    EntityResponse,
    QueryEntitiesRequest,
    QueryRelationshipsRequest,
    QueryEntitiesResponse,
)

from .mutation_dtos import (
    AddEntityResponse,
    TripleIngestItem,
    TripleIngestManyRequest,
    TripleIngestManyResponse,
    DeleteByMetadataRequest,
    DeleteResponse,
)


__all__ = [
    # Search
    "SearchRequest",
    "SearchCompetencyRequest",
    "SearchOccupationRequest",
    "SearchResponse",
    "SearchResultCompact",
    "SearchResultFull",
    "VacancyTextRequest",
    "ExtractedCompetency",
    "SkillExtractionResponse",
    # Browse
    "BrowseEntitiesRequest",
    "BrowseEntitiesResponse",
    "BrowseEntityCompact",
    "BrowseEntityFull",
    # Query
    "GetEntityRequest",
    "EntityResponse",
    "QueryEntitiesRequest",
    "QueryRelationshipsRequest",
    "QueryEntitiesResponse",
    # Mutation
    "AddEntityResponse",
    "TripleIngestItem",
    "TripleIngestManyRequest",
    "TripleIngestManyResponse",
    "DeleteByMetadataRequest",
    "DeleteResponse",
]
