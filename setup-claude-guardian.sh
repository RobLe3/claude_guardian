#!/bin/bash
# =============================================================================
# Claude Guardian - Intelligent Setup Script
# Handles dependencies, environment, and Claude Code integration automatically
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
GUARDIAN_DIR="claude_guardian"
MCP_PORT=8083
CLAUDE_CONFIG_DIR="$HOME/.config/claude-code"

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

banner() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗"
    echo -e "║        🛡️  Claude Guardian Setup        ║"
    echo -e "║     AI-Powered Security for Claude Code ║"
    echo -e "╚════════════════════════════════════════╝${NC}"
    echo ""
}

check_dependencies() {
    log_info "Checking system dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    log_success "Python ${PYTHON_VERSION} found"
    
    # Check Docker (optional for MCP-only setup)
    if command -v docker &> /dev/null; then
        log_success "Docker found - full stack available"
        DOCKER_AVAILABLE=true
    else
        log_warn "Docker not found - MCP-only setup available"
        DOCKER_AVAILABLE=false
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        log_error "Git is required but not installed"
        exit 1
    fi
    log_success "Git found"
    
    # Check Go (optional)
    if command -v go &> /dev/null; then
        log_success "Go found - full development features available"
        GO_AVAILABLE=true
    else
        log_warn "Go not found - using Python-only setup"
        GO_AVAILABLE=false
    fi
}

clone_repository() {
    log_info "Setting up Claude Guardian..."
    
    if [ -d "$GUARDIAN_DIR" ]; then
        log_warn "Directory $GUARDIAN_DIR already exists"
        read -p "Remove and re-clone? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$GUARDIAN_DIR"
        else
            log_info "Using existing directory"
            return
        fi
    fi
    
    git clone https://github.com/RobLe3/claude_guardian.git "$GUARDIAN_DIR"
    cd "$GUARDIAN_DIR"
    log_success "Repository cloned successfully"
}

setup_environment() {
    log_info "Setting up environment configuration..."
    
    if [ -f "deployments/production/.env" ]; then
        log_warn "Environment file already exists"
        return
    fi
    
    cd deployments/production
    
    # Generate secure passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-32)
    
    # Create .env file with secure defaults
    cat > .env << EOF
# Claude Guardian Production Environment
POSTGRES_DB=claude_guardian
POSTGRES_USER=cguser
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
JWT_SECRET=${JWT_SECRET}
SECURITY_LEVEL=moderate
QDRANT_DATA_PATH=./data/qdrant
POSTGRES_DATA_PATH=./data/postgres
ENABLE_MONITORING=false
ENABLE_DEBUG_LOGGING=false
DEVELOPMENT_MODE=false
EOF

    log_success "Environment configuration created with secure defaults"
    cd ../..
}

install_python_dependencies() {
    log_info "Installing Python dependencies for MCP service..."
    
    # Create virtual environment if needed
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Virtual environment created"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install websockets
    
    log_success "Python dependencies installed"
}

start_mcp_service() {
    log_info "Starting Claude Guardian MCP service..."
    
    # Check if service is already running
    if lsof -i :$MCP_PORT &> /dev/null; then
        log_warn "Port $MCP_PORT is already in use"
        read -p "Kill existing service and restart? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            lsof -ti :$MCP_PORT | xargs kill -9
            sleep 2
        else
            log_info "Using existing service on port $MCP_PORT"
            return
        fi
    fi
    
    # Start MCP service in background
    python3 scripts/start-mcp-service.py --port $MCP_PORT > /tmp/claude-guardian-mcp.log 2>&1 &
    MCP_PID=$!
    
    # Wait for service to start
    sleep 3
    
    if lsof -i :$MCP_PORT &> /dev/null; then
        log_success "MCP service started successfully (PID: $MCP_PID, Port: $MCP_PORT)"
        echo "MCP_PID=$MCP_PID" > .mcp_pid
    else
        log_error "Failed to start MCP service"
        exit 1
    fi
}

setup_docker_stack() {
    if [ "$DOCKER_AVAILABLE" = false ]; then
        log_warn "Skipping Docker stack setup (Docker not available)"
        return
    fi
    
    log_info "Setting up Docker stack..."
    
    cd deployments/production
    
    # Handle missing Go dependencies gracefully
    if [ "$GO_AVAILABLE" = false ]; then
        log_warn "Go not available - using simplified Docker setup"
        # We could create a simplified docker-compose here or skip
        log_warn "Full Docker stack requires Go - proceeding with MCP-only setup"
        cd ../..
        return
    fi
    
    # Full Docker setup with Go
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services
    log_info "Waiting for services to start..."
    sleep 10
    
    # Verify services
    if docker-compose -f docker-compose.production.yml ps | grep -q "Up"; then
        log_success "Docker stack started successfully"
    else
        log_error "Some Docker services failed to start"
    fi
    
    cd ../..
}

configure_claude_code() {
    log_info "Configuring Claude Code MCP integration..."
    
    CURRENT_DIR=$(pwd)
    MCP_SCRIPT_PATH="$CURRENT_DIR/scripts/start-mcp-service.py"
    
    # Create Claude Code config directory if it doesn't exist
    mkdir -p "$CLAUDE_CONFIG_DIR"
    
    # Generate MCP configuration
    MCP_CONFIG=$(cat << EOF
{
  "name": "claude-guardian",
  "command": "python3",
  "args": ["$MCP_SCRIPT_PATH", "--port", "$MCP_PORT"],
  "env": {
    "GUARDIAN_VERSION": "1.3.2",
    "GUARDIAN_MODE": "production"
  }
}
EOF
)

    log_success "Claude Code MCP configuration generated:"
    echo -e "${YELLOW}$MCP_CONFIG${NC}"
    
    echo ""
    log_info "To complete Claude Code integration:"
    echo "1. Add the above configuration to your Claude Code MCP settings"
    echo "2. Or copy this configuration to: $CLAUDE_CONFIG_DIR/mcp-config.json"
    echo "3. Restart Claude Code to load the MCP service"
    
    # Optionally save to file
    read -p "Save configuration to file? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "$MCP_CONFIG" > claude-code-mcp-config.json
        log_success "Configuration saved to claude-code-mcp-config.json"
    fi
}

validate_setup() {
    log_info "Validating Claude Guardian setup..."
    
    # Test version system
    if python3 scripts/version.py > /dev/null; then
        log_success "Version system: OK"
    else
        log_error "Version system: FAILED"
    fi
    
    # Test MCP service
    if lsof -i :$MCP_PORT &> /dev/null; then
        log_success "MCP service: Running on port $MCP_PORT"
    else
        log_error "MCP service: NOT RUNNING"
    fi
    
    # Test MCP tools
    if python3 scripts/validate-mcp-tools.py > /tmp/mcp-validation.log 2>&1; then
        log_success "MCP tools: All 5 security tools validated"
    else
        log_warn "MCP tools: Validation issues - check /tmp/mcp-validation.log"
    fi
}

setup_summary() {
    echo ""
    log_success "🎉 Claude Guardian setup completed!"
    echo ""
    echo -e "${GREEN}📊 Setup Summary:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🛡️  Claude Guardian: Ready"
    echo "🐍  Python MCP Service: Running on port $MCP_PORT"
    if [ "$DOCKER_AVAILABLE" = true ] && [ "$GO_AVAILABLE" = true ]; then
        echo "🐳  Docker Stack: Available"
    else
        echo "🐳  Docker Stack: Simplified setup (MCP-only)"
    fi
    echo "🔧  Management Scripts: Available"
    echo "📝  Configuration: Auto-generated"
    echo ""
    echo -e "${BLUE}🚀 Next Steps:${NC}"
    echo "1. Add Claude Guardian MCP configuration to Claude Code"
    echo "2. Restart Claude Code to load the security service"
    echo "3. Test with: 'scan this code for security issues'"
    echo ""
    echo -e "${YELLOW}📁 Installation Directory: $(pwd)${NC}"
    echo -e "${YELLOW}🔗 MCP Configuration: claude-code-mcp-config.json${NC}"
    echo -e "${YELLOW}📊 Service Status: scripts/guardian-mcp status${NC}"
}

# Main execution
main() {
    banner
    check_dependencies
    clone_repository
    setup_environment
    install_python_dependencies
    start_mcp_service
    setup_docker_stack
    configure_claude_code
    validate_setup
    setup_summary
}

# Run main function
main "$@"