#!/bin/bash
set -e

echo "=== Task Management API Startup ==="
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Railway sets PORT automatically, use it or default to 8000
export PORT=${PORT:-8000}
export DATABASE_URL=${DATABASE_URL:-"sqlite+aiosqlite:///./data/tasks.db"}
export SECRET_KEY=${SECRET_KEY:-"railway-production-secret-key-$(openssl rand -hex 32)"}
export API_KEY=${API_KEY:-"123456"}
export DEBUG=${DEBUG:-"False"}

echo "Environment configured:"
echo "- PORT: $PORT"
echo "- DATABASE_URL: $DATABASE_URL"
echo "- DEBUG: $DEBUG"

# Create data directory for SQLite
if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="sqlite+aiosqlite:////app/data/tasks.db"
else
    echo "Using provided DATABASE_URL"
fi

# add explicit path for sqlite
mkdir -p /app/data
chmod 755 /app/data
touch /app/data/tasks.db
chown appuser:appuser /app/data/tasks.db Test if main.py exists

if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found!"
    ls -la
    exit 1
fi
echo "Testing Python imports..."
python -c "import fastapi; print('FastAPI imported successfully')"
python -c "import uvicorn; print('Uvicorn imported successfully')"

echo "Starting FastAPI application on port $PORT..."
exec python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info --access-log