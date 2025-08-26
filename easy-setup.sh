#!/bin/bash
# =============================================================================
# Claude Guardian - Easy Setup (No Dependencies Required)
# Streamlined setup for Claude Code integration - Python only
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${GREEN}🛡️  Claude Guardian - Easy Setup${NC}"
echo -e "${BLUE}Python-only setup for Claude Code integration${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip3 install --user websockets fastapi uvicorn pydantic

# Create minimal .env for MCP service
echo -e "${BLUE}⚙️  Creating MCP configuration...${NC}"
cat > .env << EOF
# Minimal configuration for MCP service
GUARDIAN_MODE=mcp_only
SECURITY_LEVEL=moderate
MCP_PORT=8083
EOF

# Start MCP service
echo -e "${BLUE}🚀 Starting Claude Guardian MCP service...${NC}"

# Check if service is already running
if lsof -i :8083 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Service already running on port 8083${NC}"
    echo -e "${GREEN}✅ Using existing MCP service${NC}"
    MCP_PID=$(lsof -ti :8083)
else
    python3 scripts/start-mcp-service.py --port 8083 > /tmp/claude-guardian-mcp.log 2>&1 &
    MCP_PID=$!
    
    # Wait and verify
    sleep 3
    if lsof -i :8083 &> /dev/null; then
        echo -e "${GREEN}✅ MCP service running (PID: $MCP_PID)${NC}"
    else
        echo -e "${RED}❌ MCP service failed to start${NC}"
        echo "Check logs: tail /tmp/claude-guardian-mcp.log"
        exit 1
    fi
fi

echo "MCP_PID=$MCP_PID" > .mcp_pid

# Generate Claude Code configuration
CURRENT_DIR=$(pwd)
MCP_SCRIPT_PATH="$CURRENT_DIR/scripts/start-mcp-service.py"

cat > claude-code-config.json << EOF
{
  "name": "claude-guardian",
  "command": "python3",
  "args": ["$MCP_SCRIPT_PATH", "--port", "8083"],
  "env": {
    "GUARDIAN_MODE": "production"
  }
}
EOF

echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Copy this configuration to Claude Code:"
echo ""
cat claude-code-config.json
echo ""
echo "2. Or use this file: claude-code-config.json"
echo "3. Restart Claude Code to load Claude Guardian"
echo ""
echo -e "${BLUE}Test with: 'scan this code for security issues'${NC}"