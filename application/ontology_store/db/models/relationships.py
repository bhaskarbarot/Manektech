from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Identity, Index, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Timestamps


class Relationship(Timestamps, Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    subject_uri: Mapped[str] = mapped_column(Text)
    predicate_uri: Mapped[str] = mapped_column(Text)
    object_uri: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"))
    dataset_id: Mapped[str | None] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))

    __table_args__ = (
        UniqueConstraint("subject_uri", "predicate_uri", "object_uri", name="uq_relationships_triple"),
        Index("ix_relationships_dataset_id", "dataset_id"),
    )


Index("ix_relationships_metadata", Relationship.meta, postgresql_using="gin", postgresql_ops={"metadata": "jsonb_path_ops"})
