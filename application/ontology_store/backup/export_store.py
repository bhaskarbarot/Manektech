import argparse
from pathlib import Path

from ..factory import open_store
from ..ingestion.canonical_files import write_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Export datasets back to canonical files that import_canonical can reload")
    parser.add_argument("--out", default="exports")
    parser.add_argument("--dataset", action="append", help="dataset id, can be repeated; default is all datasets")
    args = parser.parse_args()
    store = open_store()
    dataset_ids = args.dataset or [d["id"] for d in store.list_datasets()]
    for dataset_id in dataset_ids:
        manifest, entities, relationships = store.export_dataset(dataset_id)
        folder = write_dataset(Path(args.out) / dataset_id.replace("@", "-"), manifest, entities, relationships)
        print(f"{dataset_id}: {len(entities)} entities, {len(relationships)} relationships -> {folder}")


if __name__ == "__main__":
    main()
