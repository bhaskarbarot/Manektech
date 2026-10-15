import pytest
from sqlalchemy import select, text

from ontology_store.db.models import Embedding
from ontology_store.db.models.vector_indexes import hnsw_index_name
from ontology_store.indexing.embedding_model import HashingEmbeddingModel
from ontology_store.ingestion.import_canonical import import_canonical
from ontology_store.store.postgres_store import PostgresOntologyStore

from .conftest import FIXTURE, PYTHON


def test_query_equal_to_entity_text_finds_that_entity(store):
    hits = store.vector_search("programmeren in Python")
    assert hits[0]["uri"] == PYTHON
    assert hits[0]["score"] > hits[1]["score"]


def test_scores_are_sorted(store):
    scores = [h["score"] for h in store.vector_search("data analyseren", limit=8)]
    assert scores == sorted(scores, reverse=True)


def test_filters_are_applied(store):
    hits = store.vector_search("data", {"class": "occupation", "language": "nl"}, limit=10)
    assert len(hits) == 3
    assert all(h["class"] == "occupation" for h in hits)


def test_embedding_metadata_is_stored(store):
    with store.sessions() as session:
        row = session.scalars(select(Embedding).where(Embedding.entity_uri == PYTHON)).one()
    assert row.model_name == "hashing-char-ngram"
    assert row.model_version == "v1-d256-n3"
    assert row.dim == 256
    assert row.text_fields == "label,description"
    assert row.source_text == "programmeren in Python Software schrijven, testen en onderhouden met de programmeertaal Python."


def test_hnsw_index_is_created_for_the_model(store):
    model = store.vectors.model
    name = hnsw_index_name(model.name, model.version, "label,description")
    with store.sessions() as session:
        found = session.scalar(text("select indexdef from pg_indexes where indexname = :n"), {"n": name})
    assert "hnsw" in found and "vector(256)" in found


def test_two_models_live_side_by_side(store, engine):
    small = PostgresOntologyStore(engine, HashingEmbeddingModel(dim=64))
    assert small.rebuild_embeddings() == 16
    assert small.vector_search("programmeren in Python")[0]["uri"] == PYTHON
    assert store.vector_search("programmeren in Python")[0]["uri"] == PYTHON
    with store.sessions() as session:
        assert len(session.scalars(select(Embedding)).all()) == 32


def test_force_rebuild_reembeds_everything(store):
    assert store.rebuild_embeddings() == 0
    assert store.rebuild_embeddings(force=True) == 16


def test_label_only_embeddings(engine, empty_store):
    import_canonical(empty_store, FIXTURE, build_embeddings=False)
    label_store = PostgresOntologyStore(engine, HashingEmbeddingModel(), text_fields=("label",))
    assert label_store.rebuild_embeddings() == 16
    assert label_store.embedded_text(PYTHON) == "programmeren in Python"


def test_semantic_model_matches_meaning():
    pytest.importorskip("sentence_transformers")
    from ontology_store.indexing.embedding_model import SentenceTransformerModel

    model = SentenceTransformerModel()
    query, leadership, sql = model.embed_texts(["leidinggeven aan een team", "leiderschap", "SQL gebruiken"])
    similarity = lambda a, b: sum(x * y for x, y in zip(a, b))
    assert similarity(query, leadership) > similarity(query, sql)
