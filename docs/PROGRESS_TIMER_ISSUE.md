# Progress Timer Display Issue

**Date**: 2025-11-09
**Status**: ⚠️ KNOWN ISSUE - Documented for Future Fix

---

## Problem

The Gradio web app progress bar behaves incorrectly during financial analysis:

1. **Resets for each step** - Progress goes 0→100% for each individual agent step instead of showing cumulative progress
2. **No step description** - User cannot see which step is currently executing (e.g., "Analyzing financials...", "Generating risk analysis...")
3. **Misleading completion** - Shows 100% completion multiple times before analysis is actually complete

**User Feedback**: "there is no description of where it is up to and it seems to be running for each individual process then resetting"

---

## Current Behavior

```
Step 1: Planning analysis...    [████████████████████] 100%
Step 2: Downloading SEC data... [████████████████████] 100%
Step 3: Analyzing financials... [████████████████████] 100%
Step 4: Analyzing risk...       [████████████████████] 100%
...

User sees: Progress bar repeatedly filling and resetting
```

**Expected Behavior**:

```
Overall Progress: [████████░░░░░░░░░░░░] 40%
Currently: Analyzing financial statements...
```

---

## Root Cause

**File**: [web_app.py:345-444](financial_research_agent/web_app.py#L345-L444)

The `progress_callback` is called by `EnhancedFinancialResearchManager` during analysis, but the manager reports progress for **each individual agent step** (0-100%), not overall progress.

### How Progress Currently Works:

1. **Manager calls**: `progress_callback(0.2, "Downloading filings...")`
2. **Web app updates**: Progress bar to 20%
3. **Next step starts**: `progress_callback(0.1, "Analyzing financials...")`
4. **Progress resets**: Bar goes back to 10%

### Why This Happens:

Each agent in the workflow (planner → edgar → financials → risk → metrics → writer) reports its own progress independently. The system doesn't track:
- Total number of steps
- Current step number
- Overall completion percentage

---

## Technical Details

### Progress Implementation

**File**: [web_app.py:391-418](financial_research_agent/web_app.py#L391-L418)

```python
def _run_comprehensive_analysis(self, ticker: str, progress=gr.Progress()):
    """Run comprehensive analysis with progress tracking."""
    def progress_callback(pct: float, msg: str):
        progress(pct, desc=msg)

    try:
        progress(0, desc="Starting analysis...")

        result = self.manager.run_comprehensive_analysis(
            ticker=ticker,
            progress_callback=progress_callback
        )

        # ... result processing ...
```

**Problem**: `progress_callback` receives progress from individual agents, not overall workflow.

### Where Progress Originates

**File**: `financial_research_agent/manager.py` (EnhancedFinancialResearchManager)

The manager calls `progress_callback` during:
- `run_planner_agent()`
- `run_edgar_agent()`
- `run_financial_statement_agent()`
- `run_risk_agent()`
- `run_metrics_agent()`
- `run_writer_agent()`

Each agent reports 0-100% progress for its own task, causing the bar to reset.

---

## Impact

**Severity**: Low - Cosmetic issue only
- ✅ Analysis completes successfully
- ✅ All functionality works correctly
- ⚠️ Progress indication is misleading but doesn't block usage

**User Experience**: Confusing progress indication makes it unclear:
- How much of the overall analysis is complete
- What step is currently running
- How long the remaining work will take

---

## Potential Solutions

### Option 1: Track Overall Progress (Recommended)

**Approach**: Modify manager to calculate overall completion across all steps.

**Implementation**:
```python
# In EnhancedFinancialResearchManager:
TOTAL_STEPS = 7  # planner, edgar, financials, risk, metrics, writer, verification

def run_comprehensive_analysis(self, ticker, progress_callback=None):
    current_step = 0

    def step_progress(step_name: str, step_pct: float):
        # Calculate overall progress
        overall_pct = (current_step + step_pct) / TOTAL_STEPS
        progress_callback(overall_pct, f"Step {current_step+1}/{TOTAL_STEPS}: {step_name}")

    # Step 1: Planning
    current_step = 0
    result = run_planner_agent(progress=lambda p, m: step_progress(m, p))

    # Step 2: EDGAR
    current_step = 1
    result = run_edgar_agent(progress=lambda p, m: step_progress(m, p))

    # ... etc
```

**Pros**: Accurate cumulative progress, clear step indication
**Cons**: Requires refactoring manager.py

### Option 2: Simplified Step-Based Progress

**Approach**: Show step numbers without percentage.

**Implementation**:
```python
def progress_callback(step_num: int, step_name: str):
    progress(step_num / 7, desc=f"Step {step_num}/7: {step_name}")
```

**Pros**: Simple, no need for percentage tracking within steps
**Cons**: Less granular feedback

### Option 3: Disable Progress Bar

**Approach**: Remove progress bar, show simple status message.

**Implementation**:
```python
# Remove progress parameter
def _run_comprehensive_analysis(self, ticker: str):
    status = gr.Textbox(value="Analysis in progress...")
    # ... run analysis ...
    status.update(value="Analysis complete!")
```

**Pros**: No misleading information
**Cons**: Less user feedback

---

## Recommended Fix

**Phase 2 or 3** of UX redesign should implement **Option 1** (Overall Progress Tracking):

1. Modify `EnhancedFinancialResearchManager.run_comprehensive_analysis()`
2. Add step tracking: `current_step / TOTAL_STEPS`
3. Pass step names to progress_callback
4. Update web_app.py to display: "Step X/Y: Description"

**Estimated Effort**: 1-2 hours
**Priority**: Medium - UX improvement, not critical

---

## Workaround

**For Now**: Users should understand that:
- Multiple progress bars will appear during analysis
- Each bar represents a different step
- Analysis is complete when final report appears
- Typical analysis takes 2-3 minutes total

---

## Decision Log

**User Decision (2025-11-09)**: "ok just leave as is and document as an issue"

**Rationale**:
- System is working correctly (analyses complete successfully)
- Progress indication is cosmetic issue only
- Phase 1 complete, don't want to risk breaking working system
- Can improve in Phase 2 or 3 when doing broader UX work

---

## Related Files

- [web_app.py:345-444](financial_research_agent/web_app.py#L345-L444) - Progress callback implementation
- `financial_research_agent/manager.py` - EnhancedFinancialResearchManager (calls progress_callback)

---

## Testing Notes

When implementing fix, test with:
1. Short analysis (gpt-5-nano models) - verify progress doesn't skip
2. Long analysis (gpt-5 models) - verify progress is smooth
3. Analysis with errors - verify progress handles failures gracefully

---

**Status**: Documented ⚠️
**Next Action**: Implement fix during Phase 2 or 3 UX redesign
**Priority**: Medium (UX improvement)
