from alembic import context
from sqlalchemy import create_engine, pool

from ontology_store.config import database_url
from ontology_store.db.models import Base
from ontology_store.db.models.vector_indexes import HNSW_PREFIX

config = context.config
target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "index" and name and name.startswith(HNSW_PREFIX):
        return False
    return True


def run_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url") or database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_online() -> None:
    engine = create_engine(config.get_main_option("sqlalchemy.url") or database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_offline()
else:
    run_online()
