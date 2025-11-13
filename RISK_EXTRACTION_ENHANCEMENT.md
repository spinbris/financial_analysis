# Risk Extraction Enhancement with EdgarTools

## Current State

Your [risk_agent_enhanced.py](financial_research_agent/agents/risk_agent_enhanced.py) currently uses **MCP server tools**:
- `search_10k(cik="AAPL", query="risk factors")`
- `search_10q(cik="AAPL", query="management discussion")`
- `get_recent_filings(cik="AAPL")`

These work, but have the same limitations as the financial_metrics_agent had:
- MCP server round-trips (slower)
- Search-based (may miss structured sections)
- Requires LLM to parse search results
- Less deterministic

## EdgarTools Risk Capabilities

EdgarTools provides **direct, structured access** to risk information:

### 1. Direct Section Extraction (Most Powerful)

```python
from edgar import Company

company = Company("AAPL")
filing = company.get_filings(form="10-K")[0]  # Latest 10-K

# Get structured filing object
filing_obj = filing.obj()

# Extract specific sections by Item number
risk_factors = filing_obj.get_section("1A")  # Item 1A = Risk Factors
legal_proceedings = filing_obj.get_section("3")  # Item 3 = Legal Proceedings
mda = filing_obj.get_section("7")  # Item 7 = MD&A

# Get text content
if risk_factors:
    risk_text = risk_factors.text
    risk_html = risk_factors.html
```

**Benefits:**
- ✅ Gets **complete** Risk Factors section (not search snippets)
- ✅ Structured extraction (knows section boundaries)
- ✅ Fast (direct access, no search needed)
- ✅ Deterministic (always same result)

### 2. Relevance-Ranked Search (Supplemental)

```python
# Search within filing for specific risks
results = filing.search("supply chain disruption")

for match in results[:5]:  # Top 5 by relevance
    print(f"Relevance: {match.score:.2f}")
    print(f"Context: {str(match)[:300]}")
```

**Use case:** Find mentions of specific risks across entire filing

### 3. Recent Filings for Material Events

```python
# Get recent 8-K filings
filings_8k = company.get_filings(form="8-K")

for filing in filings_8k[:5]:  # Last 5
    print(f"Date: {filing.filing_date}")
    print(f"Items: {filing.items}")  # 8-K item codes

    # Get filing content
    content = filing.markdown()  # or .html() or .text()
```

## Proposed Enhancement

### Option 1: Create Risk Extraction Tool (Recommended)

Similar to `extract_financial_metrics()`, create `extract_risk_factors()`:

```python
# financial_research_agent/tools/edgar_risk_extractor.py

from edgar import Company, set_identity
from typing import Dict
import os

class EdgarRiskExtractor:
    """Extract risk information directly from SEC filings using edgartools."""

    def __init__(self, identity: str = None):
        if identity is None:
            identity = os.getenv("EDGAR_IDENTITY", "User user@example.com")
        set_identity(identity)

    def extract_risk_factors(self, ticker: str) -> Dict:
        """
        Extract comprehensive risk information from SEC filings.

        Returns:
            Dict with:
            - risk_factors_10k: Complete Item 1A from annual report
            - risk_factors_10q: Risk updates from quarterly
            - legal_proceedings: Item 3 from 10-K
            - mda_risks: Risk mentions in MD&A
            - recent_8k: Material events from recent 8-Ks
        """
        company = Company(ticker)

        result = {
            'ticker': ticker,
            'company_name': company.name,
        }

        # 1. Get Risk Factors from latest 10-K (most comprehensive)
        try:
            filing_10k = company.get_filings(form="10-K")[0]
            filing_obj = filing_10k.obj()

            risk_section = filing_obj.get_section("1A")
            if risk_section:
                result['risk_factors_10k'] = {
                    'text': risk_section.text,
                    'filing_date': filing_10k.filing_date,
                    'period': filing_10k.period_of_report,
                    'form': '10-K',
                    'length_chars': len(risk_section.text),
                }

            # Also get legal proceedings (Item 3)
            legal_section = filing_obj.get_section("3")
            if legal_section:
                result['legal_proceedings'] = {
                    'text': legal_section.text,
                    'filing_date': filing_10k.filing_date,
                }

            # Get MD&A (Item 7) - contains operational risks
            mda_section = filing_obj.get_section("7")
            if mda_section:
                # Search for risk keywords within MD&A
                mda_text = mda_section.text
                result['mda'] = {
                    'text': mda_text[:10000],  # First 10k chars
                    'length_chars': len(mda_text),
                }
        except Exception as e:
            result['risk_factors_10k_error'] = str(e)

        # 2. Get Risk Factor updates from latest 10-Q
        try:
            filing_10q = company.get_filings(form="10-Q")[0]
            filing_obj_q = filing_10q.obj()

            # 10-Q Item 1A (if present - companies update risks quarterly)
            risk_section_q = filing_obj_q.get_section("1A")
            if risk_section_q:
                result['risk_factors_10q'] = {
                    'text': risk_section_q.text,
                    'filing_date': filing_10q.filing_date,
                    'period': filing_10q.period_of_report,
                    'form': '10-Q',
                }
        except Exception as e:
            result['risk_factors_10q_error'] = str(e)

        # 3. Get recent 8-K filings for material events
        try:
            filings_8k = company.get_filings(form="8-K")[:5]  # Last 5

            recent_events = []
            for filing in filings_8k:
                # Get filing summary
                event = {
                    'filing_date': str(filing.filing_date),
                    'items': getattr(filing, 'items', []),
                    'description': filing.description if hasattr(filing, 'description') else None,
                }

                # Get first 1000 chars of content
                try:
                    content = filing.text()
                    event['summary'] = content[:1000]
                except:
                    event['summary'] = None

                recent_events.append(event)

            result['recent_8k_filings'] = recent_events
        except Exception as e:
            result['recent_8k_error'] = str(e)

        # 4. Search for specific risk keywords across filings
        try:
            # Search latest 10-K for key risk areas
            risk_searches = [
                "supply chain",
                "cybersecurity",
                "regulatory",
                "litigation",
                "competition",
            ]

            search_results = {}
            for keyword in risk_searches:
                matches = filing_10k.search(keyword)
                if matches:
                    # Get top 3 matches
                    top_matches = [
                        {
                            'score': match.score,
                            'snippet': str(match)[:200]
                        }
                        for match in matches[:3]
                    ]
                    search_results[keyword] = top_matches

            result['risk_keyword_search'] = search_results
        except Exception as e:
            result['risk_search_error'] = str(e)

        return result


# Tool function for agent
from agents import function_tool

@function_tool
def extract_risk_factors(ticker: str) -> Dict:
    """
    Extract comprehensive risk information from SEC filings using edgartools.

    Provides:
    - Complete Item 1A Risk Factors from 10-K (annual)
    - Risk factor updates from 10-Q (quarterly)
    - Legal proceedings (Item 3)
    - MD&A risk discussions (Item 7)
    - Recent 8-K material events
    - Keyword search results for specific risks

    All extracted directly from SEC filings with exact text.
    """
    extractor = EdgarRiskExtractor()
    return extractor.extract_risk_factors(ticker)
```

### Option 2: Keep Current MCP Approach (Simpler)

Your current approach works fine if:
- ✅ MCP server handles rate limiting
- ✅ Search results are sufficient
- ✅ Don't need complete section text

## Comparison

| Aspect | Current (MCP) | Enhanced (EdgarTools) |
|--------|---------------|----------------------|
| **Data Source** | Search snippets | Complete sections |
| **Speed** | Slower (round-trips) | Faster (direct) |
| **Completeness** | Partial (search results) | Complete (full sections) |
| **Deterministic** | No (search varies) | Yes (structured) |
| **Code Complexity** | Simpler (just search) | More complex (section parsing) |
| **Best For** | Quick risk mentions | Comprehensive analysis |

## When to Enhance

Consider enhancing if:
- ✅ Want **complete** Risk Factors section (not snippets)
- ✅ Need deterministic extraction for testing
- ✅ Want to eliminate MCP dependency
- ✅ Analyzing risks systematically (not ad-hoc)
- ✅ Need to categorize/structure risks programmatically

Keep current approach if:
- ✅ Search snippets are sufficient
- ✅ MCP server already deployed
- ✅ Don't need complete section text
- ✅ Prefer simpler implementation

## Example Usage

**Current (MCP):**
```python
# Agent prompt instructs:
risk_factors = search_10k(cik="AAPL", query="risk factors")
# Returns: Search snippets mentioning "risk factors"
```

**Enhanced (EdgarTools):**
```python
# Agent uses tool:
risk_data = extract_risk_factors("AAPL")

# Returns complete structured data:
{
  'risk_factors_10k': {
    'text': '... complete 20,000 character Item 1A text ...',
    'filing_date': '2024-11-01',
    'length_chars': 20000
  },
  'legal_proceedings': { ... },
  'recent_8k_filings': [ ... ],
  'risk_keyword_search': {
    'supply chain': [{'score': 0.95, 'snippet': '...'}],
    'cybersecurity': [{'score': 0.89, 'snippet': '...'}]
  }
}
```

## Implementation Effort

**If you want to implement:**

1. **Create tool** (1 hour)
   - File: `financial_research_agent/tools/edgar_risk_extractor.py`
   - Copy pattern from `edgartools_wrapper.py`
   - Add `extract_risk_factors()` function tool

2. **Update risk agent** (30 minutes)
   - Add tool to `risk_agent_enhanced.py` imports
   - Update prompt to use tool
   - Keep MCP as fallback option

3. **Test** (30 minutes)
   - Test with AAPL, MSFT, TSLA
   - Compare output to current MCP approach
   - Verify completeness

**Total: ~2 hours**

## Recommendation

**For now: Keep current MCP approach** ✅

**Why:**
- Your risk agent already works well
- MCP search provides sufficient context
- Focus on higher-priority items first
- Can enhance later if needed

**Future enhancement priority: Medium**

Consider enhancing when:
- You notice incomplete risk coverage
- You want to automate risk categorization
- You're removing other MCP dependencies
- You need deterministic risk extraction for testing

## Quick Answer to Your Question

**"Does edgartools include any information on risks?"**

**Yes!** EdgarTools provides:
1. ✅ **Complete Risk Factors section** (Item 1A from 10-K/10-Q)
2. ✅ **Legal Proceedings** (Item 3)
3. ✅ **MD&A with risk discussions** (Item 7)
4. ✅ **Relevance-ranked search** for specific risks
5. ✅ **Recent 8-K filings** for material events

Your risk agent **could** use these directly (like we did for financial_metrics), but your current MCP search approach is working fine, so it's **optional, not critical**.

---

**Priority:** Low (current approach works)
**Effort:** 2 hours if you want to implement
**Benefit:** Complete risk sections instead of search snippets
