# SJP Financial Analysis - Complete Integration Architecture

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    SJP Consulting Site (Next.js)                │
│                    https://sjpconsulting.com                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Landing Page │  │   Services   │  │  About/Contact       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│         │                   │                                    │
│         └───────────────────┴───> Link to Analysis Tool         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Gradioappfrontend (React/Vite)                     │
│              https://analysis.sjpconsulting.com                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Beautiful Figma-designed UI with Radix components       │  │
│  │  - Query Knowledge Base                                   │  │
│  │  - Add Company Analysis                                   │  │
│  │  - Extract Existing Analysis                             │  │
│  │  - View Full Reports                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/REST API
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Bridge (NEW!)                          │
│                  Port: 8000                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  REST API Endpoints:                                      │  │
│  │  - POST /api/query          (Query RAG)                  │  │
│  │  - POST /api/analyze        (New Analysis)               │  │
│  │  - GET  /api/companies      (List Companies)             │  │
│  │  - GET  /api/reports/:id    (Get Report)                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│            Financial Analysis Gradio Backend                    │
│            (Existing - with Modal deployment)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - launch_web_app.py (Gradio UI)                         │  │
│  │  - modal_app.py (Modal deployment)                       │  │
│  │  - ChromaDB RAG system                                   │  │
│  │  - SEC EDGAR integration                                 │  │
│  │  - OpenAI Agents SDK                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Why This Architecture?

1. **FastAPI Bridge Layer** - Provides clean REST API for React frontend
2. **Separation of Concerns** - Frontend/Backend can deploy independently
3. **Gradio Intact** - Keep existing Gradio UI for power users/debugging
4. **Professional UI** - Figma-designed React app for end users
5. **Scalability** - Modal handles backend scaling

---

## Implementation Steps

### Phase 1: Create FastAPI Bridge (2-3 days)

This bridge sits between your React frontend and Gradio backend.

**Location**: `financial_analysis/fastapi_bridge/`

**Key Files**:
```
financial_analysis/
├── fastapi_bridge/
│   ├── main.py              # FastAPI app
│   ├── models.py            # Pydantic models
│   ├── gradio_client.py     # Calls Gradio backend
│   └── requirements.txt     # Dependencies
├── launch_web_app.py        # Existing Gradio (keep!)
└── modal_app.py             # Existing Modal (keep!)
```

### Phase 2: Update React Frontend (1-2 days)

**Location**: `Gradioappfrontend/`

Update the API integration files to call FastAPI bridge.

### Phase 3: Deploy Everything (1 day)

1. Deploy Gradio backend to Modal (already done!)
2. Deploy FastAPI bridge (Railway/Render)
3. Deploy React frontend (Vercel)
4. Update Next.js site to link to React frontend

---

## Detailed Implementation

### Step 1: Create FastAPI Bridge

This bridge translates REST API calls to Gradio function calls.

```python
# financial_analysis/fastapi_bridge/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add parent directory to path to import from financial_analysis
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from financial_research_agent.rag.chroma_manager import FinancialRAGManager
from financial_research_agent.main_enhanced import run_analysis

app = FastAPI(
    title="SJP Financial Analysis API",
    description="REST API for financial analysis powered by AI",
    version="1.0.0"
)

# Configure CORS - Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev
        "http://localhost:5173",  # Vite dev
        "https://analysis.sjpconsulting.com",  # Production
        "https://sjpconsulting.com"  # Main site
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG manager
rag = FinancialRAGManager(persist_directory="./chroma_db")

# Pydantic Models
class QueryRequest(BaseModel):
    query: str
    ticker: Optional[str] = None
    n_results: int = 5

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[dict]
    confidence: str

class AnalysisRequest(BaseModel):
    ticker: str
    force_refresh: bool = False

class Company(BaseModel):
    name: str
    ticker: str
    last_updated: Optional[str] = None

# API Endpoints

@app.get("/")
async def root():
    return {
        "service": "SJP Financial Analysis API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/companies")
async def list_companies():
    """Get list of all companies in knowledge base"""
    try:
        companies = rag.list_companies()
        return [
            Company(
                name=comp["ticker"],  # You might want to map ticker to full name
                ticker=comp["ticker"],
                last_updated=comp.get("last_updated")
            )
            for comp in companies
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def query_knowledge_base(request: QueryRequest):
    """Query the financial knowledge base using RAG"""
    try:
        # Use your existing RAG system
        results = rag.query(
            query=request.query,
            ticker=request.ticker,
            n_results=request.n_results
        )
        
        # Format results for frontend
        sources = []
        answer_parts = []
        
        for result in results["results"]:
            sources.append({
                "ticker": result["ticker"],
                "type": result["analysis_type"],
                "content": result["content"][:200] + "...",  # Preview
                "distance": result["distance"]
            })
            answer_parts.append(result["content"])
        
        # Simple concatenation - you might want to use GPT to synthesize
        answer = "\n\n".join(answer_parts[:3])  # Top 3 results
        
        confidence = "high" if results["results"][0]["distance"] < 0.5 else "medium"
        
        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            confidence=confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def run_new_analysis(request: AnalysisRequest):
    """
    Run a new financial analysis for a company.
    This is a long-running operation (3-5 min).
    """
    try:
        # Check if analysis exists and is recent (unless force_refresh)
        if not request.force_refresh:
            existing = rag.query(
                query=f"{request.ticker} latest analysis",
                ticker=request.ticker,
                n_results=1
            )
            if existing["results"]:
                # Return existing if less than 7 days old
                return {
                    "status": "existing_found",
                    "ticker": request.ticker,
                    "message": "Recent analysis found",
                    "data": existing["results"][0]
                }
        
        # Run new analysis - this calls your existing code!
        result = run_analysis(
            query=f"Analyze {request.ticker}'s most recent quarterly performance",
            ticker=request.ticker
        )
        
        return {
            "status": "completed",
            "ticker": request.ticker,
            "message": "Analysis completed successfully",
            "output_dir": result.get("output_dir")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{ticker}")
async def get_full_report(ticker: str):
    """Get the full financial report for a company"""
    try:
        # Query all analysis types for this ticker
        results = rag.query(
            query=f"{ticker} comprehensive analysis",
            ticker=ticker,
            n_results=20
        )
        
        if not results["results"]:
            raise HTTPException(
                status_code=404, 
                detail=f"No analysis found for {ticker}"
            )
        
        # Organize by analysis type
        report = {
            "ticker": ticker,
            "timestamp": results["results"][0].get("timestamp"),
            "financial_statements": [],
            "financial_metrics": [],
            "risk_analysis": [],
            "comprehensive_report": []
        }
        
        for result in results["results"]:
            analysis_type = result["analysis_type"]
            if analysis_type in report:
                report[analysis_type].append(result)
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare")
async def compare_companies(tickers: List[str], query: str):
    """Compare multiple companies on a specific aspect"""
    try:
        comparison = rag.compare_peers(
            tickers=tickers,
            query=query,
            n_results_per_company=3
        )
        return comparison
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Requirements**:
```txt
# financial_analysis/fastapi_bridge/requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.10.0
python-multipart==0.0.20
```

### Step 2: Update React Frontend API Integration

```typescript
// Gradioappfrontend/src/api/integration.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');

interface QueryRequest {
  query: string;
  ticker?: string;
  n_results?: number;
}

interface QueryResponse {
  query: string;
  answer: string;
  sources: Array<{
    ticker: string;
    type: string;
    content: string;
    distance: number;
  }>;
  confidence: string;
}

interface AnalysisRequest {
  ticker: string;
  force_refresh?: boolean;
}

interface Company {
  name: string;
  ticker: string;
  last_updated?: string;
}

async function fetchWithTimeout(url: string, options: RequestInit = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout - analysis may still be running');
    }
    throw error;
  }
}

export async function queryKnowledgeBase(
  request: QueryRequest
): Promise<QueryResponse> {
  return await fetchWithTimeout(`${API_BASE_URL}/api/query`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function runAnalysis(
  request: AnalysisRequest
): Promise<any> {
  return await fetchWithTimeout(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getCompanies(): Promise<Company[]> {
  return await fetchWithTimeout(`${API_BASE_URL}/api/companies`);
}

export async function getFullReport(ticker: string): Promise<any> {
  return await fetchWithTimeout(`${API_BASE_URL}/api/reports/${ticker}`);
}

export async function compareCompanies(
  tickers: string[],
  query: string
): Promise<any> {
  return await fetchWithTimeout(`${API_BASE_URL}/api/compare`, {
    method: 'POST',
    body: JSON.stringify({ tickers, query }),
  });
}
```

**Environment Configuration**:
```bash
# Gradioappfrontend/.env.local

# Development
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=60000

# Production (update after deployment)
# VITE_API_URL=https://api.sjpconsulting.com
```

### Step 3: Update React Components

Replace mock data with real API calls in your components.

Example for Query component:

```typescript
// Gradioappfrontend/src/components/QueryKnowledgeBase.tsx

import { useState } from 'react';
import { queryKnowledgeBase } from '../api/integration';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';

export function QueryKnowledgeBase() {
  const [query, setQuery] = useState('');
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await queryKnowledgeBase({
        query,
        ticker: ticker || undefined,
        n_results: 5
      });
      setResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Input
            placeholder="Enter your question..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            required
          />
        </div>
        
        <div>
          <Input
            placeholder="Filter by ticker (optional, e.g., AAPL)"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
          />
        </div>

        <Button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search Knowledge Base'}
        </Button>
      </form>

      {error && (
        <Card className="p-4 bg-red-50 border-red-200">
          <p className="text-red-600">{error}</p>
        </Card>
      )}

      {result && (
        <div className="space-y-4">
          <Card className="p-6">
            <h3 className="font-semibold mb-2">Answer</h3>
            <p className="whitespace-pre-wrap">{result.answer}</p>
            <div className="mt-4 text-sm text-gray-500">
              Confidence: {result.confidence}
            </div>
          </Card>

          <div>
            <h3 className="font-semibold mb-2">Sources</h3>
            <div className="space-y-2">
              {result.sources.map((source, idx) => (
                <Card key={idx} className="p-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="font-medium">{source.ticker}</span>
                      <span className="text-gray-500 ml-2">
                        ({source.type})
                      </span>
                    </div>
                    <span className="text-xs text-gray-400">
                      Score: {(1 - source.distance).toFixed(2)}
                    </span>
                  </div>
                  <p className="text-sm mt-2 text-gray-600">
                    {source.content}
                  </p>
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Deployment Plan

### Phase 1: Local Testing (1 day)

1. **Start Gradio Backend**:
```bash
cd financial_analysis
python launch_web_app.py
# Runs on http://localhost:7860
```

2. **Start FastAPI Bridge**:
```bash
cd financial_analysis/fastapi_bridge
uvicorn main:app --reload --port 8000
# Runs on http://localhost:8000
```

3. **Start React Frontend**:
```bash
cd Gradioappfrontend
npm install
npm run dev
# Runs on http://localhost:3000
```

4. **Test Flow**:
   - Visit http://localhost:3000
   - Try querying knowledge base
   - Try running analysis
   - Check browser console for errors

### Phase 2: Production Deployment (1-2 days)

**Option A: All-in-One (Simpler)**

Deploy everything to Modal:
- Gradio backend (already done)
- FastAPI bridge (add to Modal)
- React frontend (static files served by Modal)

**Option B: Distributed (Recommended)**

1. **Gradio Backend → Modal** (already done!)
   ```bash
   cd financial_analysis
   modal deploy modal_app.py
   ```

2. **FastAPI Bridge → Railway/Render**
   ```bash
   # Create Dockerfile for FastAPI
   # Push to Railway/Render
   ```

3. **React Frontend → Vercel**
   ```bash
   cd Gradioappfrontend
   vercel --prod
   ```

4. **Main Site → Vercel**
   ```bash
   cd sjp-consulting-site
   vercel --prod
   ```

### Custom Domains

- `sjpconsulting.com` → Main Next.js site
- `analysis.sjpconsulting.com` → React frontend
- `api.sjpconsulting.com` → FastAPI bridge
- (Gradio backend stays on Modal URL for debugging)

---

## Next Steps

### Week 1: Integration
- ✅ Create FastAPI bridge
- ✅ Update React API integration
- ✅ Test locally
- ✅ Fix any bugs

### Week 2: Polish
- ✅ Add loading states
- ✅ Add error handling
- ✅ Add authentication (if needed)
- ✅ Style matching

### Week 3: Deploy
- ✅ Deploy FastAPI bridge
- ✅ Deploy React frontend
- ✅ Configure domains
- ✅ Update main site

### Week 4: Launch
- ✅ Final testing
- ✅ User documentation
- ✅ Marketing/announcement

---

## Cost Estimate

- **Modal**: ~$10-20/month (Gradio backend)
- **Railway/Render**: ~$7-20/month (FastAPI)
- **Vercel**: Free (both frontends)
- **OpenAI API**: Pay-per-use (~$0.08/analysis)
- **Domain**: ~$15/year

**Total**: ~$25-50/month + API costs

---

## Benefits of This Architecture

✅ **Clean Separation**: Each component has a single responsibility
✅ **Scalable**: Can scale each part independently
✅ **Professional UI**: Figma-designed React app for users
✅ **Power User Mode**: Keep Gradio for debugging/admin
✅ **Flexible**: Easy to swap components
✅ **Cost-Effective**: Modal scales to zero when idle

---

## Questions?

Common issues and solutions will be documented as we encounter them.
