#!/bin/sh
echo "Running database migrations..."
alembic upgrade head

echo "Starting FastAPI application on port ${PORT:-8000}..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}