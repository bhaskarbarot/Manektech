from sqlalchemy import Index, func

from .entities import Entity

LITERAL_FIELDS = ("label", "description")

label_trgm = Index("ix_entities_label_trgm", Entity.label, postgresql_using="gin", postgresql_ops={"label": "gin_trgm_ops"})
description_trgm = Index(
    "ix_entities_description_trgm", Entity.description, postgresql_using="gin", postgresql_ops={"description": "gin_trgm_ops"}
)
label_lower = Index("ix_entities_label_lower", func.lower(Entity.label))
