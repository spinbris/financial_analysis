#!/bin/bash
#
# Bootstrap Modal deployment with initial 10 mega-cap companies
#
# Usage: ./scripts/bootstrap_modal.sh
#
# Prerequisites:
# 1. modal CLI installed and authenticated
# 2. Modal secrets created (openai-secret, brave-secret)
# 3. Virtual environment activated with dependencies installed

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Modal Financial Research Agent - Week 1 Bootstrap${NC}"
echo -e "${BLUE}  Initial 10 Mega-Cap Companies${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Top 10 mega-cap companies
TICKERS=(
    "AAPL"   # Apple
    "MSFT"   # Microsoft
    "GOOGL"  # Alphabet
    "AMZN"   # Amazon
    "NVDA"   # NVIDIA
    "META"   # Meta
    "TSLA"   # Tesla
    "BRK.B"  # Berkshire Hathaway
    "JNJ"    # Johnson & Johnson
    "UNH"    # UnitedHealth Group
)

# Configuration
OUTPUT_DIR="financial_research_agent/output"
MODAL_APP="modal_app.py"
SEC_EDGAR_USER_AGENT="${SEC_EDGAR_USER_AGENT:-FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)}"

# Counters
TOTAL=${#TICKERS[@]}
SUCCESS=0
FAILED=0
SKIPPED=0

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo -e "${YELLOW}Step 1: Verify Prerequisites${NC}"
echo ""

# Check if modal is installed
if ! command -v .venv/bin/modal &> /dev/null; then
    echo -e "${RED}✗ Modal CLI not found. Install with: pip install modal${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Modal CLI installed${NC}"

# Check if authenticated (check for token file)
if [ ! -f "$HOME/.modal.toml" ]; then
    echo -e "${RED}✗ Not authenticated with Modal. Run: modal token new${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Modal authenticated${NC}"

# Check if Python virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠ Virtual environment not detected. Assuming system Python.${NC}"
else
    echo -e "${GREEN}✓ Virtual environment active: $VIRTUAL_ENV${NC}"
fi

# Check if modal_app.py exists
if [[ ! -f "$MODAL_APP" ]]; then
    echo -e "${RED}✗ $MODAL_APP not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Modal app found${NC}"

echo ""
echo -e "${YELLOW}Step 2: Deploy Modal App${NC}"
echo ""

# Deploy Modal app
echo -e "${BLUE}Deploying Modal app...${NC}"
if .venv/bin/modal deploy "$MODAL_APP"; then
    echo -e "${GREEN}✓ Modal app deployed successfully${NC}"
else
    echo -e "${RED}✗ Failed to deploy Modal app${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 3: Generate & Upload Analyses${NC}"
echo ""
echo -e "${BLUE}Processing $TOTAL companies...${NC}"
echo ""

# Process each ticker
for i in "${!TICKERS[@]}"; do
    TICKER="${TICKERS[$i]}"
    NUM=$((i + 1))

    echo -e "${BLUE}[$NUM/$TOTAL] Processing $TICKER${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Generate analysis locally
    echo "  🔍 Generating analysis..."

    if echo "Analyze $TICKER's latest financial performance" | \
       SEC_EDGAR_USER_AGENT="$SEC_EDGAR_USER_AGENT" \
       .venv/bin/python -m financial_research_agent.main_enhanced > /tmp/bootstrap_${TICKER}.log 2>&1; then

        echo -e "  ${GREEN}✓ Analysis generated${NC}"

        # Find the most recent output directory for this ticker
        LATEST_DIR=$(ls -td "$OUTPUT_DIR"/2025* 2>/dev/null | head -1)

        if [[ -z "$LATEST_DIR" ]]; then
            echo -e "  ${RED}✗ Could not find output directory${NC}"
            ((FAILED++))
            continue
        fi

        echo "  📤 Uploading to Modal ChromaDB..."

        # Upload to Modal
        if modal run "$MODAL_APP"::index_local_analysis \
           --output-dir-path "$LATEST_DIR" \
           --ticker "$TICKER" > /tmp/upload_${TICKER}.log 2>&1; then

            echo -e "  ${GREEN}✓ Uploaded to Modal${NC}"
            ((SUCCESS++))
        else
            echo -e "  ${RED}✗ Upload failed${NC}"
            echo "  See log: /tmp/upload_${TICKER}.log"
            ((FAILED++))
        fi
    else
        echo -e "  ${RED}✗ Analysis generation failed${NC}"
        echo "  See log: /tmp/bootstrap_${TICKER}.log"
        ((FAILED++))
    fi

    echo ""
done

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Bootstrap Complete${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "Total companies: $TOTAL"
echo -e "${GREEN}Successful: $SUCCESS${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [[ $SUCCESS -gt 0 ]]; then
    echo -e "${YELLOW}Next Steps:${NC}"
    echo ""
    echo "1. Get your Modal web endpoint:"
    echo "   modal app list"
    echo ""
    echo "2. Test query API:"
    echo "   curl https://YOUR-USERNAME--financial-research-agent-web-app.modal.run/api/query \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"query\": \"What are Apple main revenue sources?\", \"ticker\": \"AAPL\"}'"
    echo ""
    echo "3. List indexed companies:"
    echo "   curl https://YOUR-USERNAME--financial-research-agent-web-app.modal.run/api/companies"
    echo ""
    echo -e "${GREEN}✓ Your financial research API is ready!${NC}"
fi

if [[ $FAILED -gt 0 ]]; then
    echo ""
    echo -e "${YELLOW}⚠ Some analyses failed. Check logs in /tmp/bootstrap_*.log and /tmp/upload_*.log${NC}"
    exit 1
fi
