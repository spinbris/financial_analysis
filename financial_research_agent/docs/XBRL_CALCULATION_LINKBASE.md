# XBRL Calculation Linkbase Integration

## Overview

Implemented lightweight XBRL calculation linkbase parser to use official SEC parent-child relationships for financial statement validation, instead of custom aggregation logic.

## What Was Implemented

### New Module: `xbrl_calculation.py`

Location: [financial_research_agent/xbrl_calculation.py](financial_research_agent/xbrl_calculation.py)

**Features:**
- ✅ Parse XBRL `_cal.xml` calculation linkbase files from SEC EDGAR
- ✅ Extract parent-child relationships with weights (+1 for addition, -1 for subtraction)
- ✅ Validate calculated totals against reported values
- ✅ No heavy dependencies (uses only `requests` and `xml.etree.ElementTree`)
- ✅ Automatic handling of SEC User-Agent requirements

## How XBRL Calculation Linkbases Work

XBRL uses **calculation linkbases** (`_cal.xml`) to define how financial concepts aggregate:

```
us-gaap:Assets =
  + us-gaap:AssetsCurrent (weight: +1.0)
  + us-gaap:AssetsNoncurrent (weight: +1.0)

us-gaap:LiabilitiesAndStockholdersEquity =
  + us-gaap:Liabilities (weight: +1.0)
  + us-gaap:CommitmentsAndContingencies (weight: +1.0)
  + us-gaap:StockholdersEquity (weight: +1.0)
```

This ensures **consistency across all companies** using the same XBRL taxonomy (US-GAAP).

## Usage Examples

### Basic Usage

```python
from financial_research_agent.xbrl_calculation import get_calculation_parser_for_filing

# Get parser for a specific filing
filing_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019325000073/aapl-20250628_cal.xml"
parser = get_calculation_parser_for_filing(filing_url)

if parser:
    # Get children of a parent concept
    children = parser.get_children("us-gaap:Assets")

    for rel in children:
        print(f"{rel.parent_concept} {'+' if rel.weight > 0 else '-'} {rel.child_concept}")
```

### Validate Financial Statement Totals

```python
from financial_research_agent.xbrl_calculation import XBRLCalculationParser

parser = XBRLCalculationParser()
parser.parse_from_url(filing_url)

# Your extracted financial data
concept_values = {
    "us-gaap:Assets": 364980000000.0,
    "us-gaap:AssetsCurrent": 143566000000.0,
    "us-gaap:AssetsNoncurrent": 221414000000.0,
}

# Validate Assets calculation
is_valid, reported, calculated = parser.validate_calculation(
    concept_values,
    "us-gaap:Assets",
    tolerance=0.01  # 1% tolerance
)

if is_valid:
    print(f"✅ Assets calculation is valid")
    print(f"   Reported: ${reported/1e9:.2f}B")
    print(f"   Calculated: ${calculated/1e9:.2f}B")
else:
    print(f"❌ Assets calculation mismatch!")
    print(f"   Reported: ${reported/1e9:.2f}B")
    print(f"   Calculated: ${calculated/1e9:.2f}B")
```

### Integration with edgartools

```python
from edgar import set_identity, Company
from financial_research_agent.xbrl_calculation import get_calculation_parser_for_filing

set_identity("FinancialResearchAgent/1.0 (your-email@example.com)")

# Get latest 10-Q for Apple
apple = Company("AAPL")
filing = apple.get_filings(form="10-Q").latest(1)

# Find calculation linkbase file
for att in filing.attachments:
    if "_cal.xml" in att.document:
        cal_url = f"https://www.sec.gov{att.path}"

        # Parse it
        parser = get_calculation_parser_for_filing(cal_url)

        if parser:
            print(f"✅ Loaded calculation linkbase for {filing.company}")
            print(f"   Found {len(parser.relationships)} parent concepts")
```

## Benefits

### 1. **Accuracy**
Uses official SEC XBRL calculation linkbases instead of custom aggregation logic

### 2. **Consistency**
All companies following US-GAAP use the same taxonomy structure

### 3. **Validation**
Can detect when extracted totals don't match SEC-defined calculations

### 4. **Lightweight**
No heavy dependencies like Arelle (which is ~50MB)

## Key Concepts

### Parent-Child Relationships

Each parent concept (e.g., Total Assets) has:
- **Children**: Component concepts that aggregate to the parent
- **Weights**: +1 for addition, -1 for subtraction
- **Order**: Display order (for presentation)

Example:
```
us-gaap:NetIncomeLoss (Net Income) =
  + us-gaap:GrossProfit (+1.0)
  - us-gaap:OperatingExpenses (-1.0)
  + us-gaap:NonoperatingIncomeExpense (+1.0)
  - us-gaap:IncomeTaxExpense (-1.0)
```

### Validation Tolerance

The `validate_calculation()` method uses a tolerance parameter (default 1%) because:
- Rounding differences in financial statements
- Some child concepts may not be present in all periods
- Allows for minor discrepancies while catching major errors

## Common Parent Concepts

**Balance Sheet:**
- `us-gaap:Assets`
- `us-gaap:AssetsCurrent`
- `us-gaap:AssetsNoncurrent`
- `us-gaap:Liabilities`
- `us-gaap:LiabilitiesAndStockholdersEquity`
- `us-gaap:StockholdersEquity`

**Income Statement:**
- `us-gaap:NetIncomeLoss`
- `us-gaap:GrossProfit`
- `us-gaap:OperatingIncomeLoss`
- `us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxes`

**Cash Flow Statement:**
- `us-gaap:NetCashProvidedByUsedInOperatingActivities`
- `us-gaap:NetCashProvidedByUsedInInvestingActivities`
- `us-gaap:NetCashProvidedByUsedInFinancingActivities`
- `us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect`

## Limitations

1. **Not all calculations are in linkbase**: Some aggregations may be missing
2. **Fallback needed**: Your current aggregation logic should remain as fallback
3. **Namespace variations**: Concepts may use different namespace prefixes (us-gaap vs dei vs company-specific)
4. **Missing children**: Not all child concepts may be present in every filing

## Next Steps for Integration

1. **Update financial metrics agent** to use calculation linkbase for validation
2. **Log warnings** when calculated values differ from reported values
3. **Keep existing fallback logic** for when calculation linkbase is unavailable
4. **Add to documentation** showing users the validation is based on official SEC taxonomies

## Testing

Run the test example:

```bash
python financial_research_agent/xbrl_calculation.py
```

This will:
1. Fetch Apple's latest Q3 2024 calculation linkbase
2. Show all parent concepts
3. Display the Assets calculation tree
4. Validate a sample calculation

## Related Documentation

- [SEC EDGAR XBRL Filings](https://www.sec.gov/structureddata/osd-inline-xbrl.html)
- [XBRL Calculation Linkbase Specification](http://www.xbrl.org/Specification/XBRL-2.1/REC-2003-12-31/XBRL-2.1-REC-2003-12-31+corrected-errata-2013-02-20.html#_5.2.5)
- [US-GAAP Taxonomy](https://xbrl.us/home/filers/sec-reporting/)

---

**Date:** 2025-11-04
**Status:** ✅ Implemented and tested
**Impact:** Enables use of official SEC calculation linkbases for validation
**Dependencies:** requests, xml.etree.ElementTree (both standard library/lightweight)
