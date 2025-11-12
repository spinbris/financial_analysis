#!/bin/bash

# Script to regenerate all company analyses in parallel with corrected markdown formatting
# This will update the local ChromaDB with properly formatted reports

export SEC_EDGAR_USER_AGENT="FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

# Array of tickers to analyze
TICKERS=("AAPL" "MSFT" "GOOGL" "AMZN" "NVDA" "META" "BRK" "JNJ" "UNH" "NFLX" "DELL")

# Create logs directory
mkdir -p /tmp/analyses_logs

echo "Starting parallel analysis for ${#TICKERS[@]} companies..."
echo "Logs will be written to /tmp/analyses_logs/"
echo ""

# Launch all analyses in parallel, redirect output to log files
for ticker in "${TICKERS[@]}"; do
    echo "Starting analysis for $ticker..."
    echo "Comprehensive financial analysis of $ticker" | .venv/bin/python -m financial_research_agent.main_enhanced \
        --ticker "$ticker" \
        --mode full \
        > "/tmp/analyses_logs/${ticker}.log" 2>&1 &
done

echo ""
echo "All analyses started in background."
echo "Monitor progress with:"
echo "  tail -f /tmp/analyses_logs/AAPL.log"
echo ""
echo "Check completion status with:"
echo "  for ticker in AAPL MSFT GOOGL AMZN NVDA META BRK JNJ UNH NFLX DELL; do echo \"=== \$ticker ===\"; tail -30 /tmp/analyses_logs/\$ticker.log; done"
echo ""
echo "Wait for all to complete:"
echo "  wait"

# Wait for all background jobs to complete
wait

echo ""
echo "All analyses complete!"
echo "Check the logs in /tmp/analyses_logs/ for any errors."
