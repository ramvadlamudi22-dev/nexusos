#!/bin/bash
# NexusOS Development Start Script
# Starts both backend and frontend services with colored output.

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  NexusOS Development Server${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: node is not installed${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}All prerequisites found.${NC}"
echo ""

# Install backend dependencies if needed
if ! python3 -c "import fastapi" &> /dev/null || [ "$1" == "--install" ]; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip install -r "$PROJECT_ROOT/backend/requirements.txt" --quiet
    echo -e "${GREEN}Backend dependencies installed.${NC}"
fi

# Install frontend dependencies if needed
if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ] || [ "$1" == "--install" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    (cd "$PROJECT_ROOT/frontend" && npm ci --silent)
    echo -e "${GREEN}Frontend dependencies installed.${NC}"
fi

echo ""
echo -e "${BLUE}Starting services...${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}Services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${GREEN}[Backend]${NC} Starting on http://localhost:8000"
(cd "$PROJECT_ROOT" && uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start frontend
echo -e "${GREEN}[Frontend]${NC} Starting on http://localhost:3000"
(cd "$PROJECT_ROOT/frontend" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  Backend:  http://localhost:8000${NC}"
echo -e "${GREEN}  Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Wait for both processes
wait
