# 🚀 Launch Instructions - Web Interface

## ✅ Everything is Ready!

All tests passed. Your web interface is ready to launch.

## Quick Start

```bash
# From the project directory:
.venv/bin/python launch_web_app.py
```

**That's it!** The interface will open at: http://localhost:7860

## What You'll See

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     📊 FINANCIAL RESEARCH AGENT - WEB INTERFACE              ║
║                                                               ║
║     Investment-Grade Financial Analysis                       ║
║     Powered by SEC EDGAR                                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Starting web server...

The interface will open in your default browser.
If it doesn't open automatically, navigate to: http://localhost:7860

Press Ctrl+C to stop the server.

Running on local URL:  http://127.0.0.1:7860
```

## First Analysis (Recommended)

1. **Click "Tesla Q3 2025 Performance"** template
2. **Click "Generate Analysis"** button
3. **Wait 30-60 seconds** while it:
   - Extracts data from SEC EDGAR
   - Analyzes financial statements
   - Calculates 15+ financial ratios
   - Generates comprehensive report

4. **View results** in tabs:
   - **Comprehensive Report** - Full 3-5 page analysis
   - **Financial Statements** - Balance Sheet, Income, Cash Flow
   - **Financial Metrics** - Ratios with YoY trends (↑/↓)
   - **Data Verification** - Quality assurance report

## Interface Features

### Tab 1: Query 🔍
- **7 Pre-built Templates:**
  - Tesla Q3 2025 Performance
  - Apple Quarterly Analysis
  - Microsoft Financial Health
  - Amazon Risk Assessment
  - NVIDIA Profitability Analysis
  - Google vs Microsoft Comparison
  - Meta Investment Potential

- **Custom Queries:**
  - "Analyze [Company]'s Q[X] 202[X] financial performance"
  - "What are [Company]'s key financial risks?"
  - "Evaluate [Company]'s profitability trends"

### Tab 2: Comprehensive Report 📄
- Executive Summary
- Financial Performance Analysis
- Risk Assessment
- Forward-Looking Indicators
- Synthesis & Recommendations

### Tab 3: Financial Statements 💰
- **Balance Sheet** (40+ line items)
  - Current Assets, Liabilities, Equity
  - Comparative periods with actual dates
  - Human-readable labels

- **Income Statement** (25+ line items)
  - Revenue, Expenses, Net Income
  - YoY comparison

- **Cash Flow Statement** (30+ line items)
  - Operating, Investing, Financing
  - Actual XBRL precision

### Tab 4: Financial Metrics 📈
**With YoY Comparison:**

| Ratio | 2025-09-30 | 2024-12-31 | Change | % Change |
|-------|------------|------------|--------|----------|
| Current Ratio | 2.07 | 2.02 | +0.05 | +2.5% ↑ |

**Categories:**
- Liquidity (Current, Quick, Cash ratios)
- Solvency (Debt-to-Equity, Debt-to-Assets)
- Profitability (Margins, ROA, ROE)
- Efficiency (Turnover ratios)

### Tab 5: Data Verification ✅
- ✅ All statements present
- ✅ Balance sheet equation verified
- ✅ 47 line items extracted
- ✅ Comparative data complete
- Source: SEC EDGAR XBRL

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'gradio'"

**Solution:**
```bash
.venv/bin/pip install gradio
```

### Issue: "Port 7860 already in use"

**Solution 1 - Kill existing process:**
```bash
lsof -i :7860
kill -9 <PID>
```

**Solution 2 - Use different port:**
```bash
.venv/bin/python -m financial_research_agent.web_app --server-port 8080
```

### Issue: "Address already in use" on Mac

**Solution:**
```bash
# Find process
lsof -ti:7860 | xargs kill -9
```

### Issue: Analysis times out or fails

**Possible causes:**
1. No internet connection (needs SEC.gov access)
2. SEC EDGAR user agent not set in `.env`
3. Invalid company name

**Check:**
```bash
# Verify .env exists
cat .env

# Should contain:
# SEC_EDGAR_USER_AGENT="FinancialResearchAgent/1.0 (your-email@example.com)"
```

## Testing Before Launch

Run the test suite:
```bash
.venv/bin/python test_web_app.py
```

Expected output:
```
============================================================
TEST RESULTS
============================================================
Imports................................. ✅ PASS
Theme................................... ✅ PASS
Templates............................... ✅ PASS
Interface............................... ✅ PASS
============================================================
✅ ALL TESTS PASSED
```

## Advanced Options

### Share Publicly (Temporary URL)
```bash
.venv/bin/python launch_web_app.py --share
# Creates a temporary public URL for 72 hours
```

### Network Access (Other Devices)
```bash
.venv/bin/python launch_web_app.py --server-name 0.0.0.0
# Access from: http://<your-ip>:7860
```

### Custom Port
```bash
.venv/bin/python launch_web_app.py --server-port 8080
# Access at: http://localhost:8080
```

## Stopping the Server

Press **Ctrl+C** in the terminal where it's running:

```
^C
Keyboard interruption in main thread... closing server.
Killing tunnel <your-tunnel-id>
```

## What's Generated

Each analysis creates a timestamped directory:

```
financial_research_agent/output/YYYYMMDD_HHMMSS/
├── 03_financial_statements.md
├── 04_financial_metrics.md
├── 06_final_research_report.md
└── data_verification.md
```

**Reports are saved** even after closing the browser. You can:
- Open markdown files directly
- Copy to other applications
- Archive for later reference

## Next Steps

After trying the interface:

### Phase 2 Features (Optional)
- [ ] Dashboard with interactive charts
- [ ] PDF export functionality
- [ ] Search previous analyses
- [ ] Company comparison mode

### Database Integration (Optional)
See [DATABASE_INTEGRATION.md](DATABASE_INTEGRATION.md) for options:
- SQLite - Simple, embedded
- PostgreSQL - Production-grade
- ChromaDB - Semantic search

### Deployment (Optional)
- **Hugging Face Spaces** - Free Gradio hosting
- **Docker** - Containerized deployment
- **Railway/Render** - Cloud platforms

## Documentation

- **Quick Start:** [WEB_INTERFACE_QUICKSTART.md](WEB_INTERFACE_QUICKSTART.md)
- **Full Guide:** [WEB_APP_GUIDE.md](WEB_APP_GUIDE.md)
- **Database Options:** [DATABASE_INTEGRATION.md](DATABASE_INTEGRATION.md)
- **Technical Summary:** [WEB_INTERFACE_SUMMARY.md](WEB_INTERFACE_SUMMARY.md)

## Support

If you encounter issues:

1. **Check the documentation** above
2. **Run the test suite**: `.venv/bin/python test_web_app.py`
3. **Verify .env file** has SEC_EDGAR_USER_AGENT
4. **Check terminal output** for specific error messages

## Success Checklist

- [x] Virtual environment activated (`.venv`)
- [x] Gradio installed (`pip show gradio`)
- [x] Tests passing (`test_web_app.py`)
- [x] .env file configured
- [ ] Launch the app: `.venv/bin/python launch_web_app.py`
- [ ] Generate your first analysis
- [ ] Review all tabs
- [ ] Try different templates

---

**Ready?** Run: `.venv/bin/python launch_web_app.py`

The professional financial research interface awaits! 📊
