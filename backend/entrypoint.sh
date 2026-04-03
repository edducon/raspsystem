#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."

until python -c "
import os
import psycopg
psycopg.connect(
    host=os.getenv('POSTGRES_SERVER', 'postgres'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    dbname=os.getenv('POSTGRES_DB', 'rasp_db'),
    user=os.getenv('POSTGRES_USER', 'rasp_user'),
    password=os.getenv('POSTGRES_PASSWORD', 'rasp_password'),
).close()
"; do
  echo "PostgreSQL is unavailable - retrying in 2 seconds..."
  sleep 2
done

echo "PostgreSQL is up."
echo "Applying Alembic migrations..."
alembic upgrade head

echo "Starting backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
