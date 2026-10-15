from typing import Any

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Timestamps


class Dataset(Timestamps, Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    version: Mapped[str] = mapped_column(String(40))
    source: Mapped[str | None] = mapped_column(Text)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    entity_count: Mapped[int] = mapped_column(Integer, default=0)
    relationship_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (UniqueConstraint("name", "version", name="uq_datasets_name_version"),)
