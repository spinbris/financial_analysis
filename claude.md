# Financial Analysis Project - Claude Context & Guardrails

## Project Overview

This is an **AI-powered financial research system** that produces investment-grade reports with SEC EDGAR integration. It's currently in **active development** and being used to investigate technologies rather than as an operational tool.

**⚠️ IMPORTANT: This is NOT a production tool for making financial decisions. It's an educational/research prototype.**

---

## Purpose & Scope

### What This Project Does
- Fetches and analyzes SEC EDGAR filings (10-K, 10-Q, 8-K)
- Extracts 118+ financial statement line items using XBRL
- Calculates comprehensive financial ratios and metrics
- Generates 3-5 page investment-grade analysis reports
- Provides semantic search over historical analyses via ChromaDB RAG
- Offers both Gradio web UI and REST API access

### What This Project Is NOT
- ❌ NOT financial advice or investment recommendations
- ❌ NOT a production trading system
- ❌ NOT suitable for real investment decisions
- ❌ NOT complete or fully tested
- ❌ NOT a replacement for professional financial analysis

### Current Status
- ✅ Core analysis pipeline working
- ✅ XBRL extraction functional
- ✅ RAG integration operational
- ⚠️ Still in development - incomplete features
- ⚠️ Modal deployment is prototype-level
- ⚠️ Error handling needs improvement
- ⚠️ Testing coverage incomplete

---

## Architecture

```
User Input (Ticker + Query)
    ↓
Planner Agent → Creates search strategy
    ↓
Search Agent → Gathers market context (Brave API)
    ↓
ChromaDB Filing Cache → Check for cached 10-K/10-Q filings
    ↓ (cache hit: 0.02s, cache miss: download & cache)
EDGAR Agent → Fetches SEC filings (edgartools)
    ↓
Specialist Agents:
├─ Financial Statements Agent → Extracts XBRL (118+ items)
├─ Financial Metrics Agent → Calculates ratios
├─ Financials Agent → 800-1200 word analysis
└─ Risk Agent → 800-1200 word risk assessment (uses cached filings)
    ↓
Writer Agent → Synthesizes comprehensive report
    ↓
Verification Agent → Quality checks
    ↓
ChromaDB RAG → Indexes for future retrieval
```

### SEC Filing Cache

ChromaDB stores two separate collections:
1. **`financial_analyses`** - Indexed analysis reports for semantic search
2. **`sec_filings_cache`** - Raw SEC filing content (10-K, 10-Q) for instant retrieval

**How it works:**
- First analysis for a ticker: Downloads 10-K/10-Q from SEC EDGAR, extracts Item 1A (Risk Factors), Item 2 (MD&A), Item 3 (Legal), stores in cache
- Subsequent analyses: Retrieves from cache (~0.02s vs ~7s download) - **99.7% speedup**
- 8-K filings: Always fetched fresh (they contain material events that change frequently)

**Key files:**
- `financial_research_agent/rag/chroma_manager.py` - Contains `store_sec_filing()`, `get_cached_filing()`, `reset_filings_cache()`
- `financial_research_agent/edgar_tools.py` - `extract_risk_factors()` function with cache integration

---

## Critical Guardrails for AI Assistants

### Financial Analysis Ethics

**NEVER:**
- Make specific buy/sell/hold recommendations
- Predict future stock prices
- Guarantee investment returns
- Suggest this is suitable for real trading decisions
- Encourage users to make financial decisions based solely on this tool
- Present analysis as professional financial advice

**ALWAYS:**
- Emphasize this is educational/research only
- Remind users to consult qualified financial advisors
- Note the limitations and potential errors
- Highlight the incomplete development state
- Encourage verification of data from primary sources

### Data Accuracy & Limitations

**Be Clear About:**
- XBRL data is extracted programmatically and may contain parsing errors
- Web search results provide market context but aren't verified
- AI-generated analysis reflects patterns, not professional judgment
- Historical data doesn't predict future performance
- The system doesn't account for qualitative factors (management quality, competitive moats, etc.)
- RAG search results depend on available analyses in ChromaDB

**When Helping Users:**
- Encourage verification against official SEC filings
- Suggest cross-referencing with multiple sources
- Note where data might be stale or incomplete
- Point out calculation assumptions

### Code Modification Safety

**Be Cautious With:**
- Changing financial calculation formulas (could produce incorrect ratios)
- Modifying XBRL extraction logic (could break data integrity)
- Altering agent prompts without understanding impact on quality
- Changing ChromaDB schema (could break existing analyses)
- Modifying Modal deployment without testing costs
- **RAG ticker extraction** in `rag/utils.py` - edgartools validation is critical
- **Web search rate limiting** in `web_app.py` - semaphore prevents API throttling
- **Synthesis agent prompts** in `rag/synthesis_agent.py` - controls answer quality

**Test Changes:**
- Always run data verification checks after modifying financial calculations
- Compare output against known-good analyses
- Check balance sheet equation validation (Assets = Liabilities + Equity)
- Verify XBRL extraction with raw CSV audit files
- Test ticker extraction with queries like "Tesla's key financial risks" (should not extract "KEY")
- Test multi-company queries for rate limiting (e.g., 5+ companies with web search enabled)

---

## Key File Locations & Purposes

### Core Code
```
financial_research_agent/
├── main_enhanced.py          # Main analysis pipeline (production)
├── main_budget.py            # Budget mode (cost-optimized)
├── web_app.py                # Gradio web interface implementation
├── agents/                   # Specialist agents
│   ├── planner.py
│   ├── search_agent.py       # Multi-provider web search (Brave/Serper)
│   ├── edgar.py
│   ├── financial_statements.py
│   ├── financial_metrics.py
│   ├── financials.py
│   ├── risk.py
│   ├── writer.py
│   └── verifier.py
├── rag/
│   ├── chroma_manager.py     # RAG/ChromaDB integration
│   ├── synthesis_agent.py    # AI-powered answer synthesis with web search
│   └── utils.py              # Ticker extraction (edgartools validation)
├── tools/
│   ├── edgar_tools.py        # XBRL extraction logic
│   └── brave_search.py       # Brave Search API integration
└── utils/
    └── sector_detection.py   # Sector-specific logic & ticker normalization
```

### Deployment
```
modal_app.py                  # Modal deployment config
launch_web_app.py             # Gradio web interface launcher
```

### Output
```
output/YYYYMMDD_HHMMSS/       # Timestamped analysis results
├── 00_query.md
├── 03_financial_statements.md
├── 04_financial_metrics.md
├── 07_comprehensive_report.md
└── xbrl_raw_*.csv            # Audit trail
```

### Documentation Structure
```
root/
├── README.md                 # Project overview
├── QUICKSTART.md             # Quick start guide
├── ARCHITECTURE.md           # System architecture
├── CLAUDE.md                 # AI assistant context (this file)
└── docs/
    ├── SETUP.md              # Detailed setup
    ├── COST_GUIDE.md         # Cost optimization
    ├── WEB_APP_GUIDE.md      # Web interface guide
    ├── DEV_WORKFLOW.md       # Development workflow
    ├── MASTER_DEV_PLAN.md    # Roadmap
    └── archive/              # Completed implementation docs
```

---

## Common Tasks & Guidance

### Running Analysis

```bash
# Standard analysis
python -m financial_research_agent.main_enhanced

# Budget mode (cheaper, lower quality)
python -m financial_research_agent.main_budget

# Web interface
python launch_web_app.py

# Modal deployment
modal deploy modal_app.py
```

### Modifying Agent Behavior

**Agent Prompts** are in each agent file. When modifying:
1. Read the existing prompt carefully
2. Understand the agent's role in the pipeline
3. Test with known companies (AAPL, MSFT) before deploying
4. Check output quality matches expectations
5. Verify data verification still passes

### Adding New Financial Metrics

1. Edit `financial_research_agent/agents/financial_metrics.py`
2. Add calculation logic with clear comments
3. Include the metric in the output template
4. Test against known values (e.g., published company ratios)
5. Update documentation

### Working with XBRL Data

**XBRL is complex:**
- Different companies use different tags
- Not all items are present in all filings
- Presentation order matters (reflects official SEC filing structure)
- Abstract items (headers) don't have values

**When debugging XBRL extraction:**
- Check the `xbrl_raw_*.csv` files for audit trail
- Compare against official SEC filing (HTML viewer)
- Look for missing line items in edgartools output
- Be aware of fiscal year vs calendar year differences

---

## Development Priorities (Incomplete Features)

### High Priority (Should Address Soon)
- [ ] Error handling for missing XBRL tags
- [ ] Rate limiting for API calls
- [ ] Better handling of non-standard fiscal years
- [ ] User authentication for web interface
- [ ] Cost tracking and budgeting per user
- [ ] Comprehensive test suite

### Medium Priority
- [ ] Support for international companies (non-US)
- [ ] Historical trend analysis (multi-year)
- [ ] Industry peer comparisons (automated)
- [ ] Export to PDF/Excel
- [ ] Email notifications for completed analyses

### Future Considerations
- [ ] Real-time price data integration
- [ ] News sentiment analysis
- [ ] Management compensation analysis
- [ ] Insider trading tracking
- [ ] Custom report templates

---

## Known Issues & Limitations

### Data Issues
- **Fiscal Year Mismatches**: Some companies' fiscal years don't align with calendar years
- **Restatements**: Historical data may be restated; system uses latest filings
- **Missing Items**: Not all XBRL tags are present in all companies
- **Foreign Companies**: Limited support for non-US companies

### Technical Issues
- **Long Running Time**: Analysis takes 3-5 minutes (API calls + processing)
- **Cost**: ~$0.08 per analysis (OpenAI API usage)
- **Memory**: ChromaDB requires significant RAM for large databases
- **Rate Limits**: SEC EDGAR and Brave API have rate limits

### Quality Issues
- **AI Hallucination Risk**: LLM-generated analysis should be verified
- **Calculation Errors**: Complex ratios may have edge cases
- **Context Window**: Very long financial statements may exceed limits
- **Duplicate Handling**: ChromaDB upsert prevents duplicates but may update when unnecessary

---

## Recent RAG Improvements (November 2025)

### Ticker Extraction Enhancement
**Problem**: Queries like "Compare Microsoft and Google's cloud strategies" extracted "CLOUD" as a ticker. "What are Tesla's key financial risks?" extracted "KEY" and "RISKS".

**Solution**: Implemented edgartools validation in [rag/utils.py](financial_research_agent/rag/utils.py):
- `_validate_ticker_with_edgar(ticker)` function uses `Company(ticker)` lookup
- Checks for "Entity -999999999" placeholder for invalid tickers
- Reduced common_words blacklist to only basic English words
- Sustainable approach - no more hardcoded financial term blacklists

**Impact**: Eliminated false positive ticker extraction, more accurate KB queries

### Web Search Rate Limiting
**Problem**: KB query web search hit HTTP 429 errors when querying multiple companies (e.g., "Compare AI spend among AAPL, MSFT, GOOGL, META, NVDA") - only 1 of 5 succeeded.

**Solution**: Implemented rate limiting in [web_app.py](financial_research_agent/web_app.py):
- `asyncio.Semaphore(2)` limits concurrent Brave API requests
- Exponential backoff retry (1s, 2s, 4s) for 429 errors
- 0.5 second spacing between successful requests
- Enhanced error tracking and user-visible error messages

**Impact**: Reliable multi-company queries, no more rate limit failures

### Visualization Suggestions
**Enhancement**: RAG synthesis agent now suggests appropriate visualizations in [rag/synthesis_agent.py](financial_research_agent/rag/synthesis_agent.py):
- Trends over time → Line chart suggestion
- Multi-company comparisons → Grouped bar chart suggestion
- Composition/breakdown → Pie chart suggestion
- Added `ChartData` Pydantic model for structured chart specifications

**Impact**: Users know when visualizations would improve data comprehension

### Multi-Company Query Balance
**Enhancement**: Per-company query strategy ensures equal representation:
- 2 financial_metrics chunks + 1 general chunk per company
- Prevents single company dominating results
- More balanced comparison answers

---

## API Keys & Secrets

### Required Keys
- `OPENAI_API_KEY`: For AI agents (required)
- `BRAVE_API_KEY`: For web search (optional but recommended)

### Modal Secrets Setup
```bash
# Create secrets in Modal
modal secret create openai-secret OPENAI_API_KEY=sk-proj-...
modal secret create brave-secret BRAVE_API_KEY=BSA...
```

### Local Development
```bash
# Create .env file
echo "OPENAI_API_KEY=sk-proj-..." > .env
echo "BRAVE_API_KEY=BSA..." >> .env
```

**Never commit API keys to git!**

---

## Cost Management

### Per-Analysis Costs
- Standard mode: ~$0.08 (GPT-4.1 + o3-mini)
- Budget mode: ~$0.10 (gpt-4o-mini, but lower quality)

### Cost Optimization
- Use 7-day caching to avoid re-analyzing recent companies
- Consider batch processing during off-peak hours
- Use budget mode for exploratory analysis
- Monitor OpenAI usage dashboard

### Modal Costs
- Compute: ~$0.001/minute
- Storage: Free for first 50GB
- Network: Minimal for API calls

---

## Testing & Verification

### Data Verification
Every analysis includes automatic checks:
- ✅ Balance Sheet Equation: Assets = Liabilities + Equity (0.1% tolerance)
- ✅ XBRL Audit Trail: Raw CSV files for manual verification
- ✅ Comparative Period Data: Current vs prior period

### Testing Suggestions
```python
# Run test analysis
python -m financial_research_agent.main_enhanced

# Compare against known company
# AAPL is good for testing - stable, well-documented

# Check data verification
cat output/*/data_verification.md

# Review XBRL audit trail
cat output/*/xbrl_raw_balance_sheet_*.csv
```

---

## Integration Points

### Gradio Web Interface
- Located in `launch_web_app.py`
- Three modes: Run New, View Existing, Query Knowledge Base
- Runs on port 7860 by default
- KB query mode includes:
  - Intelligent ticker extraction with edgartools validation
  - Web search supplementation with rate limiting
  - Multi-company balanced queries
  - Visualization suggestions
  - Error reporting for web search issues

### Modal API
- REST endpoints for programmatic access
- Requires user-provided OpenAI keys for new analyses
- Shared ChromaDB for all users
- See README for API documentation

### ChromaDB RAG
- Persistent vector database
- Semantic search over analyses
- Automatic indexing after each analysis
- Query via Python API or REST
- AI synthesis agent (gpt-4o-mini) for coherent answers
- Web search fallback via Brave API (with rate limiting)
- Ticker extraction uses edgartools Company lookup to prevent false positives

---

## Compliance & Legal

### Disclaimers Required

**In Any User-Facing Implementation:**
- This is not financial advice
- Not suitable for investment decisions
- Educational/research purposes only
- Consult qualified professionals for financial advice
- No warranties or guarantees

### Data Attribution
- SEC EDGAR data: Public domain (U.S. Government)
- edgartools: MIT License (Dwight Gunning)
- OpenAI Agents SDK: MIT License (OpenAI)
- SEC EDGAR MCP: AGPL-3.0 (Stefano Amorelli)

See ATTRIBUTION.md for complete licensing information.

### Investment Advisor Compliance
- This tool does NOT provide investment advice
- Not registered with SEC or other regulatory bodies
- Users must comply with local securities regulations
- Professional use may require proper licensing

---

## When Helping Users

### Good Practices
✅ Encourage understanding of how the system works
✅ Explain limitations and potential errors
✅ Suggest verification against official sources
✅ Help debug technical issues
✅ Provide context for financial metrics
✅ Explain XBRL data structure

### Avoid
❌ Making financial predictions
❌ Suggesting this replaces professional analysis
❌ Recommending specific stocks
❌ Guaranteeing accuracy of results
❌ Encouraging production use without proper testing
❌ Modifying code without understanding implications

---

## Quick Reference

### Start Analysis
```bash
python launch_web_app.py
# Visit http://localhost:7860
```

### Query ChromaDB
```python
from financial_research_agent.rag.chroma_manager import FinancialRAGManager
rag = FinancialRAGManager(persist_directory="./chroma_db")
results = rag.query("What is AAPL revenue?", ticker="AAPL")
```

### Deploy to Modal
```bash
modal deploy modal_app.py
```

### View Logs
```bash
modal app logs financial-research-agent
```

---

## Support & Documentation

### Key Docs

**Root Level:**
- README.md - Overview and setup
- QUICKSTART.md - Quick start guide
- ARCHITECTURE.md - System architecture
- CLAUDE.md - This file (AI assistant context)

**docs/ Folder:**
- SETUP.md - Detailed installation
- COST_GUIDE.md - Cost breakdown
- EDGAR_INTEGRATION_GUIDE.md - XBRL details
- WEB_APP_GUIDE.md - Web interface usage
- DEV_WORKFLOW.md - Development workflow
- MASTER_DEV_PLAN.md - Long-term roadmap
- ISSUES_ENHANCEMENTS.md - Known issues

**docs/archive/ Folder:**
- Completed implementation documentation (banking ratios, UI fixes, phase completions)
- Historical reference only - not current guidance

**Legal:**
- ATTRIBUTION.md - Licensing
- LICENSE - MIT License text

### Getting Help
1. Check error_log.txt in output directory
2. Review data_verification.md for data issues
3. Check Modal logs for deployment issues
4. Consult SEC EDGAR documentation for filing questions
5. Review OpenAI Agents SDK docs for agent issues
6. For completed features, check docs/archive/ for implementation details

---

## Final Reminders for AI Assistants

1. **This is educational/research software** - always emphasize this
2. **Not for production financial decisions** - make this crystal clear
3. **Verify calculations** - encourage checking against official data
4. **Test changes** - especially financial calculations
5. **Respect licenses** - maintain proper attribution
6. **Cost awareness** - remind users of API costs
7. **Data limitations** - be honest about what the system can/can't do
8. **Security** - protect API keys, don't expose user data

---

**Remember: We're building a research tool to learn about financial data extraction and AI agents, not a production financial advisory system.**
