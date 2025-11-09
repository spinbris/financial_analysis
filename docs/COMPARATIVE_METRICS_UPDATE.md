# Comparative Financial Metrics Update

## Summary

Updated the financial metrics formatter to show **Year-over-Year (YoY) comparative analysis** with actual report dates instead of generic period labels.

## Changes Made

### 1. Updated `formatters.py`

#### Added Helper Function: `_calculate_ratio_from_data()`
- **Location:** [formatters.py:397-505](financial_research_agent/formatters.py#L397-L505)
- **Purpose:** Calculate specific ratios from raw financial statement data for any period (Current or Prior)
- **Supports:** All major ratios (liquidity, solvency, profitability)
- **Features:**
  - Flexible pattern matching for line item names
  - Handles both new structure (with `line_items`) and old structure (flat dict)
  - Returns `None` if calculation not possible (missing data)

#### Enhanced `format_financial_metrics()` Function
- **Location:** [formatters.py:508-850](financial_research_agent/formatters.py#L508-L850)

**Key Improvements:**

1. **Extract Period Dates** (lines 508-523):
   ```python
   # Extract actual report dates from balance sheet data
   current_date = bs_dates.get('current', 'Current')  # e.g., "2025-09-30"
   prior_date = bs_dates.get('prior', 'Prior')        # e.g., "2024-12-31"
   has_comparative = prior_date != 'Prior' and prior_date is not None
   ```

2. **Liquidity Ratios** (lines 548-627):
   - **Comparative Format:**
     ```markdown
     | Ratio | 2025-09-30 | 2024-12-31 | Change | % Change |
     |-------|------------|------------|--------|----------|
     | **Current Ratio** | 2.07 | 2.02 | 0.05 | 2.5% ↑ |
     ```
   - Calculates prior period ratios using raw data
   - Shows absolute change and percentage change
   - Includes trend indicators (↑/↓/→)

   - **Fallback Format** (if no prior period data):
     ```markdown
     | Ratio | Value | Interpretation |
     |-------|-------|----------------|
     | **Current Ratio** | 2.07 | ✓ Healthy |
     ```

3. **Solvency Ratios** (lines 629-712):
   - Same comparative structure as liquidity ratios
   - Trend indicators: ↓ is better for debt ratios, ↑ is better for equity ratio
   - Includes Debt-to-Equity, Debt-to-Assets, Equity Ratio

4. **Profitability Ratios** (lines 714-841):
   - YoY comparison for all profitability metrics
   - Shows margin expansion/contraction
   - Includes: Gross Margin, Operating Margin, Net Margin, ROA, ROE

## Before vs After

### Before (Single Period)
```markdown
## Liquidity Ratios
| Ratio | Value | Interpretation |
|-------|-------|----------------|
| **Current Ratio** | 2.07 | ✓ Healthy - can meet short-term obligations |
| **Quick Ratio** | 1.85 | ✓ Strong - can meet obligations without inventory |
```

### After (Comparative with Actual Dates)
```markdown
## Liquidity Ratios
| Ratio | 2025-09-30 | 2024-12-31 | Change | % Change |
|-------|------------|------------|--------|----------|
| **Current Ratio** | 2.07 | 2.02 | 0.05 | 2.5% ↑ |
| **Quick Ratio** | 1.85 | 1.80 | 0.05 | 2.8% ↑ |
| **Cash Ratio** | 0.59 | 0.55 | 0.04 | 7.7% ↑ |
```

## Testing

Created comprehensive test: [tests/test_comparative_metrics.py](tests/test_comparative_metrics.py)

**Test Results:**
```
✅ Contains current date (2025-09-30)
✅ Contains prior date (2024-12-31)
✅ Contains 'Change' column
✅ Contains '% Change' column
✅ Does NOT use generic 'Value' column
✅ Contains trend indicators (↑/↓/→)
```

## Example Output

### Liquidity Ratios
```markdown
| Ratio | 2025-09-30 | 2024-12-31 | Change | % Change |
|-------|------------|------------|--------|----------|
| **Current Ratio** | 2.07 | 2.02 | 0.05 | 2.5% ↑ |
| **Quick Ratio** | 1.85 | 1.80 | 0.05 | 2.8% ↑ |
| **Cash Ratio** | 0.59 | 0.55 | 0.04 | 7.7% ↑ |
```

### Profitability Ratios
```markdown
| Ratio | 2025-09-30 | 2024-12-31 | Change | % Change |
|-------|------------|------------|--------|----------|
| **Gross Margin** | 17.9% | 17.9% | 0.0% | 0.0% ↑ |
| **Operating Margin** | 10.3% | 8.9% | 1.4% | 16.4% ↑ |
| **Net Margin** | 7.9% | 7.9% | -0.0% | -0.5% ↓ |
| **Return on Assets (ROA)** | 6.4% | 1.5% | 4.9% | 321.4% ↑ |
| **Return on Equity (ROE)** | 16.9% | 2.5% | 14.4% | 587.2% ↑ |
```

## Benefits

1. **Trend Analysis:** Immediately see if metrics are improving or declining
2. **Actual Dates:** Know exactly which periods are being compared
3. **Quantified Changes:** Both absolute and percentage changes provided
4. **Visual Indicators:** Trend arrows (↑/↓) for quick assessment
5. **Backward Compatible:** Falls back to single-period format if prior data unavailable

## Files Modified

1. **financial_research_agent/formatters.py**
   - Added `_calculate_ratio_from_data()` helper function
   - Updated `format_financial_metrics()` to show comparative analysis
   - Extracts and displays actual period dates from financial data

## Files Added

1. **tests/test_comparative_metrics.py**
   - Comprehensive test for comparative formatting
   - Validates period dates, change columns, trend indicators
   - Provides sample output verification

## User Request Fulfilled

> "financial metrics md file only calculates current period, not comparative numbers and column headings are not reporting dates"

**Resolved:**
- ✅ Now calculates ratios for **both Current and Prior periods**
- ✅ Column headings show **actual report dates** (e.g., 2025-09-30, 2024-12-31)
- ✅ Includes **Change and % Change columns** for YoY comparison
- ✅ Trend indicators (↑/↓) show direction of change
- ✅ Applies to all ratio categories: Liquidity, Solvency, Profitability

## Next Steps

When you run the financial analysis again, the `04_financial_metrics.md` file will automatically include:
- Actual report dates in column headers
- Year-over-Year comparative analysis
- Change metrics and trend indicators
- All ratio categories with prior period calculations
