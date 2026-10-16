## Bhaskar's Presentation : Loom link 
# Ontology Store

Prototype of the ontology store refactor described in `application/ontology_service/Task.md`.
It loads a canonical dataset into PostgreSQL, keeps literal, vector and graph retrieval in separate layers,
and puts the existing competency service DTOs on top of a generic store interface.

The design write-up (current state review, proposed schema, lifecycle, open questions) is in [DESIGN.md](DESIGN.md).

## Quick start (one command)

You need three things installed first:

| | Linux | macOS | Windows |
|---|---|---|---|
| Git | `sudo apt install git` | comes with Xcode tools | https://git-scm.com/download/win |
| Docker | Docker Engine or Docker Desktop, running | Docker Desktop, running | Docker Desktop, running |
| Python 3.11+ | `sudo apt install python3 python3-venv` | `brew install python@3.12` | https://www.python.org/downloads/ (tick "Add python.exe to PATH") |

Then clone and run the file for your system:

**Linux**

```bash
git clone https://github.com/bhaskarbarot/manektech.git
cd manektech
./linux.sh
```

**macOS**

```bash
git clone https://github.com/bhaskarbarot/manektech.git
cd manektech
./mac.sh
```

**Windows** (Command Prompt)

```bat
git clone https://github.com/bhaskarbarot/manektech.git
cd manektech
windows.bat
```

In PowerShell the last line is `.\windows.bat`. Double-clicking `windows.bat` in Explorer also works.

The script does everything in order and stops with a clear message if something is missing:

1. checks Docker is installed and running (starts Docker Desktop on Linux/macOS if it is installed but stopped)
2. checks Python 3.11 or newer
3. starts PostgreSQL 16 + pgvector in Docker on port 5433 and waits until it is healthy
4. creates the virtual environment `.venv`
5. installs the project and the local multilingual embedding model (CPU only)
6. creates the database schema with Alembic
7. runs the test suite (64 tests)
8. runs the demo: loads the sample dataset and runs one query of each type
9. installs Streamlit and opens a small test UI in your browser at http://localhost:8501 (press Ctrl+C to stop it)

The first run takes about 3 to 5 minutes, most of it downloading the embedding model.
Running the script again is safe and much faster.
The UI step comes after the success message, so if it cannot start, the setup, tests and demo results above are still valid.

**How to know it worked:** the tests line says `64 passed`, the demo prints results for sections 1 to 11, and the
last lines say `Setup, tests and demo finished successfully.` In the demo, vector search for
`leidinggeven aan een team` ("leading a team") should return `leiderschap` ("leadership") first. The words are
different but the meaning is the same.

**Quick mode:** `./linux.sh quick`, `./mac.sh quick` or `windows.bat quick` skips the embedding model download
and uses the small built-in hashing model. Everything still runs; the tests line then says `63 passed, 1 skipped`
(the skipped test needs the multilingual model), and vector search matches similar spelling, not meaning.

After the script, these work directly:

```bash
.venv/bin/python -m ontology_store.demo --model st
.venv/bin/pytest
.venv/bin/python -m streamlit run ui/app.py
docker compose down
```

(on Windows: `.venv\Scripts\python -m ontology_store.demo --model st`, `.venv\Scripts\pytest`,
`.venv\Scripts\python -m streamlit run ui\app.py`)

## Test UI

A small Streamlit page (`ui/app.py`) to try the store by hand. It uses the same database and embedding model as the demo,
and loads the sample dataset by itself if the database is empty.

| Tab | What you can do |
|---|---|
| Search | type any text, run literal search, vector search or both side by side, filter by class and framework |
| Entity explorer | pick an entity, see its details, outgoing links (e.g. competencies an occupation requires) and neighbours |
| Browse | page through all entities with class and framework filters |

Try `leidinggeven aan een team` in Search: literal search finds nothing (the words do not appear in the data), vector
search finds `leiderschap` by meaning. If the page says it cannot connect, start the database with
`docker compose up -d --wait` and reload. Streamlit is an optional extra (`pip install -e ".[ui]"`); the store and tests
do not depend on it.

**If something goes wrong**

| Message | Fix |
|---|---|
| Docker is not running | open Docker Desktop (or `sudo systemctl start docker`) and run the script again |
| Your user cannot use Docker | `sudo usermod -aG docker $USER`, log out and in, run again |
| port 5433 is already allocated | another program uses port 5433; stop it, or change `5433` in `docker-compose.yml` and in `.env.example` / `DATABASE_URL` |
| Python 3.11 or newer is required | install Python from the table above |
| could not create the virtual environment | Ubuntu/Debian: `sudo apt install python3-venv` |
| `permission denied: ./linux.sh` or `./mac.sh` | `bash linux.sh` or `bash mac.sh` |
| `windows.bat` is not recognized (PowerShell) | `.\windows.bat` |
| the window waits with "Press any key to continue" | that is on purpose so the result can be read, press any key |

## Run it step by step (manual)

Only needed if you do not want to use the scripts above.

```bash
docker compose up -d --wait
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -e ".[dev,local-embeddings]"
.venv/bin/python -m ontology_store.db.scripts.create_schema
.venv/bin/pytest
.venv/bin/python -m ontology_store.demo --model st
```

Postgres runs on port 5433 so it does not clash with a local install. Tests use the separate `ontology_test` database.

## Commands

| What | Command |
|---|---|
| create / upgrade schema | `python -m ontology_store.db.scripts.create_schema` |
| drop and recreate schema | `python -m ontology_store.db.scripts.reset_schema --yes` |
| load a canonical dataset | `python -m ontology_store.ingestion.import_canonical <folder> --model st` |
| rebuild embeddings + HNSW index | `python -m ontology_store.ingestion.rebuild_indexes --model st [--force]` |
| delete a dataset | `python -m ontology_store.ingestion.delete_dataset --dataset competency-sample@1.0.0` |
| delete by filters | `python -m ontology_store.ingestion.delete_dataset --filters '{"metadata": {"source": "seed"}}'` |
| export datasets to canonical files | `python -m ontology_store.backup.export_store --out exports` |
| reload exported datasets | `python -m ontology_store.backup.import_store exports` |
| full database backup | `application/ontology_store/backup/backup_pg_dump.sh [file]` |
| restore a backup | `application/ontology_store/backup/restore_pg_dump.sh <file>` |
| new migration after a model change | `alembic revision --autogenerate -m "..."` then review, then `alembic upgrade head` |

`DATABASE_URL`, `TEST_DATABASE_URL` and `EMBEDDING_MODEL` can be set as environment variables, see `.env.example`.

## Layout

```
linux.sh, mac.sh, windows.bat       one-command setup + tests + demo + test UI
docker-compose.yml                  PostgreSQL 16 + pgvector
ui/app.py, .streamlit/              small Streamlit test UI (optional extra "ui")
application/
├── ontology_service/data_models/   existing DTOs, unchanged
└── ontology_store/
    ├── db/models/        SQLAlchemy models = the schema (entities, relationships, embeddings, datasets, index definitions)
    ├── db/migrations/    Alembic, 0001 creates extensions, tables and indexes
    ├── db/scripts/       create_schema, reset_schema
    ├── store/            OntologyStore interface, PostgresOntologyStore, canonical record models, filters, errors
    ├── indexing/         embedding model plugins, literal index, vector index, graph index
    ├── ingestion/        canonical file reader, import, rebuild indexes, delete
    ├── backup/           export/import of canonical files, pg_dump/pg_restore scripts
    ├── service/          OntologyService + CompetencyService using the existing DTOs
    ├── tests/            pytest suite and the fixture dataset
    └── demo.py
```

## What is real, what is stubbed

| Part | Status |
|---|---|
| SQLAlchemy models + Alembic migration | real |
| canonical ingestion (manifest, validation, upsert, prune, count check) | real |
| get_entity, query_entities, browse_entities | real |
| literal search (ILIKE + pg_trgm GIN indexes, ranked) | real |
| vector search on pgvector with per-model HNSW index | real |
| graph retrieval (by subject/predicate/object, neighbours, linked entities) | real |
| delete by dataset / metadata | real |
| export, reload, pg_dump backup and restore | real, tested by hand |
| embedding plugins | hashing model (tests) and sentence-transformers (demo) are real; Azure OpenAI is design only |
| CompetencyService search / browse / query / add / delete using the existing DTOs | real |
| vacancy skill extraction | not built, needs the LLM prompt and the current code |
| HTTP layer | not built, the services return the DTOs so a FastAPI router is thin |
| Streamlit test UI | real, a thin page over the store for manual testing, not a product UI |

## Demo output

Run with `--model st`, shortened:

```
== 6. competencies required by softwareontwikkelaar
  competency | FGR | probleemoplossend vermogen | {'source': 'seed', 'relevance': 'essential'}
  skill | ESCO | programmeren in Python | {'source': 'seed', 'relevance': 'essential'}
  skill | ESCO | software testen | {'source': 'seed', 'relevance': 'essential'}
  skill | ESCO | SQL gebruiken | {'source': 'seed', 'relevance': 'optional'}

== 7. literal_search 'data'
  0.3571 | occupation | data engineer
  0.3333 | occupation | data scientist
  0.3125 | skill | data analyseren
  0.0 | skill | machine learning toepassen
  0.0 | skill | SQL gebruiken

== 9. vector_search 'leidinggeven aan een team'
  0.77 | competency | FGR | leiderschap
  0.4502 | skill | ESCO | muziekpersoneel managen
  0.2817 | skill | ESCO | met belanghebbenden communiceren

== 10. CompetencyService.search_competency (existing DTOs)
  {"results":[{"class":"competency","framework":"FGR","uri":"http://example.org/fgr/competency/001","label":"probleemoplossend vermogen", ... "similarity_score":0.8445}, ...]}
```

Literal scores are trigram similarity of the label, so description-only matches show 0.0 and are ranked last.

## Next with more time

- get the current service code and fill in the legacy review in DESIGN.md
- Azure OpenAI embedding plugin and a model switch run (two models side by side, then cut over)
- one transaction for the whole dataset load, or load into a staging schema and swap
- HNSW filtered search at ESCO scale (pgvector iterative scans), plus a benchmark
- FastAPI router on top of the services and contract tests against the current API
- vacancy extraction moved onto the new store
