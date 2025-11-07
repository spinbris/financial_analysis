# Financial Research Agent

A comprehensive AI-powered financial research system that produces investment-grade reports with SEC EDGAR integration. 

At this stage though it is very much still in development stage and is still incomplete, and in any case is being used to investigate the technologies used rather than to develop an operational tool! So please do not use for anything serious!

**Based on:** [OpenAI Agents SDK Financial Research Example](https://github.com/openai/openai-agents-python/tree/main/examples/financial_research_agent)

## Features

- **Comprehensive Analysis**: 3-5 page reports with 800-1200 word specialist analysis
- **Complete Financial Statements**: 118+ line items with comparative periods via deterministic [edgartools](https://github.com/dgunning/edgartools) extraction
  - Balance Sheet: 36+ line items (current & prior period)
  - Income Statement: 46+ line items with product/geographic breakdowns
  - Cash Flow: 36+ line items with all activities
  - **8.6x more data** than MCP tool approach
- **SEC EDGAR Integration**: Direct access to official SEC filings (10-K, 10-Q, 8-K) with exact XBRL precision
- **Specialist Agents**: Dedicated financial and risk analysts with EDGAR access
  - Risk analysis prioritizes 10-K annual filings (Item 1A Risk Factors) for comprehensive risk assessment
  - Financial metrics agent extracts 118+ line items with full comparative period data
- **Web Interface**: Gradio-based UI with ability to run new analyses or view existing reports
- **Budget Mode**: Cost-optimized configuration still available
- **Investment Grade**: Suitable for institutional investors and decision-makers
- **RAG Integration**: ChromaDB vector database for analysis indexing and retrieval with automatic duplicate handling

## Table of Contents

- [Quick Start](#quick-start)
- [Web Interface](#web-interface)
- [Modal Deployment (Optional)](#modal-deployment-optional)
- [Output Structure](#output)
- [Recent Improvements](#recent-improvements)
- [Documentation](#documentation)

## Quick Start

### Web Interface (Recommended)
```bash
python launch_web_app.py
```
- **Interactive Gradio UI** at http://localhost:7860
- **Run new analyses** or **view existing reports**
- Select from up to 50 most recent analyses
- Switch between modes with radio button
- All reports displayed in organized tabs

### Command Line
```bash
python -m financial_research_agent.main_enhanced
```
- **Time:** 3-5 minutes (first run), 2-3 minutes (cached)
- **Cost:** ~$0.08 per report
- **Reports per $20:** ~250 comprehensive reports
- Uses GPT-5-nano for planning/search, GPT-5 for analysis
- **70% faster and 47% cheaper than original!**

### Budget Mode
```bash
python -m financial_research_agent.main_budget
```
- **Time:** 8-10 minutes
- **Cost:** ~$0.10 per report (lower quality)
- **Reports per $20:** ~200 reports
- Uses gpt-4o-mini for all tasks (quality trade-off)

## Example Query

```
Analyze Apple's most recent quarterly performance
```

**Output includes:**
- Executive summary
- Comprehensive financial analysis (exact XBRL data from 10-Q)
- Risk assessment (prioritizes official Item 1A Risk Factors from 10-K annual filings)
- Complete financial statements with comparative periods
- Calculated financial ratios (liquidity, solvency, profitability, efficiency)
- Data verification report
- Strategic position analysis
- Follow-up questions

## Architecture

1. **Planning**: Planner agent creates 5-15 targeted searches
2. **Search**: Parallel web searches for market context
3. **EDGAR**: Direct SEC filing access for authoritative data
4. **Specialist Analysis**:
   - Financial Statements Agent: Extracts 118+ line items from XBRL with comparative periods
   - Financial Metrics Agent: Calculates comprehensive financial ratios
   - Financials Agent: 800-1200 word analysis with EDGAR data
   - Risk Agent: 800-1200 word assessment prioritizing 10-K Item 1A Risk Factors
5. **Writer**: Synthesizes into 1500-2500 word comprehensive report
6. **Verification**: Quality audit with balance sheet equation validation
7. **RAG Indexing**: Automatic ChromaDB indexing for future retrieval (with duplicate handling)

## Documentation

- **[QUICK_START_BUDGET.md](QUICK_START_BUDGET.md)** - Get started in 30 seconds
- **[SETUP.md](SETUP.md)** - Complete setup guide
- **[COST_GUIDE.md](COST_GUIDE.md)** - Cost breakdown and optimization
- **[EDGAR_INTEGRATION_GUIDE.md](EDGAR_INTEGRATION_GUIDE.md)** - EDGAR integration details
- **[ATTRIBUTION.md](ATTRIBUTION.md)** - Licensing and attribution

## Attribution & License

### This Project
**License:** MIT License
**Copyright:** 2025 Stephen Parton
See [LICENSE](LICENSE) for full license text.

As stated more fully in the license file: THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED

### Dependencies

**Based on OpenAI Agents SDK Example**
- Source: https://github.com/openai/openai-agents-python/tree/main/examples/financial_research_agent
- License: MIT (Copyright OpenAI)

**Financial Data Extraction: edgartools**
- Author: Dwight Gunning
- Source: https://github.com/dgunning/edgartools
- License: MIT

**SEC EDGAR MCP Server** (for EDGAR agent)
- Author: Stefano Amorelli
- Source: https://github.com/stefanoamorelli/sec-edgar-mcp
- License: AGPL-3.0
- Citation: Amorelli, S. (2025). SEC EDGAR MCP Server. https://doi.org/10.5281/zenodo.17123166

See [ATTRIBUTION.md](financial_research_agent/docs/ATTRIBUTION.md) for complete licensing information.

## Web Interface

The Gradio web interface provides three modes of operation:

### Run New Analysis
1. Enter your financial research query (e.g., "Analyze Apple's Q3 2024 performance")
2. Click "Run Analysis"
3. Watch real-time progress in organized tabs
4. View comprehensive report when complete

### View Existing Analysis
1. Switch to "View Existing Analysis" mode
2. Select from dropdown of up to 50 most recent analyses (sorted by timestamp)
3. Click "Load Selected Analysis"
4. Browse all reports in organized tabs:
   - Comprehensive Report
   - Financial Statements
   - Financial Metrics & Ratios
   - Data Verification

### Query Knowledge Base
1. Switch to "Query Knowledge Base" mode
2. Enter a natural language query (e.g., "What are Apple's main revenue sources?")
3. Optionally filter by:
   - Ticker symbol (e.g., AAPL)
   - Analysis type (risk, financial_metrics, financial_statements, etc.)
   - Number of results (1-10)
4. Click "Search Knowledge Base"
5. View AI-synthesized answer with citations, confidence assessment, and follow-up suggestions

**Features:**
- **AI-Synthesized Answers**: Lightweight gpt-4o-mini agent synthesizes raw chunks into coherent, well-cited responses
- **Source Citations**: Every factual claim cited in format `[TICKER - Analysis Type, Period]`
- **Confidence Assessment**: High/Medium/Low confidence indicators based on data quality
- **Limitation Awareness**: Explicit statements about missing data, conflicting sources, or data age
- **Follow-up Suggestions**: Proactive suggestions for relevant next questions
- **Semantic Search**: Natural language queries matched by meaning, not just keywords
- **Ticker Filtering**: Focus search on specific companies
- **Analysis Type Filtering**: Search only risks, metrics, statements, etc.
- Automatic ticker extraction for easy identification
- Mode switching with radio button
- All markdown reports formatted for readability
- No re-running needed to view previous analyses

## Modal Deployment (Optional)

Deploy to [Modal](https://modal.com) for serverless execution with shared ChromaDB RAG storage and API access.

### Prerequisites

1. **Install Modal CLI**
   ```bash
   pip install modal
   ```

2. **Authenticate with Modal**
   ```bash
   modal token new
   ```

3. **Create Modal Secrets**
   - Go to modal.com → Settings → Secrets
   - Create `openai-secret` with `OPENAI_API_KEY`
   - Create `brave-secret` with `BRAVE_API_KEY`

### Deployment

Deploy the Modal app (includes ChromaDB volume, web API, and scheduled batch jobs):

```bash
modal deploy modal_app.py
```

This creates:
- **Persistent ChromaDB volume** for RAG storage (with duplicate handling via upsert)
- **FastAPI web server** at `https://YOUR-USERNAME--financial-research-agent-web-app.modal.run`
- **Daily batch job** (2 AM) updating top 50 companies (currently disabled for prototype mode)
- **On-demand analysis function** for any ticker

**Note:** The daily batch update is currently disabled. To re-enable it, uncomment the schedule line in [modal_app.py:173](modal_app.py#L173):
```python
schedule=modal.Cron("0 2 * * *"),  # Run at 2 AM daily
```
Then redeploy with `modal deploy modal_app.py`.

### Usage

#### 1. Generate Analysis on Modal (Recommended)

Run analysis directly on Modal (uses Modal secrets for API keys):

```bash
modal run modal_app.py::analyze_company --ticker AAPL
```

Features:
- Automatic ChromaDB indexing with duplicate handling
- 7-day caching (skips re-analysis if recent one exists)
- Results available via API immediately

#### 2. Upload Local Analysis to Modal

If you've generated analyses locally with your own API keys, you can upload them to Modal's ChromaDB:

```python
python scripts/upload_to_modal.py \
  --ticker AAPL \
  --analysis-dir financial_research_agent/output/20251106_115436
```

Note: This uses Modal Mount to transfer files. The `index_local_analysis` function signature uses Modal's mount system.

#### 3. Query via REST API

Once analyses are indexed in Modal's ChromaDB:

**Natural language query:**
```bash
curl https://YOUR-USERNAME--financial-research-agent-web-app.modal.run/api/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "What are Apple main revenue sources?", "ticker": "AAPL"}'
```

**List indexed companies:**
```bash
curl https://YOUR-USERNAME--financial-research-agent-web-app.modal.run/api/companies
```

**Compare companies:**
```bash
curl https://YOUR-USERNAME--financial-research-agent-web-app.modal.run/api/compare \
  -H 'Content-Type: application/json' \
  -d '{"tickers": ["AAPL", "MSFT"], "query": "profitability and margins"}'
```

**Trigger new analysis (REQUIRES user API key):**
```bash
curl -X POST https://YOUR-USERNAME--financial-research-agent-web-app.modal.run/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "ticker": "TSLA",
    "openai_api_key": "sk-proj-YOUR-KEY-HERE",
    "brave_api_key": "BSA-YOUR-KEY (optional)",
    "force_refresh": false
  }'
```

**IMPORTANT:** The `/api/analyze` endpoint requires users to provide their own OpenAI API key. This ensures the demo service doesn't incur costs for user-requested analyses. Analyses generated with user keys are automatically indexed in the shared ChromaDB for all users to query.

### Bootstrap Script

To populate Modal ChromaDB with 10 mega-cap companies:

```bash
./scripts/bootstrap_modal.sh
```

This script:
1. Deploys Modal app
2. Generates analyses locally for AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, BRK.B, JNJ, UNH
3. Uploads each analysis to Modal ChromaDB
4. Provides API endpoint URLs for testing

### Querying the Knowledge Base

The system uses ChromaDB for semantic search across all indexed analyses. You can query locally or via Modal's API.

#### Local Python Queries

Run the interactive example script:
```bash
python scripts/query_chromadb_examples.py
```

Or use the Python API directly:
```python
from financial_research_agent.rag.chroma_manager import FinancialRAGManager

rag = FinancialRAGManager(persist_directory="./chroma_db")

# Basic semantic search
results = rag.query(
    query="What are the main revenue sources?",
    n_results=5
)

# Company-specific search
results = rag.query(
    query="key risk factors",
    ticker="AAPL",
    n_results=3
)

# Analysis type filter
results = rag.query(
    query="profit margins",
    analysis_type="financial_metrics",
    n_results=5
)

# Peer comparison
comparison = rag.compare_peers(
    tickers=["AAPL", "MSFT", "GOOGL"],
    query="cloud and AI strategy",
    n_results_per_company=2
)

# List all indexed companies
companies = rag.list_companies()
```

#### Via Modal REST API

Query from anywhere using HTTP:
```bash
# Semantic search
curl https://YOUR-USERNAME--financial-research-agent-web-app.modal.run/api/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "revenue growth trends", "ticker": "AAPL", "n_results": 3}'

# Compare companies
curl https://YOUR-USERNAME--financial-research-agent-web-app.modal.run/api/compare \
  -H 'Content-Type: application/json' \
  -d '{"tickers": ["AAPL", "MSFT"], "query": "AI investments"}'
```

**Query Features:**
- **Semantic Search**: Natural language queries find relevant content by meaning, not keywords
- **Filtered Search**: Filter by ticker, analysis type (risk, financial_metrics, etc.)
- **Peer Comparison**: Compare multiple companies on the same topic
- **Similarity Scoring**: Results ranked by relevance (cosine distance)
- **Chunked Content**: Each result includes context from the source document

### Modal Features

- **Persistent ChromaDB Volume**: All analyses stored with upsert (prevents duplicates)
- **Serverless Execution**: Pay only for actual compute time
- **Scheduled Updates**: Daily batch job keeps top 50 companies current (uses admin keys)
- **REST API**: Query analyses, trigger new analyses, compare companies
- **User API Keys Required**: Users must provide their own OpenAI key to generate new analyses
- **7-Day Caching**: Avoids redundant API calls for recent analyses
- **Semantic Search**: ChromaDB vector embeddings for intelligent query matching

### Cost Considerations

- **Modal Compute**: ~$0.001/minute for analysis generation
- **ChromaDB Storage**: Free persistent volume (up to 50GB)
- **API Calls**: Uses your Modal secrets by default, or users can provide their own keys
- **Daily Batch**: Runs automatically if scheduled (can be disabled)

## Output

Reports are saved to timestamped directories with minimal terminal output:

```
✅ Research complete!
📁 All reports saved to: financial_research_agent/output/YYYYMMDD_HHMMSS/
```

**Output Structure:**
```
financial_research_agent/output/YYYYMMDD_HHMMSS/
├── 00_query.md                               # Your query
├── 01_search_plan.md                         # Search strategy
├── 02_search_results.md                      # Web search results
├── 02_edgar_filings.md                       # SEC filing data
├── 03_financial_statements.md                # Balance Sheet, Income, Cash Flow (XBRL order)
├── 04_financial_metrics.md                   # Calculated financial ratios
├── 05_financial_analysis.md                  # 800-1200 word specialist analysis
├── 06_risk_analysis.md                       # 800-1200 word risk assessment (10-K Item 1A priority)
├── 07_comprehensive_report.md                # Main 3-5 page synthesized report
├── 08_verification.md                        # Quality check
├── data_verification.md                      # Balance sheet equation validation (✓ PASSED/✗ FAILED)
├── xbrl_raw_balance_sheet_TICKER_DATE.csv    # Raw XBRL audit trail
├── xbrl_raw_income_statement_TICKER_DATE.csv # Raw XBRL audit trail
├── xbrl_raw_cashflow_TICKER_DATE.csv         # Raw XBRL audit trail
└── error_log.txt                             # Error details (if any)
```

**Key Features:**
- **SEC XBRL Presentation Order**: Financial statements match official 10-Q/10-K structure
- **Audit Trail**: Raw XBRL CSV files with all metadata (concept, label, level, abstract, weight)
- **Comparative Periods**: Current vs. Prior period for all line items
- **Correct Totals**: Subtotals appear in proper hierarchical positions and add up correctly
- **Data Verification**: Automatic validation of balance sheet equation (Assets = Liabilities + Equity) with 0.1% tolerance

## Recent Improvements

### RAG Synthesis Agent (November 2025)
- **AI-Powered Q&A**: Lightweight gpt-4o-mini synthesis agent transforms raw ChromaDB chunks into coherent, well-cited answers
- **Source Attribution**: Every factual claim cited in format `[TICKER - Analysis Type, Period]`
- **Confidence Assessment**: Automatic high/medium/low confidence indicators based on data completeness and consistency
- **Smart Follow-ups**: Proactive suggestions for relevant next questions
- **Event Loop Handling**: Robust async handling works in main threads, worker threads (Gradio), and nested execution contexts

### Data Quality & Verification (November 2025)
- **Fixed balance sheet verification**: Corrected equity double-counting issue that was causing false failure reports
- **Enhanced risk analysis**: Risk agent now prioritizes 10-K Item 1A Risk Factors (comprehensive annual disclosures) over 10-Q quarterly updates
- **Template rendering fixes**: Resolved missing variable interpolation in financial metrics reports
- **Duplicate handling**: ChromaDB now uses upsert pattern to prevent duplicate entries when re-indexing same ticker

### User Interface Enhancements
- **Analysis selection**: Web interface now supports viewing existing analyses without re-running
- **Mode switching**: Toggle between "Run New Analysis" and "View Existing Analysis"
- **Automatic discovery**: System scans output directory and presents up to 50 most recent completed analyses
- **Ticker extraction**: Smart extraction of ticker symbols from queries for easy identification

## Customization

All prompts and sub-agents can be customized for your specific needs. See the documentation for details on:
- Modifying specialist agent prompts
- Adjusting output structure
- Adding new data sources
- Configuring models and costs

## Technology Stack

**LLM Provider:** OpenAI (GPT-4.1, o3-mini)
- Required for OpenAI Agents SDK compatibility
- Advanced function calling for EDGAR MCP tools
- Investment-grade analysis quality

**Note on Open-Source Models:**
While open-source models from [Hugging Face](https://huggingface.co/open-llm-leaderboard) (e.g., Llama 3.3 70B, Qwen 2.5 72B) are improving rapidly, this project currently requires OpenAI models due to:
- OpenAI Agents SDK framework dependency
- Reliable tool/function calling for MCP integration
- Quality requirements for financial analysis

Future versions could support open-source models with agent framework migration (LangChain, AutoGen, etc.).
