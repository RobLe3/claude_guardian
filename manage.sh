#!/bin/bash
# =============================================================================
# Claude Guardian v2.0.0-alpha - Production Management & Operations
# Unified service lifecycle management for all deployment types
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
VERSION="2.0.0-alpha"
PROJECT_NAME="claude-guardian"

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

show_usage() {
    echo ""
    echo -e "${CYAN}🛡️  Claude Guardian v${VERSION} - Management Script${NC}"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo -e "${YELLOW}Service Operations:${NC}"
    echo "  start          Start Claude Guardian services"
    echo "  stop           Stop Claude Guardian services"
    echo "  restart        Restart Claude Guardian services"
    echo "  status         Show service status"
    echo "  logs           Show service logs"
    echo ""
    echo -e "${YELLOW}Deployment Operations:${NC}"
    echo "  deploy         Deploy/update services"
    echo "  rollback       Rollback to previous version"
    echo "  scale          Scale services"
    echo ""
    echo -e "${YELLOW}Maintenance Operations:${NC}"
    echo "  backup         Backup persistent data"
    echo "  restore        Restore from backup"
    echo "  cleanup        Clean up temporary files and containers"
    echo "  health         Run comprehensive health check"
    echo ""
    echo -e "${YELLOW}Development Operations:${NC}"
    echo "  test           Run test suite"
    echo "  validate       Validate configuration"
    echo "  debug          Start services in debug mode"
    echo ""
}

detect_deployment_type() {
    if [[ -f ".mcp_pid" && -f ".env" ]] && grep -q "GUARDIAN_MODE=mcp_only" .env 2>/dev/null; then
        echo "lightweight"
    elif [[ -f "config/docker-compose/docker-compose.yml" || -f "deployments/production/docker-compose.production.yml" ]]; then
        echo "docker"
    else
        echo "unknown"
    fi
}

# Service Operations
service_start() {
    local deployment_type=$(detect_deployment_type)
    
    case $deployment_type in
        "lightweight")
            log_info "Starting lightweight MCP service..."
            if [[ -f ".mcp_pid" ]]; then
                local pid=$(cat .mcp_pid)
                if kill -0 "$pid" 2>/dev/null; then
                    log_warn "Service already running (PID: $pid)"
                    return
                fi
            fi
            
            python3 scripts/start-mcp-service.py --port 8083 > /tmp/claude-guardian-mcp.log 2>&1 &
            echo "$!" > .mcp_pid
            sleep 2
            
            if lsof -i :8083 &> /dev/null; then
                log_success "MCP service started on port 8083"
            else
                log_error "Failed to start MCP service"
                return 1
            fi
            ;;
        "docker")
            log_info "Starting Docker services..."
            if [[ -f "deployments/production/docker-compose.production.yml" ]]; then
                docker-compose -f deployments/production/docker-compose.production.yml up -d
            else
                docker-compose -f config/docker-compose/docker-compose.yml up -d
            fi
            log_success "Docker services started"
            ;;
        *)
            log_error "Unknown deployment type. Run setup.sh first"
            return 1
            ;;
    esac
}

service_stop() {
    local deployment_type=$(detect_deployment_type)
    
    case $deployment_type in
        "lightweight")
            log_info "Stopping lightweight MCP service..."
            if [[ -f ".mcp_pid" ]]; then
                local pid=$(cat .mcp_pid)
                if kill -0 "$pid" 2>/dev/null; then
                    kill "$pid"
                    rm -f .mcp_pid
                    log_success "MCP service stopped"
                else
                    log_warn "Service not running"
                    rm -f .mcp_pid
                fi
            else
                log_warn "No PID file found"
            fi
            ;;
        "docker")
            log_info "Stopping Docker services..."
            if [[ -f "deployments/production/docker-compose.production.yml" ]]; then
                docker-compose -f deployments/production/docker-compose.production.yml down
            else
                docker-compose -f config/docker-compose/docker-compose.yml down
            fi
            log_success "Docker services stopped"
            ;;
        *)
            log_error "Unknown deployment type"
            return 1
            ;;
    esac
}

service_restart() {
    log_info "Restarting Claude Guardian services..."
    service_stop
    sleep 2
    service_start
}

service_status() {
    local deployment_type=$(detect_deployment_type)
    
    echo ""
    echo -e "${CYAN}🔍 Claude Guardian Service Status${NC}"
    echo -e "${BLUE}Deployment Type:${NC} $deployment_type"
    echo ""
    
    case $deployment_type in
        "lightweight")
            if [[ -f ".mcp_pid" ]]; then
                local pid=$(cat .mcp_pid)
                if kill -0 "$pid" 2>/dev/null; then
                    echo -e "${GREEN}✅ MCP Service:${NC} Running (PID: $pid)"
                    if lsof -i :8083 &> /dev/null; then
                        echo -e "${GREEN}✅ Port 8083:${NC} Listening"
                    else
                        echo -e "${RED}❌ Port 8083:${NC} Not listening"
                    fi
                else
                    echo -e "${RED}❌ MCP Service:${NC} Not running"
                fi
            else
                echo -e "${RED}❌ MCP Service:${NC} No PID file"
            fi
            ;;
        "docker")
            if command -v docker-compose &> /dev/null; then
                if [[ -f "deployments/production/docker-compose.production.yml" ]]; then
                    docker-compose -f deployments/production/docker-compose.production.yml ps
                else
                    docker-compose -f config/docker-compose/docker-compose.yml ps
                fi
            else
                log_error "Docker Compose not available"
            fi
            ;;
        *)
            log_error "Unknown deployment type. Run setup.sh first"
            ;;
    esac
}

service_logs() {
    local deployment_type=$(detect_deployment_type)
    local service_name="$2"
    
    case $deployment_type in
        "lightweight")
            log_info "Showing lightweight MCP service logs..."
            if [[ -f "/tmp/claude-guardian-mcp.log" ]]; then
                tail -f /tmp/claude-guardian-mcp.log
            else
                log_warn "No log file found"
            fi
            ;;
        "docker")
            if [[ -n "$service_name" ]]; then
                log_info "Showing logs for service: $service_name"
                docker-compose logs -f "$service_name"
            else
                log_info "Showing all service logs..."
                if [[ -f "deployments/production/docker-compose.production.yml" ]]; then
                    docker-compose -f deployments/production/docker-compose.production.yml logs -f
                else
                    docker-compose -f config/docker-compose/docker-compose.yml logs -f
                fi
            fi
            ;;
        *)
            log_error "Unknown deployment type"
            ;;
    esac
}

# Maintenance Operations
backup_data() {
    log_info "Creating backup of persistent data..."
    
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup data directories
    if [[ -d "data" ]]; then
        log_info "Backing up data directory..."
        cp -r data/ "$backup_dir/"
    fi
    
    # Backup configuration
    if [[ -f ".env" ]]; then
        cp .env "$backup_dir/"
    fi
    
    # Backup logs if lightweight mode
    if [[ -f "/tmp/claude-guardian-mcp.log" ]]; then
        cp /tmp/claude-guardian-mcp.log "$backup_dir/"
    fi
    
    # Create backup manifest
    cat > "$backup_dir/manifest.txt" << EOF
Claude Guardian Backup
Created: $(date)
Deployment Type: $(detect_deployment_type)
Version: $VERSION
Includes: data/, .env, logs
EOF
    
    log_success "Backup created: $backup_dir"
}

cleanup_system() {
    log_info "Cleaning up temporary files and containers..."
    
    # Clean temporary files
    rm -f /tmp/claude-guardian-*.log
    rm -f .mcp_pid
    rm -f claude-code-mcp-config.json
    
    # Clean Docker if available
    local deployment_type=$(detect_deployment_type)
    if [[ "$deployment_type" == "docker" ]]; then
        log_info "Stopping and removing containers..."
        docker-compose -f config/docker-compose/docker-compose.yml down --remove-orphans 2>/dev/null || true
        
        # Remove unused images
        log_info "Cleaning unused Docker images..."
        docker image prune -f 2>/dev/null || true
    fi
    
    # Clean Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    log_success "System cleanup complete"
}

health_check() {
    log_info "Running comprehensive health check..."
    
    local deployment_type=$(detect_deployment_type)
    local health_score=0
    local total_checks=5
    
    echo ""
    echo -e "${CYAN}🏥 Health Check Report${NC}"
    echo -e "${BLUE}Deployment:${NC} $deployment_type"
    echo ""
    
    # Check 1: Service running
    case $deployment_type in
        "lightweight")
            if [[ -f ".mcp_pid" ]] && kill -0 "$(cat .mcp_pid)" 2>/dev/null; then
                echo -e "${GREEN}✅ MCP Service:${NC} Running"
                ((health_score++))
            else
                echo -e "${RED}❌ MCP Service:${NC} Not running"
            fi
            ;;
        "docker")
            local containers_running=$(docker-compose -f config/docker-compose/docker-compose.yml ps -q | wc -l)
            if [[ $containers_running -gt 0 ]]; then
                echo -e "${GREEN}✅ Docker Services:${NC} $containers_running containers running"
                ((health_score++))
            else
                echo -e "${RED}❌ Docker Services:${NC} No containers running"
            fi
            ;;
    esac
    
    # Check 2: Port accessibility
    if lsof -i :8083 &> /dev/null; then
        echo -e "${GREEN}✅ Port 8083:${NC} Accessible"
        ((health_score++))
    else
        echo -e "${RED}❌ Port 8083:${NC} Not accessible"
    fi
    
    # Check 3: API health endpoint
    if curl -s http://localhost:8083/health &> /dev/null; then
        echo -e "${GREEN}✅ API Health:${NC} Responding"
        ((health_score++))
    else
        echo -e "${RED}❌ API Health:${NC} Not responding"
    fi
    
    # Check 4: Configuration
    if [[ -f ".env" ]]; then
        echo -e "${GREEN}✅ Configuration:${NC} Present"
        ((health_score++))
    else
        echo -e "${RED}❌ Configuration:${NC} Missing .env file"
    fi
    
    # Check 5: Claude Code integration
    if [[ -f "claude-code-mcp-config.json" ]]; then
        echo -e "${GREEN}✅ Claude Integration:${NC} Config available"
        ((health_score++))
    else
        echo -e "${YELLOW}⚠️  Claude Integration:${NC} Config not generated"
    fi
    
    echo ""
    local health_percentage=$((health_score * 100 / total_checks))
    
    if [[ $health_score -eq $total_checks ]]; then
        echo -e "${GREEN}🎉 System Health: EXCELLENT (${health_score}/${total_checks})${NC}"
    elif [[ $health_score -ge 3 ]]; then
        echo -e "${YELLOW}⚠️  System Health: GOOD (${health_score}/${total_checks})${NC}"
    else
        echo -e "${RED}❌ System Health: POOR (${health_score}/${total_checks})${NC}"
        echo -e "${YELLOW}💡 Suggestion: Run setup.sh to fix configuration issues${NC}"
    fi
    echo ""
}

validate_config() {
    log_info "Validating Claude Guardian configuration..."
    
    local errors=0
    
    # Check .env file
    if [[ -f ".env" ]]; then
        log_success "Environment file exists"
        
        # Check required variables
        local required_vars=("MCP_PORT")
        for var in "${required_vars[@]}"; do
            if grep -q "^$var=" .env; then
                log_success "Required variable: $var"
            else
                log_error "Missing required variable: $var"
                ((errors++))
            fi
        done
    else
        log_error "Missing .env file"
        ((errors++))
    fi
    
    # Check Python installation
    if command -v python3 &> /dev/null; then
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            log_success "Python version compatible"
        else
            log_error "Python version incompatible"
            ((errors++))
        fi
    else
        log_error "Python 3 not found"
        ((errors++))
    fi
    
    # Check deployment-specific requirements
    local deployment_type=$(detect_deployment_type)
    case $deployment_type in
        "docker")
            if command -v docker &> /dev/null && docker info &> /dev/null 2>&1; then
                log_success "Docker available and running"
            else
                log_error "Docker not available or not running"
                ((errors++))
            fi
            ;;
        "lightweight")
            if [[ -f "scripts/start-mcp-service.py" ]]; then
                log_success "MCP service script available"
            else
                log_error "MCP service script missing"
                ((errors++))
            fi
            ;;
    esac
    
    if [[ $errors -eq 0 ]]; then
        log_success "Configuration validation passed"
    else
        log_error "Configuration validation failed ($errors errors)"
        return 1
    fi
}

run_tests() {
    log_info "Running Claude Guardian test suite..."
    
    # Check if tests directory exists
    if [[ -d "tests" ]]; then
        log_info "Running Python tests..."
        python3 -m pytest tests/ -v
    else
        log_warn "No tests directory found"
    fi
    
    # Test MCP integration if service is running
    if lsof -i :8083 &> /dev/null; then
        log_info "Testing MCP service health..."
        local health_response=$(curl -s http://localhost:8083/health || echo "failed")
        if [[ "$health_response" != "failed" ]]; then
            log_success "MCP health check passed"
        else
            log_error "MCP health check failed"
        fi
    else
        log_warn "MCP service not running - skipping integration test"
    fi
}

# Main execution
main() {
    case "$1" in
        "start")
            service_start
            ;;
        "stop")
            service_stop
            ;;
        "restart")
            service_restart
            ;;
        "status")
            service_status
            ;;
        "logs")
            service_logs "$@"
            ;;
        "backup")
            backup_data
            ;;
        "cleanup")
            cleanup_system
            ;;
        "health")
            health_check
            ;;
        "validate")
            validate_config
            ;;
        "test")
            run_tests
            ;;
        "debug")
            log_info "Starting services in debug mode..."
            export DEBUG=true
            service_start
            ;;
        "deploy")
            log_info "Redeploying services..."
            service_stop
            sleep 2
            service_start
            ;;
        "scale")
            log_warn "Scaling not implemented for current deployment type"
            ;;
        "rollback")
            log_warn "Rollback feature requires backup restoration"
            log_info "Use: $0 restore <backup_directory>"
            ;;
        "")
            show_usage
            ;;
        *)
            log_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Execute
main "$@"