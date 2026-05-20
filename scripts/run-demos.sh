#!/bin/bash
# NexusOS Demo Runner Script
# Executes all demo workflows and captures output to proofs directory.

set -euo pipefail

# Colors (matching healthcheck.sh pattern)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

HOST="${NEXUSOS_HOST:-localhost}"
PORT="${NEXUSOS_PORT:-8000}"
BASE_URL="http://${HOST}:${PORT}"
OUTPUT_DIR="proofs/full-launch/demo-outputs"
PASSED=0
FAILED=0
SERVER_PID=""

cleanup() {
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        echo -e "\n${YELLOW}Stopping backend server (PID: $SERVER_PID)...${NC}"
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT

echo -e "${YELLOW}=== NexusOS Demo Runner ===${NC}"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Start the backend server
echo -e "${YELLOW}Starting backend server...${NC}"
uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" &>/dev/null &
SERVER_PID=$!

# Wait for server to be ready
echo -e "${YELLOW}Waiting for server to be ready...${NC}"
MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/status" 2>/dev/null | grep -q "200"; then
        break
    fi
    RETRY=$((RETRY + 1))
    sleep 1
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo -e "${RED}Server failed to start within ${MAX_RETRIES}s${NC}"
    exit 1
fi

echo -e "${GREEN}Server is ready.${NC}"
echo ""

# Run each demo workflow
echo -e "${YELLOW}Running demo workflows...${NC}"
echo ""

for DEMO_FILE in demos/*.json; do
    DEMO_NAME=$(basename "$DEMO_FILE" .json)
    OUTPUT_FILE="${OUTPUT_DIR}/${DEMO_NAME}-output.json"

    # POST the demo workflow
    HTTP_CODE=$(curl -s -o "$OUTPUT_FILE" -w "%{http_code}" \
        -X POST -H "Content-Type: application/json" \
        -d @"$DEMO_FILE" \
        "${BASE_URL}/api/workflow/execute" 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "  ${GREEN}PASS${NC} ${DEMO_NAME} (HTTP ${HTTP_CODE})"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}FAIL${NC} ${DEMO_NAME} (HTTP ${HTTP_CODE})"
        FAILED=$((FAILED + 1))
    fi
done

# Summary
echo ""
echo -e "${YELLOW}=== Results ===${NC}"
TOTAL=$((PASSED + FAILED))
echo -e "  Total: ${TOTAL}"
echo -e "  ${GREEN}Passed: ${PASSED}${NC}"
echo -e "  ${RED}Failed: ${FAILED}${NC}"
echo -e "  Output: ${OUTPUT_DIR}/"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All demo workflows passed.${NC}"
    exit 0
else
    echo -e "${RED}Some demo workflows failed.${NC}"
    exit 1
fi
