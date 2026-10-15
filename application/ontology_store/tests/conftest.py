import os
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

from ontology_store.config import make_engine
from ontology_store.db.scripts.create_schema import create_schema
from ontology_store.indexing.embedding_model import HashingEmbeddingModel
from ontology_store.ingestion.import_canonical import import_canonical
from ontology_store.store.postgres_store import PostgresOntologyStore

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://ontology:ontology@localhost:5433/ontology_test"
)
FIXTURE = Path(__file__).parent / "fixtures" / "sample_dataset"

SOFTWARE_DEVELOPER = "http://example.org/esco/occupation/softwareontwikkelaar"
DATA_SCIENTIST = "http://example.org/esco/occupation/data-scientist"
DATA_ENGINEER = "http://example.org/esco/occupation/data-engineer"
PYTHON = "http://example.org/esco/skill/python-programmeren"
DATA_ANALYSIS = "http://example.org/esco/skill/data-analyseren"
ANALYTICAL = "http://example.org/fgr/competency/002"
REQUIRES = "https://objectiveye.ai/oe-ontology/competencyframework/requires"
RELATED_TO = "https://objectiveye.ai/oe-ontology/competencyframework/relatedTo"


@pytest.fixture(scope="session")
def engine():
    if not make_url(TEST_DATABASE_URL).database.endswith("_test"):
        pytest.exit("TEST_DATABASE_URL must point to a database whose name ends with _test")
    create_schema(TEST_DATABASE_URL)
    engine = make_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def empty_store(engine):
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE datasets, entities, relationships, embeddings RESTART IDENTITY CASCADE"))
    return PostgresOntologyStore(engine, HashingEmbeddingModel())


@pytest.fixture
def store(empty_store):
    import_canonical(empty_store, FIXTURE)
    return empty_store
