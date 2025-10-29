# Financial Metrics & Ratio Analysis Guide

## Overview

The Financial Metrics Agent automatically extracts complete financial statements from SEC EDGAR filings and calculates comprehensive financial ratios for liquidity, solvency, profitability, and efficiency analysis.

## Features

### Automatic Financial Statement Extraction

The agent retrieves complete financial statements with XBRL precision:
- **Balance Sheet**: All assets, liabilities, and equity line items
- **Income Statement**: Revenue through net income with all intermediate values
- **Cash Flow Statement**: Operating, investing, and financing activities

### Comprehensive Ratio Analysis

Automatically calculates and interprets 17 key financial ratios across four categories:

#### 1. Liquidity Ratios (Short-term Financial Health)
- **Current Ratio**: Current Assets ÷ Current Liabilities
  - Target: > 1.0 (can meet short-term obligations)
- **Quick Ratio**: (Current Assets - Inventory) ÷ Current Liabilities
  - Target: > 1.0 (can meet obligations without selling inventory)
- **Cash Ratio**: Cash & Equivalents ÷ Current Liabilities
  - Target: > 0.2 (adequate cash reserves)

#### 2. Solvency Ratios (Long-term Financial Stability)
- **Debt-to-Equity**: Total Debt ÷ Total Shareholders' Equity
  - Lower is better; < 2.0 generally acceptable
- **Debt-to-Assets**: Total Debt ÷ Total Assets
  - Target: < 0.5 (conservative leverage)
- **Interest Coverage**: EBIT ÷ Interest Expense
  - Target: > 2.5 (can comfortably service debt)
- **Equity Ratio**: Total Equity ÷ Total Assets
  - Target: > 0.5 (strong equity position)

#### 3. Profitability Ratios (Earnings Generation)
- **Gross Profit Margin**: Gross Profit ÷ Revenue
  - Varies by industry; higher is better
- **Operating Margin**: Operating Income ÷ Revenue
  - Indicates operational efficiency
- **Net Profit Margin**: Net Income ÷ Revenue
  - Bottom-line profitability
- **Return on Assets (ROA)**: Net Income ÷ Total Assets
  - Efficiency of asset utilization
- **Return on Equity (ROE)**: Net Income ÷ Shareholders' Equity
  - Return generated for shareholders

#### 4. Efficiency Ratios (Asset Management)
- **Asset Turnover**: Revenue ÷ Average Total Assets
  - How efficiently assets generate revenue
- **Inventory Turnover**: Cost of Goods Sold ÷ Average Inventory
  - How quickly inventory is sold
- **Receivables Turnover**: Revenue ÷ Average Accounts Receivable
  - How quickly receivables are collected
- **Days Sales Outstanding (DSO)**: (A/R ÷ Revenue) × Days in Period
  - Average collection period in days

## Output Files

The financial metrics agent generates two separate markdown files in each research session:

### 1. `03_financial_statements.md`

Complete financial statements in table format with XBRL precision:

```markdown
# Financial Statements

**Company:** Apple Inc.
**Period:** Q4 FY2024
**Filing:** 10-Q filed 2025-01-31, Accession: 0000320193-25-000006

## Consolidated Balance Sheet

| Line Item | Amount |
|-----------|--------|
| **Current Assets** | |
| Cash and cash equivalents | $29,943,000 |
| Marketable securities | $43,162,000 |
| ...continuing for all line items... |
```

**Purpose**: Authoritative source data for verification and detailed analysis

### 2. `04_financial_metrics.md`

Comprehensive ratio analysis with interpretations:

```markdown
# Financial Metrics & Ratio Analysis

**Company:** Apple Inc.
**Period:** Q4 FY2024

## Executive Summary

Apple demonstrates strong financial health with excellent liquidity...

## Liquidity Ratios

| Ratio | Value | Interpretation |
|-------|-------|----------------|
| Current Ratio | 1.05 | ✓ Healthy - can meet short-term obligations |
| Quick Ratio | 0.87 | ⚠ Below 1.0, typical for tech sector |
...continuing for all ratios...
```

**Purpose**: Analysis-ready metrics with professional interpretations

### 3. `05_financial_analysis.md`

Full comprehensive financial analysis (800-1200 words):

```markdown
# Comprehensive Financial Analysis

**Financial Health Rating:** Strong

## Executive Summary

Apple Inc. demonstrates exceptional financial performance in Q4 FY2024...

## Detailed Analysis

### Revenue Analysis
Total revenue for Q4 FY2024 was $119,575,000,000...

### Profitability Analysis
Gross profit margin of 44.3% reflects...

### Balance Sheet Strength
...continuing for 800-1200 words...
```

**Purpose**: In-depth financial narrative analysis from specialist agent

### 4. `06_risk_analysis.md`

Full comprehensive risk assessment (800-1200 words):

```markdown
# Comprehensive Risk Analysis

**Overall Risk Rating:** Moderate

## Executive Summary

Apple faces several material risks including supply chain concentration...

## Top 5 Risks (Prioritized)

1. Supply chain concentration in Asia-Pacific region
2. Regulatory scrutiny in App Store business model
3. Mature smartphone market saturation
4. Foreign exchange exposure
5. Competitive pressure in services segment

## Detailed Risk Analysis

### Strategic & Competitive Risks
The smartphone market has reached maturity...

### Operational Risks
Supply chain dependencies present...

...continuing for 800-1200 words...
```

**Purpose**: Comprehensive risk assessment from specialist agent

## Integration with Research Reports

The financial metrics agent integrates seamlessly with the research workflow:

### 1. Automatic Execution

When EDGAR integration is enabled, the financial metrics agent runs automatically after gathering EDGAR data:

```python
# In manager_enhanced.py
edgar_results = await self._gather_edgar_data(query, search_plan)
metrics_results = await self._gather_financial_metrics(query)  # Automatic
```

### 2. Available as Tool

The financial metrics agent is exposed as a tool to other agents:

```python
# Available to financials_agent_enhanced
financial_metrics_tool = financial_metrics_agent.clone(
    mcp_servers=[self.edgar_server]
).as_tool(
    tool_name="financial_metrics",
    tool_description="Extract financial statements and calculate ratios"
)
```

### 3. Referenced in Reports

The comprehensive report references the detailed files:

```markdown
## III. Financial Performance Analysis

Apple's Q4 FY2024 performance demonstrates strong profitability with a net margin
of 25.4% and ROE of 147.3% (detailed metrics available in 04_financial_metrics.md).

*Complete financial statements available in 03_financial_statements.md*
```

## File Numbering Structure

Research sessions now generate files in this order:

```
output/20251029_143022/
├── 00_query.md                      # Original user query
├── 01_search_plan.md                # Planned web searches
├── 02_search_results.md             # Web search findings
├── 02_edgar_filings.md              # SEC filing analysis
├── 03_financial_statements.md       # NEW: Complete statements (tables)
├── 04_financial_metrics.md          # NEW: Comprehensive ratio analysis
├── 05_financial_analysis.md         # NEW: Full 800-1200 word financial analysis
├── 06_risk_analysis.md              # NEW: Full 800-1200 word risk analysis
├── 07_comprehensive_report.md       # Final synthesized report (was 03)
└── 08_verification.md               # Quality check (was 04)
```

## Ratio Interpretation Symbols

The metrics file uses visual indicators for quick assessment:

- **✓** = Healthy/Strong (meets or exceeds industry standards)
- **⚠** = Moderate/Adequate (acceptable but below optimal)
- **✗** = Concerning/Weak (below standards or indicating issues)
- **-** = Data unavailable or ratio not applicable

## Example Use Cases

### 1. Quick Financial Health Check

```bash
python -m financial_research_agent.main_enhanced
Query: Apple financial health

# Output includes:
# - 03_financial_statements.md (detailed statements)
# - 04_financial_metrics.md (all ratios with interpretations)
# - 05_comprehensive_report.md (synthesized analysis)
```

### 2. Multi-Company Comparison

```bash
Query: Compare Apple and Microsoft financial metrics

# Each company's metrics saved in separate session directories
# Easy to cross-reference ratios side-by-side
```

### 3. Trend Analysis

```bash
Query: Tesla Q4 2024 vs Q3 2024 financial performance

# Ratios calculated for both periods
# YoY and QoQ comparisons included
```

## Data Accuracy & Citations

All financial data:
- ✅ Extracted from official SEC EDGAR filings
- ✅ Uses XBRL precision (no rounding from source)
- ✅ Includes filing references (form type, date, accession number)
- ✅ Citable for professional research

Example citation:
```
Revenue of $119,575,000,000 per 10-Q filed January 31, 2025,
Accession: 0000320193-25-000006
```

## Technical Implementation

### Agent Architecture

```python
# agents/financial_metrics_agent.py
class FinancialMetrics(BaseModel):
    # Executive summary
    executive_summary: str

    # 17 financial ratios (liquidity, solvency, profitability, efficiency)
    current_ratio: float | None
    debt_to_equity: float | None
    # ... all ratios ...

    # Complete statements
    balance_sheet: dict[str, Any]
    income_statement: dict[str, Any]
    cash_flow_statement: dict[str, Any]

    # Metadata
    period: str
    filing_reference: str
    calculation_notes: list[str]
```

### Formatting Utilities

```python
# formatters.py
format_financial_statements(...)  # Creates 03_financial_statements.md
format_financial_metrics(...)     # Creates 04_financial_metrics.md

# Helper functions:
format_currency(value)           # "$1,234,567"
format_percentage(value)         # "44.3%"
format_ratio(value)              # "1.05"
get_ratio_interpretation(...)    # "✓ Healthy"
```

## Configuration

Financial metrics are automatically enabled when:

```bash
# .env or .env.budget
ENABLE_EDGAR_INTEGRATION=true
SEC_EDGAR_USER_AGENT="YourCompany/1.0 (your-email@example.com)"
```

No additional configuration required - the feature activates automatically with EDGAR integration.

## Cost Impact

### Budget Mode
- Metrics extraction: **gpt-4.1** (~$0.03-0.05 per company)
- Total per report: **~$0.22-0.25** (including all analysis)

### Standard Mode
- Metrics extraction: **gpt-4.1** (~$0.03-0.05 per company)
- Total per report: **~$0.43-0.46** (including all analysis)

**Impact**: Minimal cost increase (~$0.03) for substantial value-add

## Benefits

1. **Time Savings**: Automatic extraction and calculation vs manual work
2. **Accuracy**: XBRL precision, no transcription errors
3. **Completeness**: 17 ratios across 4 categories every time
4. **Consistency**: Standardized format and interpretations
5. **Professional**: Investment-grade analysis suitable for presentations
6. **Traceable**: Every number citable with filing reference

## Limitations

### Known Edge Cases

1. **Service Companies**: May lack inventory data (affects quick ratio, inventory turnover)
2. **Financial Institutions**: Different balance sheet structure (agent notes this)
3. **Debt-Free Companies**: Interest coverage undefined (marked as N/A)
4. **Multi-Currency**: All figures in USD as reported to SEC
5. **Restatements**: Uses most recent filing; check for restatement notes

### Calculation Notes

The agent automatically adds notes when:
- Ratios cannot be calculated (missing data)
- Alternative calculations used
- Special circumstances apply

Example:
```
Calculation Notes:
- Quick ratio not calculated: inventory data unavailable (service company)
- Interest coverage not applicable: zero interest expense (debt-free)
```

## Troubleshooting

### Issue: No financial statements generated

**Solution**: Ensure EDGAR integration is enabled and functioning:
```bash
# Check configuration
echo $ENABLE_EDGAR_INTEGRATION  # Should be "true"
echo $SEC_EDGAR_USER_AGENT      # Should be valid format

# Test EDGAR connection
uvx sec-edgar-mcp  # Should download/run successfully
```

### Issue: Ratios show as "N/A"

**Cause**: Missing data in financial statements

**Resolution**: Check calculation notes in 04_financial_metrics.md for explanation

### Issue: Wrong company analyzed

**Cause**: Query ambiguity (e.g., "Apple" could be Apple Inc. or Apple Bank)

**Solution**: Use full company name or ticker symbol:
```bash
Query: Apple Inc (AAPL) financial metrics  # Unambiguous
```

## Future Enhancements

Potential additions (not yet implemented):

- [ ] Multi-period ratio comparison tables
- [ ] Industry benchmarking (median ratios for sector)
- [ ] Historical ratio trending (last 8 quarters)
- [ ] Alert thresholds (flag ratios outside norms)
- [ ] Peer comparison ratios (vs competitors)
- [ ] Custom ratio definitions (user-defined calculations)

## Examples

See example outputs in:
- `financial_research_agent/output/` (actual research sessions)
- Look for `03_financial_statements.md` and `04_financial_metrics.md` in any timestamped directory

## Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common problems
2. Review [EDGAR_INTEGRATION_GUIDE.md](./EDGAR_INTEGRATION_GUIDE.md) for setup issues
3. Open an issue on GitHub with:
   - Query used
   - Error message
   - Relevant log output

---

*This feature was added to provide comprehensive, automated financial ratio analysis as part of the investment-grade research reports.*
