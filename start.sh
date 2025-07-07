#!/bin/bash
set -e

echo "=== Task Management API Startup ==="
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Railway sets PORT automatically, use it or default to 8000
export PORT=${PORT:-8000}
export DATABASE_URL=${DATABASE_URL:-"sqlite+aiosqlite:///./data/tasks.db"}
export SECRET_KEY=${SECRET_KEY:-"railway-production-secret-key-$(date +%s)"}
export API_KEY=${API_KEY:-"123456"}
export DEBUG=${DEBUG:-"False"}

echo "Environment configured:"
echo "- PORT: $PORT"
echo "- DATABASE_URL: $DATABASE_URL"
echo "- DEBUG: $DEBUG"

# Create data directory for SQLite
if [[ $DATABASE_URL == *"sqlite"* ]]; then
    echo "Creating SQLite data directory..."
    mkdir -p /app/data
    chmod 755 /app/data
fi

# Test if main.py exists
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found!"
    exit 1
fi

echo "Starting FastAPI application on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info