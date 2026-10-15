import hashlib
from collections.abc import Iterable

from pgvector.sqlalchemy import Vector
from sqlalchemy import and_, cast, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from ..db.models import Embedding, Entity
from ..db.models.vector_indexes import hnsw_index_ddl
from ..store.filters import entity_conditions
from .embedding_model import EmbeddingModel

TEXT_ATTRIBUTES = {"label": "label", "description": "description", "group": "group_name", "subgroup": "subgroup_name"}


class VectorIndex:
    def __init__(self, model: EmbeddingModel, text_fields: tuple[str, ...] = ("label", "description"), batch_size: int = 64):
        unknown = set(text_fields) - TEXT_ATTRIBUTES.keys()
        if unknown:
            raise ValueError(f"cannot embed fields: {sorted(unknown)}")
        self.model = model
        self.text_fields = text_fields
        self.fields_key = ",".join(text_fields)
        self.batch_size = batch_size

    def text_for(self, entity: Entity) -> str:
        parts = (getattr(entity, TEXT_ATTRIBUTES[f]) for f in self.text_fields)
        return " ".join(p.strip() for p in parts if p and p.strip())

    def scope(self):
        return and_(
            Embedding.model_name == self.model.name,
            Embedding.model_version == self.model.version,
            Embedding.text_fields == self.fields_key,
        )

    def build(self, session: Session, uris: Iterable[str] | None = None, force: bool = False) -> int:
        stmt = select(Entity, Embedding.text_hash).outerjoin(Embedding, and_(Embedding.entity_uri == Entity.uri, self.scope()))
        if uris is not None:
            stmt = stmt.where(Entity.uri.in_(list(uris)))
        pending = []
        for entity, current_hash in session.execute(stmt):
            source = self.text_for(entity)
            digest = hashlib.sha256(source.encode()).hexdigest()
            if force or digest != current_hash:
                pending.append((entity.uri, source, digest))

        for start in range(0, len(pending), self.batch_size):
            batch = pending[start:start + self.batch_size]
            vectors = self.model.embed_texts([source for _, source, _ in batch])
            rows = [
                {
                    "entity_uri": uri,
                    "model_name": self.model.name,
                    "model_version": self.model.version,
                    "text_fields": self.fields_key,
                    "dim": self.model.dim,
                    "source_text": source,
                    "text_hash": digest,
                    "vector": vector,
                }
                for (uri, source, digest), vector in zip(batch, vectors)
            ]
            insert_stmt = insert(Embedding).values(rows)
            session.execute(
                insert_stmt.on_conflict_do_update(
                    constraint="uq_embeddings_entity_model_fields",
                    set_={
                        "dim": insert_stmt.excluded.dim,
                        "source_text": insert_stmt.excluded.source_text,
                        "text_hash": insert_stmt.excluded.text_hash,
                        "vector": insert_stmt.excluded.vector,
                        "created_at": func.now(),
                    },
                )
            )
        return len(pending)

    def ensure_ann_index(self, session: Session) -> None:
        session.execute(hnsw_index_ddl(self.model.name, self.model.version, self.fields_key, self.model.dim))

    def search(self, session: Session, query: str, filters: dict | None = None, limit: int = 10) -> list[tuple[Entity, float]]:
        if not query.strip():
            return []
        query_vector = self.model.embed_query(query)
        distance = cast(Embedding.vector, Vector(self.model.dim)).cosine_distance(query_vector)
        stmt = (
            select(Entity, (1 - distance).label("score"))
            .join(Embedding, Embedding.entity_uri == Entity.uri)
            .where(self.scope(), *entity_conditions(filters))
            .order_by(distance)
            .limit(limit)
        )
        return [(row.Entity, float(row.score)) for row in session.execute(stmt)]
