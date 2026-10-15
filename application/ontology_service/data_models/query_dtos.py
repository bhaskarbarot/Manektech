"""
Query operations data transfer objects.

DTOs for querying entities and relationships by URI, filters, or connections.
Tag: query
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class GetEntityRequest(BaseModel):
    """Request to get a specific entity by URI."""

    uri: str

    model_config = ConfigDict(
        json_schema_extra={
            "openapi_examples": {
                "lookup_music_management_skill": {
                    "summary": "Lookup: muziekpersoneel managen",
                    "description": "Get ESCO skill by URI",
                    "value": {
                        "uri": "http://data.europa.eu/esco/skill/0005c151-5b5a-4a66-8aac-60e734beb1ab"
                    },
                },
                "lookup_technical_director_occupation": {
                    "summary": "Lookup: inspiciënt (technical director)",
                    "description": "Get ESCO occupation by URI",
                    "value": {
                        "uri": "http://data.europa.eu/esco/occupation/00030d09-2b3a-4efd-87cc-c4ea39d27c34"
                    },
                },
                "lookup_correctional_procedures_skill": {
                    "summary": "Lookup: correctionele procedures overzien",
                    "description": "Get another ESCO skill by URI",
                    "value": {
                        "uri": "http://data.europa.eu/esco/skill/00064735-8fad-454b-90c7-ed858cc993f2"
                    },
                },
            }
        }
    )


class EntityResponse(BaseModel):
    """Response containing a single entity."""

    entity: Optional[Dict[str, Any]]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "entity": {
                        "id": "esco:skill:0005c151-5b5a-4a66-8aac-60e734beb1ab",
                        "class": "competency",
                        "uri": "http://data.europa.eu/esco/skill/0005c151-5b5a-4a66-8aac-60e734beb1ab",
                        "label": "muziekpersoneel managen",
                        "description": "Toewijzen en beheren van taken van het personeel op gebieden zoals scoring, het organiseren, kopiëren van muziek en vocale coaching.",
                        "framework": "ESCO",
                        "language": "nl",
                        "attributes": {},
                        "metadata": {
                            "status": "released",
                            "skillType": "skill/competence",
                        },
                    }
                },
                {"entity": None},
            ]
        }
    )


class QueryEntitiesRequest(BaseModel):
    """Request to query entities by metadata filters."""

    filters: Dict[str, Any]
    limit: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "openapi_examples": {
                "filter_competencies": {
                    "summary": "Find all competencies",
                    "description": "Query entities table by class",
                    "value": {"filters": {"class": "competency"}, "limit": 10},
                },
                "filter_esco_dutch": {
                    "summary": "Find ESCO entities in Dutch",
                    "description": "Query entities by framework and language",
                    "value": {"filters": {"framework": "ESCO", "language": "nl"}},
                },
                "filter_by_metadata": {
                    "summary": "Find entities by metadata",
                    "description": "Query entities by JSON metadata",
                    "value": {"filters": {"metadata": {"source": "seed"}}, "limit": 25},
                },
            }
        }
    )


class QueryRelationshipsRequest(BaseModel):
    """Request to query relationships (triples) by filters."""

    filters: Dict[str, Any]
    limit: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "openapi_examples": {
                "find_requires_relationships": {
                    "summary": "Find 'requires' relationships",
                    "description": "Query triples table by predicate",
                    "value": {
                        "filters": {
                            "predicate_uri": "https://objectiveye.ai/oe-ontology/competencyframework/requires"
                        },
                        "limit": 10,
                    },
                },
                "find_relationships_for_occupation": {
                    "summary": "Find relationships for specific occupation",
                    "description": "Query triples by subject_uri",
                    "value": {
                        "filters": {
                            "subject_uri": "http://data.europa.eu/esco/occupation/00030d09-2b3a-4efd-87cc-c4ea39d27c34"
                        },
                        "limit": 50,
                    },
                },
                "find_relationships_for_competency": {
                    "summary": "Find relationships for specific competency",
                    "description": "Query triples by object_uri",
                    "value": {
                        "filters": {
                            "object_uri": "http://data.europa.eu/esco/skill/0005c151-5b5a-4a66-8aac-60e734beb1ab"
                        },
                        "limit": 50,
                    },
                },
            }
        }
    )


class QueryEntitiesResponse(BaseModel):
    """Response containing queried entities."""

    items: List[Dict[str, Any]]
    total: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {
                            "id": "esco:skill:0005c151-5b5a-4a66-8aac-60e734beb1ab",
                            "class": "competency",
                            "uri": "http://data.europa.eu/esco/skill/0005c151-5b5a-4a66-8aac-60e734beb1ab",
                            "label": "muziekpersoneel managen",
                            "framework": "ESCO",
                            "language": "nl",
                        }
                    ],
                    "total": 1,
                }
            ]
        }
    )
