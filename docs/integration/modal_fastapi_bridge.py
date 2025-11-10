"""
Modal-Integrated FastAPI Bridge for SJP Financial Analysis

This version deploys the FastAPI bridge directly to Modal alongside your
existing Gradio backend, keeping everything in one place.

Deploy with: modal deploy modal_fastapi_bridge.py
"""

import modal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

# Create Modal app
app = modal.App("sjp-financial-api")

# Create Modal image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi==0.115.0",
        "pydantic==2.10.0",
        "chromadb==0.5.23",
        "openai==1.58.1",
    )
)

# Mount your existing code
mounts = [
    modal.Mount.from_local_dir(
        "../financial_research_agent",
        remote_path="/root/financial_research_agent"
    )
]

# Create persistent ChromaDB volume
chroma_volume = modal.Volume.from_name("financial-chroma-db", create_if_missing=True)

# ============================================================================
# Pydantic Models
# ============================================================================

class QueryRequest(BaseModel):
    query: str
    ticker: Optional[str] = None
    n_results: int = 5
    analysis_type: Optional[str] = None

class Source(BaseModel):
    ticker: str
    type: str
    content: str
    distance: float
    timestamp: Optional[str] = None

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Source]
    confidence: str
    suggestions: List[str] = []

class AnalysisRequest(BaseModel):
    ticker: str
    openai_api_key: str  # User provides their own key
    force_refresh: bool = False

class AnalysisStatus(BaseModel):
    status: str
    ticker: str
    message: str
    progress: Optional[int] = None
    output_dir: Optional[str] = None

class Company(BaseModel):
    name: str
    ticker: str
    last_updated: Optional[str] = None
    analysis_count: int = 0

class HealthResponse(BaseModel):
    status: str
    version: str
    rag_enabled: bool
    modal_deployment: bool
    timestamp: str

# ============================================================================
# Helper Functions
# ============================================================================

def get_ticker_full_name(ticker: str) -> str:
    """Map ticker to company full name"""
    ticker_map = {
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation",
        "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com Inc.",
        "NVDA": "NVIDIA Corporation",
        "META": "Meta Platforms Inc.",
        "TSLA": "Tesla Inc.",
        "BRK.B": "Berkshire Hathaway Inc.",
        "JNJ": "Johnson & Johnson",
        "UNH": "UnitedHealth Group Inc.",
    }
    return ticker_map.get(ticker.upper(), ticker.upper())

def format_rag_results(results: Dict[str, Any], query: str) -> QueryResponse:
    """Format RAG results into QueryResponse"""
    sources = []
    answer_parts = []
    
    for result in results.get("results", [])[:5]:
        sources.append(Source(
            ticker=result.get("ticker", "UNKNOWN"),
            type=result.get("analysis_type", "unknown"),
            content=result.get("content", "")[:300] + "...",
            distance=result.get("distance", 1.0),
            timestamp=result.get("timestamp")
        ))
        answer_parts.append(result.get("content", ""))
    
    # Synthesize answer
    if answer_parts:
        answer = "\n\n".join(answer_parts[:3])
    else:
        answer = "No relevant information found. Try adding companies first."
    
    # Determine confidence
    if sources and sources[0].distance < 0.3:
        confidence = "high"
    elif sources and sources[0].distance < 0.6:
        confidence = "medium"
    else:
        confidence = "low"
    
    suggestions = [
        "Can you provide more details about the financial metrics?",
        "What are the key risk factors?",
        "How does this compare to industry peers?"
    ]
    
    return QueryResponse(
        query=query,
        answer=answer,
        sources=sources,
        confidence=confidence,
        suggestions=suggestions
    )

# ============================================================================
# Create FastAPI App
# ============================================================================

web_app = FastAPI(
    title="SJP Financial Analysis API",
    description="REST API for AI-powered financial analysis (Modal Deployment)",
    version="1.0.0"
)

# Configure CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://analysis.sjpconsulting.com",
    "https://sjpconsulting.com",
]

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API Endpoints
# ============================================================================

@web_app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SJP Financial Analysis API",
        "version": "1.0.0",
        "deployment": "Modal",
        "status": "operational",
        "docs": "/docs"
    }

@web_app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        rag_enabled=True,
        modal_deployment=True,
        timestamp=datetime.now().isoformat()
    )

@web_app.get("/api/companies")
async def list_companies():
    """Get list of companies in knowledge base"""
    # Import inside function to avoid issues
    from financial_research_agent.rag.chroma_manager import FinancialRAGManager
    
    try:
        rag = FinancialRAGManager(persist_directory="/chroma-data")
        companies_data = rag.list_companies()
        
        companies = []
        for comp in companies_data:
            ticker = comp.get("ticker", "UNKNOWN")
            companies.append(Company(
                name=get_ticker_full_name(ticker),
                ticker=ticker,
                last_updated=comp.get("last_updated"),
                analysis_count=comp.get("count", 0)
            ))
        
        return companies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@web_app.post("/api/query")
async def query_knowledge_base(request: QueryRequest):
    """Query the financial knowledge base"""
    from financial_research_agent.rag.chroma_manager import FinancialRAGManager
    
    try:
        rag = FinancialRAGManager(persist_directory="/chroma-data")
        results = rag.query(
            query=request.query,
            ticker=request.ticker,
            analysis_type=request.analysis_type,
            n_results=request.n_results
        )
        
        if not results.get("results"):
            return QueryResponse(
                query=request.query,
                answer="No relevant information found. Try adding companies first.",
                sources=[],
                confidence="low",
                suggestions=[
                    "Try adding a company analysis first",
                    "Check if the ticker symbol is correct"
                ]
            )
        
        return format_rag_results(results, request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@web_app.post("/api/analyze")
async def run_analysis(request: AnalysisRequest):
    """
    Run new financial analysis.
    
    Note: User must provide their own OpenAI API key.
    Analysis takes 3-5 minutes.
    """
    from financial_research_agent.main_enhanced import run_analysis as do_analysis
    
    try:
        ticker = request.ticker.upper()
        
        # Set OpenAI key from user
        os.environ["OPENAI_API_KEY"] = request.openai_api_key
        
        # Check for existing analysis
        if not request.force_refresh:
            from financial_research_agent.rag.chroma_manager import FinancialRAGManager
            rag = FinancialRAGManager(persist_directory="/chroma-data")
            existing = rag.query(
                query=f"{ticker} comprehensive",
                ticker=ticker,
                n_results=1
            )
            if existing.get("results"):
                return AnalysisStatus(
                    status="completed",
                    ticker=ticker,
                    message="Recent analysis found (use force_refresh=true to regenerate)"
                )
        
        # Run analysis (this takes 3-5 min)
        result = do_analysis(
            query=f"Analyze {ticker}'s most recent quarterly performance",
            ticker=ticker
        )
        
        return AnalysisStatus(
            status="completed",
            ticker=ticker,
            message="Analysis completed successfully",
            output_dir=result.get("output_dir")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@web_app.get("/api/reports/{ticker}")
async def get_report(ticker: str):
    """Get full financial report for a company"""
    from financial_research_agent.rag.chroma_manager import FinancialRAGManager
    
    try:
        ticker = ticker.upper()
        rag = FinancialRAGManager(persist_directory="/chroma-data")
        results = rag.query(
            query=f"{ticker} comprehensive",
            ticker=ticker,
            n_results=50
        )
        
        if not results.get("results"):
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for {ticker}"
            )
        
        # Organize by type
        report = {
            "ticker": ticker,
            "company_name": get_ticker_full_name(ticker),
            "timestamp": results["results"][0].get("timestamp"),
            "analyses": {
                "financial_statements": [],
                "financial_metrics": [],
                "risk_analysis": [],
                "comprehensive_report": [],
            }
        }
        
        for result in results["results"]:
            analysis_type = result.get("analysis_type", "other")
            if analysis_type in report["analyses"]:
                report["analyses"][analysis_type].append({
                    "content": result.get("content"),
                    "timestamp": result.get("timestamp"),
                    "distance": result.get("distance")
                })
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Deploy to Modal
# ============================================================================

@app.function(
    image=image,
    mounts=mounts,
    volumes={"/chroma-data": chroma_volume},
    secrets=[
        modal.Secret.from_name("openai-secret"),  # Your admin OpenAI key
        modal.Secret.from_name("brave-secret")     # Your Brave API key
    ],
    container_idle_timeout=300,
    timeout=3600,
)
@modal.asgi_app()
def fastapi_app():
    """Deploy FastAPI app to Modal"""
    return web_app

# ============================================================================
# Test Function
# ============================================================================

@app.function(image=image, mounts=mounts, volumes={"/chroma-data": chroma_volume})
def test_api():
    """Test the API endpoints"""
    print("Testing API...")
    
    # Test imports
    try:
        from financial_research_agent.rag.chroma_manager import FinancialRAGManager
        print("✅ RAG imports working")
        
        rag = FinancialRAGManager(persist_directory="/chroma-data")
        companies = rag.list_companies()
        print(f"✅ Found {len(companies)} companies in database")
        
        if companies:
            print(f"   Tickers: {[c['ticker'] for c in companies[:5]]}")
    except Exception as e:
        print(f"❌ Error: {e}")

# ============================================================================
# Local Development
# ============================================================================

@app.local_entrypoint()
def main():
    """For local testing: modal run modal_fastapi_bridge.py"""
    test_api.remote()
    print("\n✅ API tests passed!")
    print("\nTo deploy:")
    print("  modal deploy modal_fastapi_bridge.py")
    print("\nYour API will be at:")
    print("  https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run")
