# Financial Research Agent - UX Improvements Implementation Plan

## Executive Summary

This document outlines a phased approach to improve the UX of the Financial Research Agent by adding intelligent routing and knowledge base awareness. The approach prioritizes low-risk, incremental improvements over a big-bang redesign.

---

## Problem Statement

**Current Issue**: Users may query the knowledge base without realizing:
1. A company hasn't been analyzed yet (empty KB for that ticker)
2. The data is stale (analysis is weeks/months old)
3. The two-tier architecture: Deep Analysis → KB Indexing → RAG Q&A

**Impact**:
- Users get "I don't have information" responses without guidance
- No visibility into data freshness or KB status
- Confusion about when to run analysis vs. query KB

---

## Solution Approach

Add an **Intelligence Layer** that:
1. Checks KB status before querying (is company indexed?)
2. Assesses data freshness (how old is the analysis?)
3. Routes users appropriately (run analysis vs. query KB)
4. Provides clear warnings and guidance

**Key Principle**: Progressive enhancement - add intelligence without breaking existing UI.

---

## Data Staleness Thresholds

### Classification

```python
def get_staleness_status(days_old: int, ticker: str) -> str:
    """
    Determine if data is fresh, aging, or stale.

    Returns: "fresh" | "aging" | "stale"
    """
    # For high-volatility stocks (tech, growth)
    if is_high_volatility(ticker):
        if days_old <= 7:
            return "fresh"         # 🟢 No warning
        elif days_old <= 30:
            return "aging"         # 🟡 Soft warning
        else:
            return "stale"         # 🔴 Strong warning

    # For stable blue chips (utilities, consumer staples)
    else:
        if days_old <= 30:
            return "fresh"
        elif days_old <= 90:
            return "aging"
        else:
            return "stale"
```

### User-Facing Indicators

- **🟢 Fresh**: No warning shown
- **🟡 Aging**: Soft warning - "Data is 15 days old, consider refreshing for latest SEC filings"
- **🔴 Stale**: Strong warning - "⚠️ Data is 45 days old. We recommend refreshing this analysis."

---

## Implementation Phases

### **Phase 0: Quick Intelligence Layer** (1-2 days) ✅ CURRENT

**Goal**: Add basic KB awareness without breaking changes

#### Tasks:
1. ✅ Add `get_companies_with_status()` to `chroma_manager.py`
2. ✅ Add ticker extraction helper function
3. ✅ Enhance KB query handler to check for missing companies
4. ✅ Show "company not in KB" banner with instructions
5. ✅ Add data age to synthesis response footer
6. ✅ Show analysis date/age in Gradio UI

#### Files to Modify:
- `financial_research_agent/rag/chroma_manager.py` (add status methods)
- `financial_research_agent/web_app.py` (enhance `query_knowledge_base()`)
- `financial_research_agent/rag/synthesis_agent.py` (add data age to response)

#### Success Criteria:
- ✅ Users querying missing companies get clear guidance
- ✅ KB queries show data age in response
- ✅ No breaking changes to existing functionality
- ✅ Analysis dates visible in Gradio UI (both view mode and after generation)

---

### **Phase 1: Smart Routing & Warnings** (3-5 days)

**Goal**: Intelligent routing based on KB status

#### Tasks:
1. Add multi-company ticker extraction
2. Add pre-query KB status checking
3. Show user prompts for missing/stale data with action buttons
4. Add data quality warnings to synthesis responses
5. Add "Knowledge Base Status" banner to UI

#### Files to Modify:
- `financial_research_agent/rag/intelligence.py` (NEW - routing logic)
- `financial_research_agent/web_app.py` (add routing and banners)
- `financial_research_agent/rag/synthesis_agent.py` (enhance RAGResponse model)

#### Example Output:

**Missing Company:**
```markdown
## ⚠️ Tesla (TSLA) Not in Knowledge Base

To answer questions about Tesla, I need to run a comprehensive analysis first.

### Options:

1. **🚀 Run Analysis for TSLA** (Recommended)
   - Time: ~3-5 minutes
   - Cost: ~$0.08
   - Includes: Complete SEC filings, 118+ line items, risk analysis

   [Switch to Run New Analysis Mode]

2. **❌ Cancel Query**

---

*Tip: Once analyzed, you can ask unlimited questions about TSLA instantly*
```

**Stale Data Warning:**
```markdown
# 💡 Answer

[... synthesized answer ...]

---

## ⚠️ Data Age Notice

This answer is based on analysis from **30 days ago** (Oct 8, 2025).

**Latest SEC filing**: 10-Q filed Nov 5, 2025 (may contain newer data)

**Recommendation**: Consider refreshing this analysis for most current information.

[Refresh Analysis] [View Anyway]
```

#### Success Criteria:
- Users can't unknowingly query empty KB
- Stale data clearly flagged with refresh suggestions
- Routing logic handles edge cases gracefully

---

### **Phase 2: Enhanced Multi-Company Handling** (1 week)

**Goal**: Better multi-company handling and confidence scoring

#### Tasks:
1. Implement data quality warnings for multi-company queries
2. Add confidence degradation for stale/mixed data
3. Add prominent data source labeling (KB data vs gaps)
4. Handle partial data scenarios (AAPL fresh, TSLA stale)

#### Files to Modify:
- `financial_research_agent/rag/synthesis_agent.py` (enhance prompt)
- `financial_research_agent/rag/chroma_manager.py` (multi-company status)
- `financial_research_agent/web_app.py` (format multi-company warnings)

#### Example Output:

**Mixed Data Ages:**
```markdown
# 💡 Comparison: Apple vs Tesla Profit Margins

## Apple (AAPL) - ✅ Recent Data
- **Gross Margin**: 45.2% [AAPL - Financial Statements, Q3 FY2024]
- **Operating Margin**: 29.8%
- **Net Margin**: 25.3%
- **Data from**: SEC Form 10-Q filed Aug 1, 2024 (2 days ago)

## Tesla (TSLA) - ⚠️ Older Data
- **Gross Margin**: 18.2% [TSLA - Financial Statements, Q2 2024]
- **Operating Margin**: 9.8%
- **Net Margin**: 8.5%
- **Data from**: SEC Form 10-Q filed Jul 8, 2024 (30 days ago)

---

## ⚠️ Data Age Warning

Apple's data is current (2 days old), but Tesla's data is 30 days old. This comparison may not reflect Tesla's most recent performance.

**Recommendation**: Refresh Tesla analysis for accurate comparison.

[🔄 Refresh Tesla Analysis]

---
**Confidence:** 🟡 MEDIUM (data age mismatch)
```

#### Success Criteria:
- Multi-company queries clearly show data provenance
- Users understand limitations of stale comparisons
- Actionable refresh suggestions provided

---

### **Phase 3: UI Enhancements** (OPTIONAL - 1-2 weeks)

**Goal**: Visual improvements without full redesign

#### Option A: Progressive Enhancement (Recommended)

Add status banner above existing UI:

```
┌─────────────────────────────────────────────────────┐
│ 💾 Knowledge Base Status                            │
│                                                      │
│ 📊 Indexed Companies (5):                           │
│   • AAPL (Apple) - 2d ago 🟢                        │
│   • MSFT (Microsoft) - 5d ago 🟢                    │
│   • TSLA (Tesla) - 30d ago 🟡                       │
│   • GOOGL (Alphabet) - 45d ago 🔴                   │
│   • AMZN (Amazon) - 7d ago 🟢                       │
│                                                      │
│ 💡 Click any company to view details or refresh     │
└─────────────────────────────────────────────────────┘

[Existing UI remains below]
```

#### Option B: Company-Centric Dashboard (Full Redesign)

Implement the full dashboard from `UX_REDESIGN_PROPOSAL.md` Option 1.

**Note**: Only pursue if Phase 0-2 insufficient.

---

## Technical Implementation Details

### 1. Ticker Extraction

```python
def extract_tickers_from_query(query: str) -> list[str]:
    """
    Extract ticker symbols from natural language query.

    Examples:
        "What are Apple's revenues?" → ["AAPL"]
        "Compare AAPL and TSLA" → ["AAPL", "TSLA"]
        "How does Microsoft compare to Google?" → ["MSFT", "GOOGL"]

    Returns:
        List of uppercase ticker symbols
    """
    import re

    # Explicit ticker patterns (e.g., "AAPL", "BRK.B")
    explicit_tickers = re.findall(r'\b([A-Z]{1,5}(?:\.[A-Z])?)\b', query)

    # Company name mapping
    company_map = {
        "apple": "AAPL",
        "microsoft": "MSFT",
        "tesla": "TSLA",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "amazon": "AMZN",
        "meta": "META",
        "facebook": "META",
        "nvidia": "NVDA",
        # ... expand as needed
    }

    query_lower = query.lower()
    name_tickers = [
        ticker for name, ticker in company_map.items()
        if name in query_lower
    ]

    # Combine and deduplicate
    all_tickers = list(set(explicit_tickers + name_tickers))

    # Filter out common false positives (IS, IT, OR, etc.)
    false_positives = {"IS", "IT", "OR", "IN", "AT", "TO", "BY"}
    return [t for t in all_tickers if t not in false_positives]
```

### 2. Analysis Age Calculation

```python
def get_analysis_age_from_directory(output_dir: Path) -> dict:
    """
    Extract analysis age from directory name.

    Args:
        output_dir: Path like "20251106_115436"

    Returns:
        {
            "analysis_date": datetime(2025, 11, 6, 11, 54, 36),
            "days_old": 2,
            "formatted": "Nov 6, 2025 (2 days ago)"
        }
    """
    from datetime import datetime

    # Parse timestamp from directory name
    timestamp_str = output_dir.name  # "20251106_115436"
    analysis_datetime = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

    # Calculate age
    days_old = (datetime.now() - analysis_datetime).days

    # Format human-readable
    date_str = analysis_datetime.strftime("%b %d, %Y")

    if days_old == 0:
        age_str = "today"
    elif days_old == 1:
        age_str = "1 day ago"
    else:
        age_str = f"{days_old} days ago"

    return {
        "analysis_date": analysis_datetime,
        "days_old": days_old,
        "formatted": f"{date_str} ({age_str})"
    }
```

### 3. KB Status Check (Enhanced ChromaManager)

```python
# In chroma_manager.py

def get_companies_with_status(self) -> list[dict]:
    """
    Get all indexed companies with status metadata.

    Returns:
        [
            {
                "ticker": "AAPL",
                "company": "Apple Inc.",
                "period": "Q3 FY2024",
                "filing": "10-Q",
                "days_old": 2,
                "status": "fresh",  # "fresh" | "aging" | "stale"
                "last_updated": "2025-11-06"
            },
            ...
        ]
    """
    all_docs = self.collection.get()

    companies_map = {}
    for metadata in all_docs["metadatas"]:
        ticker = metadata.get("ticker")
        if not ticker or ticker in companies_map:
            continue

        # Extract date from chunk_id (format: TICKER_type_s0_c0_YYYYMMDD)
        chunk_id = metadata.get("id", "")
        date_match = re.search(r'_(\d{8})$', chunk_id)

        if date_match:
            date_str = date_match.group(1)
            analysis_date = datetime.strptime(date_str, "%Y%m%d")
            days_old = (datetime.now() - analysis_date).days
        else:
            days_old = 999  # Unknown age

        companies_map[ticker] = {
            "ticker": ticker,
            "company": metadata.get("company", ""),
            "period": metadata.get("period", ""),
            "filing": metadata.get("filing", "").split()[0] if metadata.get("filing") else "",
            "days_old": days_old,
            "status": self._get_staleness_status(days_old, ticker),
            "last_updated": analysis_date.strftime("%Y-%m-%d") if date_match else "Unknown"
        }

    return sorted(companies_map.values(), key=lambda x: x["days_old"])

def check_company_status(self, ticker: str) -> dict:
    """
    Check if a specific company is in KB and its status.

    Args:
        ticker: Stock ticker symbol

    Returns:
        {
            "in_kb": bool,
            "ticker": str,
            "status": "missing" | "fresh" | "aging" | "stale",
            "days_old": int | None,
            "metadata": dict | None
        }
    """
    all_companies = self.get_companies_with_status()

    for company in all_companies:
        if company["ticker"] == ticker.upper():
            return {
                "in_kb": True,
                "ticker": ticker.upper(),
                "status": company["status"],
                "days_old": company["days_old"],
                "metadata": company
            }

    # Not found
    return {
        "in_kb": False,
        "ticker": ticker.upper(),
        "status": "missing",
        "days_old": None,
        "metadata": None
    }

def _get_staleness_status(self, days_old: int, ticker: str) -> str:
    """Determine staleness status based on age and ticker volatility."""
    # Simplified - can be enhanced with actual volatility data
    high_volatility = ticker in ["TSLA", "NVDA", "AMD", "PLTR"]

    if high_volatility:
        if days_old <= 7:
            return "fresh"
        elif days_old <= 30:
            return "aging"
        else:
            return "stale"
    else:
        if days_old <= 30:
            return "fresh"
        elif days_old <= 90:
            return "aging"
        else:
            return "stale"
```

---

## Decision: Web Search in Synthesis Agent

**Decision**: Do NOT add web search to synthesis agent in Phase 0-2.

**Rationale**:
1. Maintains clear boundary: KB = authoritative SEC data
2. Lower cost (no automatic web searches)
3. Simpler to implement and test
4. User makes explicit choice about data quality

**Alternative**: Handle missing data at routing layer:
- Detect missing company BEFORE querying KB
- Show user clear options: Run Analysis (recommended) vs. Cancel
- Keep synthesis agent focused on synthesizing existing KB data

**Future Enhancement**: Web search fallback can be added in Phase 3+ if user testing shows need.

---

## Success Metrics

### Phase 0:
- ✅ Zero "I don't have information" responses without guidance
- ✅ 100% of KB queries show data age
- ✅ Missing company detection rate: 100%
- ✅ No increase in error rate

### Phase 1:
- ✅ Users prompted before querying missing companies
- ✅ Stale data flagged with refresh suggestions
- ✅ User satisfaction increase (survey)

### Phase 2:
- ✅ Multi-company queries show clear data quality indicators
- ✅ Confidence scores correlate with data quality
- ✅ Refresh adoption rate: >20% when suggested

---

## Risks & Mitigation

### Risk 1: Complexity Creep
**Mitigation**: Strict phase boundaries, no feature creep in Phase 0

### Risk 2: False Positive Ticker Detection
**Mitigation**: Maintain false positive list, use conservative matching

### Risk 3: User Confusion from Changes
**Mitigation**: Progressive enhancement, no breaking changes, clear messaging

### Risk 4: Performance Impact
**Mitigation**: KB status checks are lightweight (metadata only), cache results

---

## Open Questions & Future Enhancements

### Answered:
- ✅ **Staleness threshold**: 7/30 days for volatile, 30/90 for stable
- ✅ **Web search**: Not in Phase 0-2, routing layer handles missing data
- ✅ **Data age source**: Use analysis timestamp from output directory

### For Future Consideration:
- **Auto-refresh**: Should system auto-refresh when new filings detected?
  - *Recommendation*: Notify only, don't auto-refresh (cost consideration)

- **Scheduled updates**: Implement daily batch refresh for tracked companies?
  - *Recommendation*: Add in Phase 3+ with user opt-in

- **Company watchlist**: Let users "follow" specific companies?
  - *Recommendation*: Good feature for Phase 3+ UI redesign

---

## Appendix: Comparison with Original Proposal

| Aspect | Original Proposal | This Plan | Rationale |
|--------|------------------|-----------|-----------|
| **Phase 1 Scope** | "Quick Win (2-3 days)" but includes 4 major changes | Phase 0 (1-2 days) with 6 focused tasks | More realistic timeline |
| **Web Search** | Add to synthesis agent immediately | Defer to Phase 3+, handle at routing layer | Simpler, clearer boundaries |
| **Staleness** | "How old is too old?" (unanswered) | Concrete thresholds (7/30/90 days) | Actionable guidance |
| **SEC Filing Check** | Call SEC API for latest filing dates | Use analysis timestamp from directory | Simpler, no external dependency |
| **UI Redesign** | Phase 1B (1 week) | Phase 3 (optional, 1-2 weeks) | De-risk, validate need first |
| **Multi-Company** | Phase 1A | Phase 2 (1 week) | More complex, needs Phase 0 foundation |

---

## Timeline Summary

- **Phase 0**: 1-2 days (Basic intelligence)
- **Phase 1**: 3-5 days (Smart routing)
- **Phase 2**: 1 week (Multi-company)
- **Phase 3**: 1-2 weeks (Optional UI redesign)

**Total**: 2-3 weeks for full implementation (excluding Phase 3)

---

## Approval & Next Steps

**Approved By**: [User]
**Date**: November 8, 2025
**Next Action**: Begin Phase 0 implementation

### Phase 0 Checklist:
- [ ] Enhance `chroma_manager.py` with status methods
- [ ] Add ticker extraction helper
- [ ] Enhance `web_app.py` KB query handler
- [ ] Add missing company detection
- [ ] Show data age in synthesis responses
- [ ] Add analysis date/age display in Gradio UI
- [ ] Test with existing analyses
- [ ] Verify no breaking changes

---

*This plan supersedes the original `UX_REDESIGN_PROPOSAL.md` with a more pragmatic, incremental approach.*
