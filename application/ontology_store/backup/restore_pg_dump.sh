#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "usage: $0 <backup.dump>"
  exit 1
fi

dump="$(realpath "$1")"
cd "$(dirname "$0")/../../.."

docker compose exec -T postgres pg_restore -U ontology -d ontology --clean --if-exists --no-owner < "$dump"
echo "restored $dump"
