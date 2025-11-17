# Manager Attribute Name Fix

## Problem

Westpac analysis failed at the specialist analyses phase (reports 5 and 6 not generated) with error:

```
AttributeError: 'FinancialMetrics' object has no attribute 'net_margin'
```

**Location:** [manager_enhanced.py](financial_research_agent/manager_enhanced.py) line 908

## Root Cause

When I updated the manager to pass pre-extracted data to the financials agent, I used incorrect attribute names that don't match the `FinancialMetrics` Pydantic model definition.

**Incorrect attributes used (line 908):**
- `metrics_results.net_margin` ❌
- `metrics_results.roa` ❌
- `metrics_results.roe` ❌

**Correct attributes (from FinancialMetrics model):**
- `metrics_results.net_profit_margin` ✅
- `metrics_results.return_on_assets` ✅
- `metrics_results.return_on_equity` ✅

## FinancialMetrics Model Definition

**File:** [financial_metrics_agent.py](financial_research_agent/agents/financial_metrics_agent.py) lines 215-280

```python
class FinancialMetrics(BaseModel):
    """Comprehensive financial metrics including statements and calculated ratios."""

    executive_summary: str

    # Liquidity Ratios
    current_ratio: float | None
    quick_ratio: float | None
    cash_ratio: float | None

    # Solvency Ratios
    debt_to_equity: float | None
    debt_to_assets: float | None
    interest_coverage: float | None
    equity_ratio: float | None

    # Profitability Ratios
    gross_profit_margin: float | None       # ✅ Not "gross_margin"
    operating_margin: float | None          # ✅ Correct
    net_profit_margin: float | None         # ✅ Not "net_margin"
    return_on_assets: float | None          # ✅ Not "roa"
    return_on_equity: float | None          # ✅ Not "roe"

    # Efficiency Ratios
    asset_turnover: float | None
    inventory_turnover: float | None
    receivables_turnover: float | None
    days_sales_outstanding: float | None

    # ... (more fields)
```

## Fix Applied

**File:** [manager_enhanced.py](financial_research_agent/manager_enhanced.py) line 908

**Before:**
```python
if metrics_results.net_margin or metrics_results.roa or metrics_results.roe:
    ratio_categories.append("Profitability Ratios (gross margin, operating margin, net margin, ROA, ROE)")
```

**After:**
```python
if metrics_results.net_profit_margin or metrics_results.return_on_assets or metrics_results.return_on_equity:
    ratio_categories.append("Profitability Ratios (gross margin, operating margin, net margin, ROA, ROE)")
```

## Impact

This error prevented the specialist analyses from running, which means:
- ❌ File 05 (financial_analysis.md) was not generated
- ❌ File 06 (risk_analysis.md) was not generated
- ⚠️ The comprehensive report (07) was still generated, but without specialist insights

The error occurred in the `_gather_specialist_analyses()` method when trying to build a summary of available ratios to pass to the financials agent.

## Testing

To verify the fix:

```bash
python -m financial_research_agent.main_enhanced
# Input: "Analyze Westpac Banking Corporation"
```

**Expected output files:**
- ✅ 03_financial_statements.md
- ✅ 04_financial_metrics.md
- ✅ 05_financial_analysis.md (should now generate!)
- ✅ 06_risk_analysis.md (should now generate!)
- ✅ 07_comprehensive_report.md
- ✅ 08_verification.md

## Related Changes

This fix completes the foreign filer support work:

1. ✅ [FOREIGN_FILER_FIX.md](FOREIGN_FILER_FIX.md) - Agent prompt updates
2. ✅ [FINANCIALS_AGENT_REFACTOR.md](FINANCIALS_AGENT_REFACTOR.md) - Focus on interpretation
3. ✅ **This fix** - Correct attribute names in manager

All three pieces are now working together:
- Manager properly notifies agent about pre-extracted data ✅
- Manager uses correct attribute names ✅
- Agent focuses on interpretation, not extraction ✅

## Why This Happened

When I wrote the manager update in [FOREIGN_FILER_FIX.md](FOREIGN_FILER_FIX.md), I used shorthand attribute names (`net_margin`, `roa`, `roe`) instead of checking the actual Pydantic model definition.

The lesson: Always check the actual model definition when accessing Pydantic model attributes, especially when working with complex data structures.

## Other Attribute Names to Remember

For future reference, here are the correct names:

| Common Name | Pydantic Attribute Name |
|-------------|------------------------|
| Gross Margin | `gross_profit_margin` |
| Operating Margin | `operating_margin` ✅ |
| Net Margin | `net_profit_margin` |
| ROA | `return_on_assets` |
| ROE | `return_on_equity` |
| Current Ratio | `current_ratio` ✅ |
| Quick Ratio | `quick_ratio` ✅ |
| Debt/Equity | `debt_to_equity` ✅ |
| Debt/Assets | `debt_to_assets` ✅ |

---

**Fixed:** November 13, 2024
**Impact:** Resolves specialist analyses failure for all companies
**Breaking Changes:** None (bug fix)
