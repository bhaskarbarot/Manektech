from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CanonicalEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    uri: str = Field(min_length=1)
    id: str | None = None
    class_: str = Field(alias="class", min_length=1)
    framework: str | None = None
    label: str = Field(min_length=1)
    description: str | None = None
    language: str | None = None
    group: str | None = None
    subgroup: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CanonicalRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_uri: str = Field(min_length=1)
    predicate_uri: str = Field(min_length=1)
    object_uri: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DatasetManifest(BaseModel):
    name: str = Field(pattern=r"^[\w.\-]+$")
    version: str = Field(pattern=r"^[\w.\-]+$")
    source: str | None = None
    description: str | None = None
    files: dict[str, str] = Field(default_factory=lambda: {"entities": "entities.jsonl", "relationships": "relationships.jsonl"})
    record_counts: dict[str, int] = Field(default_factory=dict)

    @property
    def dataset_id(self) -> str:
        return f"{self.name}@{self.version}"


@dataclass
class ImportResult:
    inserted: int = 0
    failed: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
