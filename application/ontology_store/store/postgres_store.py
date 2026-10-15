from collections.abc import Iterable
from typing import Any

from sqlalchemy import delete, func, or_, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from ..db.models import Dataset, Embedding, Entity, Relationship
from ..indexing.embedding_model import EmbeddingModel
from ..indexing.graph_index import GraphIndex
from ..indexing.literal_index import LiteralIndex
from ..indexing.vector_index import VectorIndex
from .errors import InvalidFilterError
from .filters import entity_conditions, is_entity_filter, is_relationship_filter, relationship_conditions
from .interface import OntologyStore, Record
from .models import CanonicalEntity, CanonicalRelationship, DatasetManifest, ImportResult

BATCH_SIZE = 500
MAX_PAGE_SIZE = 500


def entity_record(entity: Entity) -> Record:
    return {
        "id": entity.entity_id,
        "class": entity.entity_class,
        "framework": entity.framework,
        "uri": entity.uri,
        "label": entity.label,
        "description": entity.description,
        "language": entity.language,
        "group": entity.group_name,
        "subgroup": entity.subgroup_name,
        "attributes": entity.attributes or {},
        "metadata": entity.meta or {},
        "dataset_id": entity.dataset_id,
    }


def relationship_record(rel: Relationship) -> Record:
    return {
        "subject_uri": rel.subject_uri,
        "predicate_uri": rel.predicate_uri,
        "object_uri": rel.object_uri,
        "metadata": rel.meta or {},
        "dataset_id": rel.dataset_id,
    }


def _entity_row(record: CanonicalEntity, dataset_id: str | None) -> dict[str, Any]:
    return {
        "uri": record.uri,
        "entity_id": record.id,
        "entity_class": record.class_,
        "framework": record.framework,
        "label": record.label,
        "description": record.description,
        "language": record.language,
        "group_name": record.group,
        "subgroup_name": record.subgroup,
        "attributes": record.attributes,
        "meta": record.metadata,
        "dataset_id": dataset_id,
    }


def _chunks(items: list, size: int = BATCH_SIZE):
    for start in range(0, len(items), size):
        yield items[start:start + size]


class PostgresOntologyStore(OntologyStore):
    def __init__(self, engine: Engine, embedding_model: EmbeddingModel, text_fields: tuple[str, ...] = ("label", "description")):
        self.engine = engine
        self.sessions = sessionmaker(engine, expire_on_commit=False)
        self.literal = LiteralIndex()
        self.vectors = VectorIndex(embedding_model, text_fields)
        self.graph = GraphIndex()

    def get_entity(self, uri: str) -> Record | None:
        with self.sessions() as session:
            entity = session.get(Entity, uri)
            return entity_record(entity) if entity else None

    def query_entities(self, filters: dict | None = None, limit: int | None = None) -> list[Record]:
        stmt = select(Entity).where(*entity_conditions(filters)).order_by(Entity.uri)
        if limit:
            stmt = stmt.limit(limit)
        with self.sessions() as session:
            return [entity_record(e) for e in session.scalars(stmt)]

    def count_entities(self, filters: dict | None = None) -> int:
        stmt = select(func.count()).select_from(Entity).where(*entity_conditions(filters))
        with self.sessions() as session:
            return session.scalar(stmt)

    def browse_entities(self, page_number: int, page_size: int, filters: dict | None = None) -> list[Record]:
        if page_number < 1:
            raise ValueError("page_number starts at 1")
        if not 1 <= page_size <= MAX_PAGE_SIZE:
            raise ValueError(f"page_size must be between 1 and {MAX_PAGE_SIZE}")
        stmt = (
            select(Entity)
            .where(*entity_conditions(filters))
            .order_by(Entity.framework, Entity.entity_class, Entity.label, Entity.uri)
            .offset((page_number - 1) * page_size)
            .limit(page_size)
        )
        with self.sessions() as session:
            return [entity_record(e) for e in session.scalars(stmt)]

    def query_relationships(self, filters: dict | None = None, limit: int | None = None) -> list[Record]:
        with self.sessions() as session:
            return [relationship_record(r) for r in self.graph.query(session, filters, limit)]

    def count_relationships(self, filters: dict | None = None) -> int:
        stmt = select(func.count()).select_from(Relationship).where(*relationship_conditions(filters))
        with self.sessions() as session:
            return session.scalar(stmt)

    def get_neighbours(self, uri: str, predicates: list[str] | None = None, direction: str = "both") -> list[Record]:
        with self.sessions() as session:
            rows = self.graph.neighbours(session, uri, predicates, direction)
        return [
            {
                "direction": direction_,
                "predicate_uri": rel.predicate_uri,
                "uri": rel.object_uri if direction_ == "out" else rel.subject_uri,
                "label": entity.label if entity else None,
                "class": entity.entity_class if entity else None,
                "metadata": rel.meta or {},
            }
            for direction_, rel, entity in rows
        ]

    def get_linked_entities(
        self, uri: str, predicates: list[str] | None = None, direction: str = "out", filters: dict | None = None
    ) -> list[Record]:
        with self.sessions() as session:
            rows = self.graph.linked_entities(session, uri, predicates, direction, filters)
        return [
            entity_record(entity) | {"predicate_uri": rel.predicate_uri, "relationship_metadata": rel.meta or {}}
            for entity, rel in rows
        ]

    def literal_search(self, query: str, filters: dict | None = None, limit: int = 10) -> list[Record]:
        with self.sessions() as session:
            hits = self.literal.search(session, query, filters, limit)
        return [entity_record(entity) | {"score": round(score, 4)} for entity, score in hits]

    def vector_search(self, query: str, filters: dict | None = None, limit: int = 10) -> list[Record]:
        with self.sessions() as session:
            hits = self.vectors.search(session, query, filters, limit)
        return [entity_record(entity) | {"score": round(score, 4)} for entity, score in hits]

    def register_dataset(self, manifest: DatasetManifest) -> str:
        values = {
            "id": manifest.dataset_id,
            "name": manifest.name,
            "version": manifest.version,
            "source": manifest.source,
            "manifest": manifest.model_dump(),
        }
        stmt = insert(Dataset).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Dataset.id],
            set_={"source": stmt.excluded.source, "manifest": stmt.excluded.manifest, "updated_at": func.now()},
        )
        with self.sessions.begin() as session:
            session.execute(stmt)
        return manifest.dataset_id

    def import_entities(
        self, records: Iterable[CanonicalEntity], dataset_id: str | None = None, prune: bool = False
    ) -> ImportResult:
        result = ImportResult()
        rows: dict[str, dict] = {}
        for index, record in enumerate(records):
            if record.uri in rows:
                result.failed += 1
                result.errors.append({"index": index, "error": f"duplicate uri in input: {record.uri}"})
                continue
            rows[record.uri] = _entity_row(record, dataset_id)

        with self.sessions.begin() as session:
            for chunk in _chunks(list(rows.values())):
                stmt = insert(Entity).values(chunk)
                columns = [Entity.__mapper__.columns[key] for key in chunk[0] if key != "uri"]
                updates = {column: stmt.excluded[column.name] for column in columns}
                session.execute(
                    stmt.on_conflict_do_update(index_elements=[Entity.uri], set_=updates | {Entity.updated_at: func.now()})
                )
            if prune and dataset_id:
                session.execute(
                    delete(Entity)
                    .where(Entity.dataset_id == dataset_id, Entity.uri.not_in(list(rows)))
                    .execution_options(synchronize_session=False)
                )
        result.inserted = len(rows)
        return result

    def import_relationships(
        self,
        records: Iterable[CanonicalRelationship],
        dataset_id: str | None = None,
        check_entities_exist: bool = True,
        prune: bool = False,
    ) -> ImportResult:
        records = list(records)
        result = ImportResult()
        with self.sessions.begin() as session:
            known: set[str] = set()
            if check_entities_exist:
                wanted = {r.subject_uri for r in records} | {r.object_uri for r in records}
                for chunk in _chunks(sorted(wanted)):
                    known.update(session.scalars(select(Entity.uri).where(Entity.uri.in_(chunk))))

            rows: dict[tuple[str, str, str], dict] = {}
            for index, record in enumerate(records):
                if check_entities_exist:
                    missing = [u for u in (record.subject_uri, record.object_uri) if u not in known]
                    if missing:
                        result.failed += 1
                        result.errors.append({"index": index, "error": f"unknown entity: {', '.join(missing)}"})
                        continue
                key = (record.subject_uri, record.predicate_uri, record.object_uri)
                rows[key] = {
                    "subject_uri": record.subject_uri,
                    "predicate_uri": record.predicate_uri,
                    "object_uri": record.object_uri,
                    "meta": record.metadata,
                    "dataset_id": dataset_id,
                }

            for chunk in _chunks(list(rows.values())):
                stmt = insert(Relationship).values(chunk)
                session.execute(
                    stmt.on_conflict_do_update(
                        constraint="uq_relationships_triple",
                        set_={
                            Relationship.meta: stmt.excluded["metadata"],
                            Relationship.dataset_id: stmt.excluded.dataset_id,
                            Relationship.updated_at: func.now(),
                        },
                    )
                )
            if prune and dataset_id:
                triple = tuple_(Relationship.subject_uri, Relationship.predicate_uri, Relationship.object_uri)
                stmt = delete(Relationship).where(Relationship.dataset_id == dataset_id)
                if rows:
                    stmt = stmt.where(triple.not_in(list(rows)))
                session.execute(stmt.execution_options(synchronize_session=False))
        result.inserted = len(rows)
        return result

    def rebuild_embeddings(self, uris: Iterable[str] | None = None, force: bool = False) -> int:
        with self.sessions.begin() as session:
            built = self.vectors.build(session, uris, force)
            self.vectors.ensure_ann_index(session)
        return built

    def embedded_text(self, uri: str) -> str | None:
        with self.sessions() as session:
            return session.scalar(
                select(Embedding.source_text).where(Embedding.entity_uri == uri, self.vectors.scope())
            )

    def refresh_dataset_counts(self, dataset_id: str) -> dict[str, int]:
        with self.sessions.begin() as session:
            entities = session.scalar(select(func.count()).select_from(Entity).where(Entity.dataset_id == dataset_id))
            relationships = session.scalar(
                select(func.count()).select_from(Relationship).where(Relationship.dataset_id == dataset_id)
            )
            dataset = session.get(Dataset, dataset_id)
            if dataset:
                dataset.entity_count = entities
                dataset.relationship_count = relationships
        return {"entities": entities, "relationships": relationships}

    def delete_by_metadata(self, filters: dict) -> int:
        if not filters:
            raise InvalidFilterError("refusing to delete without filters")
        on_entities = is_entity_filter(filters)
        on_relationships = is_relationship_filter(filters)
        if not on_entities and not on_relationships:
            raise InvalidFilterError(f"filters do not apply to entities or relationships: {sorted(filters)}")
        deleted = 0
        with self.sessions.begin() as session:
            if on_entities:
                uris = list(
                    session.scalars(
                        delete(Entity)
                        .where(*entity_conditions(filters))
                        .returning(Entity.uri)
                        .execution_options(synchronize_session=False)
                    )
                )
                deleted += len(uris)
                for chunk in _chunks(uris):
                    deleted += session.execute(
                        delete(Relationship)
                        .where(or_(Relationship.subject_uri.in_(chunk), Relationship.object_uri.in_(chunk)))
                        .execution_options(synchronize_session=False)
                    ).rowcount
            if on_relationships:
                deleted += session.execute(
                    delete(Relationship).where(*relationship_conditions(filters)).execution_options(synchronize_session=False)
                ).rowcount
        return deleted

    def delete_dataset(self, dataset_id: str) -> int:
        with self.sessions.begin() as session:
            entities = session.scalar(select(func.count()).select_from(Entity).where(Entity.dataset_id == dataset_id))
            relationships = session.scalar(
                select(func.count()).select_from(Relationship).where(Relationship.dataset_id == dataset_id)
            )
            removed = session.execute(delete(Dataset).where(Dataset.id == dataset_id)).rowcount
        return entities + relationships if removed else 0

    def list_datasets(self) -> list[Record]:
        with self.sessions() as session:
            return [
                {
                    "id": d.id,
                    "name": d.name,
                    "version": d.version,
                    "source": d.source,
                    "entity_count": d.entity_count,
                    "relationship_count": d.relationship_count,
                    "loaded_at": d.updated_at.isoformat(),
                }
                for d in session.scalars(select(Dataset).order_by(Dataset.id))
            ]

    def export_dataset(
        self, dataset_id: str
    ) -> tuple[DatasetManifest, list[CanonicalEntity], list[CanonicalRelationship]]:
        with self.sessions() as session:
            dataset = session.get(Dataset, dataset_id)
            if dataset is None:
                raise LookupError(f"dataset not found: {dataset_id}")
            entities = [
                CanonicalEntity.model_validate({k: v for k, v in entity_record(e).items() if k != "dataset_id"})
                for e in session.scalars(select(Entity).where(Entity.dataset_id == dataset_id).order_by(Entity.uri))
            ]
            relationships = [
                CanonicalRelationship(subject_uri=r.subject_uri, predicate_uri=r.predicate_uri, object_uri=r.object_uri, metadata=r.meta or {})
                for r in session.scalars(select(Relationship).where(Relationship.dataset_id == dataset_id).order_by(Relationship.id))
            ]
            manifest = DatasetManifest.model_validate(dataset.manifest)
        manifest.record_counts = {"entities": len(entities), "relationships": len(relationships)}
        return manifest, entities, relationships
