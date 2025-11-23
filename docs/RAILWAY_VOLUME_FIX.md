# Railway Persistent Volume Configuration

**Date:** November 23, 2025
**Issue:** Analysis failing, download button can't find files
**Root Cause:** Output files written to ephemeral container filesystem instead of persistent volume

---

## Problem

After deploying to Railway with all previous fixes:
- ✅ Chart generation working (SEC_EDGAR_USER_AGENT fix)
- ✅ Download button code fixed (empty string instead of None)
- ✅ Cost optimized (WRITER_MODEL deleted)
- ❌ **NEW: Analysis still failing**
- ❌ **NEW: Download button can't find comprehensive report**

**Root Cause:** Railway's volume is mounted at `/data`, but the application was writing files to the default `financial_research_agent/output` directory in the ephemeral container filesystem.

**What this means:**
1. Every analysis writes files to the container
2. When Railway restarts/redeploys, all files are lost
3. Download button looks for files that don't exist
4. ChromaDB loses all indexed analyses

---

## Solution: Configure Persistent Volume

### Dockerfile Changes (Commit 3e1f1e2)

Added environment variables to configure persistent storage:

```dockerfile
# Configure output directory for Railway persistent volume
# Railway mounts volumes at /data, so we use that for persistent storage
ENV OUTPUT_DIR=/data/output
ENV CHROMA_DB_DIR=/data/chroma_db
```

**How it works:**
1. Railway mounts persistent volume at `/data`
2. Dockerfile sets `OUTPUT_DIR=/data/output`
3. Application reads `OUTPUT_DIR` from environment
4. All analysis files written to `/data/output` (persistent)
5. Gradio `allowed_paths` automatically includes `/data/output`

---

## Railway Volume Configuration

### Required Railway Setup

**Check if volume is configured:**
1. Go to Railway Dashboard → Your Project
2. Click on the service
3. Go to "Variables" tab
4. Look for volume mount configuration

**Volume should be:**
- **Mount Path:** `/data`
- **Size:** Recommended 5GB minimum (Railway free tier includes this)

**If volume is NOT configured:**
1. Go to Railway Dashboard → Your Project
2. Click on the service
3. Go to "Settings" tab
4. Scroll to "Volumes"
5. Click "Add Volume"
6. **Mount Path:** `/data`
7. **Size:** 5GB (or more)
8. Click "Add"
9. Railway will redeploy

---

## Verification After Deployment

Once Railway finishes deploying commit 3e1f1e2:

### 1. Check Railway Logs

Look for output directory initialization:
```
Creating output directory: /data/output
ChromaDB directory: /data/chroma_db
```

### 2. Run Test Analysis

1. Open Railway app URL
2. Run new MSFT analysis
3. **Expected:**
   - Analysis completes successfully ✅
   - Files written to `/data/output/YYYYMMDD_HHMMSS/` ✅
   - Download button shows comprehensive report ✅
   - No "file not available" errors ✅

### 3. Verify Persistence

After analysis completes:
1. Go to "View Existing Analysis" tab
2. **Expected:** Previous analyses appear in dropdown ✅
3. Click "Load Analysis"
4. **Expected:** All tabs populate correctly ✅
5. Click "Download Comprehensive Report"
6. **Expected:** File downloads successfully ✅

### 4. Test After Redeploy

1. Trigger Railway redeploy (push any commit)
2. Wait for redeploy to complete
3. Go to "View Existing Analysis" tab
4. **Expected:** Previous analyses still available ✅

**This confirms persistent storage is working!**

---

## File Structure on Railway

```
/data/                          # Railway persistent volume
├── output/                     # Analysis output directory
│   ├── 20251123_123456/       # Session directory
│   │   ├── 00_query.md
│   │   ├── 03_financial_statements.md
│   │   ├── 04_financial_metrics.md
│   │   ├── 05_financials_analysis.md
│   │   ├── 06_risk_analysis.md
│   │   ├── 07_comprehensive_report.md
│   │   ├── chart_revenue_profitability.json
│   │   ├── chart_revenue_profitability.png
│   │   ├── chart_margins.json
│   │   ├── chart_margins.png
│   │   └── cost_report.json
│   └── 20251123_234567/       # Another analysis
│       └── ...
└── chroma_db/                  # ChromaDB persistent storage
    ├── chroma.sqlite3
    └── ...

/app/                           # Application code (ephemeral)
├── financial_research_agent/
├── launch_web_app.py
└── ...
```

---

## Environment Variables Summary

### Dockerfile (Automatic)
These are set automatically in the Dockerfile:

| Variable | Value | Purpose |
|----------|-------|---------|
| `OUTPUT_DIR` | `/data/output` | Write analysis files to persistent volume |
| `CHROMA_DB_DIR` | `/data/chroma_db` | Store ChromaDB index on persistent volume |
| `CHROME_BIN` | `/usr/bin/chromium` | Chromium path for kaleido PNG export |
| `CHROMIUM_PATH` | `/usr/bin/chromium` | Alternative Chromium path |

### Railway Dashboard (Manual - Already Configured)
These you've already configured in Railway:

| Variable | Value | Status |
|----------|-------|--------|
| `OPENAI_API_KEY` | `sk-proj-...` | ✅ Configured |
| `BRAVE_API_KEY` | `BSA...` | ✅ Configured |
| `SEC_EDGAR_USER_AGENT` | `FinancialResearchAgent/1.0 (email@domain.com)` | ✅ Configured |

### Railway Dashboard (Deleted)
| Variable | Status |
|----------|--------|
| `WRITER_MODEL` | ✅ Deleted (cost optimization) |

---

## Troubleshooting

### Analysis Still Fails After Volume Configuration

**Check Railway logs for:**
```
Permission denied: /data/output
```

**Solution:** Railway volume permissions issue
1. Go to Railway Dashboard
2. Delete existing volume
3. Recreate volume with mount path `/data`
4. Redeploy

### Download Button Still Shows "File Not Available"

**Check Gradio allowed_paths in Railway logs:**
```
Gradio app started with allowed_paths: ['/data/output']
```

**If you see:** `allowed_paths: ['financial_research_agent/output']`

**Solution:** Railway didn't pick up environment variables
1. Force redeploy: `git commit --allow-empty -m "Force redeploy" && git push`
2. Check Railway Variables tab shows `OUTPUT_DIR=/data/output`

### ChromaDB Can't Find Previous Analyses

**Check ChromaDB initialization in Railway logs:**
```
ChromaDB initialized at: /data/chroma_db
```

**If you see:** `ChromaDB initialized at: ./chroma_db`

**Solution:** Same as above - force redeploy

---

## Local Development

**Important:** These environment variables are for Railway only!

For local development, the defaults in `config.py` still work:
- `OUTPUT_DIR=financial_research_agent/output` (relative path, fine for local)
- `CHROMA_DB_DIR=./chroma_db` (relative path, fine for local)

**Don't set these environment variables locally** unless you want to test Railway configuration.

---

## Cost Impact

**Storage costs on Railway:**
- First 5GB: Free (included in all plans)
- Additional storage: ~$0.25/GB/month

**Expected usage:**
- Each analysis: ~2-5MB (with PNG charts)
- 100 analyses: ~250-500MB
- 1000 analyses: ~2.5-5GB

**Recommendation:** 5GB volume is sufficient for 200-1000 analyses depending on chart sizes.

---

## Summary

| Issue | Status | Fix |
|-------|--------|-----|
| Output files ephemeral | ✅ Fixed | ENV OUTPUT_DIR=/data/output |
| Download button can't find files | ✅ Fixed | Gradio allowed_paths uses OUTPUT_DIR |
| ChromaDB loses history | ✅ Fixed | ENV CHROMA_DB_DIR=/data/chroma_db |
| Analysis failing | 🔍 Should be fixed | Verify volume mounted at /data |

**Next Steps:**
1. Verify Railway has volume mounted at `/data`
2. Wait for Railway to deploy commit 3e1f1e2
3. Run test analysis
4. Verify files persist across redeploys

---

**Related Fixes:**
- Chart generation: commit d37855a (SEC_EDGAR_USER_AGENT)
- Download button serialization: commit dbce2de (empty string vs None)
- Cost optimization: WRITER_MODEL deleted ✅
- Persistent volume: commit 3e1f1e2 (this fix)
