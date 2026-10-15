from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    entity_uri: Mapped[str] = mapped_column(Text, ForeignKey("entities.uri", ondelete="CASCADE", onupdate="CASCADE"))
    model_name: Mapped[str] = mapped_column(String(200))
    model_version: Mapped[str] = mapped_column(String(80))
    text_fields: Mapped[str] = mapped_column(String(200))
    dim: Mapped[int] = mapped_column(Integer)
    source_text: Mapped[str] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(String(64))
    vector: Mapped[list[float]] = mapped_column(Vector())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("entity_uri", "model_name", "model_version", "text_fields", name="uq_embeddings_entity_model_fields"),
        Index("ix_embeddings_model", "model_name", "model_version", "text_fields"),
    )
