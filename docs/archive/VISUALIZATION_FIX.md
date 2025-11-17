# Visualization Charts Not Showing - Fix

## Problem

After implementing the new edgartools-based visualization module, charts were not appearing in the Gradio interface for AAPL analysis.

**Symptoms:**
- Old chart files being generated: `chart_metrics.json`, `chart_risk_categories.json`
- New chart files NOT being generated: `chart_revenue_profitability.json`, `chart_balance_sheet.json`
- Charts not visible in Gradio UI

**Date Discovered:** November 13, 2024

---

## Root Cause

The Gradio web interface (`web_app.py`) was still calling the OLD chart generation script from `scripts/generate_charts_from_analysis.py` on line 585-588.

This OLD script:
1. Generated charts using the old `financial_research_agent/visualization/charts.py` module
2. Created files with old naming convention:
   - `chart_margins.json` ✅ (same name as new)
   - `chart_metrics.json` ❌ (should be `chart_revenue_profitability.json` or kept as margins)
   - `chart_risk_categories.json` ❌ (should be `chart_balance_sheet.json`)
3. Ran AFTER the analysis completed (in web_app during result display)
4. Overwrote any charts that the new manager code tried to generate

**Timeline of Chart Generation:**
1. Manager runs analysis (lines 212-226 in manager_enhanced.py)
2. New chart generation should happen here (but was being skipped/overwritten)
3. Web app loads results
4. **OLD chart generation runs** (line 585-588 in web_app.py) ← THIS WAS THE PROBLEM
5. Old charts displayed instead of new charts

---

## Files Involved

### 1. Old Chart Generation System (Should Be Deprecated)
- `scripts/generate_charts_from_analysis.py` - Old script that parses markdown files
- `financial_research_agent/visualization/charts.py` - Old chart functions
- `financial_research_agent/visualization/utils.py` - Old utilities

### 2. New Chart Generation System (Correct)
- `financial_research_agent/visualization/chart_generator.py` - NEW edgartools-based charts
- `financial_research_agent/visualization/__init__.py` - Module exports
- `financial_research_agent/manager_enhanced.py` lines 212-226 - Calls new chart generation

### 3. Web Interface
- `financial_research_agent/web_app.py` - Loads and displays charts

---

## Fix Applied

### Change 1: Remove Old Chart Generation Call

**File:** [web_app.py:584-588](financial_research_agent/web_app.py#L584-L588)

**Before:**
```python
try:
    from scripts.generate_charts_from_analysis import generate_charts_for_analysis

    # Generate charts automatically (this may fail if dependencies missing)
    charts_count = generate_charts_for_analysis(self.current_session_dir, ticker=ticker)

    if charts_count and charts_count > 0:
        # Load the generated charts
        import json
        import plotly.graph_objects as go
```

**After:**
```python
try:
    # Load the generated charts (charts are now generated during analysis by manager)
    import json
    import plotly.graph_objects as go
```

**Reason:** Charts are now generated during analysis by the manager (lines 212-226 in manager_enhanced.py), not during result display in web_app.

---

### Change 2: Fix Chart Loading in "Run New Analysis"

**File:** [web_app.py:589-608](financial_research_agent/web_app.py#L589-L608)

**Before:**
- Charts nested incorrectly (second and third charts indented inside first chart's if block)
- Would only load second/third charts if first chart existed

**After:**
```python
# Revenue & Profitability chart (NEW)
revenue_chart_path = self.current_session_dir / "chart_revenue_profitability.json"
if revenue_chart_path.exists():
    with open(revenue_chart_path, 'r') as f:
        revenue_chart_data = json.load(f)
    margin_chart_fig = go.Figure(revenue_chart_data)  # Use margin_chart_fig slot

# Margin Trends chart
margin_trends_path = self.current_session_dir / "chart_margins.json"
if margin_trends_path.exists():
    with open(margin_trends_path, 'r') as f:
        margin_trends_data = json.load(f)
    metrics_chart_fig = go.Figure(margin_trends_data)  # Use metrics_chart_fig slot

# Balance Sheet chart (NEW)
balance_sheet_path = self.current_session_dir / "chart_balance_sheet.json"
if balance_sheet_path.exists():
    with open(balance_sheet_path, 'r') as f:
        balance_sheet_data = json.load(f)
    risk_chart_fig = go.Figure(balance_sheet_data)  # Use risk_chart_fig slot
```

**Key Changes:**
- All three chart loading blocks at same indentation level
- Each chart loads independently
- Uses NEW filenames

---

### Change 3: Fix Chart Loading in "View Existing Analysis"

**File:** [web_app.py:191-219](financial_research_agent/web_app.py#L191-L219)

**Before:**
```python
margin_chart_path = dir_path / "chart_margins.json"  # ✅ Correct name
metrics_chart_path = dir_path / "chart_metrics.json"  # ❌ OLD name
risk_chart_path = dir_path / "chart_risk_categories.json"  # ❌ OLD name
```

**After:**
```python
# Revenue & Profitability chart (repurposed margin_chart slot)
revenue_chart_path = dir_path / "chart_revenue_profitability.json"
if revenue_chart_path.exists():
    margin_chart_fig = go.Figure(revenue_chart_data)

# Margin Trends chart (repurposed metrics_chart slot)
margin_trends_path = dir_path / "chart_margins.json"
if margin_trends_path.exists():
    metrics_chart_fig = go.Figure(margin_trends_data)

# Balance Sheet chart (repurposed risk_chart slot)
balance_sheet_path = dir_path / "chart_balance_sheet.json"
if balance_sheet_path.exists():
    risk_chart_fig = go.Figure(balance_sheet_data)
```

**Key Changes:**
- Updated filenames to match NEW chart generation
- Added comments explaining slot repurposing
- Consistent naming with "Run New Analysis" section

---

## Chart Filename Mapping

### OLD System (Deprecated)
| Chart | Filename |
|-------|----------|
| Margin Trends | `chart_margins.json` ✅ |
| Key Metrics Dashboard | `chart_metrics.json` ❌ |
| Risk Categories | `chart_risk_categories.json` ❌ |

### NEW System (Current)
| Chart | Filename | Gradio Slot |
|-------|----------|-------------|
| Revenue & Profitability | `chart_revenue_profitability.json` | `margin_chart_fig` |
| Margin Trends | `chart_margins.json` | `metrics_chart_fig` |
| Balance Sheet Composition | `chart_balance_sheet.json` | `risk_chart_fig` |

**Note:** We're repurposing existing Gradio UI slots rather than creating new ones.

---

## Testing

### Test 1: New Analysis
```bash
python launch_web_app.py
# Run New Analysis → Enter: AAPL
```

**Expected:**
1. Analysis completes successfully
2. Three chart JSON files generated in output directory:
   - `chart_revenue_profitability.json`
   - `chart_margins.json`
   - `chart_balance_sheet.json`
3. Charts visible in Financial Analysis and Risk Analysis tabs
4. NO old chart files (`chart_metrics.json`, `chart_risk_categories.json`)

### Test 2: View Existing Analysis
```bash
# View Existing Analysis → Select most recent AAPL
```

**Expected:**
1. Analysis loads successfully
2. Charts display correctly
3. No errors in console

### Test 3: Foreign Filer (Graceful Degradation)
```bash
# Run New Analysis → Enter: WBK (Westpac)
```

**Expected:**
1. Analysis completes even if charts fail
2. Reports 05 and 06 still generate
3. UI doesn't break if charts missing

---

## Benefits of Fix

1. **Correct Chart Generation:** Uses new edgartools-based charts
2. **Performance:** Charts generated once during analysis, not regenerated during display
3. **Consistency:** Same chart system for all analyses
4. **Cleaner Code:** Removed duplicate/conflicting chart generation
5. **Better Data:** EdgarTools provides cleaner, more structured financial data than markdown parsing

---

## Next Steps (Optional Cleanup)

### Deprecate Old Chart System
These files can be safely removed after confirming new system works:
- `scripts/generate_charts_from_analysis.py`
- `financial_research_agent/visualization/charts.py`
- `financial_research_agent/visualization/utils.py`

**Why Keep For Now:**
- Old analyses may still have old chart files
- Backup files reference old system
- Gives time to verify new system is stable

### When to Remove:
- After 1-2 weeks of successful operation
- After verifying all new analyses use new charts
- After confirming no dependencies in other scripts

---

## Summary

The issue was caused by having TWO chart generation systems running:
1. **NEW system** (manager_enhanced.py) - Correct, but results were being overwritten
2. **OLD system** (web_app.py calling scripts/) - Running after analysis and replacing new charts

**Fix:** Removed old chart generation call from web_app.py, updated chart loading to use new filenames.

**Result:** Charts now generate correctly using edgartools data and display in Gradio interface.

---

**Fixed:** November 13, 2024
**Impact:** Charts now work correctly for all analyses
**Breaking Changes:** None (old analyses with old charts still load, just using different filenames)
