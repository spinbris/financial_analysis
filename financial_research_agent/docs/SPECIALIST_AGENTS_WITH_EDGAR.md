# Specialist Agents with EDGAR Access

## Overview

The enhanced implementation gives **specialist agents** (financials and risk) direct access to SEC EDGAR tools, enabling them to analyze official filings when performing their specialized analysis.

## Architecture

### Without EDGAR (Original)
```
Writer Agent
    ├─ fundamentals_analysis tool
    │   └─ Financials Agent (web search data only)
    │
    └─ risk_analysis tool
        └─ Risk Agent (web search data only)
```

### With EDGAR (Enhanced)
```
Writer Agent
    ├─ fundamentals_analysis tool
    │   └─ Financials Agent + EDGAR MCP Server
    │       ├─ get_company_facts
    │       ├─ get_financial_statements
    │       ├─ get_filing_content
    │       └─ [all other EDGAR tools]
    │
    ├─ risk_analysis tool
    │   └─ Risk Agent + EDGAR MCP Server
    │       ├─ get_filing_content (Item 1A Risk Factors)
    │       ├─ get_recent_filings (8-K material events)
    │       ├─ search_10k (MD&A section)
    │       └─ [all other EDGAR tools]
    │
    └─ sec_filing_analysis tool
        └─ EDGAR Agent + EDGAR MCP Server (dedicated filing analysis)
```

## Why This Matters

### Risk Agent Benefits

SEC filings contain **extensive risk disclosures** that are legally required and highly detailed:

**Item 1A: Risk Factors** (from 10-K/10-Q)
- Pages of detailed risk disclosures
- Updated quarterly/annually
- Covers all material risks
- Legally binding (companies must disclose)

**8-K Filings: Material Events**
- Filed within 4 days of material events
- Covers: acquisitions, leadership changes, legal issues, etc.
- Real-time risk indicators

**Example Risk Factors from Apple 10-K:**
```
Item 1A. Risk Factors

The Company's business, reputation, results of operations and financial
condition can be adversely affected by various factors...

- The Company depends on component and product manufacturing and logistical
  services provided by outsourcing partners...

- The Company's business requires it to use and store confidential information...

- Global markets for the Company's products and services are highly competitive...
```

**What Risk Agent Can Now Do:**
```python
# When writer calls risk_analysis tool, the Risk Agent can:
1. Query get_filing_content("AAPL", "10-K", section="Item 1A")
2. Extract official risk factors
3. Check recent 8-K filings for material events
4. Review MD&A for management's risk commentary
5. Cite specific sections: "Per Item 1A of 10-K filed 2024-11-01..."
```

### Financials Agent Benefits

SEC filings have **exact financial data** with XBRL precision:

**Financial Statements (from 10-K/10-Q)**
- Balance Sheet
- Income Statement
- Cash Flow Statement
- All with exact XBRL values

**Segment Breakdowns**
- Revenue by product line
- Revenue by geography
- Detailed segment reporting

**Year-over-Year Comparisons**
- Multi-year trend data
- Historical financials

**Example Financial Data:**
```
Revenue (exact from XBRL): $119,575,000,000
Not rounded: $119.6B or $120B
Exactly as filed: $119,575,000,000
```

**What Financials Agent Can Now Do:**
```python
# When writer calls fundamentals_analysis tool, the Financials Agent can:
1. Query get_financial_statements("AAPL", "10-Q", "latest")
2. Extract exact revenue, net income, margins
3. Compare Q4 2024 vs Q4 2023 (YoY)
4. Extract segment breakdowns (iPhone, Services, Mac, etc.)
5. Cite: "Revenue of $119,575,000,000 per 10-Q filed 2025-01-31"
```

## Implementation Details

### Agent Cloning with MCP Servers

```python
# In manager_with_edgar.py, line 284-298

if self.edgar_enabled and self.edgar_server:
    # Clone specialist agents with EDGAR access
    financials_with_edgar = financials_agent.clone(
        mcp_servers=[self.edgar_server]
    )
    risk_with_edgar = risk_agent.clone(
        mcp_servers=[self.edgar_server]
    )

    # Convert to tools
    fundamentals_tool = financials_with_edgar.as_tool(
        tool_name="fundamentals_analysis",
        tool_description="Use to get a short write-up of key financial metrics from SEC filings and research",
        custom_output_extractor=_summary_extractor,
    )
    risk_tool = risk_with_edgar.as_tool(
        tool_name="risk_analysis",
        tool_description="Use to get a short write-up of potential red flags from SEC Risk Factors and research",
        custom_output_extractor=_summary_extractor,
    )
```

### Enhanced Agent Prompts

**Risk Agent** ([risk_agent.py](agents/risk_agent.py)):
```python
RISK_PROMPT = """You are a risk analyst...

When SEC EDGAR tools are available, prioritize using official filings:
- Item 1A "Risk Factors" section from 10-K/10-Q filings
- Recent 8-K filings for material events
- Management's Discussion and Analysis (MD&A) sections

Focus on:
- Competitive threats and market position
- Regulatory issues and legal proceedings
- Supply chain vulnerabilities
- Financial risks (debt, liquidity, currency exposure)
- Operational risks (cybersecurity, key personnel)
..."""
```

**Financials Agent** ([financials_agent.py](agents/financials_agent.py)):
```python
FINANCIALS_PROMPT = """You are a financial analyst...

When SEC EDGAR tools are available, prioritize using official filings for exact data:
- Financial statements from 10-K (annual) and 10-Q (quarterly) filings
- Use XBRL data for precise figures (no rounding)
- Extract key metrics: revenue, net income, gross profit, operating margins, EPS
- Compare year-over-year and quarter-over-quarter growth
..."""
```

## Tool Flow Example

### Query: "Analyze Apple's Q4 2024 performance and risks"

**Step 1: Writer Agent receives query**
```
Writer has tools:
- fundamentals_analysis
- risk_analysis
- sec_filing_analysis
```

**Step 2: Writer calls fundamentals_analysis**
```python
# Writer agent decides to analyze fundamentals
writer.call_tool("fundamentals_analysis", {
    "context": "Apple Q4 2024, search results: ..."
})

# Financials Agent (with EDGAR) executes:
1. Reviews web search data
2. Calls get_company_facts("AAPL")
3. Calls get_financial_statements("AAPL", "10-Q", "latest")
4. Extracts exact revenue: $119,575,000,000
5. Compares to Q4 2023: $117,154,000,000 (+2.1% YoY)
6. Returns: "Apple reported Q4 2024 revenue of $119,575,000,000,
   up 2.1% YoY (per 10-Q filed 2025-01-31)..."
```

**Step 3: Writer calls risk_analysis**
```python
# Writer agent decides to analyze risks
writer.call_tool("risk_analysis", {
    "context": "Apple Q4 2024, search results: ..."
})

# Risk Agent (with EDGAR) executes:
1. Reviews web search data
2. Calls get_filing_content("AAPL", "10-K", section="Item 1A")
3. Extracts top risk factors:
   - Component supply chain dependencies
   - Intense competition in smartphone market
   - Cybersecurity and data privacy
4. Checks recent 8-K filings for material events
5. Returns: "Key risks include supply chain concentration
   (per Item 1A of 10-K filed 2024-11-01), particularly
   dependence on Taiwan-based semiconductor manufacturers..."
```

**Step 4: Writer synthesizes final report**
```markdown
# Apple Inc. Q4 2024 Analysis

## Financial Performance
Apple reported strong Q4 2024 results with revenue of $119,575,000,000,
representing 2.1% year-over-year growth (per 10-Q filed 2025-01-31)...
[Uses exact data from Financials Agent]

## Risk Factors
Primary risks include supply chain concentration, particularly dependence
on Taiwan-based semiconductor manufacturers (per Item 1A of 10-K filed
2024-11-01)...
[Uses official risk disclosures from Risk Agent]
```

## Comparison: Before vs After

### Before (No EDGAR Access for Specialist Agents)

**Financials Agent:**
- Source: Web search results only
- Data: Third-party estimates, analyst reports
- Precision: Rounded numbers ($119.6B)
- Citation: "According to TechCrunch..."

**Risk Agent:**
- Source: News articles about risks
- Coverage: Partial, based on what media reports
- Authority: Journalist interpretations
- Citation: "Bloomberg reports concerns about..."

### After (EDGAR Access for Specialist Agents)

**Financials Agent:**
- Source: Official SEC 10-Q filing + web search
- Data: Exact XBRL values
- Precision: $119,575,000,000 (exact)
- Citation: "Per 10-Q filed 2025-01-31, Accession: ..."

**Risk Agent:**
- Source: Official Item 1A Risk Factors + 8-K filings + web search
- Coverage: Complete, legally mandated disclosures
- Authority: Company's own risk assessment
- Citation: "Per Item 1A of 10-K filed 2024-11-01..."

## Benefits

### 1. Authoritative Analysis
✅ Specialist agents cite official sources
✅ Risk factors directly from company disclosures
✅ Financial data exactly as filed with SEC

### 2. Reduced Hallucination
✅ Deterministic data from XBRL
✅ No reliance on potentially inaccurate web sources
✅ Clear distinction between official vs. commentary

### 3. Comprehensive Coverage
✅ Risk agent has access to ALL risk factors (Item 1A is comprehensive)
✅ Financials agent has complete financial statements
✅ Both agents can cross-reference multiple filings

### 4. Better Citations
✅ "Per Item 1A of 10-K filed 2024-11-01"
✅ "Revenue of $119,575,000,000 per 10-Q filed 2025-01-31"
✅ Direct SEC URLs for verification

### 5. Flexibility
✅ Agents decide when to use EDGAR vs web data
✅ Can combine multiple sources
✅ Tool filtering allows limiting EDGAR access if needed

## Tool Availability

When specialist agents have EDGAR access, they can use **all EDGAR tools**:

### Company Information
- `get_company_facts` - Company data and CIK lookup
- `get_recent_filings` - Recent SEC filings list

### Filing Content
- `get_filing_content` - Full filing or specific sections
- `search_10k` - Search annual reports
- `search_10q` - Search quarterly reports

### Financial Data
- `get_financial_statements` - Complete financials with XBRL
- Extract exact metrics: revenue, net income, margins, EPS, etc.

### Risk & Events
- `get_filing_content` with `section="Item 1A"` - Risk Factors
- `get_recent_filings` filtered by form `8-K` - Material events
- `get_insider_transactions` - Forms 3, 4, 5

## Configuration

Specialist agents automatically get EDGAR access when:

```bash
# In .env
ENABLE_EDGAR_INTEGRATION=true
SEC_EDGAR_USER_AGENT=YourCompany/1.0 (you@email.com)
```

No additional configuration needed! The manager handles it automatically.

## Performance Considerations

### Token Usage
- **Increase:** ~20-30% due to richer EDGAR data
- **Benefit:** Much higher quality analysis

### Latency
- **Financials Agent:** +2-4 seconds (if querying filings)
- **Risk Agent:** +2-4 seconds (if querying filings)
- **Total:** Minimal impact (agents run as tools, so it's inline with writer)

### API Calls
- **SEC EDGAR:** Free, no API key needed
- **Rate Limit:** 10 requests/second (built-in handling)
- **OpenAI:** Standard agent tool call costs

## Best Practices

### For Risk Analysis

**Do:**
✅ Query Item 1A for comprehensive risk factors
✅ Check recent 8-K filings for material events
✅ Review MD&A for management's risk commentary
✅ Cite specific sections and filing dates

**Don't:**
❌ Rely solely on news articles for risk analysis
❌ Skip verifying risks against official filings
❌ Ignore recent 8-K material event disclosures

### For Financial Analysis

**Do:**
✅ Use XBRL data for exact financial metrics
✅ Compare current vs. prior periods (YoY, QoQ)
✅ Extract segment breakdowns when available
✅ Cite filing dates and accession numbers

**Don't:**
❌ Use rounded numbers when exact data available
❌ Rely on third-party financial aggregators
❌ Ignore official financial statement notes

## Example Outputs

### Risk Agent with EDGAR Access
```
Based on Apple Inc.'s 10-K filed November 1, 2024 (Accession: 0000320193-24-000123),
key risk factors include:

1. Supply Chain Concentration: The company depends significantly on outsourcing
   partners, particularly for component manufacturing and assembly, primarily
   located in Asia. Any disruption could materially impact production (Item 1A).

2. Competitive Intensity: The markets for smartphones, tablets, and personal
   computers are highly competitive, with pressure from competitors in China
   and established technology companies (Item 1A).

Additionally, a recent 8-K filed December 15, 2024, disclosed a major
restructuring of operations in Europe, which may involve integration risks.
```

### Financials Agent with EDGAR Access
```
Apple Inc. reported Q4 FY2024 revenue of $119,575,000,000, up 2.1% from
$117,154,000,000 in Q4 FY2023 (per 10-Q filed January 31, 2025). Net income
was $33,916,000,000 with operating margins of 28.4%. Revenue breakdown by
segment: iPhone ($69.7B), Services ($23.1B), Mac ($7.6B), iPad ($6.4B),
Wearables ($12.8B). The Services segment showed the strongest growth at
+16% YoY, while iPhone revenue declined 1% YoY, reflecting market saturation
concerns noted in the MD&A section.
```

## Migration Notes

This enhancement is **backward compatible**:

- If `ENABLE_EDGAR_INTEGRATION=false`, agents work as before
- If `ENABLE_EDGAR_INTEGRATION=true`, agents get EDGAR access automatically
- No code changes needed in specialist agent definitions
- Prompts are enhanced to guide EDGAR usage when available

## Future Enhancements

### Short Term
1. **Tool call tracking** - Log which EDGAR tools each agent uses
2. **Performance metrics** - Track EDGAR vs web data usage
3. **Selective EDGAR** - Different tool filters per agent

### Long Term
1. **Caching** - Cache frequently accessed filings
2. **Specialized extractors** - Industry-specific risk/metric extraction
3. **Multi-filing synthesis** - Trend analysis across multiple quarters/years
4. **Agent learning** - Improve tool selection over time

## Summary

By giving specialist agents direct access to EDGAR tools:

✅ **Risk Agent** can analyze official Item 1A Risk Factors and 8-K events
✅ **Financials Agent** can extract exact XBRL financial data
✅ **Both agents** cite authoritative sources with filing references
✅ **Writer Agent** receives higher quality specialist analysis
✅ **Final reports** are more accurate, verifiable, and comprehensive

This creates a **multi-layered research system** where:
1. Web search provides recent news and context
2. EDGAR provides authoritative official data
3. Specialist agents synthesize both sources
4. Writer orchestrates comprehensive analysis

The result: **Financial research reports backed by official SEC filings with exact figures and verifiable citations.**
