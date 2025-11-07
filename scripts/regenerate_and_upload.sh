#!/bin/bash
set -e

echo "=========================================="
echo "Regenerate Analyses & Upload to Modal"
echo "=========================================="
echo ""

# Step 1: Clean output directory (keep the directory itself)
echo "Step 1: Cleaning output directory..."
if [ -d "financial_research_agent/output" ]; then
    rm -rf financial_research_agent/output/*
    echo "✅ Cleaned financial_research_agent/output/"
else
    mkdir -p financial_research_agent/output
    echo "✅ Created financial_research_agent/output/"
fi
echo ""

# Step 2: Generate analyses for top 10 mega-cap companies
echo "Step 2: Generating analyses for 10 mega-cap companies..."
echo "This will take approximately 20-30 minutes total"
echo ""

TICKERS=("AAPL" "MSFT" "GOOGL" "AMZN" "NVDA" "META" "TSLA" "BRK.B" "JNJ" "UNH")

for ticker in "${TICKERS[@]}"; do
    echo "----------------------------------------"
    echo "Analyzing $ticker..."
    echo "----------------------------------------"

    # Pipe the query to main_enhanced to avoid interactive prompt
    echo "Analyze ${ticker}'s latest financial performance" | \
        SEC_EDGAR_USER_AGENT="FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)" \
        .venv/bin/python -m financial_research_agent.main_enhanced

    if [ $? -eq 0 ]; then
        echo "✅ $ticker analysis complete"
    else
        echo "❌ $ticker analysis failed"
    fi

    # Small buffer between analyses (5 seconds) - not strictly needed for Tier 2 but safe
    sleep 5
    echo ""
done

echo ""
echo "=========================================="
echo "Step 3: Uploading to Modal ChromaDB..."
echo "=========================================="
echo ""

# Get all output directories sorted by timestamp
output_dirs=($(ls -1dt financial_research_agent/output/*/))

if [ ${#output_dirs[@]} -eq 0 ]; then
    echo "❌ No output directories found!"
    exit 1
fi

echo "Found ${#output_dirs[@]} analyses to upload"
echo ""

# Upload each analysis
uploaded=0
for dir in "${output_dirs[@]}"; do
    # Remove trailing slash
    dir_clean="${dir%/}"

    # Try to extract ticker from the comprehensive report
    ticker=""
    if [ -f "$dir_clean/07_comprehensive_report.md" ]; then
        # Try to extract ticker from query or report
        ticker=$(grep -m 1 -oE '\b[A-Z]{1,5}\b' "$dir_clean/00_query.md" 2>/dev/null | head -1)
    fi

    if [ -z "$ticker" ]; then
        echo "⚠️  Skipping $dir_clean - couldn't extract ticker"
        continue
    fi

    echo "Uploading $ticker from $dir_clean..."
    .venv/bin/python scripts/upload_to_modal.py \
        --ticker "$ticker" \
        --analysis-dir "$dir_clean"

    if [ $? -eq 0 ]; then
        echo "✅ Uploaded $ticker"
        ((uploaded++))
    else
        echo "❌ Failed to upload $ticker"
    fi
    echo ""
done

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "✅ Generated ${#output_dirs[@]} analyses"
echo "✅ Uploaded $uploaded analyses to Modal"
echo ""
echo "Next steps:"
echo "1. Deploy Modal app: modal deploy modal_app.py"
echo "2. Test API: curl https://YOUR-USERNAME--financial-research-agent-web-app.modal.run/api/companies"
echo "3. Query knowledge base via Gradio: python launch_web_app.py"
echo ""
