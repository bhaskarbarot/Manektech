# Ontology Store, Indexing and PostgreSQL Layer - Design

This covers the written deliverables from `Task.md`. The working prototype is described in [readme.md](readme.md).

A note before the review sections: the package I received contains `Task.md` and the DTO modules in
`application/ontology_service/data_models/`. The current store, service and SQL code is not included.
Sections 1 to 5 are therefore based on what the DTOs show (field names, docstrings, OpenAPI examples),
and each point that needs the real code to confirm is marked **to verify**.

## 1. Current store architecture summary

What the DTOs tell us about the current store:

- Entities are stored with `id`, `class`, `framework`, `uri`, `label`, `description`, `language`, `group`,
  `subgroup`, `attributes` (object) and `metadata` (object). Ids follow `esco:skill:<uuid>`.
- Relationships are stored as triples `subject_uri`, `predicate_uri`, `object_uri` plus `metadata`.
  The query DTO calls it the "triples table".
- Search is vector similarity: the docstrings say "uses vector embeddings", results carry `similarity_score`.
- The `add_entity` response returns `metadata.embedded_text`, so adding an entity embeds it in the same call.
  The example `"test competency Test skill for documentation examples."` shows the embedded text is
  `label + " " + description`.
- Two frameworks live in the same store: ESCO (Dutch labels, `data.europa.eu/esco/...` URIs) and FGR
  (`objectiveye.ai/fgr/...` URIs).
- Vacancy extraction uses an LLM (`extraction_prompt` with `{job_title}` and `{vacancy_text}`), then does a
  search per extracted mention in both ESCO and FGR (`limit` is per framework).

To verify: whether the embedding lives in the entity row, which table store library is used, and whether
ESCO and FGR are separate tables or one table with a `framework` column.

## 2. Current outside behaviour summary

| Operation | Request DTO | Response DTO | Behaviour to keep |
|---|---|---|---|
| search_competency | SearchCompetencyRequest | SearchResponse | vector search over skills and competencies, filters `framework`, `class`, compact/full format, default limit 10 |
| search_occupation | SearchOccupationRequest | SearchResponse | same, restricted to occupations |
| browse_entities | BrowseEntitiesRequest | BrowseEntitiesResponse | 1-based pages, default page size 25, filters, compact/full |
| get_entity | GetEntityRequest | EntityResponse | lookup by URI, `entity: null` when not found |
| query_entities | QueryEntitiesRequest | QueryEntitiesResponse | filters on columns and on `metadata` (object containment), optional limit, `total` |
| query_relationships | QueryRelationshipsRequest | QueryEntitiesResponse | filter by subject, predicate, object |
| add_entity | entity object | AddEntityResponse | returns `embedded_text` |
| add triples | TripleIngestManyRequest | TripleIngestManyResponse | per item errors with index, optional `check_entities_exist` |
| delete_by_metadata | DeleteByMetadataRequest | DeleteResponse | works for column filters (`framework`) and `metadata` filters, for entities or relationships |
| vacancy extraction | VacancyTextRequest | SkillExtractionResponse | LLM extraction + ESCO/FGR matching |

Filter values are case sensitive today ("class: lowercase only" in the docstrings). The prototype keeps exact
matching for filters so existing callers get the same results.

## 3. Current PostgreSQL / pgvector review

From the DTOs I can see the store mixes three concerns in one place: entity content, the embedding and the
search ranking. `add_entity` returning `embedded_text` is the clearest sign, the write path for content also
decides what text is embedded. That makes three things hard:

- changing the embedding model means rewriting entity rows instead of adding a new index next to the old one
- there is no record of which model or version produced a vector
- re-embedding cannot skip entities whose text did not change

To verify in the code: the vector column type and dimension, whether an ANN index exists (IVFFlat or HNSW)
or every search is a full scan, how filters are combined with the vector order, and whether the JSON
metadata has a GIN index.

## 4. Current user / service flow trace

Inferred flow for `search_competency`:

```
HTTP request -> SearchCompetencyRequest
  -> embed query text with the provider (Azure OpenAI, per Task.md)
  -> SQL: filter on class/framework, order by vector distance, limit
  -> rows -> SearchResultCompact or SearchResultFull -> SearchResponse
```

Inferred flow for vacancy extraction:

```
VacancyTextRequest (Functietitel, vacancy_description, limit, extraction_prompt)
  -> LLM prompt -> list of raw mentions
  -> for every mention: vector search in ESCO (limit) and in FGR (limit)
  -> flattened ExtractedCompetency list (raw_mention, class, uri, title, description, similarity_score, ontology)
```

To verify: the provider, prompt and caching, and whether there is a literal lookup before the vector search.

## 5. Legacy SQL / function review

Without the code I can only list what the DTO package shows and what I would look for.

Found in the package:

- `general_dtos.py` is an older copy of the browse, query and mutation DTOs. Nothing imports it. It has drifted:
  its `QueryEntitiesResponse` has no `total`, and `TripleIngestOneResponse` only exists there. Two
  definitions of the same contract will cause bugs, it should be deleted once nobody imports it.
- Naming is not consistent across responses: search results use `label` and `framework` (`"ESCO"`), but
  `ExtractedCompetency` uses `title` and `ontology` (`"esco"`). The same ESCO skill appears with
  `class: "competency"` in one example and `class: "skill"` in the filter docs.
- `VacancyTextRequest.Functietitel` is a Dutch, capitalised field name next to English snake_case fields.
- `query_relationships` returns `QueryEntitiesResponse`, which is a list of entities by name.

What I would look for in the code (from the "special attention" list in Task.md):

- functions that build and return SQL strings, especially with filter values formatted into the string
- SQL or table names reaching the service layer, for example service methods that know the table layout
- protocol code (FastAPI, request parsing) and infrastructure code (connections, provider clients) in one module
- vector, content and graph writes happening in one function, which is what `add_entity` suggests

The prototype answers these by design: every query goes through SQLAlchemy expressions with bound values,
filters are checked against a whitelist (`store/filters.py`), and the service layer only sees the
`OntologyStore` interface.

## 6. Proposed ontology store interface

`application/ontology_store/store/interface.py`. Grouped as Task.md asks:

| Group | Methods |
|---|---|
| entities | `get_entity`, `query_entities`, `count_entities`, `browse_entities` |
| relationships | `query_relationships`, `get_neighbours`, `get_linked_entities` |
| literal search | `literal_search` |
| vector search | `vector_search` |
| ingestion | `register_dataset`, `import_entities`, `import_relationships`, `rebuild_embeddings`, `refresh_dataset_counts` |
| deletion | `delete_by_metadata`, `delete_dataset` |
| backup / export | `list_datasets`, `export_dataset` |

All methods take and return plain dicts and the canonical record models in `store/models.py`, never ORM
objects or SQL. The interface knows nothing about competencies. `CompetencyService` adds the domain rules:
which classes count as competencies, the `requires` predicate, and the DTO mapping.

Filters use the same shape as the current API: `{"class": "skill"}`, lists mean IN
(`{"class": ["skill", "competency"]}`), and `{"metadata": {...}}` means JSON containment. Unknown keys raise
`InvalidFilterError` instead of being ignored.

## 7. Proposed PostgreSQL schema

The SQLAlchemy models in `db/models/` are the schema. Alembic migration `0001` was generated from them and
then reviewed by hand (extensions added).

```
datasets       id (name@version) PK, name, version, source, manifest jsonb, entity_count, relationship_count
entities       uri PK, entity_id unique, entity_class, framework, label, description, language,
               group_name, subgroup_name, attributes jsonb, metadata jsonb, dataset_id FK -> datasets ON DELETE CASCADE
relationships  id PK, subject_uri, predicate_uri, object_uri, metadata jsonb, dataset_id FK -> datasets ON DELETE CASCADE,
               unique (subject_uri, predicate_uri, object_uri)
embeddings     id PK, entity_uri FK -> entities ON DELETE CASCADE, model_name, model_version, text_fields, dim,
               source_text, text_hash, vector,
               unique (entity_uri, model_name, model_version, text_fields)
```

Indexes:

| Index | Purpose | File |
|---|---|---|
| (entity_class, framework), language, dataset_id | filters | `entities.py` |
| GIN jsonb_path_ops on entities.metadata and relationships.metadata | `metadata` containment filters | `entities.py`, `relationships.py` |
| GIN gin_trgm_ops on label and description, btree on lower(label) | literal search | `literal_indexes.py` |
| unique (s, p, o), (object_uri, predicate_uri), predicate_uri | graph lookups both directions | `relationships.py`, `graph_indexes.py` |
| (model_name, model_version, text_fields) | vector scope | `embeddings.py` |
| partial HNSW per model, created at index build time | ANN search | `vector_indexes.py` |

Choices:

- `uri` is the primary key because every operation in the API addresses entities by URI.
- No foreign keys from relationships to entities. The current API has `check_entities_exist: false`, so
  dangling edges are allowed on purpose. The check is done in the import instead.
- `class` and `group` are SQL keywords, so the columns are `entity_class` and `group_name`; the public
  records still use `class` and `group`.

Migration strategy: models are the source of truth, `alembic revision --autogenerate`, review the file,
commit it, `create_schema` runs `upgrade head`. Scripts never define tables themselves.

## 8. Proposed ingestion lifecycle

Canonical input is a folder:

```
manifest.json         name, version, source, files, record_counts
entities.jsonl        one CanonicalEntity per line
relationships.jsonl   one CanonicalRelationship per line
```

`import_canonical` does:

1. read and validate the manifest and every record (pydantic, unknown fields rejected, line number in errors)
2. compare record counts with the manifest
3. upsert the dataset row
4. upsert entities by URI, then delete entities of this dataset that are no longer in the file
5. check relationship endpoints exist, upsert by (s, p, o), delete stale relationships of this dataset
6. compare counts in the database with the files
7. build embeddings for new or changed text, create the HNSW index for the model

Running it twice gives the same state and re-embeds nothing. Changing one description re-embeds one entity.
`delete_dataset` removes the dataset row and the cascade removes its entities, relationships and embeddings.

Known gap: each step is its own transaction. A failed count check leaves the partial load in place (it can be
deleted with `delete_dataset`). With more time I would load inside one transaction or into a staging schema.

## 9. Proposed vector indexing design

- `EmbeddingModel` interface: `name`, `version`, `dim`, `embed_texts`, `embed_query`. The store depends only on
  this. Implementations: `HashingEmbeddingModel` (deterministic, no download, used in tests) and
  `SentenceTransformerModel` (multilingual MiniLM, 384 dim, used in the demo). Azure OpenAI is one more class
  with the same four members.
- Vectors live in their own table, not in the entity row. Each row stores model name, version, dim, which fields
  were embedded, the exact source text and its hash.
- The `vector` column has no fixed dimension, so models of different sizes can share the table. Each model gets a
  partial HNSW index on `vector::vector(dim)` filtered on its name, version and fields. I checked with
  `EXPLAIN` that searches use it.
- Switching model: build the new model's embeddings next to the old ones, compare results, switch the service
  config, then delete the old rows. No migration needed.
- Rebuild: `rebuild_indexes --model X` only embeds rows whose text hash changed, `--force` embeds everything.

At ESCO size (about 17k entities) with filters, HNSW returns the nearest neighbours first and filters after, which
can return fewer rows than asked. pgvector 0.8 (the version in the Docker image) has iterative index scans for
this, which I would turn on and benchmark.

## 10. Proposed literal indexing design

- Case-insensitive substring match (`ILIKE`) over label and description, wildcards in user input escaped.
- Ranking: exact label match, then label prefix, then label substring, then description only; ties by trigram
  similarity.
- `pg_trgm` GIN indexes make `ILIKE '%term%'` use an index, so no search engine is needed.
- Same filter whitelist as every other query.

A later version could add PostgreSQL full text search with a Dutch dictionary, or hybrid ranking of literal and
vector scores.

## 11. Proposed graph retrieval design

Plain relational storage of triples with indexes for both directions:

- `query_relationships` by any combination of subject, predicate, object, dataset and metadata
- `get_neighbours(uri, predicates, direction)` returns the edge, the other end and its label, in or out or both
- `get_linked_entities(uri, predicates, direction, filters)` returns full entity records with the edge metadata,
  which is what "competencies required by an occupation" needs (`CompetencyService.required_competencies`)

Multi-hop traversal (skill -> FGR competency -> other skills) can be a recursive CTE when it is needed. No graph
database.

## 12. Backup and restore proposal

Two levels, both tested by hand:

| Level | Tool | Use |
|---|---|---|
| full database | `backup_pg_dump.sh` / `restore_pg_dump.sh` (pg_dump custom format) | exact copy including embeddings and indexes, fast restore |
| dataset | `export_store` / `import_store` (canonical files) | rebuild from source, move one dataset between environments, review changes in git |

Local restore:

```bash
docker compose up -d
application/ontology_store/backup/restore_pg_dump.sh backups/<file>.dump
```

or from canonical files with any embedding model:

```bash
python -m ontology_store.db.scripts.create_schema
python -m ontology_store.backup.import_store exports --model st
```

## 13. Required files, secrets and access rights

| Item | Needed for |
|---|---|
| canonical datasets from Work Package 1 (manifest + records) | ingestion |
| `DATABASE_URL` with a user that can create tables and extensions in its own schema | migrations |
| a separate read/write user without DDL rights | the running service |
| Azure OpenAI endpoint, key, deployment name and API version | production embeddings |
| LLM endpoint and the extraction prompt | vacancy extraction |
| `vector` and `pg_trgm` extensions allowed on the managed Postgres | indexes |
| storage location for pg_dump files | backups |
| read access to the current service repository | finishing sections 1 to 5 |

No secrets are in the repository. `.env.example` lists the variable names only.

## 14. Open questions for review

1. Can I get the current store and service code to finish the legacy review?
2. Which embedding model and dimension are used in production, and should two models be served side by side
   during a switch?
3. What is the exact canonical format from Work Package 1, and are entity ids always `<framework>:<class>:<id>`?
4. When the same URI comes in two datasets or versions, should the newer one win (prototype behaviour) or should
   versions live side by side?
5. Is a local PostgreSQL + pgvector in Docker acceptable for development, and what Postgres runs in production
   (managed service, pgvector version)?
6. Should `delete_by_metadata` with an entity filter also delete the entity's relationships (prototype does) and
   should the count include them?
7. ESCO skills appear as `class: "skill"` and as `class: "competency"` in the examples. Which is correct?
8. Are filter values meant to stay case sensitive?
