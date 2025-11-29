# AI Financial Analysis Knowledge Base - Project Context

**Last Updated:** November 28, 2025

---

## 🎯 Project Overview

This is an AI-powered financial analysis application that extracts and analyzes SEC EDGAR filings to provide professional-grade financial research reports. The system combines direct edgartools library integration with LLM-powered analysis agents to produce comprehensive multi-page reports with financial statements, ratios, risk analysis, and visualizations.

**Primary Purpose:** Demonstrate sophisticated financial analysis capabilities as a portfolio piece for SJP Consulting's AI/ML services.

**Current Status:** Phase 1 complete (foundation), Phase 2 40% complete (enhancements), deployed to Railway.app

---

## 🚀 Current Implementation Status

### Phase 1: COMPLETE ✅ (Week 1 - Foundation)

**SQLite Financial Cache** - Implemented at `financial_research_agent/cache/sec_financial_cache.py`
- **Performance:** 1,425x speedup (3.5 seconds → 2.5 milliseconds on cache hits)
- **Coverage:** 10-K, 10-Q, 20-F, 6-K filings (US and foreign companies)
- **Validation:** Tested with BHP (Australian mining, 20-F) and WBKCY (Australian banking, 20-F)
- **Status:** Built but NOT yet integrated into main application (Task 2.4)

**Direct EdgarTools Integration** - Removed MCP server dependency (November 2025)
- Direct library calls to edgartools for XBRL data extraction
- 66% code reduction vs MCP wrapper approach
- 18+ comprehensive financial ratios vs 3-5 previously

**FinancialDataManager** - Created at `financial_research_agent/financial_data_manager.py`
- `FinancialMetrics` dataclass - Structured financial data
- `CalculatedRatios` dataclass - 18+ ratios across 5 categories:
  - Profitability: margins, ROA, ROE, asset turnover
  - Liquidity: current ratio, cash ratio, working capital
  - Leverage: debt-to-assets, debt-to-equity, equity ratio
  - Efficiency: asset turnover, equity turnover
  - Cash Flow: OCF ratios, free cash flow
- `RatioCalculator` - Automated ratio computation

**Enhanced EdgarTools Wrapper** - At `financial_research_agent/tools/edgartools_wrapper.py`
- `get_complete_financials()` - Multi-period financial data extraction
- `search_line_items()` - Semantic search across statements
- `get_segment_data()` - Geographic and product segment breakdowns

### Phase 1.5: COMPLETE ✅ (Visualizations)

**Visualization Module** - At `financial_research_agent/visualization/`
- 4 chart types implemented:
  1. Margin comparison (gross/operating/net)
  2. Key metrics dashboard (revenue, FCF, margins)
  3. Cash flow waterfall
  4. Revenue trends over time
- **Technology:** Plotly + Kaleido for interactive charts
- **Integration:** Charts display in Financial Analysis tab (Tab 5)
- **Files:** `charts.py`, `utils.py`

### Phase 2: 40% COMPLETE 🔄 (Week 2 - Enhancements)

**Already Done:**
- ✅ Visualization module structure exists
- ✅ 4 core chart types working
- ✅ Charts integrated into Gradio UI

**Still To Do** (from `INTEGRATED_IMPLEMENTATION_PLAN.md`):
- **Task 2.1:** Segment Data Extraction (6 hours) - Geographic + product segments from XBRL
- **Task 2.2:** Expand Visualization Suite (4 hours) - Segment charts, add to existing
- **Task 2.3:** Statement Formatter (4 hours) - Professional HTML export
- **Task 2.4:** Gradio UI Integration (6 hours) ⭐ **HIGHEST PRIORITY NEXT STEP**
  - Wire `FinancialDataManager` into `web_app.py`
  - Users immediately get 1,425x faster cached data + 18+ ratios
  - **Estimated:** 2-3 hours implementation time
  - **Impact:** Massive - unlocks all Phase 1 infrastructure

### Phase 3: PENDING ⏳ (Week 3 - Polish & Production)

- Production Railway deployment with custom domain
- Comprehensive configuration and secrets management
- Complete documentation suite
- Full testing suite (unit + integration)

---

## 🏗️ Architecture Overview

### Current Pipeline Flow

```
1. User Input → Planner Agent → Search Agent (Brave API)
2. SQLite Cache Check (2.5ms hit vs 3.5s download)
3. EdgarTools Direct Access (10-K, 10-Q, 20-F, 8-K filings)
4. FinancialDataManager (when integrated - Task 2.4):
   ├─ SecFinancialCache → SQLite caching layer
   ├─ EdgarToolsWrapper → Direct XBRL extraction
   └─ RatioCalculator → 18+ comprehensive ratios
5. Specialist Agents:
   ├─ Financial Statements (118+ XBRL items)
   ├─ Financial Metrics (profitability, liquidity, leverage, efficiency, cash flow)
   ├─ Financials Analysis (800-1200 words)
   └─ Risk Analysis (800-1200 words)
6. Writer Agent → Comprehensive report (1500-2500 words)
7. Verification Agent → Quality checks
8. ChromaDB RAG → Indexing for future retrieval
```

### Key Technical Components

**SQLite Cache Schema:**
- `filings_metadata` - Filing information (ticker, CIK, form type, dates)
- `balance_sheet` - Balance sheet line items
- `income_statement` - Income statement line items
- `cash_flow` - Cash flow statement line items
- `financial_ratios` - Pre-calculated ratios
- `segment_data` - Geographic and product segments

**Direct EdgarTools 4.29.0 API Patterns:**
```python
from edgar import Company, set_identity
import os

# CRITICAL: Set EDGAR identity (required by SEC)
os.environ['EDGAR_IDENTITY'] = "Your Name your.email@example.com"
set_identity(os.environ['EDGAR_IDENTITY'])

# Get company and filings
company = Company(ticker)
filings = company.get_filings(form=["10-K", "10-Q", "20-F"])
filing = filings[0]

# Extract XBRL data
xbrl = filing.xbrl()
balance_sheet = xbrl.get_statement_by_type('balance-sheet')
income_stmt = xbrl.get_statement_by_type('income-statement')
cash_flow = xbrl.get_statement_by_type('cash-flow')

# Access line items from 'data' key
for item in balance_sheet['data']:
    concept = item['concept']
    label = item['label']
    value = item.get('value', 0)
```

**ChromaDB Collections:**
- `financial_analyses` - Semantic search across analyses
- `sec_filings_cache` - Raw filing content cache

**Visualization System:**
- Location: `financial_research_agent/visualization/`
- Charts: `charts.py` - 4 chart types using Plotly
- Utilities: `utils.py` - Data preparation and formatting

---

## 🚂 Railway Migration (November 2025)

**Migration Complete:** Modal → Railway.app

**Why Railway?**
- Modal had persistent serverless issues (Gradio async task management broken)
- Railway provides persistent storage, no async errors, fast startup
- Custom domain + SSL support included

**Files Removed:**
- `modal_app.py`, `modal_app_with_auth.py`, `modal_fastapi_bridge.py`, `.env.modal`

**Files Added:**
- `RAILWAY_DEPLOYMENT_GUIDE.md` - Deployment instructions
- `RAILWAY_MIGRATION_SUMMARY.md` - Migration details and cost comparison

**Cost Comparison:**
- **Modal (previous, broken):** $20-40/month, 18+ min startup, ephemeral storage, async errors
- **Railway (current, stable):** $12-17/month (testing) → $37-42/month (production with Supabase auth)
  - Railway Hobby Plan: $5/month (includes $5 usage credit)
  - Additional compute: ~$5-10/month
  - Storage (10GB volume): ~$2/month
  - Supabase auth (optional): Free tier → $25/month Pro

**Benefits:**
- ✅ Persistent storage via volumes
- ✅ No async task management errors
- ✅ Fast startup (< 1 minute)
- ✅ Custom domain support (cblanalytics.com ready)
- ✅ Automatic SSL certificates

---

## 📁 File Structure

### Core Application Files

```
financial_research_agent/
├── cache/                           # SQLite cache system (Phase 1)
│   ├── sec_financial_cache.py      # Main cache implementation
│   ├── cached_manager.py            # Cache-aware data manager
│   ├── schema.sql                   # Database schema
│   └── data_cache.py                # Simple JSON file cache (currently used)
│
├── financial_data_manager.py       # Unified manager (NOT YET INTEGRATED - Task 2.4)
├── manager_enhanced.py              # Current orchestrator (uses JSON cache)
├── web_app.py                       # Gradio interface (NEEDS Task 2.4 integration)
│
├── tools/                           # Data extraction tools
│   ├── edgartools_wrapper.py       # Enhanced XBRL extraction
│   └── financial_ratios_calculator.py  # 18+ ratio calculations
│
├── agent_definitions/               # All specialist agents
│   ├── planner_agent.py
│   ├── search_agent.py
│   ├── edgar_agent.py
│   ├── financial_metrics_agent.py
│   ├── financials_agent_enhanced.py
│   ├── risk_agent_enhanced.py
│   ├── writer_agent_enhanced.py
│   └── verifier_agent.py
│
├── visualization/                   # Visualization module (Phase 1.5)
│   ├── charts.py                    # 4 chart types (Plotly)
│   ├── utils.py                     # Chart utilities
│   └── __init__.py
│
└── rag/                             # ChromaDB integration
    ├── chroma_manager.py
    ├── synthesis_agent.py
    └── utils.py
```

### Deployment Files

```
launch_web_app.py                    # Gradio launcher (Railway compatible)
launch_web_app_with_auth.py          # With Supabase authentication
pyproject.toml                       # Python 3.11+ dependencies
RAILWAY_DEPLOYMENT_GUIDE.md          # Railway deployment instructions
RAILWAY_MIGRATION_SUMMARY.md         # Migration details
```

### Documentation

```
README.md                            # Project overview
QUICKSTART.md                        # Quick start guide
ARCHITECTURE.md                      # System architecture
INTEGRATED_IMPLEMENTATION_PLAN.md    # Phase 2 & 3 tasks
CACHE_BUG_FIX.md                     # JSON cache bug documentation

docs/
├── SETUP.md                         # Development setup
├── COST_GUIDE.md                    # Cost analysis
├── EDGAR_INTEGRATION_GUIDE.md       # EdgarTools integration
├── WEB_APP_GUIDE.md                 # Web interface guide
├── FINANCIAL_METRICS_GUIDE.md       # Metrics reference
├── DEV_WORKFLOW.md                  # Development workflow
├── MASTER_DEV_PLAN.md               # Original implementation plan
└── ISSUES_ENHANCEMENTS.md           # Known issues

docs/archive/                        # Completed implementation docs (historical reference only)
```

### Output Structure

```
financial_research_agent/output/YYYYMMDD_HHMMSS/
├── 00_query.md                      # Original query
├── 01_search_plan.md                # Search strategy
├── 02_search_results.md             # Web search results
├── 02_edgar_filings.md              # SEC filing analysis
├── 03_financial_statements.md       # Balance sheet, income, cash flow
├── 04_financial_metrics.md          # 18+ ratios and YoY tables
├── 05_financial_analysis.md         # Comprehensive financial analysis
├── 06_risk_analysis.md              # Risk assessment
├── 07_comprehensive_report.md       # Final synthesized report
├── 08_verification.md               # Quality checks
├── 09_cost_report.md                # Cost breakdown
├── metadata.json                    # Company metadata
├── chart_*.json                     # Visualization data
└── xbrl_raw_*.csv                   # Audit trail (raw XBRL data)
```

---

## 🔧 EdgarTools API Patterns (CRITICAL)

**Correct Usage for edgartools 4.29.0:**

```python
# 1. Proper EDGAR identity configuration (REQUIRED)
import os
from edgar import set_identity

os.environ['EDGAR_IDENTITY'] = "Your Name your.email@example.com"
set_identity(os.environ['EDGAR_IDENTITY'])

# Alternative environment variable name (both work)
os.environ['SEC_EDGAR_USER_AGENT'] = "Your Name your.email@example.com"

# 2. Get company and filings
from edgar import Company

company = Company(ticker)
filings = company.get_filings(form=["10-K", "10-Q"])  # US companies
# OR
filings = company.get_filings(form=["20-F", "6-K"])   # Foreign companies

# 3. Extract statements (returns dictionary with 'data' key)
filing = filings[0]
xbrl = filing.xbrl()

balance_sheet = xbrl.get_statement_by_type('balance-sheet')
income_stmt = xbrl.get_statement_by_type('income-statement')
cash_flow = xbrl.get_statement_by_type('cash-flow')

# 4. Access line items from 'data' key
for item in balance_sheet['data']:
    concept = item['concept']          # XBRL concept name
    label = item['label']              # Human-readable label
    value = item.get('value', 0)       # Numerical value
    is_abstract = item.get('is_abstract', False)  # Skip headers
```

**Common Mistakes to Avoid:**

❌ Using `Company(ticker).financials` (wrong method)  
❌ Forgetting EDGAR identity configuration  
❌ Not handling missing 'data' keys  
❌ Assuming all concepts present in all filings  
❌ Using reserved SQL keywords as column names  

---

## 🐛 Known Issues and Limitations

### Current Issues (November 2025)

**CRITICAL - Cache Bug:**
- **Location:** `financial_research_agent/manager_enhanced.py` lines 580-718
- **Problem:** When financial statements are loaded from JSON cache (2nd run), they're missing `yoy_tables` and `key_metrics` computed fields
- **Impact:** Second run of analysis produces incomplete financial statements
- **Root Cause:** YoY generation is inside `if not cached_statements` block, so cached data never gets these fields added
- **Fix:** See `CACHE_BUG_FIX.md` for detailed fix instructions
- **Status:** Documented, awaiting manual fix before Railway deployment

### Data Issues

**Fiscal Year Mismatches:**
- Some companies don't align fiscal years with calendar years
- Example: Apple's fiscal year ends in September

**Restatements:**
- Historical data may be restated in newer filings
- System uses latest filings, which may differ from originally reported values

**Missing Items:**
- Not all XBRL tags present in all companies
- Some smaller companies have incomplete XBRL tagging

**IFRS vs US-GAAP:**
- Foreign companies (20-F) use IFRS accounting standards
- Different concept names and structures vs US-GAAP
- Example: "Shareholders' Equity" vs "Stockholders' Equity"

**Cache Staleness:**
- Cached data may be outdated if company files new reports
- Default TTL: 7 days (configurable via `max_age_days`)

### Technical Issues

**Long Running Time:**
- Full analysis: 3-5 minutes (API calls + processing)
- Breakdown: Web search (30s), EDGAR extraction (60-90s), LLM analysis (90-120s)

**Cost:**
- ~$0.08 per analysis (OpenAI API usage)
- Standard mode: GPT-4.1 + o3-mini
- Budget mode: gpt-4o-mini (lower quality, ~$0.10)

**Memory:**
- ChromaDB and SQLite require significant RAM
- Recommended: 4GB+ for production deployment

**Rate Limits:**
- SEC EDGAR: 10 requests/second maximum
- Brave Search API: Rate limited by plan

**Railway Storage:**
- 10GB volume limit (may need expansion for large datasets)
- Persistent volumes required or data lost on restarts

### Railway-Specific Deployment Issues

**Persistent Storage:**
- Volume must be properly configured at `/app/financial_research_agent`
- Data lost on restarts if volume not mounted

**Environment Variables:**
- Must be set in Railway dashboard, not just `.env` file
- Required: `OPENAI_API_KEY`, `SEC_EDGAR_USER_AGENT`, `BRAVE_API_KEY` (optional)

**Cold Starts:**
- First request after idle period may be slower (< 1 minute)
- Subsequent requests are fast

**Port Configuration:**
- Must use `host="0.0.0.0"` for Railway routing
- Default Gradio port 7860 works fine

---

## 📊 Recent Improvements (November 2025)

### RAG Improvements

**Ticker Extraction Validation:**
- Added edgartools validation to prevent false positives
- Example: "Tesla's key financial risks" no longer extracts "KEY" as ticker

**Web Search Rate Limiting:**
- Semaphore limits concurrent Brave API requests
- Exponential backoff for 429 (rate limit) errors
- Prevents API quota exhaustion

**Visualization Suggestions:**
- RAG synthesis agent suggests appropriate chart types
- Trends → line chart, comparisons → bar chart
- Context-aware chart recommendations

### Visualization System (Phase 1.5)

**4 Chart Types:**
1. Margin comparison (gross/operating/net margins)
2. Key metrics dashboard (revenue, FCF, margins)
3. Cash flow waterfall (operating, investing, financing)
4. Revenue trends over time

**Technology Stack:**
- Plotly for interactive charts
- Kaleido for static PNG export
- Auto-generation from analysis data

**Integration:**
- Charts display in Financial Analysis tab (Tab 5 in Gradio)
- JSON data saved for reproducibility
- PNG exports for reports

### Railway Migration

**All Modal Dependencies Removed:**
- Eliminated serverless platform issues
- Fixed Gradio async task management errors
- Removed 18+ minute cold start times

**Railway Configuration:**
- Persistent storage via volumes (10GB)
- Environment variables in dashboard
- Custom domain ready (cblanalytics.com)
- Automatic SSL certificate management

**Cost Optimization:**
- $12-17/month testing (vs $20-40/month Modal broken)
- $37-42/month production with Supabase auth
- Predictable pricing, no surprise serverless charges

---

## 🎯 Task 2.4: FinancialDataManager Integration (NEXT PRIORITY)

**Current Situation:**
- ✅ `FinancialDataManager` exists at `financial_research_agent/financial_data_manager.py`
- ✅ SQLite cache fully implemented and tested
- ✅ 18+ ratios pre-calculated and ready
- ❌ NOT integrated into `web_app.py` (still using JSON file cache)
- ❌ Users NOT benefiting from 1,425x speedup
- ❌ JSON cache bug causing missing YoY tables on 2nd run

**Goal:**
Wire `FinancialDataManager` into Gradio `web_app.py` so users get:
- 1,425x faster cached data (2.5ms vs 3.5s)
- 18+ comprehensive financial ratios automatically
- Support for foreign companies (20-F filings)
- Cache status visibility
- Force refresh option

**Estimated Time:** 2-3 hours

### Implementation Steps

**1. Import FinancialDataManager**
```python
from financial_research_agent.financial_data_manager import FinancialDataManager
```

**2. Initialize in WebApp class**
```python
class WebApp:
    def __init__(self):
        self.data_manager = FinancialDataManager()
        # ... rest of init
```

**3. Replace data fetching in generate_analysis()**
```python
async def generate_analysis(self, ticker, force_refresh=False):
    # Get cached or fresh data
    financial_data = await self.data_manager.get_financial_data(
        ticker=ticker,
        force_refresh=force_refresh
    )
    
    # Display cache status to user
    cache_status = financial_data['cache_status']
    if cache_status.get('current'):
        message = f"✅ Using cached data (age: {cache_status['cache_age_days']} days)"
    else:
        message = "⬇️ Downloading fresh SEC data..."
    
    # Use financial_data['sec_data'], financial_data['ratios'], financial_data['growth']
    # ... rest of analysis pipeline
```

**4. Add force refresh UI option**
```python
with gr.Row():
    refresh_checkbox = gr.Checkbox(label="Force refresh (ignore cache)", value=False)

# Pass to generate_analysis()
results = generate_analysis(ticker, force_refresh=refresh_checkbox)
```

### Success Criteria

- ✅ Cache hit shows 1,425x speedup
- ✅ 18+ financial ratios calculated automatically
- ✅ Foreign companies (20-F) work correctly
- ✅ Cache status visible to users
- ✅ Force refresh option available
- ✅ All existing functionality preserved

### Testing Plan

**Test Companies:**
- AAPL - US Tech (10-K)
- JPM - US Banking (10-K)
- BHP - Australian Mining (20-F)
- WBKCY - Australian Banking (20-F)

**Test Scenarios:**
1. Fresh analysis (cache miss) → Verify data extracted and cached
2. Repeat analysis (cache hit) → Verify 1,425x speedup + all data present
3. Foreign company (BHP) → Verify 20-F support works
4. Force refresh → Verify cache bypassed and data re-fetched

---

## 🧪 Testing Strategy

### Quick Tests

```bash
# Test SQLite cache
python test_cache_quick.py

# Test 20-F support
python test_20f_quick.py

# Test performance
python test_speed.py

# Full analysis
python -m financial_research_agent.main_enhanced
```

### Comprehensive Testing

**Test Companies:**
- AAPL (US Tech 10-K)
- JPM (US Banking 10-K)
- BHP (Australian Mining 20-F)
- WBKCY (Australian Banking 20-F)

**Cache Testing:**
```python
from financial_research_agent.cache.sec_financial_cache import SecFinancialCache

cache = SecFinancialCache()

# Test 1: Fresh download
import time
start = time.time()
cache.cache_company("AAPL", max_filings=4)
fresh_time = time.time() - start
print(f"Fresh download: {fresh_time:.2f}s")

# Test 2: Cache hit
start = time.time()
cached_data = cache.get_cached_financials("AAPL", periods=4)
cache_time = time.time() - start
print(f"Cache hit: {cache_time:.4f}s")
print(f"Speedup: {fresh_time/cache_time:.0f}x")

# Test 3: Search line items
results = cache.search_line_items("AAPL", "accounts payable")
print(f"Found {len(results)} matching items")
```

**Balance Sheet Verification:**
```python
# Verify accounting equation: Assets = Liabilities + Equity
def verify_balance_sheet(ticker):
    cache = SecFinancialCache()
    data = cache.get_cached_financials(ticker, periods=1)
    
    bs = data['periods'][0]['balance_sheet']
    
    # Extract values (simplified)
    assets = next((item['value'] for item in bs if 'Assets' in item['label']), 0)
    liabilities = next((item['value'] for item in bs if 'Liabilities' in item['label']), 0)
    equity = next((item['value'] for item in bs if 'Equity' in item['label']), 0)
    
    difference = abs(assets - (liabilities + equity))
    tolerance = assets * 0.001  # 0.1% tolerance
    
    if difference <= tolerance:
        print(f"✅ Balance sheet equation verified for {ticker}")
        print(f"   Difference: {difference:,.0f} ({difference/assets*100:.3f}%)")
    else:
        print(f"❌ Balance sheet equation FAILED for {ticker}")
        print(f"   Assets: {assets:,.0f}")
        print(f"   Liabilities + Equity: {liabilities + equity:,.0f}")
        print(f"   Difference: {difference:,.0f} ({difference/assets*100:.2f}%)")

verify_balance_sheet("AAPL")
```

---

## ⚙️ Environment Configuration

### Required Environment Variables

```bash
# OpenAI API (required)
OPENAI_API_KEY=sk-proj-...

# SEC EDGAR identity (required - choose one)
SEC_EDGAR_USER_AGENT="Your Name your.email@example.com"
# OR
EDGAR_IDENTITY="Your Name your.email@example.com"

# Brave Search API (optional but recommended)
BRAVE_API_KEY=BSA...

# Supabase (optional - for Railway production auth)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...

# Enable EDGAR integration
ENABLE_EDGAR_INTEGRATION=true
```

### Railway Environment Setup

**In Railway Dashboard → Variables:**
1. Add all required environment variables
2. Configure persistent volume:
   - Mount path: `/app/financial_research_agent`
   - Size: 10GB (recommended)
3. Set start command: `python launch_web_app_with_auth.py`

### Local Development Setup

```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-proj-...
SEC_EDGAR_USER_AGENT="Your Name your.email@example.com"
BRAVE_API_KEY=BSA...
ENABLE_EDGAR_INTEGRATION=true
EOF

# Install dependencies
pip install -r requirements.txt
# OR using UV (modern)
uv sync

# Run locally
python launch_web_app.py
```

---

## 💰 Cost Analysis

### Per-Analysis Costs

**Standard Mode (Recommended):**
- ~$0.08 per analysis
- Models: GPT-4.1 + o3-mini
- Quality: High

**Budget Mode:**
- ~$0.10 per analysis
- Models: gpt-4o-mini
- Quality: Lower (not recommended for production)

### Railway Hosting Costs

**Testing/Development:**
- Railway Hobby Plan: $5/month (includes $5 usage credit)
- Additional compute: ~$5-10/month
- Storage (10GB volume): ~$2/month
- **Total: $12-17/month**

**Production (with Supabase Auth):**
- Railway: $12-17/month (base)
- Supabase Pro: $25/month
- **Total: $37-42/month**

### Cost Comparison

| Platform | Monthly Cost | Startup Time | Storage | Status |
|----------|-------------|--------------|---------|--------|
| Modal (previous) | $20-40 | 18+ min | Ephemeral | ❌ Broken |
| Railway (current) | $12-17 (testing)<br>$37-42 (production) | < 1 min | Persistent | ✅ Stable |

**Cost Savings:**
- Testing: ~40% cheaper than Modal
- Production: Comparable with better reliability
- Predictable pricing (no serverless surprises)

---

## 🚀 Development Priorities

### Current Priority: Task 2.4 (2-3 hours)

**Goal:** Wire `FinancialDataManager` into Gradio `web_app.py`

**Deliverables:**
- ✅ Cache status display to users
- ✅ 18+ calculated ratios visible
- ✅ Force refresh option
- ✅ Foreign company support (20-F)
- ✅ 1,425x speedup on cache hits

### High Priority (After Task 2.4)

1. **Complete Phase 2 Remaining Tasks**
   - Task 2.1: Segment data extraction
   - Task 2.2: Expand visualization suite
   - Task 2.3: Statement formatter

2. **Production Railway Deployment**
   - Configure custom domain (cblanalytics.com)
   - Set up Supabase authentication
   - Comprehensive testing suite

3. **Performance Monitoring**
   - Add logging and metrics
   - Track cache hit rates
   - Monitor API costs

### Medium Priority

1. **Historical Trend Analysis**
   - Multi-year financial comparisons
   - Trend identification and analysis

2. **Industry Peer Comparisons**
   - Automated peer group identification
   - Comparative financial analysis

3. **Export Capabilities**
   - PDF report generation
   - Excel spreadsheet export

4. **Email Notifications**
   - Analysis completion alerts
   - Scheduled report delivery

5. **Cost Tracking**
   - Per-user cost tracking
   - Monthly cost reports

### Future Considerations

1. **Real-time Price Data**
   - Stock price integration
   - Market cap calculations

2. **News Sentiment Analysis**
   - Recent news aggregation
   - Sentiment scoring

3. **Management Compensation**
   - Executive compensation analysis
   - Pay ratio calculations

4. **Insider Trading Tracking**
   - Insider transaction monitoring
   - Form 4 analysis

5. **Custom Report Templates**
   - User-defined report formats
   - Industry-specific templates

6. **API Endpoints**
   - Programmatic access
   - Webhook integrations

---

## ⚖️ Compliance and Legal

### Required Disclaimers

**Every Report Must Include:**
- Not financial advice
- Not suitable for investment decisions
- Educational/research purposes only
- Consult qualified professionals
- No warranties or guarantees
- Data may be stale or incorrect

### Data Attribution

**SEC EDGAR Data:**
- Source: Public domain (U.S. Government)
- Access via: edgartools library

**edgartools Library:**
- License: MIT License
- Author: Dwight Gunning
- Citation: https://github.com/dgunning/edgartools

**OpenAI Agents SDK:**
- License: MIT License
- Provider: OpenAI

**Railway Platform:**
- Type: Commercial hosting platform
- Terms: https://railway.app/legal/terms

### Investment Advisor Compliance

**Important Notes:**
- This tool does NOT provide investment advice
- Not registered with SEC or regulatory bodies
- Users must comply with local securities regulations
- Professional use may require proper licensing

**For Professional Use:**
- Consult with compliance officer
- Ensure proper registrations
- Add appropriate disclaimers
- Implement audit trails

---

## 📞 Next Actions

### Today (2-3 hours)

1. **Fix JSON Cache Bug** (see `CACHE_BUG_FIX.md`)
   - Apply fix to `manager_enhanced.py` lines 580-718
   - Test with META twice (fresh + cached)
   - Verify YoY tables present in both runs

2. **Test Railway Deployment**
   - Verify cache bug is fixed
   - Test with multiple companies
   - Confirm all features working

3. **Begin Task 2.4**
   - Wire `FinancialDataManager` into `web_app.py`
   - Add cache status display
   - Test with AAPL, BHP

### This Week

1. **Complete Task 2.4**
   - Full integration testing
   - Document changes
   - Update user guide

2. **Complete Remaining Phase 2 Tasks**
   - Tasks 2.1, 2.2, 2.3
   - Comprehensive testing
   - Documentation updates

### Next Week

1. **Production Deployment**
   - Deploy to Railway with custom domain
   - Configure Supabase authentication
   - Monitor production usage

2. **Performance Optimization**
   - Profile slow operations
   - Optimize database queries
   - Cache tuning

---

## 📚 Additional Resources

### Documentation

- **Project Root:** `/Users/stephenparton/projects/financial_analysis/`
- **Main Docs:** `README.md`, `ARCHITECTURE.md`, `QUICKSTART.md`
- **Implementation Plan:** `INTEGRATED_IMPLEMENTATION_PLAN.md`
- **Railway Guide:** `RAILWAY_DEPLOYMENT_GUIDE.md`
- **Bug Fix:** `CACHE_BUG_FIX.md`

### External References

- **EdgarTools:** https://github.com/dgunning/edgartools
- **SEC EDGAR:** https://www.sec.gov/edgar
- **Railway Docs:** https://docs.railway.app
- **Gradio Docs:** https://gradio.app/docs
- **ChromaDB Docs:** https://docs.trychroma.com

### Contact & Support

- **Developer:** Stephen Parton
- **Company:** SJP Consulting
- **Email:** stephen.parton@sjpconsulting.com
- **Location:** Brisbane, Australia

---

**End of CLAUDE.md**
