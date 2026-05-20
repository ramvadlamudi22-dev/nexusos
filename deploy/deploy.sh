#!/bin/bash
# NexusOS Production Deployment Script
# Deploys backend to Railway, frontend to Vercel.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  NexusOS Production Deployment           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v railway &> /dev/null; then
    echo -e "${RED}Error: Railway CLI not installed${NC}"
    echo "  Install: npm install -g @railway/cli"
    exit 1
fi

if ! command -v vercel &> /dev/null; then
    echo -e "${RED}Error: Vercel CLI not installed${NC}"
    echo "  Install: npm install -g vercel"
    exit 1
fi

echo -e "${GREEN}Prerequisites OK${NC}"
echo ""

# Deploy backend to Railway
echo -e "${BLUE}[1/3] Deploying backend to Railway...${NC}"
railway up --detach
echo -e "${GREEN}Backend deployed${NC}"
echo ""

# Get Railway URL
RAILWAY_URL=$(railway domain 2>/dev/null || echo "https://nexusos-api.up.railway.app")
echo -e "  Backend URL: ${GREEN}${RAILWAY_URL}${NC}"

# Deploy frontend to Vercel
echo -e "${BLUE}[2/3] Deploying frontend to Vercel...${NC}"
cd frontend
NEXT_PUBLIC_API_BASE_URL="${RAILWAY_URL}" vercel --prod
cd ..
echo -e "${GREEN}Frontend deployed${NC}"
echo ""

# Validate deployment
echo -e "${BLUE}[3/3] Validating deployment...${NC}"
sleep 10

HEALTH=$(curl -s "${RAILWAY_URL}/api/health" | python3 -c "import sys,json; print(json.load(sys.stdin)['overall'])" 2>/dev/null || echo "UNREACHABLE")

if [ "$HEALTH" = "HEALTHY" ]; then
    echo -e "${GREEN}✓ Backend health: HEALTHY${NC}"
else
    echo -e "${RED}✗ Backend health: ${HEALTH}${NC}"
fi

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Deployment Complete                     ║${NC}"
echo -e "${BLUE}╠══════════════════════════════════════════╣${NC}"
echo -e "║  Backend:  ${RAILWAY_URL}"
echo -e "║  Frontend: Check Vercel dashboard"
echo -e "║  Health:   ${RAILWAY_URL}/api/health"
echo -e "║  Verify:   POST ${RAILWAY_URL}/api/verify"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
