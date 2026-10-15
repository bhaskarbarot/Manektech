"""
Browse operations data transfer objects.

DTOs for entity browsing with pagination and filtering.
Tag: browse
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class BrowseEntitiesRequest(BaseModel):
    """Request for browsing entities with pagination."""

    page_number: int  # 1-based
    page_size: Optional[int] = 25
    filters: Optional[Dict[str, Any]] = None
    response_format: Optional[str] = "compact"

    model_config = ConfigDict(
        json_schema_extra={
            "openapi_examples": {
                "simple_browse": {
                    "summary": "Simple browse (defaults)",
                    "value": {"page_number": 1},
                },
                "custom_page_size": {
                    "summary": "Custom page size",
                    "value": {"page_number": 2, "page_size": 50},
                },
                "filter_competencies": {
                    "summary": "Browse competencies only",
                    "value": {
                        "page_number": 1,
                        "filters": {"class": "competency"},
                        "response_format": "compact",
                    },
                },
                "filter_framework_full": {
                    "summary": "ESCO entities with full details",
                    "value": {
                        "page_number": 1,
                        "filters": {"framework": "ESCO"},
                        "response_format": "full",
                    },
                },
            }
        }
    )


class BrowseEntityCompact(BaseModel):
    """Compact entity representation for browse results."""

    class_: Optional[str] = Field(default=None, alias="class")
    framework: Optional[str] = None
    uri: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class BrowseEntityFull(BaseModel):
    """Full entity representation for browse results."""

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
    """Response for browse entities operation."""

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
                    "returned": 2,
                    "items": [
                        {
                            "class": "competency",
                            "framework": "ESCO",
                            "uri": "http://data.europa.eu/esco/skill/0005c151-5b5a-4a66-8aac-60e734beb1ab",
                            "label": "muziekpersoneel managen",
                            "description": "Toewijzen en beheren van taken van het personeel op gebieden zoals scoring, het organiseren, kopiëren van muziek en vocale coaching.",
                        },
                        {
                            "class": "occupation",
                            "framework": "ESCO",
                            "uri": "http://data.europa.eu/esco/occupation/00030d09-2b3a-4efd-87cc-c4ea39d27c34",
                            "label": "inspiciënt",
                            "description": "Technische directeuren realiseren zich binnen technische beperkingen de artistieke visies van de makers.",
                        },
                    ],
                }
            ]
        }
    )
