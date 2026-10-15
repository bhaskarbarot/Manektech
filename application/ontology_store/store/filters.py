from collections.abc import Mapping
from typing import Any

from sqlalchemy import ColumnElement

from ..db.models import Entity, Relationship
from .errors import InvalidFilterError

ENTITY_FILTERS = {
    "uri": Entity.uri,
    "id": Entity.entity_id,
    "class": Entity.entity_class,
    "framework": Entity.framework,
    "language": Entity.language,
    "group": Entity.group_name,
    "subgroup": Entity.subgroup_name,
    "dataset_id": Entity.dataset_id,
}

RELATIONSHIP_FILTERS = {
    "subject_uri": Relationship.subject_uri,
    "predicate_uri": Relationship.predicate_uri,
    "object_uri": Relationship.object_uri,
    "dataset_id": Relationship.dataset_id,
}


def _conditions(filters: Mapping[str, Any] | None, columns: dict, metadata_column) -> list[ColumnElement[bool]]:
    conditions = []
    for key, value in (filters or {}).items():
        if key == "metadata":
            if not isinstance(value, Mapping):
                raise InvalidFilterError("metadata filter must be an object, e.g. {\"metadata\": {\"source\": \"seed\"}}")
            conditions.append(metadata_column.contains(dict(value)))
            continue
        column = columns.get(key)
        if column is None:
            allowed = ", ".join(sorted([*columns, "metadata"]))
            raise InvalidFilterError(f"unknown filter '{key}', allowed filters: {allowed}")
        if isinstance(value, (list, tuple, set)):
            conditions.append(column.in_(list(value)))
        elif value is None:
            conditions.append(column.is_(None))
        else:
            conditions.append(column == value)
    return conditions


def entity_conditions(filters: Mapping[str, Any] | None) -> list[ColumnElement[bool]]:
    return _conditions(filters, ENTITY_FILTERS, Entity.meta)


def relationship_conditions(filters: Mapping[str, Any] | None) -> list[ColumnElement[bool]]:
    return _conditions(filters, RELATIONSHIP_FILTERS, Relationship.meta)


def is_entity_filter(filters: Mapping[str, Any]) -> bool:
    return set(filters) <= {*ENTITY_FILTERS, "metadata"}


def is_relationship_filter(filters: Mapping[str, Any]) -> bool:
    return set(filters) <= {*RELATIONSHIP_FILTERS, "metadata"}
