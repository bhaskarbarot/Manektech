import argparse

from alembic import command

from .create_schema import alembic_config


def reset_schema(url: str | None = None) -> None:
    cfg = alembic_config(url)
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


def main() -> None:
    parser = argparse.ArgumentParser(description="Drop all ontology store tables and recreate them")
    parser.add_argument("--database-url")
    parser.add_argument("--yes", action="store_true", help="confirm that all data will be removed")
    args = parser.parse_args()
    if not args.yes:
        parser.error("this removes all data, pass --yes to continue")
    reset_schema(args.database_url)
    print("schema reset")


if __name__ == "__main__":
    main()
