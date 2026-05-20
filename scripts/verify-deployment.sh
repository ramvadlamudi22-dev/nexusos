#!/bin/bash
# NexusOS Deployment Verification Script
# Starts the backend, verifies all key endpoints, and reports results.

set -euo pipefail

# Colors (matching healthcheck.sh pattern)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

HOST="${NEXUSOS_HOST:-localhost}"
PORT="${NEXUSOS_PORT:-8000}"
BASE_URL="http://${HOST}:${PORT}"
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

check_endpoint() {
    local method="$1"
    local path="$2"
    local data="${3:-}"
    local description="${4:-$method $path}"
    local url="${BASE_URL}${path}"

    if [ "$method" = "GET" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    else
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$url" 2>/dev/null || echo "000")
    fi

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "  ${GREEN}PASS${NC} $description (HTTP $HTTP_CODE)"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}FAIL${NC} $description (HTTP $HTTP_CODE)"
        FAILED=$((FAILED + 1))
    fi
}

check_endpoint_capture() {
    local method="$1"
    local path="$2"
    local data="${3:-}"
    local description="${4:-$method $path}"
    local url="${BASE_URL}${path}"

    if [ "$method" = "GET" ]; then
        HTTP_RESPONSE=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo -e "\n000")
    else
        HTTP_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$url" 2>/dev/null || echo -e "\n000")
    fi

    HTTP_CODE=$(echo "$HTTP_RESPONSE" | tail -1)
    RESPONSE=$(echo "$HTTP_RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "  ${GREEN}PASS${NC} $description (HTTP $HTTP_CODE)"
        PASSED=$((PASSED + 1))
    else
        echo -e "  ${RED}FAIL${NC} $description (HTTP $HTTP_CODE)"
        FAILED=$((FAILED + 1))
    fi
}

echo -e "${YELLOW}=== NexusOS Deployment Verification ===${NC}"
echo ""

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

# Verify all key endpoints
echo -e "${YELLOW}Verifying endpoints...${NC}"
echo ""

# Basic status
check_endpoint "GET" "/api/status" "" "GET /api/status"

# Governance
check_endpoint "GET" "/api/governance/status" "" "GET /api/governance/status"

# Workflow execution (simple 2-step workflow)
WORKFLOW_PAYLOAD='{"workflow_id":"verify-test","name":"Verification Test","steps":[{"id":"step-1","name":"Step One","step_type":"TERMINAL","config":{"command":"echo hello","working_dir":"/tmp"},"depends_on":[]},{"id":"step-2","name":"Step Two","step_type":"TERMINAL","config":{"command":"echo world","working_dir":"/tmp"},"depends_on":["step-1"]}]}'
check_endpoint "POST" "/api/workflow/execute" "$WORKFLOW_PAYLOAD" "POST /api/workflow/execute"

# Telemetry
check_endpoint "GET" "/api/telemetry/health" "" "GET /api/telemetry/health"
check_endpoint "GET" "/api/telemetry/metrics" "" "GET /api/telemetry/metrics"

# Events
check_endpoint "GET" "/api/events" "" "GET /api/events"

# Skills
check_endpoint "GET" "/api/skills" "" "GET /api/skills"

# Browser
BROWSER_PAYLOAD='{"url":"https://example.com"}'
check_endpoint "POST" "/api/browser/start" "$BROWSER_PAYLOAD" "POST /api/browser/start"

# Terminal execution (capture response for session_id)
TERMINAL_PAYLOAD='{"command":"echo test"}'
check_endpoint_capture "POST" "/api/terminal/execute" "$TERMINAL_PAYLOAD" "POST /api/terminal/execute"

# Extract session_id from terminal response for replay endpoint
SESSION_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null || echo "")
if [ -n "$SESSION_ID" ]; then
    check_endpoint "GET" "/api/replay/terminal/${SESSION_ID}" "" "GET /api/replay/terminal/{session_id}"
else
    echo -e "  ${RED}FAIL${NC} GET /api/replay/terminal/{session_id} (no session_id from terminal)"
    FAILED=$((FAILED + 1))
fi

# Summary
echo ""
echo -e "${YELLOW}=== Results ===${NC}"
TOTAL=$((PASSED + FAILED))
echo -e "  Total: ${TOTAL}"
echo -e "  ${GREEN}Passed: ${PASSED}${NC}"
echo -e "  ${RED}Failed: ${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All endpoint checks passed.${NC}"
    exit 0
else
    echo -e "${RED}Some endpoint checks failed.${NC}"
    exit 1
fi
