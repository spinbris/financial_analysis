"""
Smart routing and intelligence layer for RAG queries.

This module determines whether to route queries to RAG or suggest running
a deep analysis based on KB status.
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class QueryDecision(BaseModel):
    """Decision about how to handle a user query."""

    action: Literal["proceed_with_rag", "suggest_analysis", "mixed_quality"] = Field(
        description="What action to take with this query"
    )

    missing_tickers: list[str] = Field(
        default_factory=list,
        description="Tickers not in KB"
    )

    stale_tickers: list[str] = Field(
        default_factory=list,
        description="Tickers with stale data (>30 days for volatile, >90 days for stable)"
    )

    fresh_tickers: list[str] = Field(
        default_factory=list,
        description="Tickers with fresh data"
    )

    data_quality_warning: str | None = Field(
        default=None,
        description="Warning message about data quality if applicable"
    )

    suggested_action: str | None = Field(
        default=None,
        description="Suggested next step for user"
    )


def decide_query_routing(
    detected_tickers: list[str],
    chroma_manager,
    require_fresh: bool = False
) -> QueryDecision:
    """
    Decide how to route a query based on KB status of detected tickers.

    Args:
        detected_tickers: List of ticker symbols from query
        chroma_manager: FinancialRAGManager instance
        require_fresh: If True, flag data >7 days as stale (strict mode)

    Returns:
        QueryDecision with routing recommendation
    """
    if not detected_tickers:
        # No tickers detected - proceed with general RAG query
        return QueryDecision(
            action="proceed_with_rag",
            suggested_action="Query will search across all indexed companies"
        )

    # Check status of each ticker
    missing = []
    stale = []
    fresh = []

    for ticker in detected_tickers:
        status_info = chroma_manager.check_company_status(ticker)

        if not status_info["in_kb"]:
            missing.append(ticker)
        elif status_info["status"] == "stale":
            stale.append(ticker)
        elif status_info["status"] == "aging" and require_fresh:
            stale.append(ticker)  # Treat aging as stale in strict mode
        else:
            fresh.append(ticker)

    # Decision logic
    if missing:
        # Some or all tickers are missing
        if len(missing) == len(detected_tickers):
            # All tickers missing
            return QueryDecision(
                action="suggest_analysis",
                missing_tickers=missing,
                data_quality_warning=f"All requested companies ({', '.join(missing)}) are not in the knowledge base.",
                suggested_action=f"Run analysis for {', '.join(missing)} to answer this question."
            )
        else:
            # Partial data available
            return QueryDecision(
                action="mixed_quality",
                missing_tickers=missing,
                fresh_tickers=fresh,
                stale_tickers=stale,
                data_quality_warning=f"Some companies ({', '.join(missing)}) are not in the knowledge base.",
                suggested_action=f"Analyze {', '.join(missing)} for complete comparison, or proceed with partial data for {', '.join(fresh + stale)}."
            )

    if stale:
        # All data available but some is stale
        return QueryDecision(
            action="mixed_quality",
            stale_tickers=stale,
            fresh_tickers=fresh,
            data_quality_warning=f"Data for {', '.join(stale)} is stale (>30 days old).",
            suggested_action=f"Consider refreshing {', '.join(stale)} for most current information, or proceed with existing data."
        )

    # All tickers present and fresh
    return QueryDecision(
        action="proceed_with_rag",
        fresh_tickers=fresh,
        suggested_action="All data is fresh and ready for analysis"
    )


def format_query_decision_prompt(decision: QueryDecision, query: str, kb_companies: list[dict]) -> str:
    """
    Format a user-facing prompt based on query decision.

    Args:
        decision: QueryDecision from decide_query_routing()
        query: Original user query
        kb_companies: List of companies in KB (from get_companies_with_status())

    Returns:
        Markdown-formatted prompt for user
    """
    from financial_research_agent.rag.utils import format_company_status

    if decision.action == "proceed_with_rag":
        # No intervention needed - query can proceed
        return None

    if decision.action == "suggest_analysis":
        # All requested companies are missing
        if len(decision.missing_tickers) == 1:
            ticker = decision.missing_tickers[0]
            prompt = f"""## ⚠️ Company Not in Knowledge Base

**{ticker}** has not been analyzed yet and is not in the knowledge base.

### To answer your question: "{query}"

**Option 1: Run Analysis for {ticker}** (Recommended)
- Time: ~3-5 minutes
- Cost: ~$0.08
- Includes: Complete SEC filings, 118+ line items, risk analysis, and automatic KB indexing

**Option 2: Try Different Companies**
Query companies already in the knowledge base (see below)

---

### 📊 Companies Currently in Knowledge Base:

"""
            # Add up to 20 companies
            for company in kb_companies[:20]:
                prompt += f"- {format_company_status(company)}\n"

            if len(kb_companies) > 20:
                prompt += f"\n*...and {len(kb_companies) - 20} more companies*\n"

            prompt += f"\n---\n\n*Once {ticker} is analyzed, you can ask unlimited questions about it instantly!*"

            return prompt
        else:
            # Multiple missing tickers
            tickers = ", ".join(decision.missing_tickers)
            prompt = f"""## ⚠️ Multiple Companies Not in Knowledge Base

The following companies are not yet in the knowledge base:
**{tickers}**

### To answer your question: "{query}"

**Option 1: Analyze Each Company** (Recommended for accurate comparisons)
- Total time: ~{len(decision.missing_tickers) * 3}-{len(decision.missing_tickers) * 5} minutes
- Total cost: ~${len(decision.missing_tickers) * 0.08:.2f}
- Benefit: Complete, comparable data for all companies

**Option 2: Try Different Companies**
Query companies already in the knowledge base (see below)

---

### 📊 Companies Currently in Knowledge Base:

"""
            for company in kb_companies[:20]:
                prompt += f"- {format_company_status(company)}\n"

            if len(kb_companies) > 20:
                prompt += f"\n*...and {len(kb_companies) - 20} more companies*\n"

            prompt += "\n---\n\n*Tip: Build up your knowledge base over time by analyzing companies as needed!*"

            return prompt

    if decision.action == "mixed_quality":
        # Some data available, but quality issues
        prompt = f"""## 🔍 Data Quality Notice for: "{query}"

"""
        if decision.missing_tickers:
            prompt += f"### ❌ Missing from Knowledge Base:\n"
            for ticker in decision.missing_tickers:
                prompt += f"- **{ticker}** - Not analyzed yet\n"
            prompt += "\n"

        if decision.stale_tickers:
            prompt += f"### ⚠️ Stale Data (>30 days old):\n"
            # Get detailed status for stale tickers
            for ticker in decision.stale_tickers:
                prompt += f"- **{ticker}** - Data may be outdated\n"
            prompt += "\n"

        if decision.fresh_tickers:
            prompt += f"### ✅ Fresh Data Available:\n"
            for ticker in decision.fresh_tickers:
                prompt += f"- **{ticker}**\n"
            prompt += "\n"

        prompt += f"""---

### Your Options:

**1. Proceed with Available Data**
- Continue with partial/stale data (limited accuracy)
- Results may not reflect most recent performance

**2. Improve Data Quality** (Recommended)
"""

        if decision.missing_tickers:
            prompt += f"   - Analyze missing companies: {', '.join(decision.missing_tickers)}\n"
        if decision.stale_tickers:
            prompt += f"   - Refresh stale data: {', '.join(decision.stale_tickers)}\n"

        prompt += f"""
**3. Modify Query**
- Focus on companies with fresh data: {', '.join(decision.fresh_tickers) if decision.fresh_tickers else 'none available'}

---

*Recommendation: {decision.suggested_action}*
"""

        return prompt

    return None


def get_kb_summary_banner(chroma_manager) -> str:
    """
    Generate a summary banner of KB status for display in UI.

    Args:
        chroma_manager: FinancialRAGManager instance

    Returns:
        Markdown-formatted banner showing KB status
    """
    from financial_research_agent.rag.utils import format_company_status

    try:
        companies = chroma_manager.get_companies_with_status()

        if not companies:
            return """### 💾 Knowledge Base Status

**Empty** - No companies analyzed yet

*Run your first analysis to start building your knowledge base!*
"""

        # Count by status
        fresh_count = sum(1 for c in companies if c["status"] == "fresh")
        aging_count = sum(1 for c in companies if c["status"] == "aging")
        stale_count = sum(1 for c in companies if c["status"] == "stale")

        banner = f"""### 💾 Knowledge Base Status

**{len(companies)} Companies Indexed** | 🟢 Fresh: {fresh_count} | 🟡 Aging: {aging_count} | 🔴 Stale: {stale_count}

**Recently Updated:**
"""

        # Show top 5 most recent
        for company in companies[:5]:
            banner += f"\n- {format_company_status(company)}"

        if len(companies) > 5:
            banner += f"\n\n*...and {len(companies) - 5} more companies*"

        banner += "\n\n*💡 Tip: Click on any company ticker in the dropdown to view full reports*"

        return banner

    except Exception as e:
        return f"### 💾 Knowledge Base Status\n\n*Unable to load status: {str(e)}*"
