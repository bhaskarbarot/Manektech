from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from ..db.models import Entity
from ..db.models.literal_indexes import LITERAL_FIELDS
from ..store.filters import entity_conditions

COLUMNS = {"label": Entity.label, "description": Entity.description}


def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class LiteralIndex:
    def __init__(self, fields: tuple[str, ...] = LITERAL_FIELDS):
        unknown = set(fields) - COLUMNS.keys()
        if unknown:
            raise ValueError(f"fields without a literal index: {sorted(unknown)}")
        self.fields = fields

    def search(self, session: Session, query: str, filters: dict | None = None, limit: int = 10) -> list[tuple[Entity, float]]:
        term = query.strip()
        if not term:
            return []
        escaped = escape_like(term)
        contains = f"%{escaped}%"
        rank = case(
            (func.lower(Entity.label) == term.lower(), 0),
            (Entity.label.ilike(f"{escaped}%", escape="\\"), 1),
            (Entity.label.ilike(contains, escape="\\"), 2),
            else_=3,
        )
        score = func.similarity(Entity.label, term)
        stmt = (
            select(Entity, score.label("score"))
            .where(or_(*(COLUMNS[f].ilike(contains, escape="\\") for f in self.fields)), *entity_conditions(filters))
            .order_by(rank, score.desc(), Entity.label)
            .limit(limit)
        )
        return [(row.Entity, float(row.score)) for row in session.execute(stmt)]
