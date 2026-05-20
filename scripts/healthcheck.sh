#!/bin/bash
# NexusOS Health Check Script
# Checks the backend API health endpoint and returns appropriate exit codes.

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

HOST="${NEXUSOS_HOST:-localhost}"
PORT="${NEXUSOS_PORT:-8000}"
ENDPOINT="http://${HOST}:${PORT}/api/status"

echo -e "${YELLOW}Checking NexusOS health...${NC}"
echo "Endpoint: ${ENDPOINT}"
echo ""

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is not installed${NC}"
    exit 1
fi

# Make the health check request
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$ENDPOINT" 2>/dev/null || echo "000")

if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}Backend is healthy (HTTP 200)${NC}"

    # Get detailed status
    STATUS=$(curl -s "$ENDPOINT" 2>/dev/null)
    echo ""
    echo "Status response:"
    echo "$STATUS" | python3 -m json.tool 2>/dev/null || echo "$STATUS"
    echo ""
    echo -e "${GREEN}Health check passed.${NC}"
    exit 0
elif [ "$RESPONSE" = "000" ]; then
    echo -e "${RED}Backend is unreachable (connection refused)${NC}"
    echo "Ensure the backend is running on ${HOST}:${PORT}"
    exit 1
else
    echo -e "${RED}Backend returned HTTP ${RESPONSE}${NC}"
    exit 1
fi
