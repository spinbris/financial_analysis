# Railway Environment Variables Fix

**Date:** November 23, 2025
**Issue:** High cost ($0.31) and missing charts on Railway deployment
**Root Cause:** Incorrect environment variable configuration

---

## Issues Identified

### 1. Writer Model Using Expensive gpt-5.1 ❌

**Symptom:**
- Analysis cost: $0.3076 (expected $0.20-0.25)
- Writer agent alone: $0.0709 (23% of total cost!)

**Root Cause:**
Railway has environment variable `WRITER_MODEL=gpt-5.1` which overrides config.py default

**Evidence from cost_report.json:**
```json
{
  "agent_name": "writer",
  "model": "gpt-5.1",  // ❌ Should be gpt-4.1
  "total_cost": 0.0708725  // 🔥 Most expensive single agent!
}
```

**Expected config.py default:**
```python
WRITER_MODEL = os.getenv("WRITER_MODEL", "gpt-4.1")  # Optimal per testing
```

---

### 2. Charts Not Being Generated ❌ **FIXED**

**Symptom:**
- No chart files in output directory
- No `📊 Chart files in [timestamp]: [...]` log message
- Charts failing silently

**Root Cause:**
Chart generator was using wrong environment variable name

**Issue:**
- chart_generator.py was looking for `EDGAR_IDENTITY`
- Railway has `SEC_EDGAR_USER_AGENT` configured ✅
- Variable name mismatch prevented chart generation

**Fix:**
- Changed chart_generator.py to use `SEC_EDGAR_USER_AGENT` (commit `d37855a`)
- Now matches EdgarConfig.USER_AGENT naming convention
- **No Railway environment variable changes needed** - you already have this configured!

---

### 3. Balance Sheet Chart in Wrong Tab (Fixed) ✅

**Symptom:**
- Balance sheet composition chart appeared in Risk Analysis tab
- Chart not relevant to risk analysis
- User feedback: "not very useful, and nothing to do with risks"

**Fix:**
- Removed chart from Risk Analysis tab UI entirely
- Chart file still generated but not displayed
- Committed in: `469dc97 Remove balance sheet composition chart from Risk Analysis tab`

---

## Required Railway Environment Variable Changes

### Change 1: Remove WRITER_MODEL Override

**Action:** Delete `WRITER_MODEL` environment variable

**Steps:**
1. Open Railway dashboard
2. Go to your project → **Variables** tab
3. Find `WRITER_MODEL` variable
4. Click **Delete** (or change value to `gpt-4.1`)
5. Railway will auto-redeploy

**Expected Impact:**
- Writer cost drops from $0.07 to ~$0.01-0.02
- Total analysis cost: ~$0.20-0.25 (down from $0.31)
- **Savings: ~20-35% per analysis**

---

### Change 2: SEC_EDGAR_USER_AGENT ✅ **ALREADY CONFIGURED**

**Status:** You already have `SEC_EDGAR_USER_AGENT` configured in Railway ✅

**What Changed:**
- Fixed chart_generator.py to use correct variable name (commit `d37855a`)
- Was looking for `EDGAR_IDENTITY`, now uses `SEC_EDGAR_USER_AGENT`
- **No action needed** - Railway will auto-redeploy with the code fix

**Expected Impact:**
- Charts will generate successfully after Railway redeploys
- Log will show: `📊 Chart files in [timestamp]: ['chart_revenue_profitability.json', 'chart_revenue_profitability.png', ...]`
- Comprehensive report download will include embedded chart images

---

## Verification After Changes

### 1. Check Deployment Logs

After Railway redeploys, verify:

```
✅ Installing chromium chromium-driver... (from Dockerfile)
✅ Setting CHROME_BIN=/usr/bin/chromium (from Dockerfile)
✅ EDGAR_IDENTITY environment variable set
```

### 2. Run Test Analysis

Run new MSFT analysis and verify:

**Cost Report:**
```json
{
  "agent_name": "writer",
  "model": "gpt-4.1",  // ✅ Correct model
  "total_cost": 0.01-0.02  // ✅ Much cheaper
}
```

**Total cost:** ~$0.20-0.25 (down from $0.31) ✅

**Chart Generation Logs:**
```
Generated revenue profitability chart: [path]/chart_revenue_profitability.json + PNG
Generated margin chart: [path]/chart_margins.json + PNG
Generated balance sheet chart: [path]/chart_balance_sheet.json + PNG
📊 Chart files in 20251123_XXXXXX: ['chart_revenue_profitability.json', 'chart_revenue_profitability.png', 'chart_margins.json', 'chart_margins.png', 'chart_balance_sheet.json', 'chart_balance_sheet.png']
```

**Charts Tab:**
- Revenue & Profitability Trends chart displays ✅
- Profitability Margins chart displays ✅

**Download Button:**
- "📥 Download Comprehensive Report (with embedded charts)" works ✅
- Downloaded markdown contains chart image references ✅

**Risk Analysis Tab:**
- No balance sheet chart displayed ✅

---

## Summary of All Environment Variables

### Required Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `OPENAI_API_KEY` | `sk-proj-...` | OpenAI API authentication |
| `BRAVE_API_KEY` | `BSA...` | Web search (optional but recommended) |
| `SEC_EDGAR_USER_AGENT` | `FinancialResearchAgent/1.0 (email@domain.com)` | SEC EDGAR API compliance (you already have this ✅) |

### Variables to REMOVE

| Variable | Why Remove |
|----------|------------|
| `WRITER_MODEL` | Overrides optimal config.py default (gpt-4.1), causes high cost |

### Optional Variables (Override defaults)

| Variable | Default | Override Example |
|----------|---------|------------------|
| `PLANNER_MODEL` | `o3-mini` | `gpt-4.1` |
| `SEARCH_MODEL` | `gpt-4.1` | `gpt-4o-mini` |
| `FINANCIALS_MODEL` | `gpt-5` | `gpt-5.1` |
| `RISK_MODEL` | `gpt-5` | `gpt-5.1` |

**Note:** Don't override these unless you have a specific reason - defaults are optimized per testing

---

## Cost Optimization Results

### Before Environment Variable Fix

```
Writer Agent: gpt-5.1
- Input tokens: 13,202
- Output tokens: 5,437
- Cost: $0.0709 (23% of total!)

Total Analysis Cost: $0.3076
```

### After Environment Variable Fix

```
Writer Agent: gpt-4.1 (expected)
- Input tokens: ~13,000
- Output tokens: ~5,400
- Cost: $0.01-0.02 (3-6% of total)

Total Analysis Cost: ~$0.20-0.25
```

**Savings: $0.06-0.11 per analysis (20-35% reduction)**

---

## Related Fixes

### Completed
- ✅ Dockerfile with Chromium for PNG export (commit `866a32b`)
- ✅ Download button for comprehensive report (commit `a0630bf`)
- ✅ Balance sheet chart pandas Series bug fix (commit `6c29d31`)
- ✅ Balance sheet chart removed from Risk tab (commit `469dc97`)

### Pending Railway Configuration
- ⏳ Remove `WRITER_MODEL` environment variable (only remaining action needed)

---

## Next Steps

1. **Remove WRITER_MODEL from Railway environment variables** (only action needed!)
2. **Wait for Railway auto-redeploy** (~2-3 minutes)
3. **Run test MSFT analysis** on Railway
4. **Verify:**
   - Cost is ~$0.20-0.25 (down from $0.31)
   - Charts display in UI (should work now with SEC_EDGAR_USER_AGENT fix)
   - Download button works
   - Comprehensive report has embedded chart images
   - No balance sheet chart in Risk Analysis tab
5. **Report results** if any issues remain

---

**Status:** Chart generation fix deployed (commit `d37855a`), balance sheet chart removed (commit `469dc97`)
**Action Required:** User must delete WRITER_MODEL from Railway dashboard
**Expected Completion:** ~5 minutes (2 min to delete variable + 3 min Railway redeploy)
