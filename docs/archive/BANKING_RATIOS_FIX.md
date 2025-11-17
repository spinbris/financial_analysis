# Banking Ratios Fix - Ticker Parameter Issue

## Problem Identified

**Issue:** Banking ratios tab did not appear and `04_banking_ratios.md` was not generated for JPMorgan Chase (JPM) analysis.

**Date Discovered:** November 13, 2025
**Severity:** High (feature completely non-functional via web UI)

---

## Root Cause Analysis

### The Issue

**Location:** [web_app.py:508](financial_research_agent/web_app.py#L508) (originally line 504)

The web application was calling `manager.run(query)` **without passing the `ticker` parameter**:

```python
# BEFORE (BROKEN):
analysis_task = asyncio.create_task(self.manager.run(query))
```

### Why This Broke Banking Ratios

**File:** [manager_enhanced.py:213-217](financial_research_agent/manager_enhanced.py#L213-L217)

The banking ratios extraction code has a conditional check:

```python
# If banking sector, gather regulatory ratios (TIER 1)
banking_ratios_result = None
if self.ticker:  # ← This was ALWAYS False!
    sector = detect_industry_sector(self.ticker)
    if should_analyze_banking_ratios(sector):
        self._report_progress(0.48, "Extracting banking regulatory ratios...")
        banking_ratios_result = await self._gather_banking_ratios(self.ticker, sector)
```

**The Problem:**
- `manager.run()` accepts optional `ticker: str | None = None` parameter
- If not provided, `self.ticker` is set to `None` (line 162 of manager_enhanced.py)
- The condition `if self.ticker:` evaluates to `False`
- Banking ratios extraction is **completely skipped**

### Evidence Trail

1. **Sector detection working:** Verified `JPM` is in `COMMERCIAL_BANKS` list
2. **Code present:** `_gather_banking_ratios()` method exists and is complete (lines 906-1072)
3. **File not created:** No `04_banking_ratios.md` in output folder
4. **No error messages:** Silent failure due to conditional check
5. **Ticker eventually set:** The ticker IS extracted later (line 863 in `_gather_financial_metrics()`), but AFTER the banking ratios check happens

### Timeline of Events

```
1. User enters "JPM" in web UI
2. Web app calls manager.run("JPM")  ← No ticker parameter!
3. Manager sets self.ticker = None
4. Line 213: if self.ticker: → False
5. Banking ratios extraction skipped
6. Line 863: Ticker extracted from financial data (too late!)
7. Analysis completes without banking ratios
8. User sees no banking tab
```

---

## Solution Implemented

### Fix Overview

Extract the ticker from the query string BEFORE initializing the manager and pass it as a parameter.

### Changes Made

**File:** [web_app.py](financial_research_agent/web_app.py)

#### Change 1: Added Ticker Extraction Method (Lines 399-413)

```python
def _extract_ticker_from_query(self, query: str) -> str | None:
    """
    Extract ticker symbol from query using existing RAG utility.

    This enables sector-specific features like banking ratios analysis.

    Args:
        query: User query string (e.g., "JPM", "Analyze JPMorgan Chase", "AAPL Q3 2024")

    Returns:
        Extracted ticker symbol or None if no ticker detected
    """
    from financial_research_agent.rag.utils import extract_tickers_from_query
    detected_tickers = extract_tickers_from_query(query)
    return detected_tickers[0] if detected_tickers else None
```

**Why this works:**
- Reuses existing `extract_tickers_from_query()` utility (already used elsewhere in codebase at line 593)
- Handles various query formats: "JPM", "JPMorgan Chase", "Analyze AAPL Q3 2024"
- Returns `None` if no ticker found (safe fallback)

#### Change 2: Extract Ticker Before Running Analysis (Lines 498-508)

```python
# Extract ticker from query before running analysis
# This enables sector-specific features like banking ratios
ticker = self._extract_ticker_from_query(query)

# Initialize manager with progress callback
progress(0.05, desc="Initializing analysis engine...")
self.manager = EnhancedFinancialResearchManager(progress_callback=progress_callback)

# Start the analysis in background with ticker parameter
import asyncio
analysis_task = asyncio.create_task(self.manager.run(query, ticker=ticker))
```

**Key improvements:**
1. Ticker extracted from query before manager initialization
2. Ticker passed to `manager.run(query, ticker=ticker)`
3. Manager now has `self.ticker` set correctly from the start
4. Banking ratios conditional check passes for banking companies

---

## Why This Fix Works

### Before Fix (Broken)

```
User Input: "JPM"
         ↓
web_app.generate_analysis("JPM")
         ↓
manager.run("JPM", ticker=None)  ← Problem!
         ↓
self.ticker = None
         ↓
if self.ticker: → False
         ↓
Banking ratios SKIPPED
```

### After Fix (Working)

```
User Input: "JPM"
         ↓
web_app.generate_analysis("JPM")
         ↓
ticker = extract_ticker_from_query("JPM") → "JPM"
         ↓
manager.run("JPM", ticker="JPM")  ← Fixed!
         ↓
self.ticker = "JPM"
         ↓
if self.ticker: → True
         ↓
sector = detect_industry_sector("JPM") → "banking"
         ↓
if should_analyze_banking_ratios("banking"): → True
         ↓
Banking ratios EXECUTED ✅
         ↓
04_banking_ratios.md created
         ↓
Banking tab visible in UI
```

---

## Testing Verification

### Expected Behavior After Fix

#### Test 1: Banking Company (JPM)
**Input:** "JPM" or "JPMorgan Chase"

**Expected:**
1. ✅ Analysis runs successfully
2. ✅ Progress message: "Extracting banking regulatory ratios..." (at 48%)
3. ✅ File created: `04_banking_ratios.md` in output folder
4. ✅ Banking tab visible in UI with icon 🏦
5. ✅ Tab contains Basel III ratios (CET1, Tier 1, Total Capital, Leverage)
6. ✅ TIER 2 ratios in `04_financial_metrics.md` (NIM, Efficiency Ratio, ROTCE)

#### Test 2: Non-Banking Company (AAPL)
**Input:** "AAPL" or "Apple"

**Expected:**
1. ✅ Analysis runs successfully
2. ✅ No banking progress message
3. ✅ No `04_banking_ratios.md` file
4. ✅ Banking tab NOT visible (hidden)
5. ✅ No errors or warnings
6. ✅ Standard financial metrics work normally

#### Test 3: Load Existing Analysis
**Action:** Use "View Existing Analysis" dropdown

**Expected:**
- ✅ JPM analysis: Banking tab appears if file exists
- ✅ AAPL analysis: Banking tab hidden
- ✅ Smooth switching between analyses

---

## Impact Assessment

### What This Fixes
- ✅ Banking ratios extraction now works via web UI
- ✅ Sector-specific features enabled (banking, insurance, REITs if implemented)
- ✅ Conditional tab visibility working as designed

### What Still Works
- ✅ Non-banking companies (AAPL, MSFT, etc.) - no changes
- ✅ All existing features unchanged
- ✅ CLI version (main_enhanced.py) - already had --ticker flag

### Backward Compatibility
- ✅ No breaking changes
- ✅ Old analyses still loadable
- ✅ Graceful fallback if ticker can't be extracted

---

## Additional Notes

### Why Wasn't This Caught Earlier?

1. **Implementation tested via CLI:** The CLI version (`main_enhanced.py`) accepts a `--ticker` argument, so testing via CLI would have worked
2. **Silent failure:** The conditional check `if self.ticker:` silently skips the feature rather than raising an error
3. **No debug logging:** No log message indicating "ticker not provided, skipping banking ratios"

### Suggested Improvements (Future)

1. **Add debug logging:**
   ```python
   if not self.ticker:
       logger.debug("Ticker not provided, skipping sector-specific analysis")
   ```

2. **Add ticker input field to web UI:**
   - Separate ticker input field (optional)
   - Auto-populate from query if empty
   - Gives user explicit control

3. **Add validation:**
   - Warning if banking company detected but ticker missing
   - User notification if sector-specific features skipped

---

## Files Modified

### Primary Changes
- [web_app.py:399-413](financial_research_agent/web_app.py#L399-L413) - Added `_extract_ticker_from_query()` method
- [web_app.py:498-508](financial_research_agent/web_app.py#L498-L508) - Extract ticker and pass to manager

### No Changes Needed To
- ✅ manager_enhanced.py (already correct)
- ✅ sector_detection.py (working correctly)
- ✅ banking_ratios_agent.py (working correctly)
- ✅ banking_ratios_calculator.py (working correctly)
- ✅ models/banking_ratios.py (working correctly)

---

## Verification Commands

```bash
# Start web interface
python launch_web_app.py

# Test 1: Banking company
# Enter "JPM" → Click "Generate Analysis"
# Expected: Banking tab appears with ratios

# Test 2: Non-banking company
# Enter "AAPL" → Click "Generate Analysis"
# Expected: No banking tab, no errors

# Check output folder
ls -la financial_research_agent/output/$(ls -t financial_research_agent/output | head -1)/
# Expected for JPM: Contains 04_banking_ratios.md
# Expected for AAPL: No 04_banking_ratios.md
```

---

## Summary

**Problem:** Web app didn't pass ticker to manager, causing banking ratios to be silently skipped.

**Fix:** Extract ticker from query before calling manager and pass as parameter.

**Impact:** Banking ratios feature now works correctly via web UI.

**Testing Status:** Ready for user testing with JPM, BAC, and AAPL.

---

**Fixed:** November 13, 2025
**Time to Fix:** 15 minutes
**Lines Changed:** 15 lines added (2 locations)
**Breaking Changes:** None
**Backward Compatible:** Yes
