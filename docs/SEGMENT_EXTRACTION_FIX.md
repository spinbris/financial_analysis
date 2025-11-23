# Segment Revenue Extraction Fix

**Date:** November 23, 2025
**Issue:** Segment and geographic revenue breakdowns empty in analysis reports
**Status:** ✅ Fixed (commit d79541a)

---

## Problem

After deploying segment extraction feature (commit 658b44a), Railway logs showed:

```
Segment Revenue and Geographic Revenue Data: The required tables for segment
and geographic revenue are present in the structure but contain no actual
```

This meant the code was running but finding no data.

---

## Root Cause

The `get_revenue_segments()` method in `edgartools_wrapper.py` was using **non-existent API methods**:

```python
# ❌ This doesn't exist in current edgartools
df_with_segments = income_stmt.to_dataframe(include_dimensions=True)
df_clean = income_stmt.to_dataframe(include_dimensions=False)
```

The `include_dimensions` parameter doesn't exist in edgartools 2.29.0's `to_dataframe()` method.

**Investigation revealed:**
- `income_stmt.to_dataframe()` only takes no arguments: `() -> DataFrame`
- Segment data is NOT in the income statement DataFrame at all
- Segment data is in **XBRL dimensional facts** accessed via filing.xbrl()

---

## How Edgartools Actually Works

### Income Statement (No Segments)
```python
company = Company("MSFT")
income_stmt = company.income_statement()
df = income_stmt.to_dataframe()  # No parameters!

# Returns clean P&L with concepts like:
# - RevenueFromContractWithCustomerExcludingAssessedTax
# - OperatingIncomeLoss
# - NetIncomeLoss
# NO segment breakdowns included
```

### XBRL Dimensional Facts (Segments ARE Here)
```python
# Get 10-K filing to access XBRL
tenk = company.get_filings(form="10-K").latest(1)
xbrl = tenk.xbrl()
facts = xbrl.facts

# Get dimensional facts as DataFrame
df = facts.get_facts_with_dimensions()

# Shape: (937, 57) with columns like:
# - concept: 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
# - numeric_value: 281724000000
# - period_end: '2025-06-30'
# - dim_us-gaap_StatementBusinessSegmentsAxis: 'msft:IntelligentCloudMember'
# - dim_srt_StatementGeographicalAxis: 'country:US'
# - dim_srt_ProductOrServiceAxis: 'us-gaap:ServiceOtherMember'
```

**Key insight:** Segments are in **separate columns** named `dim_[axis_name]`, not in the index.

---

## Solution

Completely rewrote `get_revenue_segments()` to:

1. **Access XBRL filing data** instead of income statement
2. **Use `facts.get_facts_with_dimensions()`** to get DataFrame
3. **Filter by revenue concept** and dimension columns
4. **Extract consolidated revenue** from regular income statement for reconciliation

### New Implementation

```python
def get_revenue_segments(self, ticker: str, period_index: int = 0) -> Dict[str, Any]:
    # Get 10-K filing for XBRL access
    company = Company(ticker)
    tenk = company.get_filings(form="10-K").latest(1)
    xbrl = tenk.xbrl()
    facts = xbrl.facts

    # Get dimensional facts DataFrame
    df = facts.get_facts_with_dimensions()

    # Filter for revenue
    revenue_df = df[df['concept'] == 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax']

    # Get latest period
    latest_period = revenue_df['period_end'].max()

    # Extract business segments
    business_seg_df = revenue_df[revenue_df['dim_us-gaap_StatementBusinessSegmentsAxis'].notna()]
    current = business_seg_df[business_seg_df['period_end'] == latest_period]
    business_segments = []
    for idx, row in current.iterrows():
        segment_name = row['dim_us-gaap_StatementBusinessSegmentsAxis']
        # Clean: "msft:IntelligentCloudMember" -> "IntelligentCloud"
        if ':' in segment_name:
            segment_name = segment_name.split(':')[1]
        segment_name = segment_name.replace('Member', '')
        value = float(row['numeric_value'])
        business_segments.append({'name': segment_name, 'revenue': value})

    # Extract geographic segments (same pattern)
    geo_seg_df = revenue_df[revenue_df['dim_srt_StatementGeographicalAxis'].notna()]
    # ... similar extraction ...

    # Get total from regular income statement
    income_stmt = company.income_statement()
    df_stmt = income_stmt.to_dataframe()
    total_revenue = float(df_stmt.loc['RevenueFromContractWithCustomerExcludingAssessedTax', period_col])

    return {
        'business_segments': business_segments,
        'geographic_segments': geographic_segments,
        'total_revenue': total_revenue
    }
```

---

## Test Results

### Microsoft (MSFT) FY 2025

**Total Revenue:** $281.7B

**Business Segments:**
- Productivity & Business Processes: $120.8B (42.9%)
- Intelligent Cloud: $106.3B (37.7%)
- More Personal Computing: $54.6B (19.4%)
- **Sum:** $281.7B ✓ Reconciles

**Geographic Segments:**
- United States: $144.5B (51.3%)
- Non-US: $137.2B (48.7%)
- **Sum:** $281.7B ✓ Reconciles

---

## Files Changed

### [edgartools_wrapper.py](../financial_research_agent/tools/edgartools_wrapper.py)

**Lines 491-582:** Complete rewrite of `get_revenue_segments()`
- Access XBRL filing instead of income statement
- Use `facts.get_facts_with_dimensions()` for segment data
- Filter by dimension columns
- Get total from regular income statement

**Line 39:** Removed invalid `include_dimensions=False` parameter
- Changed: `df = statement_obj.to_dataframe()`
- Was: `df = statement_obj.to_dataframe(include_dimensions=False)`

---

## What This Fixes

### Before Fix
- ❌ Segment extraction code existed but returned empty data
- ❌ Railway logs: "tables...present...but contain no actual"
- ❌ Comprehensive report: "Not available in filing" for segments

### After Fix
- ✅ Segment data extracts correctly from XBRL
- ✅ Business segments reconcile to total revenue
- ✅ Geographic segments reconcile to total revenue
- ✅ Comprehensive report will show actual segment breakdowns

---

## Railway Deployment

**Commit:** d79541a
**Pushed:** November 23, 2025

Railway will auto-deploy this fix. After deployment:

1. Run new MSFT analysis on Railway
2. Check comprehensive report for segment data
3. Verify segments appear with correct amounts
4. Verify reconciliation to total revenue

**Expected comprehensive report format:**
```markdown
### Revenue Segment Breakdown

#### Business Segments
- Productivity & Business Processes: $120.8B (42.9% of total)
- Intelligent Cloud: $106.3B (37.7%)
- More Personal Computing: $54.6B (19.4%)
- **Total:** $281.7B ✓ (reconciles to consolidated revenue)

#### Geographic Revenue
- United States: $144.5B (51.3% of total)
- Non-US: $137.2B (48.7%)
- **Total:** $281.7B ✓ (reconciles to consolidated revenue)
```

---

## Technical Details

### Edgartools XBRL Axes

The XBRL filing contains multiple segment axes:

- `us-gaap_StatementBusinessSegmentsAxis` - Operating/business segments
- `srt_StatementGeographicalAxis` - Geographic segments
- `srt_ProductOrServiceAxis` - Product/service categories

These axes appear as **columns** in the `get_facts_with_dimensions()` DataFrame:
- `dim_us-gaap_StatementBusinessSegmentsAxis`
- `dim_srt_StatementGeographicalAxis`
- `dim_srt_ProductOrServiceAxis`

### Member Values

Segment members are in format: `namespace:MemberName`

Examples:
- `msft:ProductivityAndBusinessProcessesMember`
- `msft:IntelligentCloudMember`
- `country:US`
- `us-gaap:NonUsMember`

The code cleans these by:
1. Splitting on `:` to remove namespace
2. Removing `Member` suffix
3. Keeping CamelCase (human-readable)

---

## Testing Locally

To test segment extraction locally:

```bash
python
>>> from financial_research_agent.tools.edgartools_wrapper import EdgarToolsWrapper
>>> wrapper = EdgarToolsWrapper(identity="Your Name your@email.com")
>>> result = wrapper.get_revenue_segments("MSFT")
>>> result
{
  'business_segments': [
    {'name': 'ProductivityAndBusinessProcesses', 'revenue': 120810000000.0},
    {'name': 'IntelligentCloud', 'revenue': 106265000000.0},
    {'name': 'MorePersonalComputing', 'revenue': 54649000000.0}
  ],
  'geographic_segments': [
    {'name': 'US', 'revenue': 144546000000.0},
    {'name': 'NonUs', 'revenue': 137178000000.0}
  ],
  'total_revenue': 281724000000.0
}
```

---

## Key Learnings

1. **Always check actual API signatures** - Don't assume methods exist
2. **Edgartools segment data is in XBRL** - Not in income_statement()
3. **Dimensional facts are columns** - Not index values or brackets
4. **Test with actual data** - Don't rely on documentation alone
5. **Segment reconciliation is critical** - Always verify sum equals total

---

## Related Issues

- Commit 658b44a: Added segment extraction (incorrect implementation)
- Commit 2691c6d: Updated financials agent prompt to include segments
- Commit 0b1a065: Removed segment data from P&L display
- Commit d79541a: This fix (correct XBRL-based implementation)

---

**Status:** ✅ Fixed and deployed to Railway

**Next:** Wait for Railway deployment, then test with new MSFT analysis
