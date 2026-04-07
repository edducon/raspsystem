#!/bin/sh
set -eu

if [ "${1:-}" = "" ]; then
  echo "Usage: sh infra/scripts/postgres-restore.sh <backup-file.sql>"
  exit 1
fi

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

docker compose -f "${COMPOSE_FILE}" exec -T postgres sh -lc \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "${BACKUP_FILE}"

echo "Restore completed from ${BACKUP_FILE}"
