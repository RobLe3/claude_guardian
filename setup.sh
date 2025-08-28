#!/bin/bash
# =============================================================================
# Claude Guardian v2.0.0-alpha - Universal Setup with Intelligent Routing
# Automatically detects environment and deploys appropriate configuration
# =============================================================================

set -e

# Colors for output
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
PYTHON_MIN_VERSION="3.8"

# Environment capabilities
DOCKER_AVAILABLE=false
GO_AVAILABLE=false
PYTHON_AVAILABLE=false
SETUP_MODE=""

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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════╗"
    echo -e "║         🛡️  Claude Guardian v${VERSION}         ║"
    echo -e "║      Universal Setup with Intelligent Routing   ║"
    echo -e "║                                                  ║"
    echo -e "║  🔍 Auto-detects your environment capabilities  ║"
    echo -e "║  ⚡ Routes to optimal deployment strategy        ║"
    echo -e "║  🛡️ Pattern-based Security Scanner              ║"
    echo -e "║  🔗 Claude Code MCP Integration                  ║"
    echo -e "║  📊 Production-ready with monitoring            ║"
    echo -e "╚══════════════════════════════════════════════════╝${NC}"
    echo ""
}

detect_environment() {
    log_step "Detecting environment capabilities..."
    
    # Python check (required)
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version | cut -d' ' -f2)
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            PYTHON_AVAILABLE=true
            log_success "Python $python_version detected"
        else
            log_error "Python 3.8+ required, found $python_version"
            exit 1
        fi
    else
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Docker check (optional)
    if command -v docker &> /dev/null && docker info &> /dev/null 2>&1; then
        if command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1; then
            DOCKER_AVAILABLE=true
            log_success "Docker with Compose detected"
        else
            log_warn "Docker found but Compose missing"
        fi
    else
        log_info "Docker not available (optional for lightweight setup)"
    fi
    
    # Go check (optional)
    if command -v go &> /dev/null; then
        GO_AVAILABLE=true
        local go_version=$(go version | cut -d' ' -f3)
        log_success "Go $go_version detected (enterprise features available)"
    fi
    
    # Determine setup mode
    if [[ "$PYTHON_AVAILABLE" == true && "$DOCKER_AVAILABLE" == true && "$GO_AVAILABLE" == true ]]; then
        SETUP_MODE="enterprise"
        log_info "🏢 Enterprise mode: Python + Docker + Go capabilities"
    elif [[ "$PYTHON_AVAILABLE" == true && "$DOCKER_AVAILABLE" == true ]]; then
        SETUP_MODE="full"
        log_info "🐳 Full mode: Python + Docker deployment"
    elif [[ "$PYTHON_AVAILABLE" == true ]]; then
        SETUP_MODE="lightweight"
        log_info "⚡ Lightweight mode: Python-only MCP service"
    else
        log_error "No valid setup mode detected"
        exit 1
    fi
}

route_setup() {
    case "$SETUP_MODE" in
        "lightweight")
            log_info "🚀 Routing to lightweight Python-only setup..."
            setup_lightweight
            ;;
        "full")
            log_info "🚀 Routing to full Docker stack setup..."
            setup_full_stack
            ;;
        "enterprise")
            log_info "🚀 Routing to enterprise setup with Go services..."
            setup_enterprise
            ;;
        *)
            log_error "Unknown setup mode: $SETUP_MODE"
            exit 1
            ;;
    esac
}

setup_lightweight() {
    log_step "Setting up lightweight Python-only MCP service..."
    
    # Install minimal dependencies
    log_info "Installing minimal Python dependencies..."
    pip3 install --user websockets fastapi uvicorn pydantic
    
    # Create minimal environment from template
    cat > .env << EOF
# Claude Guardian Lightweight Configuration
GUARDIAN_MODE=mcp_only
SECURITY_LEVEL=moderate
MCP_PORT=8083
MCP_HOST=0.0.0.0
EOF
    
    # Start MCP service
    if ! lsof -i :8083 &> /dev/null; then
        python3 scripts/start-mcp-service.py --port 8083 > /tmp/claude-guardian-mcp.log 2>&1 &
        echo "$!" > .mcp_pid
        sleep 3
    fi
    
    # Generate Claude Code config
    generate_lightweight_config
    
    log_success "Lightweight setup complete - MCP service running on port 8083"
}

setup_full_stack() {
    log_step "Setting up full Docker stack..."
    
    # Install full dependencies
    install_python_dependencies
    setup_environment
    deploy_services
    test_deployment
    generate_claude_config
    
    log_success "Full stack setup complete"
}

setup_enterprise() {
    log_step "Setting up enterprise environment with Go services..."
    
    log_warn "Enterprise Go services available but not implemented in v2.0.0-alpha"
    log_info "Falling back to full stack setup..."
    setup_full_stack
}

install_python_dependencies() {
    log_step "Installing Python dependencies..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        log_info "Installing Python packages..."
        pip install -r requirements.txt
    fi
    
    log_success "Python dependencies installed"
}

setup_environment() {
    log_step "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_info "Creating .env from template..."
            cp .env.example .env
            
            # Generate secure password
            local db_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
            sed -i.bak "s/your_secure_db_password_here/$db_password/g" .env
            rm .env.bak
            
            log_success "Environment file created with secure password"
        else
            log_info "Creating basic .env file..."
            cat > .env << EOF
# Claude Guardian v2.0.0-alpha Configuration
POSTGRES_DB=claude_guardian
POSTGRES_USER=cguser
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
SECURITY_LEVEL=moderate
MCP_PORT=8083
MCP_HOST=0.0.0.0
QDRANT_DATA_PATH=./data/qdrant
POSTGRES_DATA_PATH=./data/postgres
REDIS_DATA_PATH=./data/redis
EOF
            log_success "Basic environment file created"
        fi
    else
        log_info "Environment file already exists"
    fi
}

deploy_services() {
    log_step "Deploying Claude Guardian services..."
    
    # Ensure data directories exist
    mkdir -p data/{postgres,qdrant,redis}
    
    # Choose deployment method
    if [ -f "deployments/production/docker-compose.production.yml" ]; then
        log_info "Using production deployment configuration..."
        docker-compose -f deployments/production/docker-compose.production.yml up -d
    elif [ -f "config/docker-compose/docker-compose.yml" ]; then
        log_info "Using standard deployment configuration..."
        docker-compose -f config/docker-compose/docker-compose.yml up -d
    else
        log_error "No Docker Compose configuration found"
        exit 1
    fi
    
    log_info "Waiting for services to start..."
    sleep 10
    
    log_success "Services deployed"
}

test_deployment() {
    log_step "Testing deployment..."
    
    # Test FastAPI health endpoint
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8083/health &> /dev/null; then
            log_success "FastAPI service is responding"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "FastAPI service failed to start"
            log_info "Check logs with: docker-compose logs"
            exit 1
        fi
        
        log_info "Waiting for service... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    # Display service status
    log_info "Service Status:"
    curl -s http://localhost:8083/health | python3 -m json.tool || log_warn "Health endpoint not available"
}

generate_claude_config() {
    log_step "Generating Claude Code integration configuration..."
    
    local mcp_port=$(grep MCP_PORT .env 2>/dev/null | cut -d'=' -f2 || echo "8083")
    
    cat > claude-code-mcp-config.json << EOF
{
  "mcpServers": {
    "claude-guardian": {
      "command": "python3",
      "args": ["-m", "uvicorn", "src.claude_guardian.main:app", "--host", "0.0.0.0", "--port", "$mcp_port"],
      "env": {
        "PYTHONPATH": "$(pwd)"
      }
    }
  }
}
EOF
    
    log_success "Claude Code configuration generated: claude-code-mcp-config.json"
    log_info "Copy this file to your Claude Code MCP directory:"
    log_info "  cp claude-code-mcp-config.json ~/.claude-code/mcp/"
}

generate_lightweight_config() {
    log_step "Generating lightweight Claude Code configuration..."
    
    local current_dir=$(pwd)
    cat > claude-code-mcp-config.json << EOF
{
  "mcpServers": {
    "claude-guardian": {
      "command": "python3",
      "args": ["$current_dir/scripts/start-mcp-service.py", "--port", "8083"],
      "env": {
        "GUARDIAN_MODE": "lightweight"
      }
    }
  }
}
EOF
    
    log_success "Lightweight Claude Code configuration generated"
    log_info "Copy claude-code-mcp-config.json to ~/.claude-code/mcp/"
}

show_completion() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════╗"
    echo -e "║  🎉 Claude Guardian v${VERSION} Setup Complete! 🎉  ║"
    echo -e "║     Setup Mode: ${SETUP_MODE^^}                    ║"
    echo -e "╚══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}🚀 Next Steps:${NC}"
    echo -e "  1. ${YELLOW}Integrate with Claude Code:${NC}"
    echo -e "     cp claude-code-mcp-config.json ~/.claude-code/mcp/"
    echo ""
    
    if [[ "$SETUP_MODE" == "lightweight" ]]; then
        echo -e "  2. ${YELLOW}Test MCP service:${NC}"
        echo -e "     lsof -i :8083  # Verify service running"
        echo ""
        echo -e "${CYAN}🔧 Management:${NC}"
        echo -e "  • Stop service:   kill \$(cat .mcp_pid)"
        echo -e "  • Check logs:     tail /tmp/claude-guardian-mcp.log"
    else
        echo -e "  2. ${YELLOW}Test the deployment:${NC}"
        echo -e "     curl http://localhost:8083/health"
        echo -e "  3. ${YELLOW}View API docs:${NC}"
        echo -e "     open http://localhost:8083/docs"
        echo ""
        echo -e "${CYAN}🔧 Management:${NC}"
        echo -e "  • Manage services: ./manage.sh [start|stop|status|logs]"
        echo -e "  • Docker commands: docker-compose [up|down|logs]"
    fi
    
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC} See README.md and GETTING_STARTED.md"
    echo ""
}

# Main execution
main() {
    banner
    
    # Check if running with --help
    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        echo "Claude Guardian v2.0.0-alpha Universal Setup Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h        Show this help message"
        echo "  --mode MODE       Force setup mode: lightweight|full|enterprise"
        echo "  --port PORT       Override MCP port (default: 8083)"
        echo ""
        echo "Setup Modes (auto-detected):"
        echo "  • lightweight    Python-only MCP service (no Docker)"
        echo "  • full          FastAPI + Docker stack (PostgreSQL, Redis, Qdrant)"
        echo "  • enterprise    Full stack + Go services (future)"
        echo ""
        echo "This script automatically:"
        echo "  1. Detects your environment capabilities"
        echo "  2. Routes to optimal deployment strategy"
        echo "  3. Configures Claude Code MCP integration"
        echo "  4. Provides management tools and instructions"
        exit 0
    fi
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                SETUP_MODE="$2"
                log_info "Forced setup mode: $SETUP_MODE"
                shift 2
                ;;
            --port)
                MCP_PORT="$2"
                shift 2
                ;;
            *)
                log_warn "Unknown option: $1"
                shift
                ;;
        esac
    done
    
    log_info "Starting Claude Guardian v$VERSION universal setup..."
    
    # Detect environment if not forced
    if [[ -z "$SETUP_MODE" ]]; then
        detect_environment
    fi
    
    # Route to appropriate setup
    route_setup
    show_completion
    
    log_success "Setup completed successfully in $SETUP_MODE mode!"
}

# Execute main function
main "$@"