#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Default values
DEFAULT_HOST=${HOST:-0.0.0.0}
DEFAULT_PORT=${PORT:-8000}
DEFAULT_WORKERS=${WORKERS:-4}
DEFAULT_LOG_LEVEL=${LOG_LEVEL:-info}

log "Starting IFF-Guardian application..."
log "Environment: ${APP_ENV:-production}"
log "Version: ${APP_VERSION:-latest}"

# Wait for database
wait_for_db() {
    log "Waiting for database connection..."
    
    if [ -n "$DATABASE_URL" ]; then
        # Extract host and port from DATABASE_URL
        DB_HOST=$(echo $DATABASE_URL | sed -E 's/.*@([^:]+):([0-9]+).*/\1/')
        DB_PORT=$(echo $DATABASE_URL | sed -E 's/.*@([^:]+):([0-9]+).*/\2/')
        
        if [ "$DB_HOST" != "$DATABASE_URL" ] && [ "$DB_PORT" != "$DATABASE_URL" ]; then
            log "Checking database connectivity to $DB_HOST:$DB_PORT"
            
            for i in {1..30}; do
                if nc -z "$DB_HOST" "$DB_PORT" > /dev/null 2>&1; then
                    success "Database is ready!"
                    return 0
                fi
                warning "Database not ready, waiting... (attempt $i/30)"
                sleep 2
            done
            
            error "Database connection timeout"
            exit 1
        else
            warning "Could not parse DATABASE_URL, skipping database check"
        fi
    else
        warning "DATABASE_URL not set, skipping database check"
    fi
}

# Wait for Redis
wait_for_redis() {
    log "Waiting for Redis connection..."
    
    if [ -n "$REDIS_URL" ]; then
        # Extract host and port from REDIS_URL
        REDIS_HOST=$(echo $REDIS_URL | sed -E 's/redis:\/\/([^:]+):([0-9]+).*/\1/')
        REDIS_PORT=$(echo $REDIS_URL | sed -E 's/redis:\/\/([^:]+):([0-9]+).*/\2/')
        
        if [ "$REDIS_HOST" != "$REDIS_URL" ] && [ "$REDIS_PORT" != "$REDIS_URL" ]; then
            log "Checking Redis connectivity to $REDIS_HOST:$REDIS_PORT"
            
            for i in {1..30}; do
                if nc -z "$REDIS_HOST" "$REDIS_PORT" > /dev/null 2>&1; then
                    success "Redis is ready!"
                    return 0
                fi
                warning "Redis not ready, waiting... (attempt $i/30)"
                sleep 2
            done
            
            error "Redis connection timeout"
            exit 1
        else
            warning "Could not parse REDIS_URL, skipping Redis check"
        fi
    else
        warning "REDIS_URL not set, skipping Redis check"
    fi
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    if command -v alembic >/dev/null 2>&1; then
        if [ -f "alembic.ini" ]; then
            alembic upgrade head
            success "Database migrations completed"
        else
            warning "alembic.ini not found, skipping migrations"
        fi
    else
        warning "Alembic not installed, skipping migrations"
    fi
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    mkdir -p /var/log/iff-guardian
    mkdir -p /var/lib/iff-guardian
    mkdir -p /tmp/uploads
    
    success "Directories created"
}

# Validate environment
validate_environment() {
    log "Validating environment..."
    
    # Check required environment variables
    required_vars=("SECRET_KEY")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
    
    # Validate SECRET_KEY length
    if [ ${#SECRET_KEY} -lt 32 ]; then
        error "SECRET_KEY must be at least 32 characters long"
        exit 1
    fi
    
    success "Environment validation passed"
}

# Set up logging
setup_logging() {
    log "Setting up logging..."
    
    # Ensure log directory exists and is writable
    if [ ! -w "/var/log/iff-guardian" ]; then
        warning "Cannot write to /var/log/iff-guardian, using /tmp for logs"
        export LOG_DIR="/tmp"
    else
        export LOG_DIR="/var/log/iff-guardian"
    fi
    
    success "Logging configured"
}

# Main execution
main() {
    # Validate environment first
    validate_environment
    
    # Set up logging
    setup_logging
    
    # Create directories
    create_directories
    
    # Wait for dependencies
    wait_for_db
    wait_for_redis
    
    # Run migrations
    if [ "$RUN_MIGRATIONS" = "true" ]; then
        run_migrations
    fi
    
    # Handle different commands
    case "$1" in
        "web"|"server"|"uvicorn")
            log "Starting web server..."
            exec uvicorn iff_guardian.main:app \
                --host "$DEFAULT_HOST" \
                --port "$DEFAULT_PORT" \
                --workers "$DEFAULT_WORKERS" \
                --log-level "$DEFAULT_LOG_LEVEL" \
                --access-log \
                --proxy-headers
            ;;
        "worker"|"celery-worker")
            log "Starting Celery worker..."
            exec celery -A iff_guardian.celery.app worker \
                --loglevel="$DEFAULT_LOG_LEVEL" \
                --concurrency="$DEFAULT_WORKERS"
            ;;
        "beat"|"celery-beat")
            log "Starting Celery beat scheduler..."
            exec celery -A iff_guardian.celery.app beat \
                --loglevel="$DEFAULT_LOG_LEVEL"
            ;;
        "migrate"|"migration")
            log "Running migrations only..."
            run_migrations
            exit 0
            ;;
        "shell")
            log "Starting interactive shell..."
            exec python -c "from iff_guardian.main import app; import IPython; IPython.embed()"
            ;;
        "test")
            log "Running tests..."
            exec pytest "${@:2}"
            ;;
        *)
            log "Starting with custom command: $*"
            exec "$@"
            ;;
    esac
}

# Trap signals for graceful shutdown
trap 'log "Shutting down gracefully..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"