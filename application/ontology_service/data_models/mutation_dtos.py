"""
Mutation operations data transfer objects.

DTOs for adding and deleting entities and relationships.
Tags: add, delete
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


# =============================================================================
# Add Operations
# =============================================================================


class AddEntityResponse(BaseModel):
    """Response from adding an entity."""

    success: bool
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "openapi_examples": {
                "success": {
                    "summary": "Entity added successfully",
                    "value": {
                        "success": True,
                        "metadata": {
                            "embedded_text": "test competency Test skill for documentation examples."
                        },
                    },
                },
                "failure": {
                    "summary": "Entity addition failed",
                    "value": {"success": False, "metadata": None},
                },
            }
        },
    )


class TripleIngestItem(BaseModel):
    """Single relationship triple for ingestion."""

    subject_uri: str
    predicate_uri: str
    object_uri: str
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "openapi_examples": {
                "occupation_requires_skill": {
                    "summary": "Occupation requires a competency",
                    "value": {
                        "subject_uri": "http://data.europa.eu/esco/occupation/00030d09-2b3a-4efd-87cc-c4ea39d27c34",
                        "predicate_uri": "https://objectiveye.ai/oe-ontology/competencyframework/requires",
                        "object_uri": "http://data.europa.eu/esco/skill/0005c151-5b5a-4a66-8aac-60e734beb1ab",
                        "metadata": {"source": "manual", "confidence": 0.95},
                    },
                },
            }
        }
    )


class TripleIngestManyRequest(BaseModel):
    """Bulk relationship ingestion request."""

    items: List[TripleIngestItem]
    check_entities_exist: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "openapi_examples": {
                "add_occupation_competencies": {
                    "summary": "Link occupation to required competencies",
                    "value": {
                        "items": [
                            {
                                "subject_uri": "http://data.europa.eu/esco/occupation/00030d09-2b3a-4efd-87cc-c4ea39d27c34",
                                "predicate_uri": "https://objectiveye.ai/oe-ontology/competencyframework/requires",
                                "object_uri": "http://data.europa.eu/esco/skill/0005c151-5b5a-4a66-8aac-60e734beb1ab",
                                "metadata": {"source": "docs_example", "test": True},
                            },
                            {
                                "subject_uri": "http://data.europa.eu/esco/occupation/00030d09-2b3a-4efd-87cc-c4ea39d27c34",
                                "predicate_uri": "https://objectiveye.ai/oe-ontology/competencyframework/requires",
                                "object_uri": "http://data.europa.eu/esco/skill/00064735-8fad-454b-90c7-ed858cc993f2",
                                "metadata": {"source": "docs_example", "test": True},
                            },
                        ],
                        "check_entities_exist": True,
                    },
                },
                "link_related_competencies": {
                    "summary": "Mark competencies as related",
                    "value": {
                        "items": [
                            {
                                "subject_uri": "http://data.europa.eu/esco/skill/0005c151-5b5a-4a66-8aac-60e734beb1ab",
                                "predicate_uri": "https://objectiveye.ai/oe-ontology/competencyframework/relatedTo",
                                "object_uri": "http://data.europa.eu/esco/skill/00064735-8fad-454b-90c7-ed858cc993f2",
                                "metadata": {"source": "docs_example", "test": True},
                            },
                        ],
                        "check_entities_exist": True,
                    },
                },
            }
        }
    )


class TripleIngestManyResponse(BaseModel):
    """Response from bulk relationship ingestion."""

    success: bool
    inserted: int
    failed: int
    errors: List[Dict[str, Any]]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"success": True, "inserted": 2, "failed": 0, "errors": []},
                {
                    "success": False,
                    "inserted": 1,
                    "failed": 1,
                    "errors": [{"index": 1, "error": "subject_uri not found"}],
                },
            ]
        }
    )


# =============================================================================
# Delete Operations
# =============================================================================


class DeleteByMetadataRequest(BaseModel):
    """Request to delete entities or relationships by metadata filters."""

    filters: Dict[str, Any]

    model_config = ConfigDict(
        json_schema_extra={
            "openapi_examples": {
                "cleanup_docs_examples": {
                    "summary": "Delete documentation example data",
                    "description": "Removes relationships added via docs examples (matches add examples above)",
                    "value": {
                        "filters": {
                            "metadata": {"source": "docs_example", "test": True}
                        }
                    },
                },
                "delete_test_framework": {
                    "summary": "Delete all TEST framework entities",
                    "value": {"filters": {"framework": "TEST"}},
                },
                "cleanup_by_run_id": {
                    "summary": "Delete test run data",
                    "value": {"filters": {"metadata": {"run_id": "test_12345"}}},
                },
            }
        }
    )


class DeleteResponse(BaseModel):
    """Response from delete operation."""

    success: bool
    deleted: int
    error: str = ""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"success": True, "deleted": 3, "error": ""},
                {"success": False, "deleted": 0, "error": "Permission denied"},
            ]
        }
    )
