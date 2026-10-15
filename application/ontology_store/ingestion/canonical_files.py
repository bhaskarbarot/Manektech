import json
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel, ValidationError

from ..store.errors import DatasetValidationError
from ..store.models import CanonicalEntity, CanonicalRelationship, DatasetManifest

MANIFEST_FILE = "manifest.json"


def read_manifest(folder: Path) -> DatasetManifest:
    path = folder / MANIFEST_FILE
    if not path.exists():
        raise DatasetValidationError(f"missing {MANIFEST_FILE} in {folder}")
    try:
        return DatasetManifest.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise DatasetValidationError(f"{path}: {exc}") from exc


def read_records(path: Path, model: type[BaseModel]) -> list:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                records.append(model.model_validate_json(line))
            except ValidationError as exc:
                raise DatasetValidationError(f"{path.name} line {line_no}: {exc.errors()[0]['msg']}") from exc
    return records


def read_dataset(folder: str | Path) -> tuple[DatasetManifest, list[CanonicalEntity], list[CanonicalRelationship]]:
    folder = Path(folder)
    manifest = read_manifest(folder)
    entities = read_records(folder / manifest.files["entities"], CanonicalEntity)
    relationships = read_records(folder / manifest.files["relationships"], CanonicalRelationship)
    for kind, found in (("entities", len(entities)), ("relationships", len(relationships))):
        expected = manifest.record_counts.get(kind)
        if expected is not None and expected != found:
            raise DatasetValidationError(f"manifest says {expected} {kind} but files contain {found}")
    return manifest, entities, relationships


def write_records(path: Path, records: Iterable[BaseModel]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.model_dump(by_alias=True), ensure_ascii=False) + "\n")


def write_dataset(
    folder: str | Path,
    manifest: DatasetManifest,
    entities: list[CanonicalEntity],
    relationships: list[CanonicalRelationship],
) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    write_records(folder / manifest.files["entities"], entities)
    write_records(folder / manifest.files["relationships"], relationships)
    (folder / MANIFEST_FILE).write_text(json.dumps(manifest.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return folder
