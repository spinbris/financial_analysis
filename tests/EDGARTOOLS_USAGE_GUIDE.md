# EdgarTools Usage Guide

## Overview
EdgarTools is a powerful Python library for fetching and analyzing SEC EDGAR filings. This guide demonstrates how to use it for financial statement analysis.

## Installation
```bash
pip install edgartools
```

## Key Concepts

### 1. Setting Identity (Required)
SEC EDGAR requires you to identify yourself:
```python
from edgar import Company, set_identity

set_identity("your.email@example.com")
```

### 2. Getting Company Data
```python
# Fetch company by ticker
company = Company("AAPL")

# Company attributes
print(company.name)          # Apple Inc.
print(company.cik)           # 320193
print(company.sic)           # 3571
```

### 3. Accessing Filings
```python
# Get latest 10-K filing
latest_10k = company.get_filings(form="10-K").latest(1)

# Get latest 10-Q filing
latest_10q = company.get_filings(form="10-Q").latest(1)

# Get multiple filings
filings_10k = company.get_filings(form="10-K").latest(5)  # Returns Filings object
```

### 4. Extracting Financial Statements
```python
# Get the filing object
financials = latest_10k.obj()

# Access XBRL financial statements
bs = financials.financials.balance_sheet()
income = financials.financials.income_statement()
cf = financials.financials.cashflow_statement()

# Convert to pandas DataFrame
bs_df = bs.to_dataframe()
income_df = income.to_dataframe()
cf_df = cf.to_dataframe()
```

### 5. DataFrame Structure
The DataFrame has these columns:
- `concept`: XBRL concept name (e.g., 'us-gaap_Assets')
- `label`: Human-readable label
- Date columns: '2025-09-27', '2024-09-28', etc.
- `level`: Hierarchy level in the statement
- `abstract`: Boolean indicating if it's a header
- Other metadata columns

### 6. Extracting Specific Line Items
```python
# Set concept as index for easier lookup
bs_df_indexed = bs_df.set_index('concept')

# Get date columns (skip metadata columns)
date_cols = [col for col in bs_df.columns if col not in ['concept', 'label', 'level', 'abstract']]
latest_col = date_cols[0]  # Most recent period

# Extract specific values
total_assets = bs_df_indexed.loc['us-gaap_Assets', latest_col]
total_liabilities = bs_df_indexed.loc['us-gaap_Liabilities', latest_col]

# Handle potential duplicates (some concepts appear multiple times)
if hasattr(total_assets, 'iloc'):
    total_assets = total_assets.iloc[0]
```

## Common XBRL Concepts

### Balance Sheet
- `us-gaap_Assets` - Total Assets
- `us-gaap_AssetsCurrent` - Total Current Assets
- `us-gaap_CashAndCashEquivalentsAtCarryingValue` - Cash
- `us-gaap_Liabilities` - Total Liabilities
- `us-gaap_LiabilitiesCurrent` - Total Current Liabilities
- `us-gaap_StockholdersEquity` - Total Stockholders' Equity

### Income Statement
- `us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax` - Revenue
- `us-gaap_CostOfGoodsAndServicesSold` - Cost of Revenue
- `us-gaap_GrossProfit` - Gross Profit
- `us-gaap_OperatingIncomeLoss` - Operating Income
- `us-gaap_NetIncomeLoss` - Net Income
- `us-gaap_EarningsPerShareBasic` - EPS (Basic)
- `us-gaap_EarningsPerShareDiluted` - EPS (Diluted)

### Cash Flow Statement
- `us-gaap_NetCashProvidedByUsedInOperatingActivities` - Operating Cash Flow
- `us-gaap_NetCashProvidedByUsedInInvestingActivities` - Investing Cash Flow
- `us-gaap_NetCashProvidedByUsedInFinancingActivities` - Financing Cash Flow
- `us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` - Cash & Equivalents

## Example: Complete Analysis

See [test_edgartools_various.py](test_edgartools_various.py) for a complete example that:
1. Fetches Apple's latest 10-K
2. Extracts balance sheet, income statement, and cash flow
3. Displays key financial metrics
4. Calculates financial ratios (Current Ratio, Profit Margin, ROE, Debt/Equity)

## Tips

1. **Always set identity first** - SEC will block requests without proper identification
2. **XBRL concepts vary by company** - Not all companies use the same concept names
3. **Handle duplicates** - Some concepts appear multiple times in statements
4. **Check for None values** - Not all line items are present in all filings
5. **Units are in source filing units** - Usually thousands or millions
6. **Fiscal years vary** - Apple's fiscal year ends in September, not December

## Advantages Over Manual XBRL Parsing

1. **Simplified API** - No need to parse complex XML
2. **Automatic data extraction** - Handles XBRL intricacies
3. **Rich display** - Beautiful terminal output for quick inspection
4. **DataFrame integration** - Easy to work with pandas
5. **Handles SEC quirks** - Properly manages rate limiting, authentication, etc.

## Running the Examples

```bash
# Simple exploration script
python tests/test_edgartools_simple.py

# Complete financial analysis
python tests/test_edgartools_various.py

# Debug XBRL concepts
python tests/debug_concepts.py
```

## Resources

- [EdgarTools Documentation](https://github.com/dgunning/edgartools)
- [SEC EDGAR](https://www.sec.gov/edgar)
- [XBRL US GAAP Taxonomy](https://xbrl.us/data-rule/dqc_0015-negatives/)
