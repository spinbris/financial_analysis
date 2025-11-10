# Quick Start: Modal-Optimized Setup (30 Minutes)

Since you're already using Modal, this is the **fastest and simplest** way to get everything working.

## 🎯 What We're Building

```
React Frontend (Vercel)
         ↓
FastAPI Bridge (Modal) ──┐
         ↓                │ Both share
Gradio Backend (Modal) ──┤ ChromaDB volume
         ↓                │
    ChromaDB ────────────┘
```

**Everything on Modal = Simpler!**

---

## ⚡ Super Quick Start (30 min)

### Step 1: Deploy FastAPI to Modal (10 min)

```bash
# 1. Copy the Modal bridge file
cd financial_analysis
# Download modal_fastapi_bridge.py from Claude

# 2. Test it
modal run modal_fastapi_bridge.py
# Should show: ✅ RAG imports working

# 3. Deploy it!
modal deploy modal_fastapi_bridge.py
```

**Copy the URL** that appears (you'll need it next):
```
https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run
```

### Step 2: Set Up React Frontend (10 min)

```bash
cd Gradioappfrontend

# 1. Copy API integration file
mkdir -p src/api
# Download react_api_integration.ts → src/api/integration.ts

# 2. Create environment file
cat > .env.local << EOF
VITE_API_URL=https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run
VITE_API_TIMEOUT=60000
EOF

# 3. Install and run
npm install
npm run dev
```

Visit http://localhost:3000 🎉

### Step 3: Generate Test Data (10 min)

```bash
# Use your existing Gradio setup
cd financial_analysis
python launch_web_app.py

# Visit http://localhost:7860
# Run an analysis for AAPL
# Wait 3-5 minutes
```

Now try querying from your React app!

---

## ✅ Verify It's Working

### Test the Modal API

```bash
# Replace with YOUR actual URL
export API_URL="https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run"

# 1. Health check
curl $API_URL/api/health

# 2. List companies
curl $API_URL/api/companies

# 3. Query knowledge base
curl -X POST $API_URL/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AAPL revenue?", "ticker": "AAPL"}'
```

### Test the React App

1. Open http://localhost:3000
2. Try the query interface
3. Search for "revenue" or "risk"
4. Check browser console (F12) for errors
5. Verify results appear

---

## 🎨 Update Your Components

Now replace the mock data in your Figma components with real API calls.

### Example: Update Query Component

```typescript
// In your QueryKnowledgeBase.tsx
import { queryKnowledgeBase } from '../api/integration';

const handleSearch = async () => {
  const result = await queryKnowledgeBase({
    query: userQuery,
    ticker: selectedTicker
  });
  setResults(result);
};
```

See `example_component.tsx` for a complete working example!

---

## 📝 File Locations

After setup, your structure should be:

```
financial_analysis/
├── modal_fastapi_bridge.py      ← NEW! Your API bridge
├── modal_app.py                 ← EXISTING (Gradio)
├── launch_web_app.py            ← EXISTING (local Gradio)
└── financial_research_agent/    ← EXISTING (core logic)

Gradioappfrontend/
├── src/
│   ├── api/
│   │   └── integration.ts       ← NEW! API client
│   └── components/
│       └── [Your Figma components]
├── .env.local                   ← NEW! Environment vars
└── package.json

sjp-consulting-site/
└── [Your Next.js site]
```

---

## 🚀 Deploy to Production (Optional)

When you're ready:

### 1. Deploy React to Vercel

```bash
cd Gradioappfrontend

# Update .env.production
VITE_API_URL=https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run

# Deploy
vercel --prod
```

### 2. Add Custom Domain

In Vercel dashboard:
- Add domain: `analysis.sjpconsulting.com`
- Update DNS with provided CNAME record

### 3. Update CORS

Edit `modal_fastapi_bridge.py`:
```python
ALLOWED_ORIGINS = [
    "https://analysis.sjpconsulting.com",  # Add your domain
    # ... existing origins
]
```

Redeploy:
```bash
modal deploy modal_fastapi_bridge.py
```

---

## 💰 Cost

**Modal only: $10-30/month**
- FastAPI Bridge: ~$5/month
- Gradio Backend: ~$5-15/month  
- ChromaDB storage: Free (included)
- Vercel: Free

**Total: $10-30/month** 🎉

---

## 🐛 Common Issues

### "No companies found"
**Fix:** Generate data first using Gradio interface

### CORS errors
**Fix:** Check ALLOWED_ORIGINS in modal_fastapi_bridge.py

### Import errors
**Fix:** Check the mounts section in modal_fastapi_bridge.py

### Timeout errors
**Fix:** Increase VITE_API_TIMEOUT in .env.local

---

## 📚 Next Steps

1. ✅ Update React components with real API calls
2. ✅ Style matching with your Figma design
3. ✅ Add error handling and loading states
4. ✅ Deploy to production
5. ✅ Update main website with links

See the other guides for details:
- **example_component.tsx** - How to use the API
- **MODAL_DEPLOYMENT_GUIDE.md** - Full deployment details
- **IMPLEMENTATION_ROADMAP.md** - Complete timeline

---

## 🎉 You're Ready!

You now have:
- ✅ FastAPI Bridge on Modal
- ✅ Gradio Backend on Modal
- ✅ React Frontend running locally
- ✅ Shared ChromaDB
- ✅ API integration working

**Time to build!** 🚀

---

## 💡 Development Tips

### Daily Workflow

```bash
# Terminal 1: React dev server
cd Gradioappfrontend && npm run dev

# Terminal 2: View Modal logs
modal app logs sjp-financial-api --follow

# Terminal 3: Optional - local Gradio for testing
cd financial_analysis && python launch_web_app.py
```

### Making API Changes

```bash
# 1. Edit modal_fastapi_bridge.py
# 2. Deploy (takes ~30 seconds)
modal deploy modal_fastapi_bridge.py
# 3. Test immediately - no restart needed!
```

### Adding New Endpoints

Add to `modal_fastapi_bridge.py`:
```python
@web_app.get("/api/my-new-endpoint")
async def my_endpoint():
    return {"message": "Hello!"}
```

Add to `src/api/integration.ts`:
```typescript
export async function myEndpoint() {
  return await fetchWithTimeout(`${API_BASE_URL}/api/my-new-endpoint`);
}
```

---

## 📞 Need Help?

Check these in order:
1. **Error messages** - Read them carefully!
2. **Browser console** - F12 → Console tab
3. **Modal logs** - `modal app logs sjp-financial-api`
4. **API docs** - Visit `/docs` on your Modal URL
5. **Other guides** - See the complete set of docs

---

**Ready to go?** Start with Step 1 above! 🎯
