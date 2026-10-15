# Ontology Store, Indexing and PostgreSQL Layer

## Purpose

Redesign the ontology service store layer assuming a canonical dataset already exists.

Work Package 1 defines the documented datasets and canonical data input. This work package starts from that canonical input and defines how it should be loaded, indexed, searched, backed up and exposed through a clean ontology store.

The goal is a standalone ontology store module that is:

```
reproducible
testable
backend-clean
domain-agnostic at the base layer
usable by the competency ontology service
ready for vector, literal and graph-based retrieval
```

## Assumption

The input is a canonical dataset with defined record models, for example:

```
canonical entities
canonical relationships
source/context records
dataset manifests
record schemas
records files
```

The store layer should not own source-specific transformation logic. It should ingest canonical data and build indexed storage from it.

## Current Behaviour to Preserve

The current service behaviour is mostly defined through the service definitions and DTOs.

The implementation should preserve the current outside behaviour, including operations such as:

```
search_competency
search_occupation
browse_entities
get_entity
query_entities
query_relationships
add_entity
delete_by_metadata
vacancy skill extraction / mapping where currently supported
```

The current DTO boundary includes search, browse, query, mutation and vacancy extraction models.

## Main Task

Define the requirements for a clean ontology store implementation.

The developer should study the current implementation and prepare the refactor requirements for:

```
SQLAlchemy store
DDL files
pgvector indexing
literal indexing
graph relationship retrieval
canonical data ingestion
dataset lifecycle operations
backup and restore
embedding model plugin interface
base store interface
competency service integration
```

## Design Target

Separate the layers clearly:

```
canonical data input
        ↓
ontology store ingestion
        ↓
PostgreSQL tables and indexes
        ↓
generic ontology store interface
        ↓
competency ontology service
```

The base ontology store should be domain-agnostic.

The competency ontology service should sit on top and provide competency-specific behaviour.

## Required Store Capabilities

The store should support:

```
load canonical entities
load canonical relationships
retrieve entity by URI
browse entities
query entities by filters
query relationships by subject / predicate / object
literal search
vector search
metadata filtering
delete by dataset or metadata
export / backup
restore / reload
```

## Indexing Requirements

### 1. Vector indexing

Build a clean vector indexing layer.

Requirements:

```
generic embedding model interface
embedding model used as plugin
support indexing selected text fields
support storing embedding model/version metadata
support rebuilding embeddings
support pgvector search
keep vector indexing separate from entity content storage
```

The embedding layer should not be hardcoded to one provider. Azure OpenAI can be one implementation, but the store should depend on a generic interface.

Example interface direction:

```python
class EmbeddingModel:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...
```

### 2. Literal indexing

Add a simple literal indexing layer first.

Requirements:

```
exact / substring match over selected fields
case-insensitive matching where useful
filter support over declared searchable/filterable columns
no unnecessary search-engine dependency in the first version
```

This should cover the current simple lookup and matching needs before adding more advanced lexical search.

### 3. Graph retrieval

Support relationship-based retrieval from canonical relationship records.

Requirements:

```
query by subject_uri
query by predicate_uri
query by object_uri
retrieve neighbours of an entity
retrieve competencies linked to an occupation/profile
preserve relationship metadata
```

The graph layer does not need to become a full graph database. It should be clean relational storage for ontology relationships.

## PostgreSQL Requirements

Use a cleaner PostgreSQL implementation.

The developer should define requirements for:

```
SQLAlchemy
Psycopg 3 as driver
Self documenting data model
Explicit table creation flow
Explicit index creation flow
Database migration strategy
```

The current table store / pgvector integration should also be reviewed and simplified where possible.

## Data models

The `store` package should contain explicit Python data models that define the database schema using SQLAlchemy, rather than maintaining standalone SQL DDL files.

The SQLAlchemy models should be the canonical schema definition for entities, relationships, embeddings, indexes, constraints, and PostgreSQL-specific extensions where applicable. Schema changes should be managed through Alembic migrations generated from these models and reviewed before application.

Suggested structure:

```
ontology_store/
├── db/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── entities.py
│   │   ├── relationships.py
│   │   ├── embeddings.py
│   │   ├── literal_indexes.py
│   │   ├── vector_indexes.py
│   │   └── graph_indexes.p
│   │
│   ├── scripts/
│   │   ├── create_schema.py
│   │   ├── reset_schema.py
│   │   ├── backup_pg_dump.sh
│   │   ├── restore_pg_dump.sh
│   │   └── copy_dataset.py
│   │
│   ├── migrations/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │
│   └── README.md
```

Operational scripts should not contain ad hoc table definitions. They should import the SQLAlchemy metadata and/or invoke Alembic so that all schema creation and migration logic remains centralized.

## Suggested Module Structure

```
ontology_store/
├── README.md
│
├── service/
│   ├── ontology_service.py
│   ├── competency_service.py
│   └── dto.py
│
├── store/
│   ├── interface.py
│   ├── postgres_store.py
│   ├── models.py
│   └── errors.py
│
├── ingestion/
│   ├── import_canonical.py
│   ├── import_entities.py
│   ├── import_relationships.py
│   ├── rebuild_indexes.py
│   └── delete_dataset.py
│
├── indexing/
│   ├── embedding_model.py
│   ├── vector_index.py
│   ├── literal_index.py
│   └── graph_index.py
│
├── db/
│   ├── models/
│   ├── scripts/
│   └── migrations/
│
├── backup/
│   ├── export_store.py
│   ├── import_store.py
│   ├── backup_pg_dump.sh
│   └── restore_pg_dump.sh
│
└── tests/
    ├── fixtures/
    ├── test_store_interface.py
    ├── test_ingestion.py
    ├── test_literal_search.py
    ├── test_vector_search.py
    └── test_graph_retrieval.py
```

## Store Interface Requirements

Define a stable base store interface.

The interface should be generic and not tied to competencies only.

Expected operations:

```python
class OntologyStore:
    def get_entity(self, uri: str): ...
    def query_entities(self, filters: dict, limit: int | None = None): ...
    def browse_entities(self, page_number: int, page_size: int, filters: dict | None = None): ...

    def query_relationships(self, filters: dict, limit: int | None = None): ...
    def get_neighbours(self, uri: str, predicates: list[str] | None = None): ...

    def literal_search(self, query: str, filters: dict | None = None, limit: int = 10): ...
    def vector_search(self, query: str, filters: dict | None = None, limit: int = 10): ...

    def import_entities(self, records): ...
    def import_relationships(self, records): ...
    def delete_by_metadata(self, filters: dict): ...
```

The final method names can change, but the requirements should clearly separate:

```
entity operations
relationship operations
literal search
vector search
ingestion
deletion
backup/export
```

## Ingestion and Lifecycle Requirements

Define clear lifecycle operations.

Required flows:

```
create schema
load canonical dataset
insert/update entities
insert/update relationships
build literal indexes
build vector indexes
validate counts
delete dataset by metadata/source/version
export store backup
restore store backup
```

The lifecycle should make it easy to rebuild the database from canonical data.

## Backup and Export Requirements

The module should support reproducible backup and restore.

Requirements:

```
pg_dump or equivalent full database backup
restore script
export canonical store contents
copy/import script for dataset-level reload
documented local restore flow
```

The goal is that a developer can reproduce a given ontology store state from canonical data or from a backup.

## Developer Analysis Task

The developer should first inspect the current service and document:

```
current store implementation
current PostgreSQL integration
current pgvector usage
current table schemas
current service methods
current DTO/request/response boundary
current legacy SQL functions
current skill lookup flow
current indexing flow
current ingestion/deletion flow
current dependencies and secrets
```

Special attention:

```
legacy functions that return SQL code
places where SQL logic leaks through service boundaries
places where protocol and infrastructure logic are mixed
places where vector, content and graph indexing are coupled
```

## Deliverables

The developer should deliver:

```
current store architecture summary
current outside behaviour summary
current PostgreSQL/pgvector review
current user/service flow trace
legacy SQL/function review
proposed ontology store interface
proposed PostgreSQL schema/DDL structure
proposed ingestion lifecycle
proposed vector indexing design
proposed literal indexing design
proposed graph retrieval design
backup/restore proposal
required files, secrets and access rights
open questions for review
```

---

## Part 2: Practical Implementation (Required)

The analysis and design work above is necessary but not sufficient. To demonstrate this design actually holds up, implement a **working, runnable prototype** of the base ontology store — not the full production system, but enough real code to prove the interface and layering decisions out.

At minimum, the practical submission should include:

```
a working SQLAlchemy models module (entities, relationships, embeddings)
a runnable schema creation script (create_schema.py or an Alembic migration)
an ingestion script that loads a small canonical fixture dataset
  (10-20 sample entities and relationships is enough - synthetic is fine)
a working implementation of the base OntologyStore interface covering at least:
    get_entity
    query_entities
    query_relationships / get_neighbours
    literal_search
    vector_search (pgvector, or a clearly-documented local stand-in
    such as sqlite + a simple cosine-similarity fallback, if pgvector
    is not practical in the take-home environment)
a small test suite exercising ingestion + each search path
a short script or CLI demo that ingests the fixture data and runs
  one query of each type end to end, with output shown
```

This does not need to be production-hardened, and it does not need to cover graph retrieval, backup/restore, or embedding-provider pluggability beyond a clean interface stub — those can remain design-only if time is short. But the core ingestion → store → literal/vector search path must actually run, not just be described.

Be explicit in your README about what is real, what is stubbed, and what you would build out next with more time. We'd rather see a small working slice than a large undemonstrated design.

## Submission Note: Solution Walkthrough Video

Along with the code and design write-up, please record and share a short video (10–15 minutes) walking through your solution. This should cover:

```
how you approached the problem and the key decisions you made
the architecture you landed on, and why, including any
  alternatives you considered and rejected
a live walkthrough of the working prototype (the demo script/tests
  actually running, not just slides)
the trade-offs and open questions you'd want to review with the team
what you would do differently, or build out next, with more time
```

We care more about how you think and how you arrived at the design than a polished recording — a screen share with narration is exactly what we're looking for, no editing required.

## Out of Scope

This work package should not:

```
change the canonical data model
own source-data transformations
change public service behaviour without review
add new product features
replace the UI flow
build a full graph database
make one embedding provider mandatory
```

## Expected Result

At the end of this work package, the team should have both a clear implementation plan **and** a working prototype for the ontology store refactor.

The plan should explain how canonical data becomes a cleanly indexed PostgreSQL-backed ontology store, with separated vector, literal and graph retrieval layers, and with a stable interface that the competency service can build on. The prototype should demonstrate that this design actually works end to end on real (fixture) data, and the walkthrough video should make the reasoning behind both legible to someone who wasn't in the room while it was built.