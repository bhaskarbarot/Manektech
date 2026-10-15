from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Entity, Relationship
from ..store.filters import entity_conditions, relationship_conditions

DIRECTIONS = ("out", "in", "both")


class GraphIndex:
    def query(self, session: Session, filters: dict | None = None, limit: int | None = None) -> list[Relationship]:
        stmt = select(Relationship).where(*relationship_conditions(filters)).order_by(Relationship.id)
        if limit:
            stmt = stmt.limit(limit)
        return list(session.scalars(stmt))

    def neighbours(
        self, session: Session, uri: str, predicates: list[str] | None = None, direction: str = "both"
    ) -> list[tuple[str, Relationship, Entity | None]]:
        if direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {DIRECTIONS}")
        found = []
        sides = []
        if direction in ("out", "both"):
            sides.append(("out", Relationship.subject_uri, Relationship.object_uri))
        if direction in ("in", "both"):
            sides.append(("in", Relationship.object_uri, Relationship.subject_uri))
        for name, anchor, other in sides:
            stmt = select(Relationship, Entity).outerjoin(Entity, Entity.uri == other).where(anchor == uri)
            if predicates:
                stmt = stmt.where(Relationship.predicate_uri.in_(predicates))
            found += [(name, rel, entity) for rel, entity in session.execute(stmt.order_by(Relationship.id))]
        return found

    def linked_entities(
        self,
        session: Session,
        uri: str,
        predicates: list[str] | None = None,
        direction: str = "out",
        filters: dict | None = None,
    ) -> list[tuple[Entity, Relationship]]:
        if direction not in ("out", "in"):
            raise ValueError("direction must be 'out' or 'in'")
        anchor, other = (
            (Relationship.subject_uri, Relationship.object_uri)
            if direction == "out"
            else (Relationship.object_uri, Relationship.subject_uri)
        )
        stmt = (
            select(Entity, Relationship)
            .join(Relationship, other == Entity.uri)
            .where(anchor == uri, *entity_conditions(filters))
            .order_by(Entity.label)
        )
        if predicates:
            stmt = stmt.where(Relationship.predicate_uri.in_(predicates))
        return [(entity, rel) for entity, rel in session.execute(stmt)]
