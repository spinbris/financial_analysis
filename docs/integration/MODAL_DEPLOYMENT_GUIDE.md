# Modal Deployment Guide - Simplified Architecture

Since you're already using Modal, we'll deploy everything there. This is **simpler, cheaper, and easier** than using multiple platforms.

## 🎯 Updated Architecture (All-Modal)

```
┌────────────────────────────────────────────────────────────┐
│ Main Website: sjpconsulting.com                           │
│ Deploy: Vercel (free)                                      │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ Analysis Tool: analysis.sjpconsulting.com                 │
│ Deploy: Vercel (free)                                      │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ ALL BACKEND ON MODAL                                       │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ FastAPI Bridge (NEW!)                                  │ │
│ │ https://YOU--sjp-financial-api-fastapi-app.modal.run  │ │
│ │ REST API for React frontend                           │ │
│ └────────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Gradio Backend (EXISTING)                             │ │
│ │ https://YOU--financial-research-agent-web-app.modal.run│ │
│ │ ChromaDB, EDGAR, OpenAI Agents                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ Shared ChromaDB Volume: financial-chroma-db                │
└────────────────────────────────────────────────────────────┘
```

**Benefits:**
- ✅ Everything in one place
- ✅ Shared ChromaDB volume
- ✅ Single bill (~$10-30/month)
- ✅ Easier to manage
- ✅ Auto-scaling

---

## 📦 Step 1: Deploy FastAPI to Modal (10 min)

### 1.1 Copy the Modal Bridge File

Copy `modal_fastapi_bridge.py` to your `financial_analysis` directory:

```bash
cd financial_analysis
# Copy modal_fastapi_bridge.py here
```

### 1.2 Test Locally

```bash
# Test the Modal function
modal run modal_fastapi_bridge.py

# You should see:
# ✅ RAG imports working
# ✅ Found X companies in database
```

### 1.3 Deploy to Modal

```bash
modal deploy modal_fastapi_bridge.py
```

You'll see output like:
```
✓ Created objects.
├── 🔨 Created mount /root/financial_research_agent
├── 🔨 Created function test_api.
├── 🔨 Created web function fastapi_app => https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run
└── 🔨 Created function main.

✅ App deployed!
```

**Save this URL!** This is your API endpoint.

### 1.4 Test the Deployment

```bash
# Replace with your actual URL
export API_URL="https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run"

# Health check
curl $API_URL/api/health

# List companies
curl $API_URL/api/companies

# Query
curl -X POST $API_URL/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "revenue trends", "ticker": "AAPL"}'
```

---

## 📱 Step 2: Update React Frontend (5 min)

### 2.1 Update Environment Variables

Edit `Gradioappfrontend/.env.production`:

```bash
# Your Modal API URL
VITE_API_URL=https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run
VITE_API_TIMEOUT=60000
```

For local development, update `.env.local` too:

```bash
# For local development with Modal
VITE_API_URL=https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run
VITE_API_TIMEOUT=60000
```

### 2.2 Test Connection

```bash
cd Gradioappfrontend
npm run dev
```

Visit http://localhost:3000 and try querying!

---

## 🚀 Step 3: Deploy React to Vercel (5 min)

### 3.1 Update vercel.json

Create/update `Gradioappfrontend/vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "framework": "vite",
  "env": {
    "VITE_API_URL": "https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run"
  }
}
```

### 3.2 Deploy

```bash
cd Gradioappfrontend
vercel --prod
```

### 3.3 Add Custom Domain

In Vercel dashboard:
1. Settings → Domains
2. Add: `analysis.sjpconsulting.com`
3. Add CNAME record in your DNS:
   ```
   CNAME analysis → cname.vercel-dns.com
   ```

---

## 🏠 Step 4: Deploy Main Site (5 min)

### 4.1 Update Next.js Site

Edit `sjp-consulting-site/app/page.tsx`:

```tsx
<a 
  href="https://analysis.sjpconsulting.com"
  className="..."
>
  Try Our Financial Analysis Tool
</a>
```

### 4.2 Deploy

```bash
cd sjp-consulting-site
vercel --prod
```

### 4.3 Add Domain

Add `sjpconsulting.com` in Vercel, set DNS:
```
A    @ → 76.76.21.21
CNAME www → cname.vercel-dns.com
```

---

## 🔧 Step 5: Configure CORS (2 min)

Update `modal_fastapi_bridge.py` ALLOWED_ORIGINS:

```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://analysis.sjpconsulting.com",      # Your domain
    "https://sjpconsulting.com",                # Main site
    "https://www.sjpconsulting.com",            # www version
]
```

Redeploy:
```bash
modal deploy modal_fastapi_bridge.py
```

---

## 💾 Data Management

### Shared ChromaDB Volume

Both your Gradio backend and FastAPI bridge share the same ChromaDB volume: `financial-chroma-db`

**To generate data:**

```bash
# Use your existing Gradio interface
cd financial_analysis
python launch_web_app.py

# Or use Modal
modal run modal_app.py::analyze_company --ticker AAPL
```

**To backup ChromaDB:**

```bash
# Create backup script: backup_chroma.py
import modal

app = modal.App("backup-chroma")
volume = modal.Volume.from_name("financial-chroma-db")

@app.function(volumes={"/chroma": volume})
def backup():
    import subprocess
    subprocess.run(["tar", "-czf", "/tmp/chroma_backup.tar.gz", "/chroma"])
    # Upload to S3 or download

# Run backup
modal run backup_chroma.py::backup
```

---

## 💰 Cost Breakdown (All-Modal)

| Component | Cost |
|-----------|------|
| Modal (everything) | $10-30/month |
| Vercel (2 sites) | Free |
| Domain | $15/year |
| **Total** | **$10-30/month** |

**Cheaper than split architecture!** 🎉

---

## 🔍 Monitoring & Logs

### View Modal Logs

```bash
# FastAPI logs
modal app logs sjp-financial-api

# Gradio logs  
modal app logs financial-research-agent

# Live logs
modal app logs sjp-financial-api --follow
```

### View Modal Dashboard

Visit https://modal.com/apps

- See all deployed functions
- Monitor usage
- View logs
- Check costs

---

## 🧪 Testing Your Setup

### Test Checklist

```bash
# 1. Modal FastAPI is deployed
curl https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run/api/health

# 2. Can list companies
curl https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run/api/companies

# 3. Can query
curl -X POST https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "revenue", "ticker": "AAPL"}'

# 4. React site is live
open https://analysis.sjpconsulting.com

# 5. Main site is live
open https://sjpconsulting.com

# 6. No CORS errors
# Check browser console (F12) when using the app
```

---

## 🛠️ Development Workflow

### Local Development

**Option 1: Use Modal Deployment** (Recommended)
```bash
# Point React to Modal API
# .env.local
VITE_API_URL=https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run

npm run dev
```

**Option 2: Run FastAPI Locally**
```bash
# Terminal 1: Local FastAPI (still uses Modal ChromaDB)
cd financial_analysis/fastapi_bridge
python main.py

# Terminal 2: React
cd Gradioappfrontend
npm run dev
```

### Making Changes

**Update API:**
```bash
# Edit modal_fastapi_bridge.py
modal deploy modal_fastapi_bridge.py
# Changes live in ~30 seconds!
```

**Update Frontend:**
```bash
# Edit React components
vercel --prod
# Changes live in ~1 minute!
```

---

## 🔐 Security Best Practices

### 1. API Keys in Modal Secrets

Your OpenAI/Brave keys are already in Modal Secrets. Don't hardcode them!

```bash
# View secrets
modal secret list

# Update secret
modal secret create openai-secret OPENAI_API_KEY=sk-proj-...
```

### 2. Rate Limiting

Add to `modal_fastapi_bridge.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@web_app.post("/api/query")
@limiter.limit("10/minute")
async def query_knowledge_base(request: QueryRequest):
    # ... existing code
```

### 3. Authentication (Optional)

If you want to restrict access:

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@web_app.post("/api/query")
async def query_knowledge_base(
    request: QueryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify credentials.credentials (JWT token)
    # ... existing code
```

---

## 🐛 Troubleshooting

### Issue: "Volume not found"

**Solution:**
```bash
# Create the volume manually
modal volume create financial-chroma-db

# Or let it auto-create on first deploy
modal deploy modal_fastapi_bridge.py
```

### Issue: "No companies found"

**Solution:** Generate data first:
```bash
# Use Gradio interface
python launch_web_app.py

# Or Modal CLI
modal run modal_app.py::analyze_company --ticker AAPL
```

### Issue: CORS errors

**Solution:** Check ALLOWED_ORIGINS includes your domain and redeploy:
```bash
modal deploy modal_fastapi_bridge.py
```

### Issue: "Module not found"

**Solution:** Check mounts in `modal_fastapi_bridge.py`:
```python
mounts = [
    modal.Mount.from_local_dir(
        "./financial_research_agent",  # Check this path!
        remote_path="/root/financial_research_agent"
    )
]
```

---

## 🎉 You're Live!

Once everything is deployed:

✅ **FastAPI on Modal** - Your REST API  
✅ **Gradio on Modal** - Your analysis engine  
✅ **React on Vercel** - Your user interface  
✅ **Next.js on Vercel** - Your main website  

**Total setup time: ~30 minutes**  
**Monthly cost: ~$10-30**  

### URLs to Share

- Main Site: `https://sjpconsulting.com`
- Analysis Tool: `https://analysis.sjpconsulting.com`
- API Docs: `https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run/docs`

---

## 📚 Next Steps

1. ✅ Update React components to use API (see example_component.tsx)
2. ✅ Add authentication if needed
3. ✅ Add analytics
4. ✅ Write user documentation
5. ✅ Announce launch! 🚀

---

## 💡 Pro Tips

1. **Modal is serverless** - You only pay for actual usage
2. **Use Modal's caching** - Results are cached for 7 days
3. **Monitor costs** - Check Modal dashboard regularly
4. **Backup ChromaDB** - Create automated backups
5. **Use Modal's built-in logging** - Better than external services

---

**That's it!** Everything is simpler with Modal. 🎊
