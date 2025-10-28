# SEC EDGAR Integration - Quick Start

Get SEC filing data in your financial research reports in 3 steps.

## Quick Setup (5 minutes)

### 1. Install Prerequisites

```bash
# Option A: Use uvx (easiest - auto-installs on first run)
# No installation needed!

# Option B: Use pip
pip install sec-edgar-mcp

# Option C: Use Docker
docker pull stefanoamorelli/sec-edgar-mcp:latest
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env and set these two lines:
ENABLE_EDGAR_INTEGRATION=true
SEC_EDGAR_USER_AGENT=YourCompany/1.0 (your-email@example.com)
```

**Important:** Replace `your-email@example.com` with your real email. The SEC requires this.

### 3. Update Your Code

```python
# In main.py, change one line:
from .manager_with_edgar import FinancialResearchManagerWithEdgar

async def main() -> None:
    query = input("Enter a financial research query: ")
    mgr = FinancialResearchManagerWithEdgar()  # ← Use enhanced manager
    await mgr.run(query)
```

That's it! Now run your agent and it will automatically use SEC filings.

## What You Get

### Before (Web Search Only)
```
Query: "Analyze Apple's Q4 2024 performance"

Output:
- News articles about Apple's earnings
- Analyst opinions and estimates
- Third-party revenue figures (may vary)
- General commentary
```

### After (Web Search + EDGAR)
```
Query: "Analyze Apple's Q4 2024 performance"

Output:
- News articles AND official 10-Q filing
- Exact revenue: $119,575,000,000 (from XBRL)
- Exact net income: $33,916,000,000 (from XBRL)
- Direct SEC filing link for verification
- Filing date and accession number
- Management discussion & analysis from 10-Q
- Official risk factors from Item 1A
```

### BONUS: Specialist Agents Get EDGAR Too!

Not only does the main EDGAR agent have filing access, but the **specialist agents** (fundamentals and risk) also get EDGAR tools:

**Financials Agent:**
- Queries official financial statements from 10-K/10-Q
- Extracts exact XBRL data (no rounding)
- Cites: "Revenue of $119,575,000,000 per 10-Q filed 2025-01-31"

**Risk Agent:**
- Analyzes official Item 1A Risk Factors from 10-K
- Reviews recent 8-K filings for material events
- Cites: "Per Item 1A of 10-K filed 2024-11-01..."

See [SPECIALIST_AGENTS_WITH_EDGAR.md](SPECIALIST_AGENTS_WITH_EDGAR.md) for details.

## Test It

```bash
python -m financial_research_agent.main
```

Try these queries:
- "What was Microsoft's revenue last quarter?"
- "Analyze Tesla's insider trading activity"
- "Compare Apple and Google's profit margins"

## Verify It's Working

When EDGAR is enabled, you'll see:
1. Console message: `"Initializing SEC EDGAR connection..."`
2. Console message: `"SEC EDGAR connected"`
3. Output file: `02_edgar_filings.md` in your results
4. Report contains exact numbers with SEC filing citations

## Troubleshooting

**Problem:** `"SEC_EDGAR_USER_AGENT not configured"`
**Fix:** Set your User-Agent in `.env` with a real email address

**Problem:** `"Could not initialize EDGAR server"`
**Fix:** Install uvx: `pip install uv` or use Docker method

**Problem:** `"EDGAR data gathering failed"`
**Fix:** This is usually fine - agent continues with web search data

## Configuration Options

### Minimal (Just Works)
```bash
ENABLE_EDGAR_INTEGRATION=true
SEC_EDGAR_USER_AGENT=YourCompany/1.0 (you@email.com)
```

### Full Control
```bash
ENABLE_EDGAR_INTEGRATION=true
SEC_EDGAR_USER_AGENT=YourCompany/1.0 (you@email.com)

# Limit to specific tools only
EDGAR_ALLOWED_TOOLS=get_company_facts,get_recent_filings,get_financial_statements

# Use Docker instead of uvx
EDGAR_MCP_COMMAND=docker
EDGAR_MCP_ARGS=run -i --rm stefanoamorelli/sec-edgar-mcp:latest

# Custom model for EDGAR agent
EDGAR_MODEL=gpt-4o
```

## What Gets Saved

```
output/YYYYMMDD_HHMMSS/
├── 00_query.md                 # Your query
├── 01_search_plan.md           # Search strategy
├── 02_search_results.md        # Web search results
├── 02_edgar_filings.md         # ← NEW: SEC filing data
├── 03_final_report.md          # Final report (enhanced with EDGAR)
└── 04_verification.md          # Quality check
```

## Benefits

✅ **Exact Numbers** - No rounding, direct from XBRL
✅ **Verifiable** - Direct SEC URLs included
✅ **Authoritative** - Official filings, not third-party data
✅ **Comprehensive** - Combines news + official data
✅ **Traceable** - Filing dates and accession numbers

## Next Steps

- Read [EDGAR_INTEGRATION_GUIDE.md](EDGAR_INTEGRATION_GUIDE.md) for advanced usage
- Customize [edgar_agent.py](agents/edgar_agent.py) for specialized analysis
- Add custom tool filters for specific use cases
- Explore all available EDGAR tools

## Resources

- **Full Guide**: [EDGAR_INTEGRATION_GUIDE.md](EDGAR_INTEGRATION_GUIDE.md)
- **EDGAR MCP**: https://github.com/stefanoamorelli/sec-edgar-mcp
- **SEC Data Access**: https://www.sec.gov/os/accessing-edgar-data
