# Railway Deployment Guide - Instructions for Claude Code

## Overview
We're moving from Modal (which has async/serverless issues) to Railway.app for proper hosting of the full-featured Gradio financial analysis application.

**Key Decision: Domain Strategy**
- **Recommended**: Point `cblanalytics.com` directly to Railway (simplest, cheapest)
- **Alternative**: Use subdomain `app.cblanalytics.com` for Railway app if you add marketing site later
- **Cost**: $10-20/month for Railway only (vs $15-35/month with separate marketing site)

This guide follows the **recommended approach** (direct domain to Railway).

---

## STEP 1: Clean Up for Railway Deployment

**✅ COMPLETED**: Modal files removed, Groq support removed (OpenAI-only now)

### 1.1 Update .gitignore

Add these lines to `.gitignore`:

```
# Modal-specific files (not needed for Railway)
modal_app.py
modal_app_with_auth.py
modal_app_minimal.py

# Environment files
.env

# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.venv/
venv/

# Output directories (will regenerate on Railway)
financial_research_agent/output/
financial_research_agent/chroma_db/

# System files
.DS_Store
*.log

# IDE
.vscode/
.idea/
```

### 1.2 Verify pyproject.toml Dependencies

Ensure `pyproject.toml` includes ALL required dependencies:

**Core dependencies that MUST be present:**
```toml
[project]
requires-python = ">=3.11"  # IMPORTANT: Specify Python version
dependencies = [
    "gradio>=4.0.0",
    "openai>=1.0.0",
    "openai-agents>=0.4.2",
    "pandas>=2.0.0",
    "edgartools>=2.29.0",
    "yfinance>=0.2.0",
    "plotly>=5.0.0",
    "python-dotenv>=1.0.0",
    "chromadb>=0.4.24",
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    "supabase>=2.0.0",  # Optional: Only if using authentication
    "great-tables>=0.8.0",
    "rich>=13.0.0",
]
```

**Action:** Check if any dependencies are missing and add them.

**Note on Supabase**: Only needed if you want user authentication. For personal/internal use, you can remove Supabase and use Gradio's built-in `auth` parameter instead (simpler and free).

### 1.3 Create/Verify .env.example

Create `.env.example` as a template (WITHOUT actual secrets):

```bash
# .env.example
OPENAI_API_KEY=your_openai_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SEC_EDGAR_USER_AGENT=Your Name your@email.com
```

**Note:** The actual `.env` file should be in `.gitignore` and NOT committed!

### 1.4 Verify launch_web_app_with_auth.py is Ready

Check that `launch_web_app_with_auth.py`:
- ✅ Uses port 7860 (Railway default will work with this)
- ✅ Has `host="0.0.0.0"` (allows external connections)
- ✅ Loads environment variables from `.env`

Should have something like:
```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=7860,
    log_level="info"
)
```

### 1.5 Keep the web_app.py Fix

The commented-out `app.load()` in `financial_research_agent/web_app.py` is GOOD:
```python
# DISABLED FOR MODAL: Scanning analysis folders on volume mount causes 18+ minute startup delay
# app.load(
#     fn=load_dropdown_choices,
#     outputs=[existing_dropdown]
# )
```

**Action:** Keep this as-is. It makes startup fast on Railway too.

---

## STEP 2: Push to GitHub

```bash
# Add all changes
git add .

# Commit
git commit -m "Prepare for Railway deployment - remove Modal files, update dependencies"

# Push to GitHub
git push origin main
```

**Verify:** Check GitHub repo has latest code.

---

## STEP 3: Railway Deployment Configuration

### 3.1 Create Railway Account & Choose Plan

1. Go to https://railway.app
2. Sign up with GitHub
3. **Choose Plan**:
   - **Trial**: $5 free credit (no subscription) - Perfect for initial testing!
   - **Hobby**: $5/month (includes $5 credit) - Upgrade when ready for production

**Recommendation**: Start with Trial to test deployment, then upgrade to Hobby ($5/month) once you're satisfied.

**Pricing Details**:
- Trial: $5 free credit, no subscription, ~2-5 days of testing
- Hobby: $5/month subscription + $5 usage credit = $10 total value
- Usage beyond credit: Pay-as-you-go (~$0.000231/GB-sec for compute)
- Storage: ~$0.25/GB/month
- **Expected monthly cost with Hobby**: $12-17/month total

### 3.2 Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `financial-analysis` repository
4. Railway will auto-detect Python and start building

### 3.3 Configure Build Settings

In Railway dashboard → **Settings**:

**Root Directory:** `.` (default)

**Build Command:** (Railway auto-detects from pyproject.toml, but if needed)
```bash
pip install -e .
```

**Start Command:**
```bash
python launch_web_app_with_auth.py
```

### 3.4 Add Environment Variables

In Railway → **Variables** tab, add these **REQUIRED** variables:

```
# AI Provider (Required)
OPENAI_API_KEY=sk-...

# Web Search (Required for market context)
BRAVE_API_KEY=BSA...

# SEC EDGAR (Required for financial data)
SEC_EDGAR_USER_AGENT=FinancialResearchAgent/1.0 (your-email@example.com)
ENABLE_EDGAR_INTEGRATION=true

# Authentication (Required for user tracking)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
AUTH_REDIRECT_URL=https://financialanalysis-production.up.railway.app
```

**OPTIONAL variables (for advanced features):**

```
# Serper Search API (optional fallback to Brave)
SERPER_API_KEY=...

# EDGAR MCP Server (optional, for advanced EDGAR features)
EDGAR_MCP_COMMAND=/path/to/.venv/bin/python
EDGAR_MCP_ARGS=-m sec_edgar_mcp.server
```

**Get values from your local `.env` file!**

**Important Notes:**
- `BRAVE_API_KEY` is critical - without it, web searches will fail
- `SEC_EDGAR_USER_AGENT` must follow format: "AppName/Version (email@example.com)"
- `AUTH_REDIRECT_URL` should match your Railway URL (update to custom domain later)
- Railway auto-redeploys when you add/change environment variables

### 3.5 Add Persistent Volume

In Railway → **Storage** tab:

**RECOMMENDED: Single Volume (Simpler)**
1. Click "New Volume"
2. **Mount Path:** `/app/financial_research_agent`
3. **Size:** 10 GB
4. This covers both output reports and ChromaDB data

**ALTERNATIVE: Separate Volumes (More Control)**
- Volume 1 - Mount Path: `/app/financial_research_agent/output`, Size: 2 GB
- Volume 2 - Mount Path: `/app/financial_research_agent/chroma_db`, Size: 5 GB

**Important Notes:**
- Railway doesn't auto-backup volumes - consider weekly manual backups
- Monitor volume usage in Railway dashboard
- Can increase size later if needed

### 3.6 Configure Port (if needed)

Railway should auto-detect port 7860 from your code. If not:

In **Settings** → **Networking**:
- Ensure port 7860 is exposed

---

## STEP 4: Test Railway Deployment

### 4.1 Check Build Logs

In Railway → **Deployments** → Click latest deployment:
- Look for successful build
- Check for any errors

### 4.2 Test Railway URL

Railway provides a URL like:
```
https://financial-analysis-production.up.railway.app
```

**Test:**
1. Visit the URL
2. Should see login page (if using auth)
3. Try logging in
4. Try running an analysis
5. Verify reports display correctly

### 4.3 Check Application Logs

In Railway → **Logs**:
- Watch for any errors
- Verify Gradio starts successfully
- Check for "Running on http://0.0.0.0:7860"

---

## STEP 5: Add Custom Domain

### 5.1 In Railway

Railway → **Settings** → **Domains**:

1. Click "Custom Domain"
2. Enter: `cblanalytics.com`
3. Railway will provide DNS records, typically:
   ```
   Type: CNAME
   Name: @
   Value: xxx.railway.app
   ```

### 5.2 In Weebly DNS

1. Log into Weebly
2. Go to Domains → cblanalytics.com → DNS Settings
3. **Delete old records:**
   - Remove old A record pointing to Modal (3.211.143.0)
   - Remove old CNAME records pointing to Modal
4. **Add Railway records:**
   ```
   Type: CNAME
   Name: @
   Value: (from Railway, e.g., financial-analysis-production.up.railway.app)
   
   Type: CNAME
   Name: www
   Value: (same Railway URL)
   ```
5. Save changes
6. Wait 5-10 minutes for DNS propagation

### 5.3 Verify Domain

After DNS propagates:
- Visit https://cblanalytics.com
- Should see your application!
- SSL should be automatic (Railway handles this)

---

## STEP 6: Verify Everything Works

### 6.1 Functionality Checklist

- [ ] https://cblanalytics.com loads
- [ ] Login page appears (if using auth)
- [ ] Can sign in with magic link
- [ ] Can run new analysis (try AAPL)
- [ ] Reports display in all tabs
- [ ] Charts render correctly
- [ ] Q&A feature works
- [ ] Previous analyses are saved (after running 2+)

### 6.2 Performance Check

- [ ] Page loads in < 5 seconds
- [ ] Analysis completes in 3-5 minutes
- [ ] No async task errors in logs
- [ ] Reports persist after container restart

---

## TROUBLESHOOTING

### Build Fails

**Check:**
- All dependencies in `pyproject.toml`
- Python version is 3.11+ specified
- No syntax errors in code

**Fix:**
- Update dependencies
- Check Railway build logs for specific error
- Ensure `pyproject.toml` is valid TOML syntax

### App Won't Start

**Check:**
- Start command is correct: `python launch_web_app_with_auth.py`
- Environment variables are set
- Port 7860 is used in code

**Fix:**
- Verify start command in Settings
- Check all required env vars are present
- Look at application logs for errors

### Can't Access App

**Check:**
- Deployment shows "Active"
- Railway URL works before adding custom domain
- DNS has propagated (use https://dnschecker.org)

**Fix:**
- Wait for DNS (can take 10-30 min)
- Verify CNAME records are correct
- Try Railway URL directly first

### Gradio Async Errors

**Railway handles this better than Modal!**

If you still see async warnings:
- They're usually harmless on Railway
- App should still function normally
- If not, check Railway logs for actual errors

### Reports Not Persisting

**Check:**
- Volume is mounted at `/app/financial_research_agent/output`
- Volume has sufficient space
- WebApp is writing to correct directory

**Fix:**
- Verify mount path in Railway Storage settings
- Check logs for permission errors
- Increase volume size if needed

### Web Searches Returning "No relevant data"

**Symptom**: Search results show "No relevant data was retrieved" for all queries

**Cause**: Missing `BRAVE_API_KEY` environment variable

**Fix:**
1. In Railway → **Variables** tab
2. Add `BRAVE_API_KEY=BSA...` (get from https://search.brave.com/search/api)
3. Railway will auto-redeploy
4. Test search again - should work immediately

**Note**: Brave Search API is 10x cheaper than OpenAI's WebSearchTool and is the primary search provider.

### SEC EDGAR Extraction Failing

**Symptom**: SEC filing data not appearing in reports

**Cause**: Missing or misconfigured EDGAR environment variables

**Fix:**
1. In Railway → **Variables** tab, verify these are set:
   - `SEC_EDGAR_USER_AGENT=AppName/Version (your-email@example.com)`
   - `ENABLE_EDGAR_INTEGRATION=true`
2. Ensure User Agent follows SEC format (name + email)
3. Railway will auto-redeploy
4. Test analysis again

**Note**: SEC requires proper User-Agent identification per their API policy.

### Module Import Errors (e.g., "No module named 'groq'")

**Symptom**: Application crashes with `ModuleNotFoundError`

**Cause**: Code trying to import optional dependency that's not installed

**Fix:**
- **If module is no longer used**: Remove all imports and references from codebase
- **If module is needed**: Add to `pyproject.toml` dependencies
- Commit changes and push to GitHub (Railway auto-redeploys)

**Example**: We completely removed Groq support since it's no longer used, eliminating the import error.

---

## POST-DEPLOYMENT

### IMPORTANT: Supabase Setup (Required for Production)

**⚠️ Authentication is REQUIRED before going live to track user access.**

#### Step 1: Create Supabase Project

1. Go to https://supabase.com
2. Sign up / Log in
3. Create new project:
   - Project Name: `financial-research-agent`
   - Database Password: (generate strong password)
   - Region: Choose closest to your users
4. Wait for project to provision (~2 minutes)

#### Step 2: Get Supabase Credentials

In Supabase Dashboard → **Settings** → **API**:

Copy these values:
- **Project URL**: `https://xxxxx.supabase.co`
- **Anon/Public Key**: `eyJhbGciOi...` (long JWT token)

#### Step 3: Add to Railway Environment Variables

In Railway → **Variables** tab, ADD:
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOi...
```

Railway will auto-redeploy with authentication enabled.

#### Step 4: Configure Supabase Redirect URLs

In Supabase Dashboard → **Authentication** → **URL Configuration**:

**Site URL** (use Railway URL initially, update to custom domain later):
```
https://financialanalysis-production.up.railway.app
```

**Redirect URLs** (add both):
```
https://financialanalysis-production.up.railway.app/auth/callback
https://financialanalysis-production.up.railway.app
```

**After adding custom domain (cblanalytics.com), UPDATE to:**

**Site URL**:
```
https://cblanalytics.com
```

**Redirect URLs** (add both):
```
https://cblanalytics.com/auth/callback
https://cblanalytics.com
```

**Important**: Remove any old Modal URLs if still present.

**Note**: Update `AUTH_REDIRECT_URL` in Railway Variables to match your current URL.

#### Step 5: Test Authentication

1. Visit https://cblanalytics.com
2. Should see login page
3. Enter your email
4. Check email for magic link
5. Click link → Should redirect to app
6. Verify you can run an analysis

#### Step 6: Monitor User Access

In Supabase Dashboard → **Authentication** → **Users**:
- See all users who have signed up
- View last sign-in times
- Track usage patterns
- Export user data if needed

**Note**: Supabase free tier includes:
- 50,000 monthly active users
- 500 MB database
- 1 GB file storage
- Sufficient for initial deployment

Upgrade to Pro ($25/month) when needed for:
- Advanced analytics
- More database space
- Priority support

### Monitor Usage

**Railway Dashboard:**
- Check resource usage (CPU, RAM, Storage)
- Monitor costs
- Set up billing alerts

**Supabase Dashboard:**
- Check user signups
- Monitor authentication activity
- Review usage patterns

### Optimization (Optional, Later)

**Once everything works:**
- Enable Railway auto-scaling if needed
- Optimize ChromaDB settings
- Add caching for frequent queries
- Set up monitoring/alerting

---

## COST ESTIMATE

### Railway Pricing Strategy

**Phase 1: Testing (Trial)**
- Trial: $5 free credit (no subscription)
- Duration: ~2-5 days of testing
- **Cost: FREE** ✅

**Phase 2: Production (Hobby Plan)**
- Hobby subscription: $5/month (includes $5 usage credit)
- Compute usage: ~$5-10/month (beyond included credit)
- Storage (10GB): ~$2/month
- **Subtotal: $12-17/month**

**Phase 3: With User Tracking (Add Supabase)**
- Railway: $12-17/month
- Supabase Free: $0/month (50K MAU, 500MB DB)
- **Total: $12-17/month** ✅

**OR with Supabase Pro** (if you need advanced analytics):
- Railway: $12-17/month
- Supabase Pro: $25/month
- **Total: $37-42/month**

### Cost Comparison
| Service | Modal (Old) | Railway (New) |
|---------|-------------|---------------|
| Monthly Cost | $20-40/month | $12-17/month ✅ |
| Reliability | Broken ❌ | Stable ✅ |
| Startup Time | 18+ minutes ❌ | <30 seconds ✅ |
| Storage | Ephemeral ❌ | Persistent ✅ |
| User Tracking | No ❌ | Yes (with Supabase) ✅ |

**Recommended Approach**:
1. Start with Trial ($5 free) to test
2. Upgrade to Hobby ($5/month) for production
3. Use Supabase free tier for user tracking
4. **Expected cost: $12-17/month** 🎯

**Benefits:**
- ✅ Full app works perfectly
- ✅ Persistent storage
- ✅ Custom domain + SSL
- ✅ No async issues
- ✅ Professional hosting
- ✅ User access tracking
- ✅ Cheaper than Modal!

---

## SUCCESS CRITERIA

✅ Code pushed to GitHub (no Modal files)
✅ Railway project deployed
✅ Environment variables configured
✅ Persistent volumes mounted
✅ Railway URL working
✅ Custom domain (cblanalytics.com) active
✅ SSL certificate working
✅ Can log in and run analyses
✅ Reports persist between sessions
✅ No async/queue errors

---

## NEXT STEPS AFTER LIVE

1. **Test thoroughly** with multiple companies
2. **Share link** and get feedback
3. **Monitor performance** and costs
4. **Iterate** based on user feedback
5. **Add features** incrementally (Phase 2+)

---

## ROLLBACK PLAN (If Needed)

If something goes wrong:

1. **Revert GitHub:** `git revert HEAD` and push
2. **Railway auto-redeploys** from GitHub
3. **Or:** Redeploy previous working version in Railway
4. **DNS:** Can always revert DNS to previous state

---

## SUPPORT RESOURCES

**Railway:**
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

**This Project:**
- Local test: `python launch_web_app_with_auth.py`
- Logs: Check Railway dashboard
- Issues: Review error messages in logs

---

## SUMMARY OF CHANGES FROM MODAL

**Removed:**
- ❌ modal_app*.py files
- ❌ Modal-specific volume configurations
- ❌ Modal secrets setup
- ❌ Complex async workarounds

**Kept:**
- ✅ Full Gradio application
- ✅ Authentication (Supabase)
- ✅ All features and functionality
- ✅ ChromaDB integration
- ✅ Report generation

**Result:**
- ✅ Same local experience
- ✅ Now hosted professionally
- ✅ On custom domain
- ✅ With persistent data
- ✅ No compromises!

---

**Ready to deploy? Follow Steps 1-6 in order. Good luck! 🚀**
