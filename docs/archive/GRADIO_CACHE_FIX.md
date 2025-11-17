# Gradio Web App Cache Fix

## Issue Description

**Problem:** When running a new analysis in the Gradio web app, the reports displayed were from a **previous analysis** rather than populating gradually with the current analysis in progress.

**Symptom:**
- First analysis works fine
- Second analysis shows old reports immediately
- Reports don't update with new analysis progress
- Error may appear early in processing

## Root Cause

The `WebApp` class maintains a `self.current_session_dir` variable that tracks which analysis directory to load reports from. This variable was:

1. ✅ Set correctly when first analysis completes
2. ❌ **Never reset** between analyses
3. ❌ Caused subsequent analyses to load from OLD directory

### Code Flow (Before Fix)

```python
# First Analysis
analyze("Apple") → Creates 20241113_120000/ → self.current_session_dir = 20241113_120000/ ✓

# Second Analysis
analyze("Microsoft") → Creates 20241113_130000/
                     → But self.current_session_dir STILL = 20241113_120000/ ✗
                     → Loads Apple's old reports instead of Microsoft's new ones
```

## The Fix

**File:** [web_app.py:409-411](financial_research_agent/web_app.py#L409-L411)

**Added at start of `analyze()` function:**

```python
# Reset session directory for new analysis (prevents showing old reports)
self.current_session_dir = None
self.manager = None
```

### Why This Works

1. **`self.current_session_dir = None`**: Clears the old directory path
2. **`self.manager = None`**: Ensures clean manager initialization
3. **Line 487**: Creates fresh manager with `EnhancedFinancialResearchManager()`
4. **Line 503**: Sets `self.current_session_dir = self.manager.session_dir` with NEW directory
5. **Line 506**: Loads reports from correct (new) directory

### Code Flow (After Fix)

```python
# First Analysis
analyze("Apple") → Resets cache → Creates 20241113_120000/ → Shows Apple reports ✓

# Second Analysis
analyze("Microsoft") → Resets cache → Creates 20241113_130000/ → Shows Microsoft reports ✓
```

## Testing

### Before Fix
```
1. Run analysis for AAPL → Works ✓
2. Run analysis for MSFT → Shows AAPL reports ✗
```

### After Fix
```
1. Run analysis for AAPL → Shows AAPL reports ✓
2. Run analysis for MSFT → Shows MSFT reports ✓
3. Run analysis for GOOGL → Shows GOOGL reports ✓
```

## Related Code Sections

### Session Directory Creation
[manager_enhanced.py:162-164](financial_research_agent/manager_enhanced.py#L162-L164)
```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
self.session_dir = self.output_dir / timestamp
self.session_dir.mkdir(parents=True, exist_ok=True)
```

### Report Loading
[web_app.py:638-662](financial_research_agent/web_app.py#L638-L662)
```python
def _load_reports(self) -> dict[str, str]:
    """Load generated markdown reports from session directory."""
    if not self.current_session_dir or not self.current_session_dir.exists():
        return reports

    for key, filename in report_files.items():
        file_path = self.current_session_dir / filename
        if file_path.exists():
            reports[key] = file_path.read_text(encoding='utf-8')
```

### Polling Loop
[web_app.py:492-540](financial_research_agent/web_app.py#L492-L540)
```python
while not analysis_task.done():
    await asyncio.sleep(2)

    if self.manager.session_dir and self.manager.session_dir.exists():
        self.current_session_dir = self.manager.session_dir  # Updates to NEW dir
        new_reports = self._load_reports()  # Loads from NEW dir
```

## Impact

**Before:**
- ❌ Confusing user experience (wrong reports shown)
- ❌ Appearance of analysis not working
- ❌ Can't run multiple analyses in same session

**After:**
- ✅ Each analysis shows its own reports
- ✅ Live updates work correctly
- ✅ Can run unlimited analyses in same session
- ✅ No stale data issues

## Additional Notes

### Why This Wasn't Caught Earlier

1. **First analysis always works** (no prior session to cache)
2. **Testing usually done on fresh starts** (browser refresh resets state)
3. **Issue only appears on second+ analysis** in same Gradio session

### Related Variables

```python
class WebApp:
    def __init__(self):
        self.manager = None                  # ← Now reset
        self.current_session_dir = None      # ← Now reset
        self.current_reports = {}            # Not used, can be removed
        self.analysis_map = {}               # For view existing analyses
        self.session_id = None              # For API key management
```

### Future Improvements

Consider:
1. Explicitly clear `self.current_reports` as well (currently unused)
2. Add session ID to status display
3. Show "Starting new analysis..." message before resetting
4. Add timestamp comparison to detect stale cache

## Verification

To verify the fix works:

```bash
# 1. Start Gradio app
python launch_web_app.py

# 2. Run first analysis
Query: "Analyze Apple"
→ Should show Apple reports ✓

# 3. Run second analysis (same session, don't refresh browser)
Query: "Analyze Microsoft"
→ Should show Microsoft reports (not Apple) ✓

# 4. Run third analysis
Query: "Analyze Google"
→ Should show Google reports ✓
```

## Files Changed

1. ✅ [web_app.py:409-411](financial_research_agent/web_app.py#L409-L411) - Added cache reset

## Related Issues

This fix resolves:
- Reports showing from previous analysis
- Gradio errors when starting new analysis
- Confusion about which analysis is running
- Inability to run multiple analyses in one session

---

**Fix implemented:** November 13, 2024
**Status:** ✅ Tested and working
**Breaking changes:** None (pure bug fix)

---

## Summary

**The Issue:** Session directory cached between analyses
**The Fix:** Reset `self.current_session_dir = None` at start of each analysis
**The Result:** Each analysis shows its own reports correctly

Simple 2-line fix for a frustrating caching bug! 🎉
