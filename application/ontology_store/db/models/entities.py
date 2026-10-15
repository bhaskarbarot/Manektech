from typing import Any

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Timestamps


class Entity(Timestamps, Base):
    __tablename__ = "entities"

    uri: Mapped[str] = mapped_column(Text, primary_key=True)
    entity_id: Mapped[str | None] = mapped_column(Text, unique=True)
    entity_class: Mapped[str] = mapped_column(String(64))
    framework: Mapped[str | None] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(16))
    group_name: Mapped[str | None] = mapped_column(Text)
    subgroup_name: Mapped[str | None] = mapped_column(Text)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"))
    dataset_id: Mapped[str | None] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))

    __table_args__ = (
        Index("ix_entities_class_framework", "entity_class", "framework"),
        Index("ix_entities_language", "language"),
        Index("ix_entities_dataset_id", "dataset_id"),
    )


Index("ix_entities_metadata", Entity.meta, postgresql_using="gin", postgresql_ops={"metadata": "jsonb_path_ops"})
