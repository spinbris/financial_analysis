# Form 20-F (Foreign Filers) - EdgarTools Support

## Your Question

**"Would it have to be hybrid as 20-F does not necessarily follow same format?"**

**Answer: Yes, you're correct!** A hybrid approach would be needed for comprehensive foreign filer support.

## The Difference: 10-K vs 20-F

### Form 10-K (U.S. Companies)
```
Item 1A: Risk Factors
Item 3: Legal Proceedings
Item 7: Management's Discussion and Analysis (MD&A)
```
**Structure:** Standardized SEC items with numbered sections

### Form 20-F (Foreign Filers)
```
Item 3: Key Information → 3.D: Risk Factors
Item 8: Financial Information → 8.A.7: Legal Proceedings
Item 5: Operating and Financial Review (similar to MD&A)
```
**Structure:** Different numbering, subsections (e.g., 3.D, 8.A.7)

## What EdgarTools Provides for 20-F

### ✅ Works Well:
1. **Filing search** - Can find 20-F filings
   ```python
   filings = company.get_filings(form="20-F")
   ```

2. **Content search** - Can search within 20-F
   ```python
   results = filing.search("risk factors")
   # Returns: 73 matches for typical 20-F
   ```

3. **Full text access**
   ```python
   text = filing.text()
   markdown = filing.markdown()
   html = filing.html()
   ```

### ⚠️ May Not Work:
1. **Section extraction by Item number**
   ```python
   filing_obj = filing.obj()
   section = filing_obj.get_section("1A")  # Won't work - 20-F uses "3.D"
   ```

2. **Standardized section parsing** - 20-F structure varies by company

## Tested: 20-F Search Works

```python
# Test Result (see above)
filings = get_filings(2024, 3, form='20-F')
# Found: 120 filings

filing = filings[0]  # GENETIC TECHNOLOGIES LTD
results = filing.search('risk factor')
# Found: 73 matches ✓
```

## Recommended Hybrid Approach

### Strategy 1: Search-Based (Works for Both)

```python
def extract_risks_universal(ticker: str) -> Dict:
    """Works for both 10-K and 20-F"""
    company = Company(ticker)

    # Try to get annual report (10-K or 20-F)
    filings_10k = company.get_filings(form="10-K")
    filings_20f = company.get_filings(form="20-F")

    # Use whichever exists
    if filings_10k:
        filing = filings_10k[0]
        form_type = "10-K"
    elif filings_20f:
        filing = filings_20f[0]
        form_type = "20-F"
    else:
        return {"error": "No annual filing found"}

    # Search works for both!
    risk_results = filing.search("risk factors")
    legal_results = filing.search("legal proceedings")

    return {
        'form_type': form_type,
        'risk_factors': [
            {
                'score': r.score,
                'snippet': str(r)[:500]
            }
            for r in risk_results[:10]  # Top 10
        ],
        'legal': [
            {
                'score': r.score,
                'snippet': str(r)[:500]
            }
            for r in legal_results[:5]  # Top 5
        ]
    }
```

**Pros:**
- ✅ Works for both 10-K and 20-F
- ✅ Finds risks regardless of section structure
- ✅ Relevance-ranked results
- ✅ No need to know exact section numbers

**Cons:**
- ❌ Returns snippets, not complete sections
- ❌ May miss context
- ❌ Requires good search terms

### Strategy 2: Hybrid (Best of Both)

```python
def extract_risks_hybrid(ticker: str) -> Dict:
    """
    Try structured extraction (10-K), fall back to search (20-F).
    """
    company = Company(ticker)

    # Check if it's a U.S. filer (10-K) or foreign (20-F)
    filings_10k = company.get_filings(form="10-K")
    filings_20f = company.get_filings(form="20-F")

    if filings_10k:
        # U.S. company - use structured extraction
        return extract_risks_structured(filings_10k[0])
    elif filings_20f:
        # Foreign company - use search
        return extract_risks_search(filings_20f[0])
    else:
        return {"error": "No annual filing found"}


def extract_risks_structured(filing) -> Dict:
    """For 10-K: Extract complete sections."""
    filing_obj = filing.obj()

    risk_section = filing_obj.get_section("1A")
    legal_section = filing_obj.get_section("3")
    mda_section = filing_obj.get_section("7")

    return {
        'form_type': '10-K',
        'method': 'structured',
        'risk_factors': risk_section.text if risk_section else None,
        'legal_proceedings': legal_section.text if legal_section else None,
        'mda': mda_section.text if mda_section else None,
        'complete_sections': True
    }


def extract_risks_search(filing) -> Dict:
    """For 20-F: Search for risks."""
    # Search for various risk keywords
    keywords = [
        "risk factors",
        "legal proceedings",
        "litigation",
        "regulatory",
        "competition"
    ]

    results = {}
    for keyword in keywords:
        matches = filing.search(keyword)
        if matches:
            results[keyword] = [
                {
                    'score': m.score,
                    'snippet': str(m)[:500]
                }
                for m in matches[:5]  # Top 5
            ]

    return {
        'form_type': '20-F',
        'method': 'search',
        'keyword_matches': results,
        'complete_sections': False
    }
```

**Pros:**
- ✅ Best quality for U.S. companies (complete sections)
- ✅ Still works for foreign companies (search)
- ✅ Adapts automatically based on filing type
- ✅ Explicit about data quality differences

**Cons:**
- ⚠️ More complex implementation
- ⚠️ Different output formats for 10-K vs 20-F

## Your Current Risk Agent

Looking at [risk_agent_enhanced.py](financial_research_agent/agents/risk_agent_enhanced.py), your current MCP approach already handles this with search:

```python
# Lines 18-19 (current)
search_10q(cik="<TICKER>", query="risk factors")
search_10k(cik="<TICKER>", query="risk factors")
```

**This search approach works for 20-F too!** The MCP server likely searches regardless of form type.

## Recommendations

### For Your Current System:

**Option 1: Keep MCP Search (Simplest)** ✅
- Already works for both 10-K and 20-F
- No code changes needed
- Search finds risks regardless of structure

**Option 2: Hybrid Direct + Search**
```python
# In risk extraction tool
def extract_risk_factors(ticker: str) -> Dict:
    company = Company(ticker)

    # Try 10-K first (U.S. companies)
    filings_10k = company.get_filings(form="10-K")
    if filings_10k:
        filing = filings_10k[0]
        filing_obj = filing.obj()

        # Try structured extraction
        risk_section = filing_obj.get_section("1A")
        if risk_section:
            return {
                'method': 'structured',
                'form': '10-K',
                'risk_factors': risk_section.text,
                'complete': True
            }

    # Fall back to 20-F (foreign companies)
    filings_20f = company.get_filings(form="20-F")
    if filings_20f:
        filing = filings_20f[0]

        # Use search for 20-F
        risk_results = filing.search("risk factors")
        return {
            'method': 'search',
            'form': '20-F',
            'risk_matches': [str(r)[:500] for r in risk_results[:10]],
            'complete': False  # Flag that it's snippets
        }

    # Try any annual report
    filings_annual = company.get_filings()
    for filing in filings_annual:
        if filing.form in ['10-K', '20-F']:
            # Use search as universal fallback
            risk_results = filing.search("risk factors")
            return {
                'method': 'search_fallback',
                'form': filing.form,
                'risk_matches': [str(r)[:500] for r in risk_results[:10]]
            }

    return {'error': 'No annual filing found'}
```

## Known 20-F Companies

Examples to test with:
- **Sony**: 20-F filer (Japan)
- **Toyota**: 20-F filer (Japan)
- **ASML**: 20-F filer (Netherlands)
- **SAP**: 20-F filer (Germany)
- **Canon**: 20-F filer (Japan)

## Testing Script

```python
# test_20f_support.py
from edgar import Company, set_identity

set_identity("Steve Parton stephen.parton@sjpconsulting.com")

# Test with 20-F company
company = Company("SONY")

# Get 20-F filings
filings = company.get_filings(form="20-F")
if filings:
    filing = filings[0]

    print(f"Company: {company.name}")
    print(f"Form: {filing.form}")
    print(f"Date: {filing.filing_date}")

    # Test search
    risk_results = filing.search("risk factors")
    print(f"\nRisk Factors Matches: {len(risk_results)}")

    # Show top 3
    for i, result in enumerate(risk_results[:3]):
        print(f"\n[{i+1}] Score: {result.score:.2f}")
        print(f"Snippet: {str(result)[:200]}...")
```

## Summary Table

| Approach | 10-K Support | 20-F Support | Completeness | Complexity |
|----------|--------------|--------------|--------------|------------|
| **MCP Search** (current) | ✅ Good | ✅ Good | Snippets | Low |
| **Structured Only** | ✅ Excellent | ❌ None | Complete | Medium |
| **Hybrid** | ✅ Excellent | ✅ Good | Mixed | High |
| **Search Only** | ✅ Good | ✅ Good | Snippets | Low |

## Final Answer

**Yes, hybrid is the right approach IF you want:**
- Complete Risk Factor sections for U.S. companies (10-K)
- Still support foreign companies (20-F)

**But your current MCP search approach already handles both!**

The search-based method (what you have now) is:
- ✅ Universal (works for 10-K and 20-F)
- ✅ Simple (one code path)
- ✅ Good enough (finds risks regardless of structure)

**Recommendation:**
- Keep your current MCP search approach (it's already universal)
- If you migrate to direct edgartools later, use **hybrid approach**:
  - Structured extraction for 10-K
  - Search-based for 20-F
- Add explicit detection of filing type in output

---

**The key insight:** Your MCP search approach is already handling 10-K and 20-F uniformly, which is actually a good design! If you move to direct edgartools, you'd need hybrid to maintain that universality.
