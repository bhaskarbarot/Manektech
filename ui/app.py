"""Small Streamlit UI to try the ontology store by hand.

Run from the project root:  streamlit run ui/app.py
It uses the same database (DATABASE_URL) and embedding model (EMBEDDING_MODEL) as the demo.
"""
import json

import streamlit as st

from ontology_store.db.scripts.create_schema import create_schema
from ontology_store.demo import FIXTURE, default_model
from ontology_store.factory import open_store
from ontology_store.ingestion.import_canonical import import_canonical

st.set_page_config(page_title="Ontology Store", page_icon="🔎", layout="wide")


@st.cache_resource(show_spinner="Connecting to the database and loading the embedding model...")
def get_store():
    create_schema()
    store = open_store(default_model())
    if store.count_entities() == 0:
        import_canonical(store, FIXTURE)
    else:
        store.rebuild_embeddings()  # only embeds what is missing for this model
    return store


def short(uri: str | None) -> str:
    return (uri or "").rstrip("/").rsplit("/", 1)[-1]


def table(rows: list[dict], columns: list[str], empty: str = "No results.") -> None:
    if not rows:
        st.info(empty)
        return
    cells = [
        {c: json.dumps(r.get(c), ensure_ascii=False) if isinstance(r.get(c), (dict, list)) else r.get(c) for c in columns}
        for r in rows
    ]
    st.dataframe(cells, width="stretch", hide_index=True)


def filters_from(classes: list[str], frameworks: list[str]) -> dict:
    filters = {}
    if classes:
        filters["class"] = classes
    if frameworks:
        filters["framework"] = frameworks
    return filters


try:
    store = get_store()
except Exception as exc:
    st.error(
        "Could not connect to the ontology store. Start the database with `docker compose up -d --wait` "
        "(or run windows.bat / mac.sh / linux.sh first), then reload this page."
    )
    st.exception(exc)
    st.stop()

entities = store.query_entities()
all_classes = sorted({e["class"] for e in entities})
all_frameworks = sorted({e["framework"] for e in entities if e["framework"]})

model = store.vectors.model
with st.sidebar:
    st.header("Ontology Store")
    st.caption(f"Embedding model: `{model.name}` (dim {model.dim})")
    st.metric("Entities", store.count_entities())
    st.metric("Relationships", store.count_relationships())
    for dataset in store.list_datasets():
        st.caption(f"Dataset `{dataset['id']}`")
    if model.name.startswith("hashing"):
        st.warning("Hashing model: vector search matches spelling, not meaning. Run the full setup for the multilingual model.")

search_tab, entity_tab, browse_tab = st.tabs(["🔎 Search", "🧩 Entity explorer", "📋 Browse"])

with search_tab:
    query = st.text_input("Search text", value="leidinggeven aan een team")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    mode = col1.radio("Search type", ["Both", "Literal", "Vector"], horizontal=True)
    classes = col2.multiselect("Class", all_classes)
    frameworks = col3.multiselect("Framework", all_frameworks)
    limit = col4.number_input("Max results", min_value=1, max_value=50, value=5)
    filters = filters_from(classes, frameworks)
    columns = ["score", "label", "class", "framework", "description"]

    if query.strip():
        shown = ["Literal", "Vector"] if mode == "Both" else [mode]
        for column, kind in zip(st.columns(len(shown)), shown):
            with column:
                if kind == "Literal":
                    st.subheader("Literal search")
                    st.caption("Words that appear in label or description, ranked by label similarity.")
                    table(
                        store.literal_search(query, filters, int(limit)),
                        columns,
                        "No literal match: this exact text does not appear in any label or description. "
                        "Compare with vector search, which matches on meaning.",
                    )
                else:
                    st.subheader("Vector search")
                    st.caption("Closest meaning (cosine similarity on pgvector).")
                    table(store.vector_search(query, filters, int(limit)), columns)

with entity_tab:
    names = {e["uri"]: f"{e['label']}  ({e['class']}, {e['framework']})" for e in sorted(entities, key=lambda e: e["label"])}
    uri = st.selectbox("Entity", list(names), format_func=names.get)
    if uri:
        entity = store.get_entity(uri)
        st.subheader(entity["label"])
        st.write(entity["description"] or "")
        st.json({k: entity[k] for k in ("uri", "class", "framework", "language", "group", "subgroup", "metadata")}, expanded=False)

        st.markdown("**Linked entities (outgoing)**")
        linked = store.get_linked_entities(uri)
        for row in linked:
            row["relation"] = short(row["predicate_uri"])
        table(linked, ["relation", "label", "class", "framework", "relationship_metadata"], "No outgoing links.")

        st.markdown("**Neighbours (both directions)**")
        neighbours = store.get_neighbours(uri)
        for row in neighbours:
            row["relation"] = short(row["predicate_uri"])
        table(neighbours, ["direction", "relation", "label", "class", "metadata"], "No neighbours.")

with browse_tab:
    col1, col2, col3, col4 = st.columns(4)
    classes = col1.multiselect("Class", all_classes, key="browse_class")
    frameworks = col2.multiselect("Framework", all_frameworks, key="browse_framework")
    page_size = col3.selectbox("Page size", [5, 10, 25, 50], index=1)
    filters = filters_from(classes, frameworks)
    total = store.count_entities(filters)
    pages = max(1, -(-total // page_size))
    page = col4.number_input(f"Page (of {pages})", min_value=1, max_value=pages, value=1)
    st.caption(f"{total} entities match")
    table(store.browse_entities(int(page), page_size, filters), ["label", "class", "framework", "group", "language", "uri"])
