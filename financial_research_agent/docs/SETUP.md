# Setup Guide - Enhanced Financial Research Agent

## Quick Start Checklist

### ✅ Step 1: Set Your OpenAI API Key

Edit the `.env` file and replace `your_openai_api_key_here` with your actual API key:

```bash
# Open .env file
code financial_research_agent/.env  # or use your preferred editor

# Update this line:
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### ✅ Step 2: Verify EDGAR Configuration

The `.env` file already has EDGAR enabled with your email:

```bash
ENABLE_EDGAR_INTEGRATION=true
SEC_EDGAR_USER_AGENT=FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)
```

**This is already correct!** ✓

### ✅ Step 3: Install Dependencies (if needed)

```bash
# From the project root
# Preferred: use the project's `uv` workflow if installed in your environment
uv pip install python-dotenv

# Alternative (using the project's virtual environment):
# Activate the venv (recommended) and install:
source .venv/bin/activate
pip install python-dotenv

# Or install without activating by invoking the venv's pip directly:
./.venv/bin/python -m pip install python-dotenv
```

**Note:** `openai-agents` and `rich` should already be installed from your existing setup.

### ✅ Step 4: Run the Enhanced Agent

```bash
# RECOMMENDED: Use the venv Python directly (ensures all dependencies are available)
.venv/bin/python -m financial_research_agent.main_enhanced

# Alternative: Activate venv first, then run
source .venv/bin/activate
python -m financial_research_agent.main_enhanced

# Or directly with venv Python:
.venv/bin/python financial_research_agent/main_enhanced.py
```

**Note:** Using `.venv/bin/python` ensures all installed dependencies are available.

### ✅ Step 5: Try It Out

Example queries to test:
```
Analyze Apple's most recent quarterly performance
What are the key risks facing Tesla?
Compare Microsoft and Google's financial health
```

## What to Expect

### First Run
1. **EDGAR Connection**: You'll see "Initializing SEC EDGAR connection..." (takes 2-3 seconds)
2. **Planning**: Agent plans 5-15 searches
3. **Searching**: Web searches execute in parallel
4. **EDGAR Data**: Gathers SEC filing data
5. **Specialist Analysis**:
   - Financials agent produces 800-1200 word analysis
   - Risk agent produces 800-1200 word analysis
6. **Report Synthesis**: Writer creates 1500-2500 word comprehensive report
7. **Verification**: Quality check of final report

### Total Time
- **Without EDGAR**: 2-4 minutes
- **With EDGAR**: 4-7 minutes

### Output Location
```
financial_research_agent/output/YYYYMMDD_HHMMSS/
├── 00_query.md
├── 01_search_plan.md
├── 02_search_results.md
├── 02_edgar_filings.md              ← SEC filing data
├── 03_financial_statements.md       ← Complete financial statements (tables)
├── 04_financial_metrics.md          ← Comprehensive ratio analysis
├── 05_financial_analysis.md         ← Full 800-1200 word financial analysis
├── 06_risk_analysis.md              ← Full 800-1200 word risk analysis
├── 07_comprehensive_report.md       ← Main 3-5 page report (synthesized)
└── 08_verification.md               ← Quality check
```

## Troubleshooting

### Error: "OPENAI_API_KEY not set"
**Solution:** Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-proj-your-key-here
```

### Error: "SEC_EDGAR_USER_AGENT not configured"
**Solution:** Already fixed in your `.env` file! ✓

### Warning: "Could not initialize EDGAR server"
**Possible causes:**
1. `uvx` not installed
2. Network issues
3. EDGAR MCP package unavailable

**Solution:**
```bash
# Check if uvx is available
uvx --version

# If not, install uv:
pip install uv

# Test EDGAR MCP manually:
SEC_EDGAR_USER_AGENT="FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)" uvx sec-edgar-mcp
```

**Note:** Agent will continue without EDGAR if connection fails, using web search only.

### Error: "Module not found: dotenv"
**Solution:**
```bash
**Solution:**
```bash
# If you use the project's `uv` tool (recommended):
uv pip install python-dotenv

# Or using the project's virtualenv:
source .venv/bin/activate
pip install python-dotenv
```

## Configuration Options

### Disable EDGAR (faster, but less authoritative)
```bash
# In .env
ENABLE_EDGAR_INTEGRATION=false
```

### Use Different Models
```bash
# In .env
PLANNER_MODEL=gpt-4o  # Instead of o3-mini
WRITER_MODEL=gpt-4o   # Instead of gpt-4.1
```

### Adjust Search Retries
```bash
# In .env
MAX_SEARCH_RETRIES=5
SEARCH_RETRY_DELAY=3.0
```

### Use Docker for EDGAR (instead of uvx)
```bash
# In .env
EDGAR_MCP_COMMAND=docker
EDGAR_MCP_ARGS=run -i --rm stefanoamorelli/sec-edgar-mcp:latest

# Requires Docker to be installed:
docker pull stefanoamorelli/sec-edgar-mcp:latest
```

## Comparing Enhanced vs Basic Version

### Run Basic Version (faster, shorter output)
```python
# In a Python script
from financial_research_agent.manager_with_edgar import FinancialResearchManagerWithEdgar

async def main():
    query = "Analyze Apple"
    mgr = FinancialResearchManagerWithEdgar()
    await mgr.run(query)
```

**Output:** ~500-800 words

### Run Enhanced Version (comprehensive, investment-grade)
```python
# In a Python script
from financial_research_agent.manager_enhanced import EnhancedFinancialResearchManager

async def main():
    query = "Analyze Apple"
    mgr = EnhancedFinancialResearchManager()
    await mgr.run(query)
```

**Output:** 1500-2500 words (3-5 pages)

## Next Steps

1. **Set your OpenAI API key** in `.env`
2. **Run the agent:**
   ```bash
   .venv/bin/python -m financial_research_agent.main_enhanced
   ```
3. **Check output:**
   ```bash
   ls -la financial_research_agent/output/
   ```
4. **Read the comprehensive report:**
   ```bash
   # Find the latest output directory
   cat financial_research_agent/output/*/07_comprehensive_report.md
   ```
5. **View financial metrics:**
   ```bash
   # Financial statements
   cat financial_research_agent/output/*/03_financial_statements.md

   # Ratio analysis
   cat financial_research_agent/output/*/04_financial_metrics.md
   ```

## Documentation

- **[EDGAR_QUICK_START.md](EDGAR_QUICK_START.md)** - EDGAR integration basics
- **[EDGAR_INTEGRATION_GUIDE.md](EDGAR_INTEGRATION_GUIDE.md)** - Comprehensive EDGAR docs
- **[COMPREHENSIVE_OUTPUT_GUIDE.md](COMPREHENSIVE_OUTPUT_GUIDE.md)** - Output structure explanation
- **[SPECIALIST_AGENTS_WITH_EDGAR.md](SPECIALIST_AGENTS_WITH_EDGAR.md)** - How specialist agents use EDGAR

## Support

If you encounter issues:
1. Check this setup guide
2. Review error messages carefully
3. Check the troubleshooting section
4. Consult the documentation links above

## Summary

**You're almost ready to go!** Just need to:
1. ✅ Add your OpenAI API key to `.env`
2. ✅ Run: `python -m financial_research_agent.main_enhanced`

Everything else is already configured!
