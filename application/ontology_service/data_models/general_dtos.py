from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class BrowseEntitiesRequest(BaseModel):
    page_number: int  # 1-based
    page_size: Optional[int] = 25
    filters: Optional[Dict[str, Any]] = None
    response_format: Optional[str] = "compact"

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"page_number": 1},
                {"page_number": 2, "page_size": 50},
                {
                    "page_number": 1,
                    "filters": {"class": "competency"},
                    "response_format": "compact",
                },
                {
                    "page_number": 1,
                    "filters": {"framework": "FGR"},
                    "response_format": "full",
                },
            ]
        }
    )


class BrowseEntityCompact(BaseModel):
    class_: Optional[str] = Field(default=None, alias="class")
    framework: Optional[str] = None
    uri: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class BrowseEntityFull(BaseModel):
    id: Optional[str] = None
    class_: Optional[str] = Field(default=None, alias="class")
    framework: Optional[str] = None
    uri: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    group: Optional[str] = None
    subgroup: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True)


class BrowseEntitiesResponse(BaseModel):
    page_number: int
    page_size: int
    returned: int
    items: List[Union[BrowseEntityCompact, BrowseEntityFull]]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "page_number": 1,
                    "page_size": 25,
                    "returned": 1,
                    "items": [
                        {
                            "class": "competency",
                            "framework": "OE_TEST",
                            "uri": "https://objectiveye.ai/test/competency/...",
                            "label": "Analytical thinking",
                            "description": "Structure problems and evaluate options.",
                        }
                    ],
                }
            ]
        }
    )


class GetEntityRequest(BaseModel):
    uri: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "uri": (
                        "https://objectiveye.ai/test/competency/" "analytical-thinking"
                    )
                }
            ]
        }
    )


class EntityResponse(BaseModel):
    entity: Optional[Dict[str, Any]]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "entity": {
                        "id": "oe:test:1",
                        "uri": (
                            "https://objectiveye.ai/test/competency/"
                            "analytical-thinking"
                        ),
                        "label": "Analytical thinking",
                    }
                },
                {"entity": None},
            ]
        }
    )


# Filter query DTOs
class QueryEntitiesRequest(BaseModel):
    filters: Dict[str, Any]
    limit: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"filters": {"class": "competency"}, "limit": 10},
                {"filters": {"framework": "OE_TEST"}},
                {"filters": {"metadata": {"run_id": "demo"}}, "limit": 50},
            ]
        }
    )


class QueryEntitiesResponse(BaseModel):
    items: List[Dict[str, Any]]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {
                            "id": "oe:test:1",
                            "class": "competency",
                            "label": "Analytical thinking",
                        }
                    ]
                }
            ]
        }
    )


# Ingest DTOs
class AddEntityResponse(BaseModel):
    success: bool
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "metadata": {"embedded_text": "Analytical thinking"},
                },
                {"success": False, "metadata": None},
            ]
        },
    )


class TripleIngestItem(BaseModel):
    subject_uri: str
    predicate_uri: str
    object_uri: str
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "subject_uri": ("https://objectiveye.ai/occupation/mlops-engineer"),
                    "predicate_uri": (
                        "https://objectiveye.ai/oe-ontology/"
                        "competencyframework/requires"
                    ),
                    "object_uri": (
                        "https://objectiveye.ai/competency/data-engineering"
                    ),
                    "metadata": {"source": "seed", "confidence": 0.95},
                }
            ]
        }
    )


class TripleIngestOneResponse(BaseModel):
    success: bool
    error: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"success": True}, {"success": False, "error": "..."}]
        }
    )


class TripleIngestManyRequest(BaseModel):
    items: List[TripleIngestItem]
    check_entities_exist: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {
                            "subject_uri": (
                                "https://objectiveye.ai/occupation/"
                                "mlops-engineer"
                            ),
                            "predicate_uri": (
                                "https://objectiveye.ai/oe-ontology/"
                                "competencyframework/requires"
                            ),
                            "object_uri": (
                                "https://objectiveye.ai/competency/"
                                "data-engineering"
                            ),
                            "metadata": {"source": "seed"},
                        },
                        {
                            "subject_uri": (
                                "https://objectiveye.ai/occupation/"
                                "mlops-engineer"
                            ),
                            "predicate_uri": (
                                "https://objectiveye.ai/oe-ontology/"
                                "competencyframework/requires"
                            ),
                            "object_uri": (
                                "https://objectiveye.ai/competency/"
                                "vector-search"
                            ),
                            "metadata": {"source": "seed"},
                        },
                    ],
                    "check_entities_exist": True,
                }
            ]
        }
    )


class TripleIngestManyResponse(BaseModel):
    success: bool
    inserted: int
    failed: int
    errors: List[Dict[str, Any]]  # {"index": i, "error": "..."}

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"success": True, "inserted": 1, "failed": 0, "errors": []},
                {
                    "success": False,
                    "inserted": 0,
                    "failed": 1,
                    "errors": [{"index": 0, "error": "..."}],
                },
            ]
        }
    )


# Delete DTOs
class DeleteByMetadataRequest(BaseModel):
    filters: Dict[str, Any]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"filters": {"metadata": {"run_id": "demo"}}},
                {"filters": {"framework": "OE_TEST"}},
            ]
        }
    )


class DeleteResponse(BaseModel):
    success: bool
    deleted: int
    error: str = ""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"success": True, "deleted": 3, "error": ""},
                {"success": False, "deleted": 0, "error": "..."},
            ]
        }
    )
