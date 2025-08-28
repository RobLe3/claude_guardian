#!/bin/bash
# Test script for IFF-Guardian MCP integration
# This script starts the necessary services and runs MCP integration tests

set -e

# Configuration
MCP_SERVICE_PORT=8083
TEST_TIMEOUT=30
LOG_DIR="./logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 IFF-Guardian MCP Integration Test Suite${NC}"
echo "=================================================="

# Create logs directory
mkdir -p "$LOG_DIR"

# Function to cleanup processes
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up test processes...${NC}"
    if [[ -n $MCP_PID ]]; then
        kill $MCP_PID 2>/dev/null || true
        wait $MCP_PID 2>/dev/null || true
    fi
    if [[ -n $AUTH_PID ]]; then
        kill $AUTH_PID 2>/dev/null || true
        wait $AUTH_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo -e "${RED}❌ Go is not installed or not in PATH${NC}"
    echo "Please install Go 1.21+ to run the MCP service"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed or not in PATH${NC}"
    echo "Please install Python 3.8+ to run the test client"
    exit 1
fi

echo -e "\n${BLUE}📋 Environment Check${NC}"
echo "Go version: $(go version)"
echo "Python version: $(python3 --version)"
echo "Test timeout: ${TEST_TIMEOUT}s"
echo "MCP service port: ${MCP_SERVICE_PORT}"

# Install Python dependencies
echo -e "\n${BLUE}📦 Installing Python test dependencies...${NC}"
pip3 install websockets pytest asyncio > /dev/null 2>&1 || {
    echo -e "${YELLOW}⚠️ Could not install Python dependencies automatically${NC}"
    echo "Please install: pip3 install websockets pytest asyncio"
}

# Check if MCP service port is available
if nc -z localhost $MCP_SERVICE_PORT 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Port $MCP_SERVICE_PORT is already in use${NC}"
    echo "Attempting to use the existing service..."
else
    echo -e "\n${BLUE}🔧 Starting IFF-Guardian MCP Service...${NC}"
    
    # Start the MCP service in the background
    cd "$(dirname "$0")/.."
    
    export IFF_GUARDIAN_PORT=$MCP_SERVICE_PORT
    export IFF_GUARDIAN_ENV=test
    export IFF_GUARDIAN_LOG_LEVEL=info
    
    # Check if the MCP service source exists
    if [[ ! -f "services/mcp-service/main.go" ]]; then
        echo -e "${RED}❌ MCP service source not found: services/mcp-service/main.go${NC}"
        exit 1
    fi
    
    # Start MCP service
    echo "Starting MCP service on port $MCP_SERVICE_PORT..."
    go run services/mcp-service/main.go > "$LOG_DIR/mcp-service.log" 2>&1 &
    MCP_PID=$!
    
    # Wait for service to start
    echo "Waiting for MCP service to start..."
    WAIT_COUNT=0
    while ! nc -z localhost $MCP_SERVICE_PORT && [ $WAIT_COUNT -lt $TEST_TIMEOUT ]; do
        sleep 1
        WAIT_COUNT=$((WAIT_COUNT + 1))
        echo -n "."
    done
    echo
    
    if ! nc -z localhost $MCP_SERVICE_PORT; then
        echo -e "${RED}❌ MCP service failed to start within ${TEST_TIMEOUT} seconds${NC}"
        echo "Check logs: $LOG_DIR/mcp-service.log"
        exit 1
    fi
    
    echo -e "${GREEN}✅ MCP service started successfully${NC}"
fi

# Wait a moment for the service to be fully ready
sleep 2

# Test basic connectivity
echo -e "\n${BLUE}🔍 Testing basic connectivity...${NC}"
if curl -s -f "http://localhost:$MCP_SERVICE_PORT/health" > /dev/null; then
    echo -e "${GREEN}✅ MCP service health check passed${NC}"
else
    echo -e "${RED}❌ MCP service health check failed${NC}"
    exit 1
fi

# Run the Python MCP integration tests
echo -e "\n${BLUE}🧪 Running MCP Integration Tests...${NC}"
cd "$(dirname "$0")/.."

python3 tests/mcp-integration/test_mcp_basic.py 2>&1 | tee "$LOG_DIR/mcp-test-results.log"
TEST_RESULT=$?

# Display results
echo -e "\n=================================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}🎉 MCP Integration Tests: PASSED${NC}"
    echo -e "${GREEN}✅ IFF-Guardian MCP integration is working correctly${NC}"
else
    echo -e "${RED}❌ MCP Integration Tests: FAILED${NC}"
    echo -e "${RED}⚠️ Check logs in $LOG_DIR/ for details${NC}"
fi

# Show quick service status
echo -e "\n${BLUE}📊 Service Status Summary${NC}"
if nc -z localhost $MCP_SERVICE_PORT; then
    echo -e "MCP Service: ${GREEN}✅ Running${NC} (port $MCP_SERVICE_PORT)"
else
    echo -e "MCP Service: ${RED}❌ Not Running${NC}"
fi

echo -e "\n${BLUE}📁 Test Artifacts${NC}"
echo "Logs directory: $LOG_DIR/"
echo "  - mcp-service.log: MCP service output"
echo "  - mcp-test-results.log: Test execution results"

# Additional debug information if tests failed
if [ $TEST_RESULT -ne 0 ]; then
    echo -e "\n${YELLOW}🔍 Debug Information${NC}"
    echo "MCP Service Health:"
    curl -s "http://localhost:$MCP_SERVICE_PORT/health" 2>/dev/null || echo "Health check failed"
    echo -e "\nMCP Service Ready Check:"
    curl -s "http://localhost:$MCP_SERVICE_PORT/health/ready" 2>/dev/null || echo "Ready check failed"
fi

exit $TEST_RESULT