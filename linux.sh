#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-full}"
VENV_PY=".venv/bin/python"

step() { printf '\n==> %s\n' "$1"; }
fail() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }

if [ "$MODE" != "full" ] && [ "$MODE" != "quick" ]; then
  fail "usage: ./linux.sh [full|quick]"
fi

step "Checking Docker"
command -v docker >/dev/null 2>&1 || fail "Docker is not installed. Install it from https://docs.docker.com/engine/install/ and run this script again."
if ! docker info >/dev/null 2>&1; then
  if systemctl --user list-unit-files docker-desktop.service >/dev/null 2>&1; then
    echo "Docker Desktop is not running, starting it..."
    systemctl --user start docker-desktop || true
    for _ in $(seq 1 40); do docker info >/dev/null 2>&1 && break; sleep 3; done
  fi
fi
if ! docker info >/dev/null 2>&1; then
  if docker info 2>&1 | grep -qi "permission denied"; then
    fail "Your user cannot use Docker. Run: sudo usermod -aG docker \$USER, log out and in again, then rerun."
  fi
  fail "Docker is not running. Start it (sudo systemctl start docker, or open Docker Desktop) and run this script again."
fi
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is missing. Install the docker compose plugin."

step "Checking Python 3.11+"
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    PYTHON="$candidate"
    break
  fi
done
[ -n "$PYTHON" ] || fail "Python 3.11 or newer is required. On Ubuntu: sudo apt install python3 python3-venv"
echo "using $($PYTHON --version)"

step "Starting PostgreSQL + pgvector in Docker (port 5433)"
docker compose up -d --wait

step "Creating virtual environment .venv"
if [ ! -x "$VENV_PY" ]; then
  "$PYTHON" -m venv .venv || fail "Could not create the virtual environment. On Ubuntu/Debian: sudo apt install python3-venv"
fi
"$VENV_PY" -m pip install --quiet --upgrade pip

step "Installing the project"
"$VENV_PY" -m pip install --quiet -e ".[dev]"

MODEL="hashing"
if [ "$MODE" = "full" ]; then
  step "Installing the local multilingual embedding model (CPU only, first run downloads a few hundred MB)"
  if "$VENV_PY" -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu \
    && "$VENV_PY" -m pip install --quiet -e ".[dev,local-embeddings]"; then
    MODEL="st"
  else
    echo "WARNING: could not install the local model, continuing with the built-in hashing model"
  fi
fi

step "Creating the database schema"
"$VENV_PY" -m ontology_store.db.scripts.create_schema

step "Running the tests"
"$VENV_PY" -m pytest -q

step "Running the demo (model: $MODEL)"
"$VENV_PY" -m ontology_store.demo --model "$MODEL"

step "Done"
echo "Setup, tests and demo finished successfully."
echo "Run the demo again:  .venv/bin/python -m ontology_store.demo --model $MODEL"
echo "Run the tests again: .venv/bin/pytest"
echo "Stop the database:   docker compose down"
