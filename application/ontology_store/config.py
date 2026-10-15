import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

DEFAULT_DATABASE_URL = "postgresql+psycopg://ontology:ontology@localhost:5433/ontology"


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def make_engine(url: str | None = None) -> Engine:
    return create_engine(url or database_url())
