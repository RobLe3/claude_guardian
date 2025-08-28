#!/bin/bash
# =============================================================================
# Claude Guardian - Easy Setup (Deprecated - Redirects to Universal Setup)
# This script now redirects to the new intelligent setup system
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${YELLOW}📢 easy-setup.sh has been consolidated into setup.sh${NC}"
echo -e "${CYAN}🔄 Redirecting to universal setup with intelligent routing...${NC}"
echo ""

echo -e "${BLUE}🔄 The universal setup will automatically detect your environment${NC}"
echo -e "${BLUE}   and choose the optimal deployment strategy for you.${NC}"
echo ""
echo -e "${GREEN}✨ Features of the new setup:${NC}"
echo -e "  • Intelligent environment detection"
echo -e "  • Automatic routing to best deployment type"
echo -e "  • Unified management with ./manage.sh"
echo -e "  • Better error handling and rollback"
echo ""
echo -e "${CYAN}🚀 Running universal setup now...${NC}"
echo ""

# Check if setup.sh exists and execute it in lightweight mode
if [[ -f "setup.sh" ]]; then
    exec ./setup.sh --mode lightweight
else
    echo -e "${RED}❌ setup.sh not found in current directory${NC}"
    echo -e "${YELLOW}💡 Please run this script from the Claude Guardian root directory${NC}"
    exit 1
fi