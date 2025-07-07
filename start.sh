#!/bin/bash
set -e

echo "Starting Task Management API..."

# Set default environment variables if not provided
export DATABASE_URL=${DATABASE_URL:-"sqlite+aiosqlite:///./data/tasks.db"}
export SECRET_KEY=${SECRET_KEY:-"your-secret-key-change-this-in-production"}
export API_KEY=${API_KEY:-"123456"}
export PORT=${PORT:-8000}

echo "Environment configured:"
echo "- PORT: $PORT"
echo "- DATABASE_URL: $DATABASE_URL"
echo "- DEBUG: ${DEBUG:-False}"

# Create data directory if using SQLite
if [[ $DATABASE_URL == *"sqlite"* ]]; then
    echo "Creating SQLite data directory..."
    mkdir -p /app/data
    chmod 755 /app/data
fi

# Start the application
echo "Starting FastAPI application on port $PORT..."
exec python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info