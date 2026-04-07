#!/bin/sh
set -eu

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
OUTPUT_DIR="${OUTPUT_DIR:-./backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT_FILE="${OUTPUT_DIR}/postgres_${TIMESTAMP}.sql"

mkdir -p "${OUTPUT_DIR}"

docker compose -f "${COMPOSE_FILE}" exec -T postgres sh -lc \
  'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "${OUTPUT_FILE}"

echo "Backup saved to ${OUTPUT_FILE}"
