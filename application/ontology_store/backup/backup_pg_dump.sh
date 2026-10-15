#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."
mkdir -p backups
target="${1:-backups/ontology_$(date +%Y%m%d_%H%M%S).dump}"

docker compose exec -T postgres pg_dump -U ontology -d ontology --format=custom > "$target"
echo "backup written to $target"
