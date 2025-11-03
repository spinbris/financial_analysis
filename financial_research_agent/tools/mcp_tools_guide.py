"""
MCP Tools Documentation for SEC EDGAR Integration.

This module provides comprehensive documentation of available MCP tools
from the SEC EDGAR server, helping agents understand what tools they can use.
"""

from agents import function_tool


@function_tool
def get_available_edgar_tools() -> str:
    """
    Get comprehensive documentation of all available SEC EDGAR MCP tools.

    Returns detailed information about:
    - Tool names and purposes
    - Required parameters
    - Return value formats
    - Example usage
    - Best practices

    Use this when you need to know what SEC EDGAR tools are available
    or how to use a specific tool properly.

    Returns:
        Detailed documentation of all available SEC EDGAR MCP tools
    """
    return """# SEC EDGAR MCP Tools Documentation

## Overview

The SEC EDGAR MCP server provides tools to access official SEC filings and XBRL financial data.
These tools give you direct access to authoritative financial data with exact precision.

---

## Available Tools

### 1. **get_company_facts**
**Purpose:** Retrieve complete XBRL company facts for a specific company

**Parameters:**
- `cik` (string, required): Company CIK number (e.g., "0000320193" for Apple)
  - Can also accept ticker symbol which will be resolved to CIK
- `concept` (string, optional): Specific XBRL concept to retrieve (e.g., "Assets", "Revenue")
  - If omitted, returns ALL facts for the company

**Returns:**
- Complete XBRL financial data with exact values
- Multiple periods/dates for trend analysis
- All units and dimensions
- Typically 100+ data points per company

**Example Usage:**
```python
# Get all facts for Apple
get_company_facts(cik="0000320193")

# Get specific concept
get_company_facts(cik="0000320193", concept="Assets")

# Using ticker (will auto-resolve to CIK)
get_company_facts(cik="AAPL")
```

**Best Practice:**
- This is the PRIMARY tool for extracting financial statements
- Returns the most comprehensive data
- Use WITHOUT concept parameter to get complete financial picture
- Data comes directly from SEC XBRL with precision to the penny

---

### 2. **get_recent_filings**
**Purpose:** Find recent SEC filings for a company

**Parameters:**
- `cik` (string, required): Company CIK or ticker
- `form_type` (string, optional): Filter by form type (e.g., "10-K", "10-Q", "8-K")
- `limit` (integer, optional): Maximum number of filings to return (default: 10)

**Returns:**
- List of recent filings with:
  - Filing date
  - Form type (10-K, 10-Q, 8-K, etc.)
  - Accession number
  - Filing URL
  - Report date

**Example Usage:**
```python
# Get all recent filings
get_recent_filings(cik="TSLA")

# Get only quarterly reports
get_recent_filings(cik="TSLA", form_type="10-Q", limit=4)

# Get annual reports
get_recent_filings(cik="TSLA", form_type="10-K", limit=3)
```

**Best Practice:**
- Use to find the latest filing before extracting data
- Combine with get_company_facts to get data from specific filing
- Form types: 10-K (annual), 10-Q (quarterly), 8-K (current events)

---

### 3. **search_10k**
**Purpose:** Search within 10-K annual reports

**Parameters:**
- `cik` (string, required): Company CIK or ticker
- `query` (string, required): Search term or phrase
- `year` (integer, optional): Specific year to search

**Returns:**
- Matching sections from 10-K with context
- Page references
- Surrounding text for context

**Example Usage:**
```python
# Search for risk factors
search_10k(cik="AAPL", query="risk factors")

# Search specific year
search_10k(cik="AAPL", query="revenue recognition", year=2024)

# Search for specific topics
search_10k(cik="AAPL", query="supply chain")
```

**Best Practice:**
- Use for qualitative information (MD&A, Risk Factors, etc.)
- Good for understanding business context
- NOT for extracting precise financial numbers (use get_company_facts instead)

---

### 4. **search_10q**
**Purpose:** Search within 10-Q quarterly reports

**Parameters:**
- `cik` (string, required): Company CIK or ticker
- `query` (string, required): Search term or phrase
- `year` (integer, optional): Specific year to search
- `quarter` (integer, optional): Specific quarter (1, 2, 3)

**Returns:**
- Matching sections from 10-Q with context
- Quarter and year information
- Page references

**Example Usage:**
```python
# Search recent quarters
search_10q(cik="TSLA", query="production")

# Search specific quarter
search_10q(cik="TSLA", query="deliveries", year=2025, quarter=3)
```

**Best Practice:**
- Use for quarterly updates and trends
- Good for MD&A and management commentary
- For exact numbers, use get_company_facts

---

### 5. **get_filing_content**
**Purpose:** Retrieve full content of a specific filing

**Parameters:**
- `accession_number` (string, required): SEC accession number
  - Format: "0001234567-25-000123"
  - Get from get_recent_filings

**Returns:**
- Complete filing content
- All sections and exhibits
- HTML or text format

**Example Usage:**
```python
# Get specific filing by accession number
get_filing_content(accession_number="0001628280-25-045968")
```

**Best Practice:**
- Use when you need complete filing text
- Good for reading specific sections
- Can be large (10-K can be 200+ pages)

---

## Recommended Workflow

### For Financial Analysis:

1. **Find Latest Filing**
```python
filings = get_recent_filings(cik="TSLA", form_type="10-Q", limit=1)
```

2. **Extract Complete Financial Data**
```python
# This gets ALL XBRL data - hundreds of line items
data = get_company_facts(cik="TSLA")
```

3. **Search for Qualitative Context** (if needed)
```python
risks = search_10q(cik="TSLA", query="risk factors")
```

### For Specific Financial Items:

```python
# Get specific balance sheet item
assets = get_company_facts(cik="AAPL", concept="Assets")

# Get specific income statement item
revenue = get_company_facts(cik="AAPL", concept="RevenueFromContractWithCustomerExcludingAssessedTax")
```

---

## Important Notes

### XBRL Concept Names

Common XBRL concepts you'll encounter:

**Balance Sheet:**
- `Assets` - Total assets
- `AssetsCurrent` - Current assets
- `Liabilities` - Total liabilities
- `LiabilitiesCurrent` - Current liabilities
- `StockholdersEquity` - Stockholders' equity
- `CashAndCashEquivalentsAtCarryingValue` - Cash
- `PropertyPlantAndEquipmentNet` - PP&E

**Income Statement:**
- `RevenueFromContractWithCustomerExcludingAssessedTax` - Revenue
- `CostOfRevenue` - Cost of goods sold
- `GrossProfit` - Gross profit
- `OperatingIncomeLoss` - Operating income
- `NetIncomeLoss` - Net income

**Cash Flow:**
- `NetCashProvidedByUsedInOperatingActivities` - Operating cash flow
- `NetCashProvidedByUsedInInvestingActivities` - Investing cash flow
- `NetCashProvidedByUsedInFinancingActivities` - Financing cash flow
- `PaymentsToAcquirePropertyPlantAndEquipment` - Capital expenditures

### CIK vs Ticker

- **CIK:** Official SEC identifier (10 digits, e.g., "0000320193")
- **Ticker:** Stock symbol (e.g., "AAPL")
- Most tools accept both, but CIK is more reliable
- Common CIKs:
  - Apple: 0000320193
  - Microsoft: 0000789019
  - Tesla: 0001318605
  - Amazon: 0001018724
  - Google/Alphabet: 0001652044

### Data Precision

- XBRL data from `get_company_facts` is **exact** (to the penny)
- Values are typically in actual dollars (not thousands/millions)
- Always include units in your analysis
- Dates are in ISO format (YYYY-MM-DD)

### Rate Limits

- SEC EDGAR has rate limits (10 requests per second)
- The MCP server handles this automatically
- Be patient with large data requests

---

## Troubleshooting

**"Company not found"**
- Try using CIK instead of ticker
- Verify the company files with SEC
- Check spelling of company name

**"No data returned"**
- Some companies may not have XBRL data for all periods
- Older filings may not be in XBRL format
- Try a different period or filing

**"Concept not found"**
- XBRL concepts vary by company
- Use company-specific concepts (prefix with company ticker)
- Get all facts first, then explore available concepts

---

## Examples by Use Case

### Complete Financial Statement Extraction:
```python
# Step 1: Get all XBRL data
all_data = get_company_facts(cik="TSLA")

# This returns 100+ line items including:
# - Complete balance sheet
# - Complete income statement
# - Complete cash flow statement
# - Multiple periods for comparison
```

### Quarterly Performance Analysis:
```python
# Step 1: Get recent 10-Q
filings = get_recent_filings(cik="AAPL", form_type="10-Q", limit=1)

# Step 2: Get XBRL data
data = get_company_facts(cik="AAPL")

# Step 3: Get MD&A for context
mda = search_10q(cik="AAPL", query="management discussion")
```

### Risk Assessment:
```python
# Get risk factors from 10-K
risks = search_10k(cik="TSLA", query="risk factors")

# Get specific risks
supply_chain = search_10k(cik="TSLA", query="supply chain disruption")
```

---

## Best Practices Summary

1. **Always use `get_company_facts` for numerical data** - It's the most accurate
2. **Use search tools for context** - MD&A, risks, business description
3. **Cite accession numbers** - For traceability and verification
4. **Extract complete datasets** - Don't cherry-pick individual items
5. **Include comparative periods** - XBRL data includes multiple periods
6. **Verify arithmetic** - Balance sheet should balance, cash flows should reconcile

---

*This documentation covers the core SEC EDGAR MCP tools. For additional tools or
features, refer to the MCP server documentation or use introspection.*
"""


# Make the tool available for import
__all__ = ['get_available_edgar_tools']
