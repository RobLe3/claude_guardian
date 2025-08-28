#!/bin/bash
# =============================================================================
# Claude Guardian Production Deployment Script
# =============================================================================
set -euo pipefail

# Configuration
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env"
PROJECT_NAME="claude-guardian"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose v2 is not available. Please upgrade Docker."
        exit 1
    fi
    
    # Check system resources
    local total_mem=$(free -m | awk '/^Mem:/{print $2}')
    if [[ $total_mem -lt 4096 ]]; then
        log_warn "System has less than 4GB RAM. Claude Guardian may run slowly."
    fi
    
    local free_space=$(df . | awk 'NR==2 {print $4}')
    if [[ $free_space -lt 20971520 ]]; then  # 20GB in KB
        log_warn "Less than 20GB free space available."
    fi
    
    log_success "Prerequisites check completed"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f ".env.template" ]]; then
            cp .env.template "$ENV_FILE"
            log_warn "Created $ENV_FILE from template. Please edit with your configuration."
            echo
            echo "REQUIRED: Edit the following variables in $ENV_FILE:"
            echo "  - POSTGRES_PASSWORD (set a secure password)"  
            echo "  - JWT_SECRET (minimum 32 characters)"
            echo
            read -p "Press Enter after updating $ENV_FILE..."
        else
            log_error "$ENV_FILE not found and no template available."
            exit 1
        fi
    fi
    
    # Validate required environment variables
    source "$ENV_FILE"
    
    if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
        log_error "POSTGRES_PASSWORD not set in $ENV_FILE"
        exit 1
    fi
    
    if [[ -z "${JWT_SECRET:-}" ]] || [[ ${#JWT_SECRET} -lt 32 ]]; then
        log_error "JWT_SECRET not set or too short (minimum 32 characters) in $ENV_FILE"
        exit 1
    fi
    
    # Create data directories
    mkdir -p "${QDRANT_DATA_PATH:-./data/qdrant}"
    mkdir -p "${POSTGRES_DATA_PATH:-./data/postgres}"
    mkdir -p "./data/logs"
    
    log_success "Environment setup completed"
}

# Deploy services
deploy_services() {
    log_info "Deploying Claude Guardian services..."
    
    # Pull latest images
    docker compose -f "$COMPOSE_FILE" pull
    
    # Start services
    docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
    
    log_success "Services deployment initiated"
}

# Wait for services
wait_for_services() {
    log_info "Waiting for services to become healthy..."
    
    local max_attempts=60
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if docker compose -f "$COMPOSE_FILE" ps --format table | grep -q "healthy"; then
            if [[ $(docker compose -f "$COMPOSE_FILE" ps --format table | grep -c "healthy") -ge 2 ]]; then
                log_success "Core services are healthy"
                break
            fi
        fi
        
        ((attempt++))
        echo -n "."
        sleep 5
    done
    echo
    
    if [[ $attempt -ge $max_attempts ]]; then
        log_error "Services failed to become healthy within expected time"
        log_info "Checking service status:"
        docker compose -f "$COMPOSE_FILE" ps
        exit 1
    fi
}

# Test deployment
test_deployment() {
    log_info "Testing deployment..."
    
    # Test MCP health endpoint
    if curl -f -s "http://127.0.0.1:8083/health" > /dev/null; then
        log_success "MCP service is responding"
    else
        log_error "MCP service health check failed"
        return 1
    fi
    
    # Test database connectivity
    if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER:-cguser}" > /dev/null; then
        log_success "PostgreSQL is accepting connections"
    else
        log_error "PostgreSQL connection failed"
        return 1
    fi
    
    # Test Qdrant
    if curl -f -s "http://localhost:6333/readyz" > /dev/null 2>&1; then
        log_success "Qdrant vector database is ready"
    else
        log_warn "Qdrant health check failed (this may be normal if not exposed)"
    fi
    
    log_success "Deployment testing completed"
}

# Show deployment info
show_info() {
    echo
    echo "=============================================================================="
    echo "                    Claude Guardian Deployment Complete"
    echo "=============================================================================="
    echo
    echo "🚀 MCP Endpoint:     ws://127.0.0.1:8083"
    echo "🏥 Health Check:     http://127.0.0.1:8083/health"
    echo "📊 Service Status:   docker compose -f $COMPOSE_FILE ps"
    echo "📋 Service Logs:     docker compose -f $COMPOSE_FILE logs -f [service]"
    echo
    echo "Configuration for Claude Code:"
    echo '{'
    echo '  "mcpServers": {'
    echo '    "claude-guardian": {'
    echo '      "command": "docker",'
    echo '      "args": ["exec", "claude-guardian-mcp", "/app/claude-guardian-mcp"],'
    echo '      "env": {'
    echo '        "MCP_ENDPOINT": "ws://127.0.0.1:8083"'
    echo '      }'
    echo '    }'
    echo '  }'
    echo '}'
    echo
    echo "Next Steps:"
    echo "1. Configure Claude Code with the MCP server endpoint"
    echo "2. Test security tool functionality"
    echo "3. Review audit logs: docker compose -f $COMPOSE_FILE logs claude-guardian-mcp"
    echo "4. Monitor performance: docker stats"
    echo
    echo "Documentation: README.md"
    echo "=============================================================================="
}

# Show usage
usage() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  deploy      Deploy Claude Guardian (default)"
    echo "  start       Start existing services"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"  
    echo "  status      Show service status"
    echo "  logs        Show service logs"
    echo "  cleanup     Remove all containers and volumes"
    echo "  update      Pull latest images and restart"
    echo "  help        Show this help message"
    echo
}

# Main execution
main() {
    local command="${1:-deploy}"
    
    case "$command" in
        deploy)
            check_prerequisites
            setup_environment
            deploy_services
            wait_for_services
            test_deployment
            show_info
            ;;
        start)
            docker compose -f "$COMPOSE_FILE" start
            log_success "Services started"
            ;;
        stop)
            docker compose -f "$COMPOSE_FILE" stop
            log_success "Services stopped"
            ;;
        restart)
            docker compose -f "$COMPOSE_FILE" restart
            log_success "Services restarted"
            ;;
        status)
            docker compose -f "$COMPOSE_FILE" ps
            ;;
        logs)
            docker compose -f "$COMPOSE_FILE" logs -f "${2:-}"
            ;;
        cleanup)
            read -p "This will remove all containers and data. Are you sure? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
                docker system prune -f
                log_success "Cleanup completed"
            fi
            ;;
        update)
            docker compose -f "$COMPOSE_FILE" pull
            docker compose -f "$COMPOSE_FILE" up -d
            log_success "Update completed"
            ;;
        help)
            usage
            ;;
        *)
            log_error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"