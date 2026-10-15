from .config import make_engine
from .indexing.embedding_model import load_embedding_model
from .store.postgres_store import PostgresOntologyStore


def open_store(model: str | None = None, database_url: str | None = None) -> PostgresOntologyStore:
    return PostgresOntologyStore(make_engine(database_url), load_embedding_model(model))
