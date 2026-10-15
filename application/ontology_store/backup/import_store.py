import argparse
from pathlib import Path

from ..factory import open_store
from ..ingestion.canonical_files import MANIFEST_FILE
from ..ingestion.import_canonical import import_canonical


def main() -> None:
    parser = argparse.ArgumentParser(description="Reload every exported dataset folder found under a directory")
    parser.add_argument("folder", nargs="?", default="exports")
    parser.add_argument("--model", help="embedding model: hashing, st or st:<name>")
    args = parser.parse_args()
    store = open_store(args.model)
    folders = sorted(p.parent for p in Path(args.folder).glob(f"*/{MANIFEST_FILE}"))
    if not folders:
        raise SystemExit(f"no dataset folders found in {args.folder}")
    for folder in folders:
        summary = import_canonical(store, folder)
        print(f"{summary['dataset_id']}: {summary['entities']} entities, {summary['relationships']} relationships")


if __name__ == "__main__":
    main()
