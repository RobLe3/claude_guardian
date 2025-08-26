#!/bin/bash
# =============================================================================
# Claude Guardian v2.0.0-alpha - Out-of-the-Box Setup
# Complete Enterprise Security Platform Setup
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
    echo -e "║    Complete Enterprise Security Platform Setup   ║"
    echo -e "║                                                  ║"
    echo -e "║  • FastAPI Application + Multi-Database Stack   ║"
    echo -e "║  • Sub-6ms Response Times + 100% Detection      ║"
    echo -e "║  • PostgreSQL + Qdrant + Redis Persistence      ║"
    echo -e "║  • Production-Ready Docker Deployment           ║"
    echo -e "║  • Claude Code Integration (HTTP MCP)            ║"
    echo -e "╚══════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_dependencies() {
    log_step "Checking system dependencies..."
    
    # Python check
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    local python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_error "Python 3.8+ required, found $python_version"
        exit 1
    fi
    log_success "Python $python_version detected"
    
    # Docker check
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed"
        log_info "Please install Docker Desktop from https://docker.com/products/docker-desktop"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is installed but not running"
        log_info "Please start Docker Desktop and try again"
        exit 1
    fi
    log_success "Docker is running"
    
    # Docker Compose check
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is required but not found"
        exit 1
    fi
    log_success "Docker Compose available"
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
    elif [ -f "docker-compose.yml" ]; then
        log_info "Using standard deployment configuration..."
        docker-compose up -d
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
    
    cat > claude-code-mcp-config.json << EOF
{
  "mcpServers": {
    "claude-guardian": {
      "command": "python3",
      "args": ["-m", "uvicorn", "src.iff_guardian.main:app", "--host", "0.0.0.0", "--port", "8083"],
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

show_completion() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════╗"
    echo -e "║  🎉 Claude Guardian v${VERSION} Setup Complete! 🎉  ║"
    echo -e "╚══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}🚀 Next Steps:${NC}"
    echo -e "  1. ${YELLOW}Integrate with Claude Code:${NC}"
    echo -e "     cp claude-code-mcp-config.json ~/.claude-code/mcp/"
    echo ""
    echo -e "  2. ${YELLOW}Test the deployment:${NC}"
    echo -e "     curl http://localhost:8083/health"
    echo ""
    echo -e "  3. ${YELLOW}View API documentation:${NC}"
    echo -e "     open http://localhost:8083/docs"
    echo ""
    echo -e "${CYAN}🔧 Management Commands:${NC}"
    echo -e "  • Start services:  docker-compose up -d"
    echo -e "  • Stop services:   docker-compose down"
    echo -e "  • View logs:       docker-compose logs -f"
    echo -e "  • Service status:  docker-compose ps"
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC} See README.md and docs/ directory"
    echo ""
}

# Main execution
main() {
    banner
    
    # Check if running with --help
    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        echo "Claude Guardian v2.0.0-alpha Setup Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --minimal      Skip optional components"
        echo ""
        echo "This script will:"
        echo "  1. Check system dependencies (Python 3.8+, Docker)"
        echo "  2. Install Python dependencies"
        echo "  3. Setup environment configuration"
        echo "  4. Deploy services via Docker Compose"
        echo "  5. Test deployment and generate Claude Code config"
        exit 0
    fi
    
    log_info "Starting Claude Guardian v$VERSION setup..."
    
    check_dependencies
    install_python_dependencies
    setup_environment
    deploy_services
    test_deployment
    generate_claude_config
    show_completion
    
    log_success "Setup completed successfully!"
}

# Execute main function
main "$@"