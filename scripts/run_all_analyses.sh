#!/bin/bash
#
# Run all 10 company analyses with nohup (survives terminal disconnect)
# and caffeinate (keeps Mac awake)
#
# Usage: ./scripts/run_all_analyses.sh
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
TICKERS=(
    "MSFT"   # Microsoft (skip AAPL as it's already running)
    "GOOGL"  # Alphabet
    "AMZN"   # Amazon
    "NVDA"   # NVIDIA
    "META"   # Meta
    "TSLA"   # Tesla
    "BRK.B"  # Berkshire Hathaway
    "JNJ"    # Johnson & Johnson
    "UNH"    # UnitedHealth Group
)

SEC_EDGAR_USER_AGENT="FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Running 9 Company Analyses (AAPL already in progress)${NC}"
echo -e "${BLUE}  Process will survive terminal disconnect and Mac sleep${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Create logs directory
mkdir -p /tmp/analyses_logs

# Track PIDs
PIDS=()

# Start caffeinate to keep Mac awake
echo -e "${YELLOW}Starting caffeinate to keep Mac awake...${NC}"
caffeinate -d -i &
CAFFEINATE_PID=$!
echo -e "${GREEN}✓ Caffeinate running (PID: $CAFFEINATE_PID)${NC}"
echo ""

# Queue up all analyses with nohup
for ticker in "${TICKERS[@]}"; do
    echo -e "${BLUE}Queuing $ticker analysis...${NC}"

    # Run with nohup so it survives terminal disconnect
    nohup bash -c "
        echo 'Analyze $ticker latest financial performance' | \
        SEC_EDGAR_USER_AGENT='$SEC_EDGAR_USER_AGENT' \
        .venv/bin/python -m financial_research_agent.main_enhanced
    " > /tmp/analyses_logs/${ticker}.log 2>&1 &

    PID=$!
    PIDS+=($PID)

    echo -e "${GREEN}✓ Started $ticker (PID: $PID, log: /tmp/analyses_logs/${ticker}.log)${NC}"

    # Small delay to avoid overwhelming the system
    sleep 15
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}All analyses queued!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Running processes:"
for i in "${!TICKERS[@]}"; do
    echo "  ${TICKERS[$i]}: PID ${PIDS[$i]}"
done
echo ""
echo -e "${YELLOW}Monitor progress:${NC}"
echo "  tail -f /tmp/analyses_logs/MSFT.log"
echo ""
echo -e "${YELLOW}Check running processes:${NC}"
echo "  ps aux | grep python | grep main_enhanced"
echo ""
echo -e "${YELLOW}To stop caffeinate when done:${NC}"
echo "  kill $CAFFEINATE_PID"
echo ""
echo -e "${GREEN}✓ Safe to close terminal or lock screen - processes will continue!${NC}"
