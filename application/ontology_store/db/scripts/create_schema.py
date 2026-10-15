import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config

from ontology_store.config import database_url

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def alembic_config(url: str | None = None) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", url or database_url())
    return cfg


def create_schema(url: str | None = None) -> None:
    command.upgrade(alembic_config(url), "head")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or upgrade the ontology store schema to the latest migration")
    parser.add_argument("--database-url")
    args = parser.parse_args()
    create_schema(args.database_url)
    print("schema upgraded to head")


if __name__ == "__main__":
    main()
