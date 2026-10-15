import argparse
import importlib.util
import json
import os
from pathlib import Path

from ontology_service.data_models import SearchCompetencyRequest, SearchOccupationRequest

from .db.scripts.create_schema import create_schema
from .factory import open_store
from .ingestion.import_canonical import import_canonical
from .service.competency_service import REQUIRES, CompetencyService

FIXTURE = Path(__file__).parent / "tests" / "fixtures" / "sample_dataset"
SOFTWARE_DEVELOPER = "http://example.org/esco/occupation/softwareontwikkelaar"


def default_model() -> str:
    if os.environ.get("EMBEDDING_MODEL"):
        return os.environ["EMBEDDING_MODEL"]
    return "st" if importlib.util.find_spec("sentence_transformers") else "hashing"


def title(text: str) -> None:
    print(f"\n== {text}")


def show(rows: list[dict], *keys: str) -> None:
    if not rows:
        print("  (no results)")
    for row in rows:
        print("  " + " | ".join(str(row.get(k)) for k in keys))


def main() -> None:
    parser = argparse.ArgumentParser(description="Load the fixture dataset and run one query of each type")
    parser.add_argument("--model", default=default_model(), help="embedding model: hashing, st or st:<name>")
    args = parser.parse_args()

    title("1. schema + ingestion")
    create_schema()
    store = open_store(args.model)
    summary = import_canonical(store, FIXTURE)
    model = store.vectors.model
    print(f"  dataset {summary['dataset_id']}: {summary['entities']} entities, {summary['relationships']} relationships")
    print(f"  embeddings updated: {summary['embedded']} (model {model.name}, version {model.version}, dim {model.dim})")

    title("2. get_entity")
    entity = store.get_entity(SOFTWARE_DEVELOPER)
    print("  " + json.dumps({k: entity[k] for k in ("class", "framework", "label", "language")}, ensure_ascii=False))

    title("3. query_entities  filters={'framework': 'FGR', 'class': 'competency'}")
    show(store.query_entities({"framework": "FGR", "class": "competency"}), "uri", "label", "group")

    title("4. query_relationships  filters={'subject_uri': softwareontwikkelaar}")
    show(store.query_relationships({"subject_uri": SOFTWARE_DEVELOPER}), "predicate_uri", "object_uri", "metadata")

    title("5. get_neighbours  analytisch vermogen (incoming edges)")
    show(store.get_neighbours("http://example.org/fgr/competency/002", direction="in"), "direction", "label", "class", "metadata")

    title("6. competencies required by softwareontwikkelaar")
    show(store.get_linked_entities(SOFTWARE_DEVELOPER, [REQUIRES]), "class", "framework", "label", "relationship_metadata")

    title("7. literal_search 'data'")
    show(store.literal_search("data", limit=5), "score", "class", "label")

    title("8. literal_search 'SQL' with filters={'class': 'skill'}")
    show(store.literal_search("SQL", {"class": "skill"}), "score", "label", "description")

    for query in ("Python programmeren", "leidinggeven aan een team", "werken met grote datasets"):
        title(f"9. vector_search '{query}'")
        show(store.vector_search(query, limit=3), "score", "class", "framework", "label")

    service = CompetencyService(store)
    title("10. CompetencyService.search_competency (existing DTOs)")
    request = SearchCompetencyRequest(query="probleemoplossend vermogen", filters={"framework": "FGR"}, limit=2)
    print("  " + service.search_competency(request).model_dump_json(by_alias=True, exclude_none=True))
    title("11. CompetencyService.search_occupation (existing DTOs)")
    request = SearchOccupationRequest(query="softwareontwikkelaar", limit=2)
    print("  " + service.search_occupation(request).model_dump_json(by_alias=True, exclude_none=True))


if __name__ == "__main__":
    main()
