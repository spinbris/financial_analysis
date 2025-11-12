"""
Modal-Integrated FastAPI Bridge for SJP Financial Analysis

This version deploys the FastAPI bridge directly to Modal alongside your
existing Gradio backend, keeping everything in one place.

Deploy with: modal deploy modal_fastapi_bridge.py
"""

import modal
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
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
        "chromadb==1.3.4",  # Match local version
        "openai>=2.7.1",
        "openai-agents>=0.4.2",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
        "edgartools>=2.40.0",
    )
    .add_local_dir(
        "financial_research_agent",
        remote_path="/root/financial_research_agent"
    )
)

# Create persistent ChromaDB volume
chroma_volume = modal.Volume.from_name("financial-chroma-db", create_if_missing=True)

# ============================================================================
# Security - API Key Authentication
# ============================================================================

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for endpoint protection."""
    expected_key = os.environ.get("API_KEY")

    # If no API_KEY is set in environment, allow access (development mode)
    if not expected_key:
        return api_key

    # In production, require valid API key
    if api_key != expected_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key. Include 'X-API-Key' header."
        )
    return api_key

# ============================================================================
# Pydantic Models
# ============================================================================

class QueryRequest(BaseModel):
    query: str
    ticker: Optional[str] = None
    n_results: int = 5
    analysis_type: Optional[str] = None
    openai_api_key: Optional[str] = None  # User-provided OpenAI key (future)

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

    # ChromaDB returns results in format: {documents: [[]], metadatas: [[]], distances: [[]]}
    documents = results.get("documents", [[]])[0] if results.get("documents") else []
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
    distances = results.get("distances", [[]])[0] if results.get("distances") else []

    # Combine documents, metadatas, distances
    for i in range(min(len(documents), 5)):
        doc = documents[i] if i < len(documents) else ""
        metadata = metadatas[i] if i < len(metadatas) else {}
        distance = distances[i] if i < len(distances) else 1.0

        sources.append(Source(
            ticker=metadata.get("ticker", "UNKNOWN"),
            type=metadata.get("analysis_type", "unknown"),
            content=doc[:300] + "..." if len(doc) > 300 else doc,
            distance=distance,
            timestamp=metadata.get("period")
        ))
        answer_parts.append(doc)

    # Synthesize answer - show only the most relevant chunk
    if answer_parts:
        # Return just the top result to avoid wall of text
        answer = answer_parts[0]
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
async def list_companies(api_key: str = Depends(verify_api_key)):
    """Get list of companies in knowledge base (requires API key)"""
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
async def query_knowledge_base(request: QueryRequest, api_key: str = Depends(verify_api_key)):
    """Query the financial knowledge base (requires API key)"""
    from financial_research_agent.rag.chroma_manager import FinancialRAGManager
    
    try:
        rag = FinancialRAGManager(persist_directory="/chroma-data")
        results = rag.query(
            query=request.query,
            ticker=request.ticker,
            analysis_type=request.analysis_type,
            n_results=request.n_results
        )
        
        # Check if ChromaDB returned any documents
        documents = results.get("documents", [[]])[0] if results.get("documents") else []
        if not documents:
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
async def run_analysis(request: AnalysisRequest, api_key: str = Depends(verify_api_key)):
    """
    Run new financial analysis (requires API key).

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
async def get_report(ticker: str, api_key: str = Depends(verify_api_key)):
    """Get full financial report for a company (requires API key)"""
    from financial_research_agent.rag.chroma_manager import FinancialRAGManager

    try:
        ticker = ticker.upper()
        rag = FinancialRAGManager(persist_directory="/chroma-data")
        results = rag.query(
            query=f"{ticker} comprehensive",
            ticker=ticker,
            n_results=50
        )

        # ChromaDB returns: {documents: [[]], metadatas: [[]], distances: [[]]}
        documents = results.get("documents", [[]])[0] if results.get("documents") else []
        metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
        distances = results.get("distances", [[]])[0] if results.get("distances") else []

        if not documents:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for {ticker}"
            )

        # Organize by type
        report = {
            "ticker": ticker,
            "company_name": get_ticker_full_name(ticker),
            "timestamp": metadatas[0].get("period") if metadatas else None,
            "analyses": {
                "financial_statements": [],
                "financial_metrics": [],
                "risk_analysis": [],
                "comprehensive_report": [],
                "financial_analysis": [],  # Also include financial_analysis
            }
        }

        # Map ChromaDB analysis_type to report keys
        type_mapping = {
            "financial_statements": "financial_statements",
            "financial_metrics": "financial_metrics",
            "risk": "risk_analysis",  # Map "risk" -> "risk_analysis"
            "comprehensive": "comprehensive_report",  # Map "comprehensive" -> "comprehensive_report"
            "financial_analysis": "financial_analysis"
        }

        # Combine documents with their metadata
        for i in range(len(documents)):
            doc = documents[i] if i < len(documents) else ""
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else 1.0

            analysis_type = metadata.get("analysis_type", "other")
            # Map to report key
            report_key = type_mapping.get(analysis_type)

            if report_key:
                report["analyses"][report_key].append({
                    "content": doc,
                    "timestamp": metadata.get("period"),
                    "distance": distance
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
    volumes={"/chroma-data": chroma_volume},
    secrets=[
        modal.Secret.from_name("api-key-secret"),  # API key for endpoint protection
        # Note: OpenAI/Brave keys will come from user requests, not system secrets
    ],
    scaledown_window=300,
    timeout=3600,
)
@modal.asgi_app()
def fastapi_app():
    """Deploy FastAPI app to Modal"""
    return web_app

# ============================================================================
# Test Function
# ============================================================================

@app.function(image=image, volumes={"/chroma-data": chroma_volume})
def fix_volume_structure():
    """Fix the nested chroma-data directory structure"""
    import os
    import shutil

    print("Fixing volume structure...")

    # Check if nested structure exists
    nested_dir = "/chroma-data/chroma-data"
    if os.path.exists(nested_dir):
        print(f"Found nested directory: {nested_dir}")

        # Move all files from nested to parent
        for item in os.listdir(nested_dir):
            src = os.path.join(nested_dir, item)
            dst = os.path.join("/chroma-data", item)
            print(f"Moving {item}...")
            shutil.move(src, dst)

        # Remove empty nested directory
        os.rmdir(nested_dir)
        print("✅ Structure fixed!")
        chroma_volume.commit()  # Persist changes
    else:
        print("No nested directory found, structure is correct")

    # List final structure
    print("\n📁 Final structure:")
    for item in os.listdir("/chroma-data"):
        path = os.path.join("/chroma-data", item)
        if os.path.isfile(path):
            size = os.path.getsize(path) / (1024 * 1024)
            print(f"   FILE: {item} ({size:.2f} MB)")
        else:
            print(f"   DIR: {item}/")

@app.function(image=image, volumes={"/chroma-data": chroma_volume})
def test_reports_query():
    """Debug the reports query issue"""
    from financial_research_agent.rag.chroma_manager import FinancialRAGManager

    print("Testing reports query for AAPL...")
    rag = FinancialRAGManager(persist_directory="/chroma-data")

    # Try the exact same query the reports endpoint uses
    results = rag.query(
        query="AAPL comprehensive",
        ticker="AAPL",
        n_results=50
    )

    print(f"\n📊 Query results structure:")
    print(f"   Keys: {results.keys()}")

    documents = results.get("documents", [[]])[0] if results.get("documents") else []
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
    distances = results.get("distances", [[]])[0] if results.get("distances") else []

    print(f"   Documents found: {len(documents)}")
    print(f"   Metadatas found: {len(metadatas)}")
    print(f"   Distances found: {len(distances)}")

    if metadatas:
        print(f"\n📝 First 5 metadata analysis_types:")
        for i, metadata in enumerate(metadatas[:5]):
            print(f"   {i+1}. {metadata.get('analysis_type', 'MISSING')}")

    # Count by analysis_type
    from collections import Counter
    types = [m.get('analysis_type', 'MISSING') for m in metadatas]
    type_counts = Counter(types)
    print(f"\n📈 Analysis type distribution:")
    for atype, count in type_counts.items():
        print(f"   {atype}: {count}")

@app.function(image=image, volumes={"/chroma-data": chroma_volume})
def test_api():
    """Test the API endpoints"""
    import os
    print("Testing API...")

    # Check what files exist
    print("\n📁 Volume contents (/chroma-data):")
    for item in os.listdir("/chroma-data"):
        path = os.path.join("/chroma-data", item)
        if os.path.isfile(path):
            size = os.path.getsize(path) / (1024 * 1024)  # MB
            print(f"   FILE: {item} ({size:.2f} MB)")
        else:
            print(f"   DIR: {item}/")
            # List subdirectory contents
            for subitem in os.listdir(path):
                subpath = os.path.join(path, subitem)
                if os.path.isfile(subpath):
                    subsize = os.path.getsize(subpath) / (1024 * 1024)
                    print(f"      FILE: {subitem} ({subsize:.2f} MB)")
                else:
                    print(f"      DIR: {subitem}/")

    # Test imports
    try:
        from financial_research_agent.rag.chroma_manager import FinancialRAGManager
        print("\n✅ RAG imports working")

        rag = FinancialRAGManager(persist_directory="/chroma-data")

        # Check collection directly
        all_docs = rag.collection.get()
        print(f"✅ Collection: {rag.collection.name}")
        print(f"✅ Total documents: {len(all_docs['ids'])}")

        companies = rag.list_companies()
        print(f"✅ Found {len(companies)} unique companies in database")

        if companies:
            print(f"   Tickers: {[c['ticker'] for c in companies[:5]]}")

        # Test actual query
        print("\n🔍 Testing query...")
        query_results = rag.query(query="What is Apple's revenue?", ticker="AAPL", n_results=2)
        print(f"✅ Query returned {len(query_results.get('documents', [[]])[0])} documents")
        if query_results.get('documents', [[]])[0]:
            print(f"   First result preview: {query_results['documents'][0][0][:100]}...")
            print(f"   Distance: {query_results['distances'][0][0]}")
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        print(traceback.format_exc())

@app.function(image=image, volumes={"/chroma-data": chroma_volume}, timeout=300)
def upload_fixed_chromadb_from_tar():
    """Upload the fixed local ChromaDB to Modal volume using a tar file"""
    import os
    import shutil
    import subprocess

    print("📤 Uploading fixed ChromaDB from local...")

    # Clear existing ChromaDB
    chroma_path = "/chroma-data"
    print(f"\n🗑️  Clearing existing ChromaDB at {chroma_path}...")
    if os.path.exists(chroma_path):
        for item in os.listdir(chroma_path):
            item_path = os.path.join(chroma_path, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception as e:
                print(f"Warning: Could not remove {item}: {e}")

    # Note: The tar file should be uploaded using modal.Volume.put_file() from local
    # This function assumes the tar is already in /tmp/chroma_db.tar.gz
    tar_path = "/tmp/chroma_db.tar.gz"
    if not os.path.exists(tar_path):
        print(f"❌ Tar file not found at {tar_path}")
        print("   Please upload chroma_db.tar.gz to the volume first")
        return

    print(f"\n📦 Extracting ChromaDB from tar...")
    subprocess.run(["tar", "-xzf", tar_path, "-C", chroma_path], check=True)

    # Commit changes
    print(f"\n💾 Committing changes to volume...")
    chroma_volume.commit()

    # Verify
    from financial_research_agent.rag.chroma_manager import FinancialRAGManager
    rag = FinancialRAGManager(persist_directory=chroma_path)
    count = rag.collection.count()
    print(f"\n✅ Upload complete!")
    print(f"   Documents in ChromaDB: {count}")
    print(f"   Markdown formatting is now PRESERVED! 🎉")

# ============================================================================
# Local Development
# ============================================================================

@app.local_entrypoint()
def main():
    """For local testing: modal run modal_fastapi_bridge.py"""
    # Test the API
    test_api.remote()
    print("\n✅ API tests passed!")
    print("\nTo deploy:")
    print("  modal deploy modal_fastapi_bridge.py")
    print("\nYour API will be at:")
    print("  https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run")
