#!/bin/sh

echo "=== Task Management API Startup ==="
echo "Environment: ${RAILWAY_ENVIRONMENT:-local}"
echo "Port: ${PORT:-8000}"

# Create data directory if it doesn't exist
mkdir -p /app/data

# Check if we're in Railway environment
if [ -n "$RAILWAY_ENVIRONMENT" ] || [ -n "$PORT" ]; then
    echo "Running in Railway environment"

    # Set default environment variables for Railway if not provided
    export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./data/tasks.db}"
    export SECRET_KEY="${SECRET_KEY:-$(openssl rand -base64 32)}"
    export ALGORITHM="${ALGORITHM:-HS256}"
    export ACCESS_TOKEN_EXPIRE_MINUTES="${ACCESS_TOKEN_EXPIRE_MINUTES:-30}"
    export API_KEY="${API_KEY:-123456}"
    export APP_NAME="${APP_NAME:-Task Management API}"
    export DEBUG="${DEBUG:-False}"

    echo "Environment variables configured for Railway"
else
    echo "Running in local environment"
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head
echo "Database migrations completed!"

echo "Starting FastAPI application..."
echo "Listening on 0.0.0.0:${PORT:-8000}"

# Start the FastAPI application
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info