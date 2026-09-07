#!/bin/sh
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Seeding initial approvers and test users from config..."
python -m app.core.seed

echo "Starting Uvicorn..."

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload


