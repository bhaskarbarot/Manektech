import json
import shutil

import pytest
from sqlalchemy import func, select

from ontology_store.db.models import Embedding, Entity, Relationship
from ontology_store.ingestion.canonical_files import read_dataset, write_dataset
from ontology_store.ingestion.import_canonical import import_canonical
from ontology_store.store.errors import DatasetValidationError, InvalidFilterError
from ontology_store.store.models import CanonicalRelationship

from .conftest import DATA_ENGINEER, FIXTURE, PYTHON


def count(store, model):
    with store.sessions() as session:
        return session.scalar(select(func.count()).select_from(model))


def test_import_loads_all_records(empty_store):
    summary = import_canonical(empty_store, FIXTURE)
    assert summary == {"dataset_id": "competency-sample@1.0.0", "entities": 16, "relationships": 19, "embedded": 16}
    dataset = empty_store.list_datasets()[0]
    assert (dataset["entity_count"], dataset["relationship_count"]) == (16, 19)


def test_reimport_is_idempotent(store):
    summary = import_canonical(store, FIXTURE)
    assert summary["embedded"] == 0
    assert (count(store, Entity), count(store, Relationship), count(store, Embedding)) == (16, 19, 16)


def test_reimport_removes_records_dropped_from_dataset(store, tmp_path):
    manifest, entities, relationships = read_dataset(FIXTURE)
    entities = [e for e in entities if e.uri != DATA_ENGINEER]
    relationships = [r for r in relationships if r.subject_uri != DATA_ENGINEER]
    manifest.record_counts = {"entities": len(entities), "relationships": len(relationships)}
    write_dataset(tmp_path, manifest, entities, relationships)

    summary = import_canonical(store, tmp_path)

    assert (summary["entities"], summary["relationships"]) == (15, 17)
    assert store.get_entity(DATA_ENGINEER) is None
    assert store.query_relationships({"subject_uri": DATA_ENGINEER}) == []


def test_changed_text_is_reembedded_alone(store, tmp_path):
    manifest, entities, relationships = read_dataset(FIXTURE)
    for entity in entities:
        if entity.uri == PYTHON:
            entity.description = "Applicaties en scripts bouwen in Python."
    write_dataset(tmp_path, manifest, entities, relationships)

    assert import_canonical(store, tmp_path)["embedded"] == 1
    assert store.embedded_text(PYTHON) == "programmeren in Python Applicaties en scripts bouwen in Python."


def test_manifest_count_mismatch_is_rejected(tmp_path):
    shutil.copytree(FIXTURE, tmp_path, dirs_exist_ok=True)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    manifest["record_counts"]["entities"] = 99
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(DatasetValidationError, match="99 entities"):
        read_dataset(tmp_path)


def test_invalid_record_reports_line(tmp_path):
    shutil.copytree(FIXTURE, tmp_path, dirs_exist_ok=True)
    with (tmp_path / "entities.jsonl").open("a") as handle:
        handle.write('{"uri": "http://example.org/x", "class": "skill"}\n')
    with pytest.raises(DatasetValidationError, match="line 17"):
        read_dataset(tmp_path)


def test_relationship_to_unknown_entity_is_reported(store):
    records = [
        CanonicalRelationship(subject_uri=PYTHON, predicate_uri="http://example.org/p", object_uri="http://example.org/missing"),
        CanonicalRelationship(subject_uri=PYTHON, predicate_uri="http://example.org/p", object_uri=DATA_ENGINEER),
    ]
    result = store.import_relationships(records)
    assert (result.inserted, result.failed) == (1, 1)
    assert result.errors[0]["index"] == 0
    assert "http://example.org/missing" in result.errors[0]["error"]


def test_relationship_check_can_be_disabled(store):
    record = CanonicalRelationship(subject_uri=PYTHON, predicate_uri="http://example.org/p", object_uri="http://example.org/later")
    result = store.import_relationships([record], check_entities_exist=False)
    assert (result.inserted, result.failed) == (1, 0)


def test_delete_dataset_removes_everything(store):
    assert store.delete_dataset("competency-sample@1.0.0") == 35
    assert (count(store, Entity), count(store, Relationship), count(store, Embedding)) == (0, 0, 0)
    assert store.list_datasets() == []


def test_delete_by_metadata_removes_entities_and_their_edges(store):
    deleted = store.delete_by_metadata({"framework": "FGR"})
    assert deleted == 4 + 9
    assert store.query_entities({"framework": "FGR"}) == []
    assert store.query_relationships({"object_uri": "http://example.org/fgr/competency/001"}) == []


def test_delete_by_relationship_metadata_only_touches_edges(store):
    assert store.delete_by_metadata({"metadata": {"mapping": "broad"}}) == 3
    assert count(store, Entity) == 16


def test_delete_requires_filters(store):
    with pytest.raises(InvalidFilterError):
        store.delete_by_metadata({})
    with pytest.raises(InvalidFilterError):
        store.delete_by_metadata({"label": "leiderschap"})


def test_export_and_reload_gives_same_store(store, tmp_path):
    before = store.get_entity(PYTHON)
    manifest, entities, relationships = store.export_dataset("competency-sample@1.0.0")
    write_dataset(tmp_path, manifest, entities, relationships)
    store.delete_dataset("competency-sample@1.0.0")

    summary = import_canonical(store, tmp_path)

    assert (summary["entities"], summary["relationships"]) == (16, 19)
    assert store.get_entity(PYTHON) == before
