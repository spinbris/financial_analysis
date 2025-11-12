# Financial Research Agent - UX & Architecture Redesign Proposal

## Executive Summary

**Problem**: Current Gradio interface doesn't clearly communicate the two-tier architecture: (1) SEC EDGAR-based company analyses → (2) RAG-powered Q&A. Users may query the knowledge base expecting fresh data when analyses are stale or missing.

**Proposed Solution**: Redesign UX to guide users through the recommended workflow, with intelligent detection of missing/stale data and options to refresh or proceed with web search fallback.

---

## Current State Analysis

### Current Architecture (What Actually Happens)

```
1. USER QUERY
   ↓
2. DEEP ANALYSIS (3-5 min, ~$0.08)
   ├─ Planner: Creates targeted web searches
   ├─ Search Agent: Executes parallel searches
   ├─ EDGAR Agent: Fetches SEC filings (10-K, 10-Q)
   ├─ Financial Statements Agent: Extracts 118+ XBRL line items
   ├─ Financial Metrics Agent: Calculates ratios
   ├─ Financials Agent: 800-1200 word analysis
   ├─ Risk Agent: 800-1200 word risk assessment
   └─ Writer: Synthesizes comprehensive 1500-2500 word report
   ↓
3. AUTO-INDEX TO CHROMADB
   ├─ Chunks analysis into semantic blocks
   └─ Stores with metadata (ticker, type, period, filing)
   ↓
4. KNOWLEDGE BASE READY
   └─ User can now query via RAG
```

### Current UX Issues

**Issue 1: Mode Confusion**
- Three modes presented as equal alternatives: "Run New Analysis", "View Existing Analysis", "Query Knowledge Base"
- Reality: They're sequential steps in a workflow, not alternatives
- Users may jump to "Query Knowledge Base" expecting fresh data

**Issue 2: Missing Data Awareness**
- No indication if company is in knowledge base before querying
- No prompt to run analysis if data missing/stale
- Synthesis agent returns "I don't have information about X" - but doesn't suggest running analysis

**Issue 3: Data Staleness**
- Knowledge base could be days/weeks/months old
- No timestamp shown for indexed analyses
- No warning about potentially outdated data
- No mechanism to detect if newer filings available

**Issue 4: Synthesis Agent Limitations**
- Currently synthesizes ONLY from knowledge base chunks
- Cannot access web search tool to augment stale data
- Cannot flag when data is too old to be reliable
- No fallback strategy when knowledge base empty

**Issue 5: Workflow Clarity**
- Not clear to users that recommended flow is:
  1. Run analysis for company (builds knowledge base)
  2. Query knowledge base (fast, cheap Q&A on existing data)
  3. Re-run analysis periodically to refresh
- Templates suggest "Analyze X" but this runs full analysis, not KB query

---

## Proposed Solutions

### Option 1: Guided Workflow with Intelligence (RECOMMENDED)

**Redesign UX to guide users through optimal workflow:**

#### 1.1 Company Dashboard (New Primary Interface)

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Financial Research Agent                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                              │
│ 🏢 Select or Add Company                                    │
│                                                              │
│ [Dropdown: AAPL - Apple Inc. (Last updated: 2 days ago) ▼]  │
│                                                              │
│ Or enter new ticker: [_____] [+ Add Company]                │
│                                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                              │
│ 📈 Apple Inc. (AAPL)                                        │
│ ✅ In Knowledge Base | Last Analysis: Nov 6, 2025 (2d ago)  │
│ 📁 Q3 FY2024 (Most recent filing)                           │
│                                                              │
│ [🔍 Ask Questions]  [🔄 Refresh Analysis]  [📊 View Reports]│
│                                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                              │
│ 💭 Quick Questions for AAPL:                                │
│ • What were Apple's Q3 revenues?                            │
│ • What are the main risk factors?                           │
│ • How has profitability changed?                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 1.2 Intelligent Query Handler

When user asks a question:

```python
def intelligent_query_handler(query: str, ticker: str = None):
    """
    Handle query with intelligence about data availability.

    Flow:
    1. Extract ticker from query if not provided
    2. Check if company in knowledge base
    3. Check data age vs. latest SEC filing date
    4. Route to appropriate handler
    """

    # Extract ticker
    detected_ticker = extract_ticker(query) or ticker

    if not detected_ticker:
        return ask_user_for_ticker(query)

    # Check knowledge base
    kb_status = check_knowledge_base(detected_ticker)

    if kb_status == "missing":
        return prompt_run_analysis(detected_ticker, reason="not_in_kb")

    if kb_status == "stale":  # e.g., >7 days old
        return prompt_refresh_or_continue(detected_ticker, kb_status)

    if kb_status == "fresh":
        return query_knowledge_base_with_synthesis(query, detected_ticker)
```

**Example User Flows:**

**Flow A: Company Not in KB**
```
User: "What are Tesla's main revenue sources?"

System:
┌────────────────────────────────────────────────────┐
│ ⚠️  Tesla (TSLA) Not in Knowledge Base            │
│                                                    │
│ To answer questions about Tesla, I need to run a  │
│ comprehensive analysis first (~3-5 min, $0.08).   │
│                                                    │
│ This will:                                         │
│ • Extract complete financials from SEC filings     │
│ • Analyze 118+ line items with comparative periods│
│ • Assess risk factors from 10-K                   │
│ • Index all data for future instant Q&A           │
│                                                    │
│ [🚀 Run Analysis Now]  [❌ Cancel]                 │
│                                                    │
│ Or, I can attempt to answer using only web search │
│ (less accurate, no SEC filing data):              │
│ [🌐 Use Web Search Fallback]                      │
└────────────────────────────────────────────────────┘
```

**Flow B: Stale Data**
```
User: "What are Apple's Q3 results?"

System:
┌────────────────────────────────────────────────────┐
│ ⏰ Apple Analysis May Be Outdated                 │
│                                                    │
│ Last analysis: Nov 2, 2025 (5 days ago)           │
│ Latest SEC filing: 10-Q filed Nov 5, 2025 (NEW!)  │
│                                                    │
│ Recommendation: Refresh analysis to get latest Q3 │
│ data from Nov 5 filing.                           │
│                                                    │
│ [🔄 Refresh Analysis (~3 min)]                    │
│ [📋 Answer from Existing Data (Nov 2)]            │
│ [🌐 Augment with Web Search]                      │
└────────────────────────────────────────────────────┘
```

**Flow C: Fresh Data**
```
User: "What are Apple's main revenue sources?"

System: [Immediately queries KB and synthesizes]

# 💡 Answer

Apple's primary revenue sources in Q3 FY2024 were:

1. **iPhone**: $39.3B (45.8% of total revenue) [AAPL - Financial Statements, Q3 FY2024]
2. **Services**: $24.2B (28.2% of total revenue) [AAPL - Financial Statements, Q3 FY2024]
3. **Mac**: $7.0B (8.2%) [AAPL - Financial Statements, Q3 FY2024]

[... rest of synthesis ...]

---
**Confidence:** 🟢 HIGH
**Data Source:** SEC Form 10-Q filed Aug 1, 2024 (3 days ago)
```

#### 1.3 Enhanced Synthesis Agent with Web Search

**Add search tool access to synthesis agent:**

```python
RAG_SYNTHESIS_PROMPT_ENHANCED = """You are a financial research assistant specializing in synthesizing
information from financial analysis documents stored in a knowledge base.

## Available Tools

1. **Knowledge Base Search**: Query indexed financial analyses (SEC EDGAR data)
2. **Web Search**: Search for recent news, market data, or context (use sparingly)

## When to Use Each Tool

**Knowledge Base (Primary)**:
- Financial statements (most authoritative)
- Historical SEC filing data
- Risk factors from 10-K/10-Q
- Calculated financial ratios

**Web Search (Supplementary)**:
- Recent news/events not in SEC filings
- Market context (stock price, analyst ratings)
- Competitive landscape updates
- Management changes/strategic announcements

## Response Strategy

1. **Always start with knowledge base** - most authoritative
2. **Augment with web search** if:
   - User asks about very recent events (last 7 days)
   - Knowledge base data >30 days old and question is time-sensitive
   - Question requires external context (e.g., "How does AAPL compare to MSFT on margins?")
3. **Clearly label sources**:
   - KB: `[AAPL - Financial Statements, Q3 FY2024 per SEC 10-Q]`
   - Web: `[Reuters, Nov 7 2025]` or `[Google Finance, Nov 7 2025]`

## When Knowledge Base is Insufficient

If knowledge base lacks data for the question:
1. **State limitation explicitly**: "I don't have SEC filing data for [company/period]"
2. **Offer alternatives**:
   - "I can search the web for general information (less reliable)"
   - "Would you like me to run a comprehensive analysis for [company]?"
3. **Never make up financial data** - cite sources or admit ignorance

Current datetime: {current_time}
"""
```

**Modified synthesis agent:**

```python
def create_rag_synthesis_agent_enhanced() -> Agent:
    """Create synthesis agent with web search capability."""
    from financial_research_agent.agents.search_agent import brave_search_tool

    return Agent(
        name="RAG Synthesis Agent",
        instructions=RAG_SYNTHESIS_PROMPT_ENHANCED.format(current_time=datetime.now()),
        model="gpt-4o-mini",  # Fast and cheap
        output_type=RAGResponse,
        tools=[brave_search_tool]  # Add web search as fallback
    )
```

### Option 2: Simpler Two-Stage Interface

**Clearer separation of workflows:**

```
┌─────────────────────────────────────────────────────┐
│ 📊 Financial Research Agent                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                      │
│ Choose Your Workflow:                               │
│                                                      │
│ ┌──────────────────────┐  ┌──────────────────────┐ │
│ │ 🔬 DEEP ANALYSIS     │  │ 💬 QUICK Q&A         │ │
│ │                      │  │                      │ │
│ │ Run comprehensive    │  │ Query knowledge base │ │
│ │ SEC filing analysis  │  │ for instant answers  │ │
│ │                      │  │                      │ │
│ │ Time: 3-5 minutes    │  │ Time: 5-10 seconds   │ │
│ │ Cost: ~$0.08         │  │ Cost: ~$0.002        │ │
│ │                      │  │                      │ │
│ │ [Start Analysis] ──┐ │  │ [Ask Question] ────┐ │ │
│ └────────────────────┘ │ │ └───────────────────┘ │ │
│                        │ │                       │ │
│                        └─┼───────────────────────┘ │
│                          │                         │
│                          ↓                         │
│               Indexes to Knowledge Base            │
└─────────────────────────────────────────────────────┘
```

---

## Recommended Implementation Plan

### Phase 1: Backend Intelligence (Week 1)

**Files to modify:**

1. **`financial_research_agent/rag/chroma_manager.py`**
   - Add `check_company_status(ticker)` → returns: "missing" | "stale" | "fresh"
   - Add `get_latest_analysis_date(ticker)`
   - Add `list_companies_with_metadata()` → returns list with last_updated, filing_date

2. **`financial_research_agent/rag/synthesis_agent.py`**
   - Add `brave_search_tool` to agent tools
   - Update prompt to RAG_SYNTHESIS_PROMPT_ENHANCED
   - Modify to cite web sources separately from KB sources

3. **`financial_research_agent/utils/sec_filing_checker.py`** (NEW)
   - Add `get_latest_filing_date(ticker)` via EDGAR API
   - Add `compare_to_indexed_date(ticker, indexed_date)`

### Phase 2: UX Redesign (Week 1-2)

**Files to modify:**

1. **`financial_research_agent/web_app.py`**
   - Replace three-mode radio with company-centric dashboard
   - Add company selector dropdown with metadata
   - Add intelligent routing based on data availability
   - Add warning banners for stale/missing data

2. **New components:**
   - `CompanyStatusCard` - shows KB status, last analysis, latest filing
   - `DataFreshnessWarning` - shows stale data alerts
   - `SmartQueryHandler` - routes based on data availability

### Phase 3: User Prompts & Guidance (Week 2)

**Add contextual help:**

1. **First-time user flow**
   - "Welcome! To get started, run an analysis for a company"
   - Show suggested companies (AAPL, MSFT, GOOGL, etc.)

2. **Empty knowledge base**
   - "Your knowledge base is empty. Run your first analysis!"

3. **Successful analysis**
   - "✅ Analysis complete! You can now ask questions about AAPL"
   - Show example questions

4. **Stale data detection**
   - Auto-detect when >7 days since last analysis
   - Show refresh suggestion banner

---

## Alternative: Hybrid Query Mode

**For users who want flexibility:**

```python
def hybrid_query(query: str, mode: str = "auto"):
    """
    Hybrid query that intelligently combines KB and web search.

    Modes:
    - "auto": Automatically decide based on data availability
    - "kb_only": Only use knowledge base (fail if missing)
    - "kb_primary": Use KB + web search augmentation
    - "web_fallback": Try KB, fall back to web if missing
    """

    if mode == "auto":
        # Detect if KB has data
        if has_fresh_kb_data(query):
            mode = "kb_primary"
        else:
            mode = "web_fallback"

    # Execute based on mode
    # ...
```

---

## User Flow Examples (Redesigned)

### Flow 1: New User, Empty KB

```
1. User arrives at app
   → Sees: "Welcome! Your knowledge base is empty."
   → Shows: List of popular companies (AAPL, MSFT, GOOGL, TSLA)

2. User clicks "AAPL - Apple Inc."
   → Status: "⚠️ Not analyzed yet"
   → Shows: [Run Analysis] button with time/cost estimate

3. User clicks "Run Analysis"
   → Shows progress with real-time updates
   → Completes in ~3-5 min

4. After completion:
   → "✅ Apple analysis complete! Ask me anything:"
   → Shows quick question suggestions
   → User can now query instantly
```

### Flow 2: Experienced User, Checking for Updates

```
1. User selects "AAPL" from dropdown
   → Status: "✅ In KB | Last: Nov 2 | Latest filing: Nov 5 (NEW!)"
   → Shows: [Refresh] [Ask Questions] [View Reports]

2. User clicks "Refresh"
   → System fetches Nov 5 filing
   → Updates KB with new data
   → Shows: "✅ Updated with Q3 FY2024 data"

3. User asks: "How did revenue change?"
   → Synthesis agent uses BOTH Nov 2 and Nov 5 data
   → Answers: "Revenue increased from X to Y [comparing filings]"
```

### Flow 3: Ad-hoc Query for New Company

```
1. User types: "What are Netflix's subscriber numbers?"

2. System detects:
   → Ticker: NFLX
   → Status: Not in KB

3. System shows:
   ┌──────────────────────────────────────────┐
   │ ⚠️  Netflix (NFLX) not in knowledge base │
   │                                          │
   │ Choose approach:                         │
   │                                          │
   │ 🎯 Recommended:                          │
   │ [Run Full Analysis] (~3 min, SEC data)   │
   │                                          │
   │ ⚡ Quick & Dirty:                        │
   │ [Web Search Only] (~5 sec, less reliable)│
   └──────────────────────────────────────────┘

4. User chooses web search:
   → Gets answer from Google/Reuters/etc.
   → Shows: "⚠️ This answer is from web search, not SEC filings"
   → Suggests: "For authoritative data, run full analysis"
```

---

## Technical Requirements

### New Backend Functions

```python
# financial_research_agent/rag/intelligence.py

def check_company_status(ticker: str) -> dict:
    """
    Check if company is in KB and data freshness.

    Returns:
        {
            "in_kb": bool,
            "last_analysis": datetime | None,
            "latest_filing": datetime | None,
            "status": "missing" | "stale" | "fresh",
            "days_since_analysis": int | None,
            "needs_refresh": bool
        }
    """
    pass

def extract_ticker_from_query(query: str) -> str | None:
    """Extract ticker symbol from natural language query."""
    # Use regex + LLM for ambiguous cases
    pass

def get_latest_sec_filing_date(ticker: str) -> datetime | None:
    """Check SEC EDGAR for latest 10-K/10-Q filing date."""
    # Use edgartools or SEC API
    pass

def recommend_action(query: str, ticker: str) -> str:
    """
    Recommend action based on data availability.

    Returns: "run_analysis" | "refresh_analysis" | "query_kb" | "web_fallback"
    """
    pass
```

### Enhanced Synthesis Agent

```python
class RAGResponseEnhanced(BaseModel):
    """Enhanced response with source breakdown."""

    answer: str
    sources_cited: list[str]
    kb_sources: list[str]  # SEC filing sources
    web_sources: list[str]  # Web search sources
    confidence: str
    data_age_warning: str | None  # "Data is 14 days old"
    limitations: str | None
    suggested_followup: list[str] | None
    suggested_refresh: bool  # Should user refresh analysis?
```

---

## Success Metrics

**User Experience:**
- ✅ Users understand the two-tier workflow
- ✅ Users don't query empty knowledge base unknowingly
- ✅ Users are alerted when data is stale
- ✅ Users can make informed choice: refresh vs. use existing data

**Data Quality:**
- ✅ Synthesis agent cites authoritative SEC data when available
- ✅ Synthesis agent augments with web search only when appropriate
- ✅ Clear labeling of KB vs. web sources
- ✅ Confidence scores reflect data quality

**Cost Efficiency:**
- ✅ Users avoid redundant full analyses (use KB queries instead)
- ✅ Users refresh analyses only when needed (filing updates)
- ✅ Web search fallback available for one-off questions

---

## Recommendation

**Implement Option 1 (Guided Workflow) in two phases:**

**Phase 1A (Quick Win - 2-3 days):**
1. Add knowledge base status checker
2. Add intelligent routing to query handler
3. Add warning banners for missing/stale data
4. Add web search tool to synthesis agent

**Phase 1B (Full Redesign - 1 week):**
1. Redesign Gradio interface to company-centric dashboard
2. Add company selector with metadata
3. Implement suggested user flows
4. Add contextual help and guidance

**Why this approach:**
- Preserves existing functionality
- Adds intelligence layer without breaking changes
- Guides users to optimal workflow
- Allows web search fallback for flexibility
- Clearly communicates data provenance and freshness

---

## Open Questions

1. **Staleness threshold**: How old is "too old"?
   - Suggestion: 7 days for actively traded stocks, 30 days for blue chips

2. **Auto-refresh**: Should system auto-refresh when new filings detected?
   - Suggestion: Notify user, don't auto-refresh (cost consideration)

3. **Web search default**: Allow web search fallback by default, or require user opt-in?
   - Suggestion: Offer as option, warn about reduced reliability

4. **Company comparison queries**: How to handle "Compare AAPL vs MSFT"?
   - **Answer**: Implement multi-company status check with clear UX (see section below)

5. **Partial data**: If AAPL fresh but MSFT stale, how to handle comparison?
   - **Answer**: Provide partial answer with prominent data quality warnings (see section below)

---

## Multi-Company Query Handling (IMPORTANT)

### Problem Statement

User asks: **"Compare Apple's profit margins with Tesla's"**

**Scenario 1**: AAPL in KB (fresh), TSLA not in KB
**Scenario 2**: AAPL in KB (fresh), TSLA in KB (stale - 30 days old)
**Scenario 3**: AAPL in KB (stale), TSLA not in KB
**Scenario 4**: Both companies missing from KB

**Challenge**: System must clearly communicate data availability status for each company to avoid misleading comparisons.

---

### Proposed Solution: Multi-Company Intelligence Layer

#### Backend Function

```python
# financial_research_agent/rag/intelligence.py

def check_multi_company_status(tickers: list[str]) -> dict[str, dict]:
    """
    Check status for multiple companies.

    Args:
        tickers: List of ticker symbols

    Returns:
        {
            "AAPL": {
                "in_kb": True,
                "status": "fresh",
                "last_analysis": datetime(2025, 11, 6),
                "days_old": 1
            },
            "TSLA": {
                "in_kb": False,
                "status": "missing",
                "last_analysis": None,
                "days_old": None
            }
        }
    """
    results = {}
    for ticker in tickers:
        results[ticker] = check_company_status(ticker)
    return results


def extract_all_tickers_from_query(query: str) -> list[str]:
    """
    Extract all ticker symbols from comparison query.

    Examples:
        "Compare AAPL and TSLA" → ["AAPL", "TSLA"]
        "How do Apple and Tesla compare?" → ["AAPL", "TSLA"]
        "MSFT vs GOOGL margins" → ["MSFT", "GOOGL"]

    Returns:
        List of ticker symbols (uppercase)
    """
    # Use regex + LLM for company name resolution
    # e.g., "Apple" → "AAPL", "Tesla" → "TSLA"
    pass
```

#### User Flow Examples

**Scenario 1: One Company Missing**

```
User: "Compare Apple's profit margins with Tesla's"

System detects:
- AAPL: In KB (fresh, 1 day old)
- TSLA: NOT in KB

System shows:
┌──────────────────────────────────────────────────────────┐
│ ⚠️  Partial Data Available                              │
│                                                          │
│ Your comparison query requires data for:                │
│ • ✅ AAPL (Apple) - In knowledge base (updated 1d ago)  │
│ • ❌ TSLA (Tesla) - NOT in knowledge base               │
│                                                          │
│ Options:                                                 │
│                                                          │
│ 🎯 Recommended:                                          │
│ [Run Analysis for TSLA] (~3 min)                        │
│ → Then compare with authoritative SEC data              │
│                                                          │
│ 📊 Alternative:                                          │
│ [Compare Anyway (AAPL only from KB, TSLA from web)]     │
│ → Less reliable for TSLA, no SEC filing data            │
│                                                          │
│ [❌ Cancel]                                              │
└──────────────────────────────────────────────────────────┘
```

**If user chooses "Compare Anyway" (web fallback for TSLA):**

```
# 💡 Answer

## Profit Margin Comparison

### Apple (AAPL) - ✅ SEC Filing Data
- **Gross Margin**: 45.2% [AAPL - Financial Statements, Q3 FY2024 per SEC 10-Q]
- **Operating Margin**: 29.8% [AAPL - Financial Statements, Q3 FY2024]
- **Net Margin**: 25.3% [AAPL - Financial Statements, Q3 FY2024]

### Tesla (TSLA) - ⚠️ Web Search Data
- **Gross Margin**: ~18% (approximate) [Google Finance, Nov 7 2025]
- **Operating Margin**: ~10% (approximate) [Reuters, Nov 7 2025]
- **Net Margin**: ~9% (approximate) [Yahoo Finance, Nov 7 2025]

## ⚠️ Important Data Quality Warning

**Apple data** is from authoritative SEC Form 10-Q filings with exact XBRL precision.
**Tesla data** is from web sources and may be:
- Approximate or estimated
- Not from official SEC filings
- Potentially outdated or incorrect
- Missing comparative period data

**Recommendation**: Run full analysis for Tesla to get authoritative SEC data for an accurate comparison.

[🚀 Run Tesla Analysis Now]

---
**Confidence:** 🟡 MEDIUM (mixed data sources)
**Data Sources:**
- AAPL: SEC Form 10-Q filed Aug 1, 2024 (1 day ago)
- TSLA: Web search results (reliability unknown)
```

---

**Scenario 2: One Company Stale**

```
User: "Compare Apple and Tesla profit margins"

System detects:
- AAPL: In KB (fresh, 1 day old)
- TSLA: In KB (stale, 30 days old)

System shows:
┌──────────────────────────────────────────────────────────┐
│ ⏰ Mixed Data Ages Detected                              │
│                                                          │
│ Your comparison query uses data of different ages:      │
│ • ✅ AAPL (Apple) - Fresh data (updated 1 day ago)      │
│ • ⚠️  TSLA (Tesla) - Stale data (updated 30 days ago)   │
│                                                          │
│ Options:                                                 │
│                                                          │
│ 🎯 Recommended:                                          │
│ [Refresh TSLA Analysis] (~3 min)                        │
│ → Compare both with recent SEC data                     │
│                                                          │
│ 📊 Alternative:                                          │
│ [Compare with Existing Data]                            │
│ → Answer will note data age difference                  │
│                                                          │
│ [❌ Cancel]                                              │
└──────────────────────────────────────────────────────────┘
```

**If user chooses "Compare with Existing Data":**

```
# 💡 Answer

## Profit Margin Comparison

### Apple (AAPL) - ✅ Recent Data
- **Gross Margin**: 45.2% [AAPL - Financial Statements, Q3 FY2024]
- **Operating Margin**: 29.8% [AAPL - Financial Statements, Q3 FY2024]
- **Net Margin**: 25.3% [AAPL - Financial Statements, Q3 FY2024]
- **Data from**: SEC Form 10-Q filed Aug 1, 2024 (1 day ago)

### Tesla (TSLA) - ⚠️ Older Data
- **Gross Margin**: 18.2% [TSLA - Financial Statements, Q2 2024]
- **Operating Margin**: 9.8% [TSLA - Financial Statements, Q2 2024]
- **Net Margin**: 8.5% [TSLA - Financial Statements, Q2 2024]
- **Data from**: SEC Form 10-Q filed Jul 8, 2024 (30 days ago)

## ⚠️ Data Age Warning

Apple's data is from their most recent Q3 filing (1 day old), while Tesla's data is from their Q2 filing (30 days old). This comparison may not reflect Tesla's most recent performance.

**Recommendation**: Refresh Tesla analysis to compare both companies using latest available filings.

[🔄 Refresh Tesla Analysis]

---
**Confidence:** 🟡 MEDIUM (data age mismatch)
**Data Sources:**
- AAPL: Q3 FY2024 (Aug 1, 2024 filing - 1 day old)
- TSLA: Q2 2024 (Jul 8, 2024 filing - 30 days old)
```

---

**Scenario 3: Both Companies Missing**

```
User: "Compare Netflix and Spotify profit margins"

System detects:
- NFLX: NOT in KB
- SPOT: NOT in KB

System shows:
┌──────────────────────────────────────────────────────────┐
│ ❌ No Companies in Knowledge Base                        │
│                                                          │
│ Neither company has been analyzed yet:                   │
│ • ❌ NFLX (Netflix) - Not in knowledge base             │
│ • ❌ SPOT (Spotify) - Not in knowledge base             │
│                                                          │
│ Options:                                                 │
│                                                          │
│ 🎯 Recommended:                                          │
│ [Analyze Both Companies] (~6-8 min total, $0.16)        │
│ → Get authoritative SEC data for both                   │
│                                                          │
│ ⚡ Quick & Dirty:                                        │
│ [Web Search Comparison] (~10 sec, less reliable)        │
│ → Answer from Google/Reuters/etc. (no SEC data)         │
│                                                          │
│ [❌ Cancel]                                              │
└──────────────────────────────────────────────────────────┘
```

**If user chooses "Analyze Both":**
- System runs both analyses sequentially (or parallel if implemented)
- Shows progress for each: "Analyzing NFLX... (1/2)" → "Analyzing SPOT... (2/2)"
- After completion, automatically runs the comparison query

---

### Implementation: Enhanced Synthesis Agent

#### Updated RAGResponse Model

```python
class RAGResponseEnhanced(BaseModel):
    """Enhanced response with multi-company status."""

    answer: str
    sources_cited: list[str]
    kb_sources: list[str]  # From knowledge base
    web_sources: list[str]  # From web search
    confidence: str  # "high" | "medium" | "low"

    # NEW: Company-specific data quality indicators
    company_statuses: dict[str, dict] | None = Field(
        default=None,
        description="Status for each company in query"
    )
    # Example:
    # {
    #     "AAPL": {"source": "kb", "age_days": 1, "filing_date": "2024-08-01"},
    #     "TSLA": {"source": "web", "age_days": None, "filing_date": None}
    # }

    data_quality_warnings: list[str] | None = Field(
        default=None,
        description="Specific warnings about data quality"
    )
    # Example:
    # [
    #     "TSLA data from web sources (not SEC filings)",
    #     "Data age mismatch: AAPL (1d old) vs TSLA (30d old)"
    # ]

    limitations: str | None
    suggested_followup: list[str] | None
    suggested_refresh: list[str] | None = Field(
        default=None,
        description="Companies that should be refreshed"
    )
    # Example: ["TSLA"]
```

#### Updated Synthesis Prompt

```python
RAG_SYNTHESIS_PROMPT_MULTI_COMPANY = """You are a financial research assistant specializing in synthesizing
information from financial analysis documents stored in a knowledge base.

## Available Tools

1. **Knowledge Base Search**: Query indexed financial analyses (SEC EDGAR data)
2. **Web Search**: Search for recent news, market data, or context

## Multi-Company Query Handling (CRITICAL)

When comparing multiple companies, you MUST:

1. **Check data availability for EACH company**
   - Identify which companies have KB data vs. web-only data
   - Note data age for each company

2. **Clearly label data sources**
   - KB data: `[AAPL - Financial Statements, Q3 FY2024 per SEC 10-Q filed Aug 1, 2024]`
   - Web data: `[Reuters, Nov 7 2025]` or `[Google Finance, Nov 7 2025]`

3. **Highlight data quality differences**
   - If comparing KB data with web data, add WARNING section
   - If data ages differ significantly (>7 days), note in WARNING section

4. **Structure comparison clearly**
   ```
   ### Company A (TICKER_A) - ✅ SEC Filing Data
   [metrics from KB]
   Data from: SEC Form 10-Q filed [date] ([days] ago)

   ### Company B (TICKER_B) - ⚠️ Web Search Data
   [metrics from web]
   Data from: Web sources (reliability unknown)

   ## ⚠️ Data Quality Warning
   [Explain the difference in data quality and reliability]
   ```

5. **Set confidence appropriately**
   - High: All companies from fresh KB data
   - Medium: Mixed sources (KB + web) OR data age mismatch
   - Low: All from web sources OR very old KB data

6. **Recommend improvements**
   - Suggest which companies should be analyzed/refreshed
   - Provide actionable next steps

Current datetime: {current_time}
"""
```

---

### Web App Integration

#### Query Handler with Multi-Company Detection

```python
def query_knowledge_base_smart(query: str) -> str:
    """Smart query handler with multi-company detection."""
    from financial_research_agent.rag.intelligence import (
        extract_all_tickers_from_query,
        check_multi_company_status,
        recommend_multi_company_action
    )

    # Extract all tickers from query
    tickers = extract_all_tickers_from_query(query)

    if not tickers:
        return "❌ Could not identify company ticker(s). Please specify ticker symbol(s)."

    # Check status for all companies
    statuses = check_multi_company_status(tickers)

    # Determine action
    action = recommend_multi_company_action(statuses, query)

    if action["type"] == "prompt_user":
        # Show options to user (analyze missing, refresh stale, etc.)
        return format_multi_company_prompt(action, statuses, query)

    elif action["type"] == "query_with_warnings":
        # Proceed with query but add prominent warnings
        response = rag.query_with_synthesis(query, tickers=tickers)
        return format_response_with_data_quality_warnings(response, statuses)

    elif action["type"] == "query_fresh":
        # All data fresh, proceed normally
        response = rag.query_with_synthesis(query, tickers=tickers)
        return format_response(response)
```

---

### Summary: Multi-Company Query Strategy

**Key Principles:**
1. **Transparency**: Always show which companies have KB data vs. web data
2. **Data Quality Warnings**: Prominent warnings when mixing sources or ages
3. **User Choice**: Offer options (analyze missing, use web fallback, etc.)
4. **Clear Labeling**: Every metric shows its source and age
5. **Actionable Suggestions**: Tell user how to improve answer quality
