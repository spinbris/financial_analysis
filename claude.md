# Financial Analysis Project - Claude Context & Guardrails

**Last Updated:** November 28, 2025  
**Deployment Platform:** Railway (migrated from Modal November 2025)  
**Status:** Active Development - Phase 1 Complete, Phase 2 In Progress

## Project Overview

This is an **AI-powered financial research system** that produces investment-grade reports with SEC EDGAR integration. It's currently in **active development** and being used to investigate technologies rather than as an operational tool.

**⚠️ IMPORTANT: This is NOT a production tool for making financial decisions. It's an educational/research prototype.**

---

## Purpose & Scope

### What This Project Does
- Fetches and analyzes SEC EDGAR filings (10-K, 10-Q, 20-F, 8-K)
- Extracts 118+ financial statement line items using direct XBRL access via [edgartools](https://github.com/dgunning/edgartools)
- Calculates 18+ comprehensive financial ratios automatically
- Generates 3-5 page investment-grade analysis reports
- Provides semantic search over historical analyses via ChromaDB RAG
- Offers Gradio web UI with three modes: Run New, View Existing, Query Knowledge Base
- **Supports international companies** with 20-F filing support (tested with Australian companies like BHP)
- **Intelligent caching** via SQLite - 1,425x speedup on repeat queries (3.5s → 2.5ms)

### What This Project Is NOT
- ❌ NOT financial advice or investment recommendations
- ❌ NOT a production trading system  
- ❌ NOT suitable for real investment decisions
- ❌ NOT complete or fully tested
- ❌ NOT a replacement for professional financial analysis

### Current Status (November 2025)

**✅ Phase 1 Complete (Week 1 - Foundation):**
- SQLite financial cache with 20-F support implemented
- Direct edgartools library integration (no MCP server)
- Enhanced wrapper with `get_complete_financials()`, `search_line_items()`, `get_segment_data()`
- FinancialDataManager class created (unified interface)
- RatioCalculator with 18+ comprehensive ratios
- 1,425x performance improvement (3.5s → 2.5ms) via caching
- Validated with US companies (AAPL, MSFT) and foreign companies (BHP, WBKCY)

**🔄 Phase 2 In Progress (Week 2 - Enhancements):**
- ✅ Visualization module exists (4 chart types with Plotly)
- ⏳ Segment data extraction (Task 2.1) - 6 hours remaining
- ⏳ Expand visualization suite (Task 2.2) - 4 hours remaining
- ⏳ Statement formatter (Task 2.3) - 4 hours remaining
- ⏳ **Gradio UI integration (Task 2.4) - NEXT PRIORITY** - 6 hours remaining
  - Wire FinancialDataManager into web_app.py
  - Users will get faster cached data + 18+ ratios immediately

**⏳ Phase 3 Pending (Week 3 - Polish & Production):**
- Production deployment to Railway
- Comprehensive configuration system
- Complete documentation
- Full testing suite

**Deployment:**
- ✅ Railway deployment guide complete
- ✅ Modal files removed (November 2025)
- ✅ Railway-compatible configuration
- ⏳ Production deployment pending completion of Phase 2

---

## Architecture

```
User Input (Ticker + Query)
    ↓
Planner Agent → Creates search strategy
    ↓
Search Agent → Gathers market context (Brave API)
    ↓
SQLite Cache Check → Check for cached XBRL data
    ↓ (cache hit: 2.5ms, cache miss: download & cache)
EdgarTools Direct Access → Fetches SEC filings (10-K, 10-Q, 20-F, 8-K)
    ↓
FinancialDataManager (if integrated)
    ├─ SecFinancialCache → SQLite caching layer
    ├─ EdgarToolsWrapper → Direct XBRL extraction
    └─ RatioCalculator → 18+ comprehensive ratios
    ↓
Specialist Agents:
├─ Financial Statements Agent → Extracts 118+ XBRL items
├─ Financial Metrics Agent → Calculates ratios
├─ Financials Agent → 800-1200 word analysis
└─ Risk Agent → 800-1200 word risk assessment
    ↓
Writer Agent → Synthesizes comprehensive report
    ↓
Verification Agent → Quality checks
    ↓
ChromaDB RAG → Indexes for future retrieval
```

### Key Technical Components

**1. SQLite Financial Cache (`financial_research_agent/cache/`)**
- Stores structured financial data from SEC filings
- Supports both 10-K (US companies) and 20-F (foreign companies)
- Smart filing detection: latest annual + subsequent quarterlies
- 1,425x speedup on cache hits
- Schema includes: filings_metadata, balance_sheet, income_statement, cash_flow, financial_ratios, segment_data

**2. Direct EdgarTools Integration**
- No MCP server dependency (removed November 2025)
- Direct library access via `from edgar import Company`
- Proper EDGAR identity configuration via environment variables
- Financial statement extraction using `xbrl.get_statement_by_type()`
- Handles dictionary structures with 'data' keys containing line items

**3. FinancialDataManager (Ready for Integration)**
- Unified interface combining cache + wrapper + calculator
- Location: `financial_research_agent/financial_data_manager.py`
- Provides: FinancialMetrics dataclass, CalculatedRatios dataclass, RatioCalculator
- **Status:** Created but not yet wired into Gradio web_app.py (Task 2.4)

**4. ChromaDB RAG System**
- Two collections:
  - `financial_analyses` - Indexed analysis reports for semantic search
  - `sec_filings_cache` - Raw SEC filing content (10-K, 10-Q) for instant retrieval
- First analysis: Downloads and caches
- Subsequent analyses: Cache hit (~0.02s vs ~7s download)
- 8-K filings: Always fetched fresh (material events change frequently)

**5. Visualization System (Phase 1.5 Complete)**
- Location: `financial_research_agent/visualization/`
- 4 core chart types: margin comparison, key metrics dashboard, cash flow waterfall, revenue trends
- Plotly + Kaleido for interactive and static charts
- Charts display in Financial Analysis tab (Tab 5)
- Auto-generates from analysis data

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
- Highlight the development stage
- Encourage verification of data from primary sources

### Data Accuracy & Limitations

**Be Clear About:**
- XBRL data is extracted programmatically and may contain parsing errors
- Web search results provide market context but aren't verified
- AI-generated analysis reflects patterns, not professional judgment
- Historical data doesn't predict future performance
- System doesn't account for qualitative factors (management quality, competitive moats, etc.)
- RAG search results depend on available analyses in ChromaDB
- **Cache may be stale** - users should force refresh for critical decisions

**When Helping Users:**
- Encourage verification against official SEC filings
- Suggest cross-referencing with multiple sources
- Note where data might be stale or incomplete
- Point out calculation assumptions
- Explain the difference between cached and fresh data

### Code Modification Safety

**Be Cautious With:**
- Changing financial calculation formulas (could produce incorrect ratios)
- Modifying XBRL extraction logic (could break data integrity)
- Altering agent prompts without understanding impact on quality
- Changing ChromaDB or SQLite schema (could break existing data)
- **SQLite cache schema** (`cache/schema.sql`) - changes require migration
- **EdgarTools API patterns** - edgartools 4.29.0 has specific requirements
- **Railway deployment config** - affects production environment

**Always Test Changes:**
- Run data verification checks after modifying financial calculations
- Compare output against known-good analyses
- Check balance sheet equation validation (Assets = Liabilities + Equity)
- Verify XBRL extraction with multiple companies
- Test with both US companies (10-K) and foreign companies (20-F)
- **Verify cache hit/miss behavior** after cache changes
- **Test Railway deployment** before pushing to production

### EdgarTools API Patterns (Critical for Implementation)

**Correct Usage (edgartools 4.29.0):**
```python
# Proper EDGAR identity configuration
os.environ['EDGAR_IDENTITY'] = "Your Name your.email@example.com"

# Get statements
from edgar import Company
company = Company(ticker)
xbrl = company.get_filings(form=["10-K", "10-Q"])[0].xbrl()

# Extract statements - returns dictionary with 'data' key
balance_sheet = xbrl.get_statement_by_type('balance-sheet')
income_stmt = xbrl.get_statement_by_type('income-statement')
cash_flow = xbrl.get_statement_by_type('cash-flow')

# Access line items from 'data' key
for item in balance_sheet['data']:
    concept = item['concept']
    label = item['label']
    value = item.get('value', 0)
```

**Common Mistakes to Avoid:**
- ❌ Using `Company(ticker).financials` - wrong method
- ❌ Forgetting EDGAR identity configuration
- ❌ Not handling missing 'data' keys
- ❌ Assuming all concepts are present in all filings
- ❌ Using reserved SQL keywords (like "quarter") as column names

---

## Key File Locations & Purposes

### Core Code Structure

```
financial_research_agent/
├── cache/
│   ├── __init__.py
│   ├── sec_financial_cache.py       # SQLite cache implementation (Phase 1)
│   ├── cached_manager.py            # Cache-aware manager
│   ├── data_cache.py                # Data caching utilities
│   └── schema.sql                   # Database schema
├── tools/
│   ├── edgartools_wrapper.py        # Enhanced wrapper (Phase 1)
│   └── financial_ratios_calculator.py # 18+ ratios calculator
├── financial_data_manager.py        # Unified manager (Phase 1, not integrated)
├── manager_enhanced.py              # Current orchestrator (uses cache)
├── web_app.py                       # Gradio interface (needs Task 2.4)
├── visualization/
│   ├── charts.py                    # 4 chart types (Phase 1.5)
│   └── utils.py                     # Chart data extraction
├── agent_definitions/               # Specialist agents
│   ├── planner_agent.py
│   ├── search_agent.py
│   ├── edgar_agent.py
│   ├── financial_statements_agent.py
│   ├── financial_metrics_agent.py
│   ├── financials_agent_enhanced.py
│   ├── risk_agent_enhanced.py
│   ├── writer_agent_enhanced.py
│   └── verifier_agent.py
├── rag/
│   ├── chroma_manager.py            # RAG/ChromaDB integration
│   ├── synthesis_agent.py           # AI-powered answer synthesis
│   └── utils.py                     # Ticker extraction
├── edgar_tools.py                   # XBRL extraction utilities
└── config.py                        # Configuration management
```

### Deployment Files

```
Root Directory:
├── launch_web_app.py                # Gradio launcher (Railway compatible)
├── launch_web_app_with_auth.py     # With Supabase auth (Railway)
├── Dockerfile                       # Railway deployment (if needed)
├── pyproject.toml                   # Python 3.11+ dependencies
├── RAILWAY_DEPLOYMENT_GUIDE.md     # Railway deployment instructions
└── RAILWAY_MIGRATION_SUMMARY.md    # Migration details from Modal
```

### Output Structure

```
financial_research_agent/output/YYYYMMDD_HHMMSS/
├── 00_query.md                      # Original query
├── 01_search_plan.md                # Planner output
├── 02_search_results.md             # Web search results
├── 03_financial_statements.md       # XBRL statements (118+ items)
├── 04_financial_metrics.md          # 18+ calculated ratios
├── 05_financial_analysis.md         # Financial agent analysis
├── 06_risk_analysis.md              # Risk agent analysis
├── 07_comprehensive_report.md       # Final synthesized report
├── 08_data_verification.md          # Quality checks
├── 09_cost_report.md                # Cost tracking
├── metadata.json                    # Session metadata
├── chart_margins.json               # Visualization data (if generated)
├── chart_metrics.json               # Visualization data (if generated)
└── xbrl_raw_*.csv                   # Audit trail (raw XBRL data)
```

### Documentation Structure

```
Root:
├── README.md                        # Project overview
├── QUICKSTART.md                    # Quick start guide
├── ARCHITECTURE.md                  # System architecture
├── CLAUDE.md                        # This file (AI assistant context)
├── RAILWAY_DEPLOYMENT_GUIDE.md     # Railway deployment
├── RAILWAY_MIGRATION_SUMMARY.md    # Migration details
└── INTEGRATED_IMPLEMENTATION_PLAN.md # Phase 1-3 roadmap

docs/:
├── SETUP.md                         # Detailed setup
├── COST_GUIDE.md                    # Cost optimization
├── EDGAR_INTEGRATION_GUIDE.md      # EDGAR/XBRL details
├── WEB_APP_GUIDE.md                # Web interface usage
├── FINANCIAL_METRICS_GUIDE.md      # Financial ratios reference
├── DEV_WORKFLOW.md                 # Development workflow
├── MASTER_DEV_PLAN.md              # Long-term roadmap
├── ISSUES_ENHANCEMENTS.md          # Known issues
└── archive/                         # Completed implementation docs
```

---

## Common Tasks & Guidance

### Running the Application

**Web Interface (Recommended):**
```bash
python launch_web_app.py
# Opens at http://localhost:7860

# With Supabase authentication (Railway production):
python launch_web_app_with_auth.py
```

**Command Line Analysis:**
```bash
# Standard analysis
python -m financial_research_agent.main_enhanced

# Budget mode (cheaper, lower quality)
python -m financial_research_agent.main_budget
```

**Railway Deployment:**
```bash
# 1. Commit and push to GitHub
git add .
git commit -m "Update for Railway deployment"
git push origin main

# 2. Deploy via Railway dashboard (auto-detects Python)
# 3. Configure environment variables in Railway
# 4. Add persistent volume: /app/financial_research_agent (10GB)
# 5. Set start command: python launch_web_app_with_auth.py
```

### Working with the Cache System

**Check Cache Status:**
```python
from financial_research_agent.cache.sec_financial_cache import SecFinancialCache

cache = SecFinancialCache()
status = cache.check_cache_status("AAPL")
print(f"Cached: {status['cached']}")
print(f"Current: {status['current']}")
print(f"Cache age: {status['cache_age_days']} days")
```

**Force Cache Refresh:**
```python
# In web interface: Use force refresh option
# In code:
cache.cache_all_required_filings("AAPL", force=True)
```

**Search for Specific Line Items:**
```python
results = cache.search_line_items("AAPL", "accounts payable")
print(f"Found {len(results)} matching line items")
```

### Testing 20-F Support (Foreign Companies)

**Australian Companies (20-F):**
```bash
# Test with BHP (validated November 2025)
python test_20f_quick.py

# Or in code:
from edgar import Company
company = Company("BHP")
filings = company.get_filings(form="20-F")
print(f"Found {len(filings)} 20-F filings")
```

**Supported Countries:**
- Australia: BHP, RIO, WBC
- Europe: SAP (Germany), various others
- Asia: SONY (Japan), various others
- Any company filing 20-F with SEC

### Modifying Agent Behavior

**Agent Prompts** are in `financial_research_agent/agent_definitions/`. When modifying:
1. Read the existing prompt carefully
2. Understand the agent's role in the pipeline
3. Test with known companies (AAPL, MSFT, BHP) before deploying
4. Check output quality matches expectations
5. Verify data verification still passes
6. **Test with both 10-K and 20-F companies**

### Adding New Financial Metrics

1. Edit `financial_research_agent/tools/financial_ratios_calculator.py`
2. Add calculation logic with clear comments
3. Include the metric in the output template
4. Test against known values (e.g., published company ratios)
5. Update `FinancialMetrics` dataclass in `financial_data_manager.py`
6. Update documentation

### Working with XBRL Data

**XBRL is complex:**
- Different companies use different tags (US-GAAP vs IFRS)
- Not all items are present in all filings
- Fiscal year vs calendar year differences matter
- Abstract items (headers) don't have values
- **edgartools 4.29.0 uses specific API patterns** (see API Patterns section above)

**When debugging XBRL extraction:**
- Check the `xbrl_raw_*.csv` files in output directory
- Compare against official SEC filing (HTML viewer)
- Use `cache.search_line_items()` to find available concepts
- Be aware of fiscal year vs calendar year differences
- **Verify EDGAR_IDENTITY is set correctly**

---

## Development Priorities

### Current Priority: Task 2.4 (Next 2-3 hours)

**Wire FinancialDataManager into Gradio UI:**
1. Update `financial_research_agent/web_app.py`
2. Import `FinancialDataManager` instead of current approach
3. Replace data fetching with manager calls
4. Display cache status to users
5. Test with cached vs fresh data
6. Validate 18+ ratios display correctly
7. Test foreign company support (BHP)

**Expected Outcome:**
- ✅ Users get 1,425x faster cached queries
- ✅ 18+ financial ratios automatically calculated
- ✅ Support for foreign companies (20-F)
- ✅ Cache status visible to users
- ✅ Force refresh option available

### High Priority (After Task 2.4)

- [ ] Complete Phase 2 remaining tasks:
  - [ ] Segment data extraction (Task 2.1)
  - [ ] Expand visualization suite (Task 2.2)
  - [ ] Statement formatter (Task 2.3)
- [ ] Production Railway deployment
- [ ] Supabase authentication setup
- [ ] Comprehensive test suite
- [ ] Performance monitoring

### Medium Priority

- [ ] Historical trend analysis (multi-year)
- [ ] Industry peer comparisons (automated)
- [ ] Export to PDF/Excel
- [ ] Email notifications for completed analyses
- [ ] Cost tracking per user

### Future Considerations

- [ ] Real-time price data integration
- [ ] News sentiment analysis
- [ ] Management compensation analysis
- [ ] Insider trading tracking
- [ ] Custom report templates
- [ ] API endpoints for programmatic access

---

## Known Issues & Limitations

### Data Issues

- **Fiscal Year Mismatches**: Some companies' fiscal years don't align with calendar years
- **Restatements**: Historical data may be restated; system uses latest filings
- **Missing Items**: Not all XBRL tags are present in all companies
- **IFRS vs US-GAAP**: Different accounting standards use different concepts
- **Cache Staleness**: Cached data may be outdated if company files new reports

### Technical Issues

- **Long Running Time**: Full analysis takes 3-5 minutes (API calls + processing)
- **Cost**: ~$0.08 per analysis (OpenAI API usage)
- **Memory**: ChromaDB and SQLite require significant RAM for large databases
- **Rate Limits**: SEC EDGAR and Brave API have rate limits
- **Railway Storage**: 10GB volume limit (may need expansion for large deployments)

### Quality Issues

- **AI Hallucination Risk**: LLM-generated analysis should be verified
- **Calculation Errors**: Complex ratios may have edge cases
- **Context Window**: Very long financial statements may exceed limits
- **Duplicate Handling**: ChromaDB upsert prevents duplicates but may update unnecessarily

### Deployment Issues (Railway-specific)

- **Persistent Storage**: Volume must be properly configured or data is lost on restarts
- **Environment Variables**: Must be set in Railway dashboard, not just .env file
- **Cold Starts**: First request after idle may be slower
- **Port Configuration**: Must use host="0.0.0.0" for Railway to route correctly

---

## Recent Improvements (November 2025)

### Phase 1 Complete: Foundation

**SQLite Financial Cache Implementation:**
- ✅ Intelligent caching of SEC filings (10-K, 10-Q, 20-F, 6-K)
- ✅ 1,425x speedup: 3.5 seconds → 2.5 milliseconds
- ✅ Smart filing detection: latest annual + subsequent quarterlies
- ✅ Support for foreign companies (20-F validated with BHP)
- ✅ Schema includes: filings_metadata, balance_sheet, income_statement, cash_flow, financial_ratios, segment_data

**Direct EdgarTools Integration:**
- ✅ Removed MCP server dependency completely
- ✅ Direct library access via `from edgar import Company`
- ✅ Proper API patterns for edgartools 4.29.0
- ✅ Financial statement extraction using `xbrl.get_statement_by_type()`
- ✅ Handles US-GAAP and IFRS accounting standards

**FinancialDataManager Created:**
- ✅ Unified interface: cache + wrapper + calculator
- ✅ FinancialMetrics dataclass for standardized data
- ✅ CalculatedRatios dataclass with 18+ ratios
- ✅ RatioCalculator with comprehensive calculations
- ⏳ Ready for Gradio integration (Task 2.4)

**Comprehensive Ratio Calculations:**
- ✅ 18+ financial ratios vs 3-5 previously
- ✅ Categories: Profitability, Liquidity, Leverage, Efficiency, Cash Flow
- ✅ Automatic growth rate calculations
- ✅ Balance sheet equation verification

### Phase 1.5 Complete: Visualizations

**Visualization Module:**
- ✅ 4 core chart types implemented
- ✅ Plotly integration with Kaleido for exports
- ✅ Charts display in Financial Analysis tab
- ✅ Auto-generation from analysis data
- ✅ Chart types: margin comparison, key metrics dashboard, cash flow waterfall, revenue trends

### Railway Migration (November 2025)

**Migration from Modal to Railway:**
- ✅ Removed all Modal-specific files
- ✅ Updated pyproject.toml for Railway (Python 3.11+)
- ✅ Enhanced .gitignore for Railway deployment
- ✅ Created comprehensive Railway deployment guide
- ✅ Railway-compatible launch scripts
- ✅ Supabase authentication option for production
- ✅ Cost optimization: $12-17/month Railway vs $20-40/month Modal

**Deployment Improvements:**
- ✅ Persistent storage via Railway volumes
- ✅ Custom domain support (cblanalytics.com ready)
- ✅ Automatic SSL certificate management
- ✅ Professional hosting environment
- ✅ No more async errors from serverless architecture
- ✅ Fast startup (no 18-minute delay)

### RAG Improvements (November 2025)

**Ticker Extraction Enhancement:**
- ✅ edgartools validation prevents false positives
- ✅ "Tesla's key financial risks" no longer extracts "KEY"
- ✅ "Compare Microsoft and Google" no longer extracts "CLOUD"
- ✅ Sustainable validation approach

**Web Search Rate Limiting:**
- ✅ Semaphore limits concurrent Brave API requests
- ✅ Exponential backoff retry for 429 errors
- ✅ Multi-company queries work reliably
- ✅ Enhanced error tracking

**Visualization Suggestions:**
- ✅ RAG synthesis suggests appropriate chart types
- ✅ Trends → Line chart suggestion
- ✅ Comparisons → Bar chart suggestion
- ✅ Composition → Pie chart suggestion

---

## API Keys & Secrets

### Required Keys

```bash
# OpenAI (Required)
OPENAI_API_KEY=sk-proj-...

# Brave Search (Optional but recommended)
BRAVE_API_KEY=BSA...

# SEC EDGAR Identity (Required for edgartools)
SEC_EDGAR_USER_AGENT="Your Name your.email@example.com"
# Or separately:
EDGAR_IDENTITY="Your Name your.email@example.com"

# Supabase (Optional - for Railway production auth)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
```

### Railway Environment Setup

```bash
# In Railway dashboard → Variables:
OPENAI_API_KEY=sk-proj-...
SEC_EDGAR_USER_AGENT=Steve Parton stephen.parton@sjpconsulting.com
BRAVE_API_KEY=BSA...  # Optional
SUPABASE_URL=https://xxx.supabase.co  # For auth
SUPABASE_ANON_KEY=eyJ...  # For auth
```

### Local Development

```bash
# Create .env file in project root
cat > .env << 'EOF'
OPENAI_API_KEY=sk-proj-...
SEC_EDGAR_USER_AGENT=Your Name your.email@example.com
BRAVE_API_KEY=BSA...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
ENABLE_EDGAR_INTEGRATION=true
EOF
```

**⚠️ Never commit API keys to git!**

---

## Cost Management

### Per-Analysis Costs

- **Standard mode:** ~$0.08 (GPT-4.1 + o3-mini)
- **Budget mode:** ~$0.10 (gpt-4o-mini, but lower quality)
- **Cached queries:** Minimal cost (no EDGAR download, faster)

### Railway Hosting Costs

- **Railway Hobby Plan:** $5/month (includes $5 usage credit)
- **Additional compute usage:** ~$5-10/month
- **Storage (10GB volume):** ~$2/month
- **Supabase (optional auth):** Free tier → $25/month for Pro
- **Total estimated:** $12-17/month (testing) → $37-42/month (production with auth)

### Cost Optimization Strategies

- ✅ Use SQLite cache to avoid re-downloading EDGAR data
- ✅ 7-day analysis caching to avoid re-analyzing recent companies
- ✅ Consider batch processing during off-peak hours
- ✅ Use budget mode for exploratory analysis
- ✅ Monitor OpenAI usage dashboard
- ✅ Railway usage tracking in dashboard

### Cost Comparison: Railway vs Modal

**Modal (Previous - Broken):**
- Compute: $20-40/month
- Issues: Async errors, 18+ min startup, ephemeral storage
- Status: Not working reliably

**Railway (Current - Stable):**
- Total: $12-17/month (testing) → $37-42/month (production)
- Benefits: Persistent storage, no async issues, fast startup, custom domain + SSL

---

## Testing & Verification

### Data Verification

Every analysis includes automatic checks:
- ✅ Balance Sheet Equation: Assets = Liabilities + Equity (0.1% tolerance)
- ✅ XBRL Audit Trail: Raw CSV files for manual verification
- ✅ Comparative Period Data: Current vs prior period
- ✅ Cache hit/miss tracking
- ✅ Ratio calculation validation

### Testing Suggestions

**Quick Tests:**
```bash
# Test cache functionality
python test_cache_quick.py

# Test 20-F support
python test_20f_quick.py

# Test speed improvement
python test_speed.py

# Run full analysis
python -m financial_research_agent.main_enhanced
```

**Comprehensive Testing:**
```python
# Test with multiple company types
companies = {
    "AAPL": "US Tech (10-K)",
    "JPM": "US Banking (10-K)", 
    "BHP": "Australian Mining (20-F)",
    "WBKCY": "Australian Banking (20-F)"
}

for ticker, desc in companies.items():
    print(f"\nTesting {desc}...")
    # Run analysis
    # Verify output
    # Check cache status
```

**Cache Testing:**
```python
from financial_research_agent.cache.sec_financial_cache import SecFinancialCache

cache = SecFinancialCache()

# Test 1: Fresh download
print("Test 1: Fresh download")
start = time.time()
cache.cache_all_required_filings("AAPL", force=True)
fresh_time = time.time() - start
print(f"Fresh download: {fresh_time:.2f}s")

# Test 2: Cache hit
print("\nTest 2: Cache hit")
start = time.time()
data = cache.get_cached_financials("AAPL")
cache_time = time.time() - start
print(f"Cache hit: {cache_time:.4f}s")
print(f"Speedup: {fresh_time/cache_time:.0f}x")

# Test 3: Search functionality
print("\nTest 3: Search line items")
results = cache.search_line_items("AAPL", "accounts payable")
print(f"Found {len(results)} matches")
```

---

## Integration Points

### Gradio Web Interface

**Current Implementation:**
- Located in `financial_research_agent/web_app.py`
- Uses `EnhancedFinancialResearchManager` for orchestration
- Three modes: Run New, View Existing, Query Knowledge Base
- Port 7860 by default
- Railway-compatible (host="0.0.0.0")

**Pending Integration (Task 2.4):**
- Wire in `FinancialDataManager` for cached data access
- Display cache status to users
- Show 18+ calculated ratios
- Support force refresh option
- Test with foreign companies

### Railway API

**REST Endpoints (Future):**
- Programmatic access via Railway deployment
- Requires user-provided OpenAI keys for new analyses
- Shared SQLite cache and ChromaDB for all users
- Supabase authentication for access control

### ChromaDB RAG

**Current Implementation:**
- Persistent vector database
- Semantic search over analyses
- Automatic indexing after each analysis
- Query via Python API or web interface
- AI synthesis agent (gpt-4o-mini) for coherent answers
- Web search fallback via Brave API (with rate limiting)
- Ticker extraction uses edgartools Company lookup

**Usage:**
```python
from financial_research_agent.rag.chroma_manager import FinancialRAGManager

rag = FinancialRAGManager(persist_directory="./chroma_db")
results = rag.query("What is Apple's revenue growth?", ticker="AAPL")
```

---

## Compliance & Legal

### Disclaimers Required

**In Any User-Facing Implementation:**
- This is not financial advice
- Not suitable for investment decisions
- Educational/research purposes only
- Consult qualified professionals for financial advice
- No warranties or guarantees
- Data may be stale or incorrect

### Data Attribution

- **SEC EDGAR data:** Public domain (U.S. Government)
- **edgartools:** MIT License (Dwight Gunning)
- **OpenAI Agents SDK:** MIT License (OpenAI)
- **Railway:** Commercial hosting platform

See [ATTRIBUTION.md](ATTRIBUTION.md) for complete licensing information.

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
✅ **Clarify cache behavior and freshness**  
✅ **Explain 10-K vs 20-F differences**  
✅ **Guide Railway deployment questions**

### Avoid

❌ Making financial predictions  
❌ Suggesting this replaces professional analysis  
❌ Recommending specific stocks  
❌ Guaranteeing accuracy of results  
❌ Encouraging production use without proper testing  
❌ Modifying code without understanding implications  
❌ **Changing cache schema without migration plan**  
❌ **Breaking edgartools API patterns**

---

## Quick Reference

### Start Analysis

```bash
# Local web interface
python launch_web_app.py
# Visit http://localhost:7860

# Railway deployment (after setup)
# Automatically starts via Railway start command
# Visit your Railway URL or custom domain
```

### Query ChromaDB

```python
from financial_research_agent.rag.chroma_manager import FinancialRAGManager

rag = FinancialRAGManager(persist_directory="./chroma_db")
results = rag.query("What is AAPL revenue?", ticker="AAPL")
```

### Check Cache Status

```python
from financial_research_agent.cache.sec_financial_cache import SecFinancialCache

cache = SecFinancialCache()
status = cache.check_cache_status("AAPL")
print(f"Cached: {status['cached']}, Current: {status['current']}")
```

### Deploy to Railway

```bash
# 1. Push to GitHub
git push origin main

# 2. Create Railway project from GitHub
# 3. Configure environment variables
# 4. Add persistent volume: /app/financial_research_agent
# 5. Set start command: python launch_web_app_with_auth.py

# See RAILWAY_DEPLOYMENT_GUIDE.md for detailed instructions
```

---

## Support & Documentation

### Key Docs

**Root Level:**
- README.md - Overview and setup
- QUICKSTART.md - Quick start guide
- ARCHITECTURE.md - System architecture
- CLAUDE.md - This file (AI assistant context)
- RAILWAY_DEPLOYMENT_GUIDE.md - Railway deployment
- RAILWAY_MIGRATION_SUMMARY.md - Migration details
- INTEGRATED_IMPLEMENTATION_PLAN.md - Phase 1-3 roadmap

**docs/ Folder:**
- SETUP.md - Detailed installation
- COST_GUIDE.md - Cost breakdown
- EDGAR_INTEGRATION_GUIDE.md - XBRL details
- WEB_APP_GUIDE.md - Web interface usage
- FINANCIAL_METRICS_GUIDE.md - Financial metrics reference
- DEV_WORKFLOW.md - Development workflow
- MASTER_DEV_PLAN.md - Long-term roadmap
- ISSUES_ENHANCEMENTS.md - Known issues

**docs/archive/ Folder:**
- Completed implementation documentation
- Historical reference only - not current guidance

**Legal:**
- ATTRIBUTION.md - Licensing
- LICENSE - MIT License text

### Getting Help

1. Check `error_log.txt` in output directory
2. Review `data_verification.md` for data issues
3. Check Railway logs for deployment issues
4. Consult SEC EDGAR documentation for filing questions
5. Review edgartools docs for API questions
6. Check `test_*.py` files for testing examples
7. For completed features, check docs/archive/

---

## Final Reminders for AI Assistants

1. **This is educational/research software** - always emphasize this
2. **Not for production financial decisions** - make this crystal clear
3. **Verify calculations** - encourage checking against official data
4. **Test changes** - especially financial calculations and cache behavior
5. **Respect licenses** - maintain proper attribution
6. **Cost awareness** - remind users of API and hosting costs
7. **Data limitations** - be honest about cache staleness and data quality
8. **Security** - protect API keys, don't expose user data
9. **Railway deployment** - reference RAILWAY_DEPLOYMENT_GUIDE.md
10. **Cache behavior** - explain when data is cached vs fresh

---

## Next Immediate Task: Task 2.4 (2-3 hours)

**Wire FinancialDataManager into Gradio web_app.py:**

**Files to Modify:**
- `financial_research_agent/web_app.py`

**Changes Needed:**
1. Import FinancialDataManager
2. Replace current data fetching with manager calls
3. Add cache status display
4. Test with cached vs fresh data
5. Validate 18+ ratios display
6. Test foreign company support

**Success Criteria:**
- ✅ Cache hit shows 1,425x speedup
- ✅ 18+ financial ratios calculated
- ✅ Foreign companies (20-F) work
- ✅ Cache status visible to users
- ✅ Force refresh option available
- ✅ All existing functionality preserved

**After Task 2.4:**
- Complete remaining Phase 2 tasks (2.1, 2.2, 2.3)
- Deploy to Railway production
- Set up Supabase authentication
- Configure custom domain (cblanalytics.com)

---

**Remember: We're building a research tool to learn about financial data extraction and AI agents, not a production financial advisory system. The Railway deployment provides a stable, professional hosting environment for ongoing development and testing.**
