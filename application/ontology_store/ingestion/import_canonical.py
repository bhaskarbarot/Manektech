import argparse
from pathlib import Path

from ..factory import open_store
from ..store.errors import DatasetValidationError
from ..store.interface import OntologyStore
from .canonical_files import read_dataset


def import_canonical(store: OntologyStore, folder: str | Path, build_embeddings: bool = True) -> dict:
    manifest, entities, relationships = read_dataset(folder)
    dataset_id = store.register_dataset(manifest)

    entity_result = store.import_entities(entities, dataset_id, prune=True)
    if entity_result.failed:
        raise DatasetValidationError(f"{entity_result.failed} entities rejected: {entity_result.errors[:3]}")

    relationship_result = store.import_relationships(relationships, dataset_id, check_entities_exist=True, prune=True)
    if relationship_result.failed:
        raise DatasetValidationError(f"{relationship_result.failed} relationships rejected: {relationship_result.errors[:3]}")

    counts = store.refresh_dataset_counts(dataset_id)
    if counts != {"entities": len(entities), "relationships": len(relationships)}:
        raise DatasetValidationError(f"count check failed for {dataset_id}: files {len(entities)}/{len(relationships)}, store {counts}")

    embedded = store.rebuild_embeddings() if build_embeddings else 0
    return {"dataset_id": dataset_id, **counts, "embedded": embedded}


def main() -> None:
    parser = argparse.ArgumentParser(description="Load a canonical dataset folder (manifest.json + jsonl files) into the store")
    parser.add_argument("folder")
    parser.add_argument("--model", help="embedding model: hashing, st or st:<name>")
    parser.add_argument("--skip-embeddings", action="store_true")
    args = parser.parse_args()
    summary = import_canonical(open_store(args.model), args.folder, build_embeddings=not args.skip_embeddings)
    print(
        f"loaded {summary['dataset_id']}: {summary['entities']} entities, "
        f"{summary['relationships']} relationships, {summary['embedded']} embeddings updated"
    )


if __name__ == "__main__":
    main()
