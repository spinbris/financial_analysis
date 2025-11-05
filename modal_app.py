"""
Modal app for financial analysis with ChromaDB RAG.

Deploy: modal deploy modal_app.py
Run locally: modal run modal_app.py::analyze_company --ticker TSLA
"""
import modal
import os
from pathlib import Path

# Create Modal app
app = modal.App("financial-research-agent")

# Define Python dependencies and include local code
# Using Modal 1.0 API: add_local_python_source instead of Mount.from_local_dir
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "chromadb>=0.4.24",
        "openai-agents>=0.4.2",  # Includes pydantic-ai, brave search MCP, etc.
        "pandas>=2.0.0",
        "edgartools>=2.29.0",
        "python-dotenv>=1.0.0",
        "great-tables>=0.8.0",  # For table formatting
        "rich>=13.0.0",
    )
    .add_local_python_source("financial_research_agent")  # Modal 1.0 way to include local code
)

# Create persistent volume for ChromaDB
chroma_volume = modal.Volume.from_name("financial-chroma-db", create_if_missing=True)

# Secrets for API keys
secrets = [
    modal.Secret.from_name("openai-secret"),  # OPENAI_API_KEY
    modal.Secret.from_name("brave-secret"),   # BRAVE_API_KEY
]


@app.function(
    image=image,
    volumes={"/data": chroma_volume},
    secrets=secrets,
    timeout=600,  # 10 minute timeout for comprehensive analysis
    cpu=2.0,
    memory=4096,  # 4GB RAM
)
def analyze_company(
    ticker: str,
    force_refresh: bool = False,
    user_openai_key: str | None = None,
    user_brave_key: str | None = None
) -> dict:
    """
    Analyze a company's latest financial performance.

    Args:
        ticker: Stock ticker symbol (e.g., "TSLA", "AAPL")
        force_refresh: If True, regenerate analysis even if recent one exists
        user_openai_key: Optional OpenAI API key (if user wants to use their own key)
        user_brave_key: Optional Brave Search API key (if user wants to use their own key)

    Returns:
        Dictionary with analysis results and ChromaDB indexing status
    """
    # Import your existing agent workflow
    from financial_research_agent.main_enhanced import run_comprehensive_analysis
    from financial_research_agent.rag.chroma_manager import FinancialRAGManager

    # Set SEC EDGAR user agent
    os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

    # Use user-provided keys if available, otherwise use admin keys from secrets
    if user_openai_key:
        os.environ["OPENAI_API_KEY"] = user_openai_key
        print("🔑 Using user-provided OpenAI key")
    else:
        print("🔑 Using admin OpenAI key from Modal secrets")

    if user_brave_key:
        os.environ["BRAVE_API_KEY"] = user_brave_key
        print("🔑 Using user-provided Brave key")
    else:
        print("🔑 Using admin Brave key from Modal secrets")

    print(f"🔍 Analyzing {ticker}...")

    # Check if recent analysis exists in ChromaDB
    rag = FinancialRAGManager(persist_directory="/data/chroma_db")

    if not force_refresh:
        existing = rag.get_latest_analysis(ticker)
        if existing and existing.get('days_old', 999) < 7:
            print(f"✓ Recent analysis found ({existing['days_old']} days old), using cached version")
            return {
                "status": "cached",
                "ticker": ticker,
                "analysis_date": existing['analysis_date'],
                "output_dir": None
            }

    # Run comprehensive analysis
    output_dir = run_comprehensive_analysis(
        query=f"Analyze {ticker}'s latest financial performance",
        output_dir="/tmp/financial_analysis_output"
    )

    print(f"✓ Analysis complete: {output_dir}")

    # Parse and index in ChromaDB
    print(f"📚 Indexing analysis in ChromaDB...")
    metadata = rag.index_analysis_from_directory(output_dir, ticker)

    # Commit volume changes
    chroma_volume.commit()

    print(f"✅ Analysis indexed: {metadata['total_chunks']} chunks")

    return {
        "status": "success",
        "ticker": ticker,
        "output_dir": output_dir,
        "chroma_metadata": metadata
    }


@app.function(
    image=image,
    volumes={"/data": chroma_volume},
    timeout=120,
)
def index_local_analysis(output_dir_path: str, ticker: str) -> dict:
    """
    Index a locally-generated analysis into Modal's ChromaDB.

    This function allows you to upload analyses you've generated locally
    (with your API keys) to the shared Modal ChromaDB for all users to query.

    Usage:
        modal run modal_app.py::index_local_analysis \\
            --output-dir-path /path/to/output/20251104_185139 \\
            --ticker TSLA

    Args:
        output_dir_path: Absolute path to local analysis output directory
        ticker: Stock ticker symbol

    Returns:
        Indexing metadata
    """
    from financial_research_agent.rag.chroma_manager import FinancialRAGManager
    from pathlib import Path

    print(f"📤 Uploading analysis for {ticker} from {output_dir_path}...")

    rag = FinancialRAGManager(persist_directory="/data/chroma_db")

    # Index the analysis
    metadata = rag.index_analysis_from_directory(output_dir_path, ticker)

    # Commit to volume
    chroma_volume.commit()

    print(f"✅ Analysis uploaded: {metadata['total_chunks']} chunks indexed")

    return metadata


@app.function(
    image=image,
    volumes={"/data": chroma_volume},
    secrets=secrets,
    schedule=modal.Cron("0 2 * * *"),  # Run at 2 AM daily
)
def daily_batch_update():
    """
    Daily batch job to update top companies.
    Runs in parallel for speed.
    """
    # Top 50 most-watched companies
    tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B", "UNH", "JNJ",
        "V", "XOM", "WMT", "JPM", "PG", "MA", "HD", "CVX", "ABBV", "MRK",
        "KO", "PEP", "COST", "AVGO", "LLY", "ADBE", "TMO", "NKE", "ACN", "MCD",
        "CSCO", "ABT", "CRM", "DHR", "WFC", "TXN", "NEE", "ORCL", "VZ", "PM",
        "UPS", "BMY", "INTC", "QCOM", "HON", "RTX", "AMGN", "SBUX", "LOW", "AMD"
    ]

    print(f"🚀 Starting daily batch update for {len(tickers)} companies...")

    # Run analyses in parallel (Modal handles distribution)
    results = []
    for result in analyze_company.map(tickers, kwargs={"force_refresh": False}):
        results.append(result)

    success_count = sum(1 for r in results if r['status'] in ['success', 'cached'])
    print(f"✅ Batch update complete: {success_count}/{len(tickers)} successful")

    return {
        "total": len(tickers),
        "successful": success_count,
        "results": results
    }


@app.function(
    image=image,
    volumes={"/data": chroma_volume},
    secrets=secrets,
)
@modal.asgi_app()
def web_app():
    """
    FastAPI web server for querying ChromaDB and serving frontend.

    Accessible at: https://<your-username>--financial-research-agent-web-app.modal.run
    """
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel

    from financial_research_agent.rag.chroma_manager import FinancialRAGManager

    app = FastAPI(title="Financial Research Agent API")
    rag = FinancialRAGManager(persist_directory="/data/chroma_db")

    class QueryRequest(BaseModel):
        query: str
        ticker: str | None = None
        analysis_type: str | None = None
        n_results: int = 5

    class AnalysisRequest(BaseModel):
        ticker: str
        force_refresh: bool = False
        openai_api_key: str | None = None  # Optional: user can provide their own key
        brave_api_key: str | None = None   # Optional: user can provide their own key

    class CompareRequest(BaseModel):
        tickers: list[str]
        query: str
        n_results_per_company: int = 3

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Simple landing page."""
        return """
        <html>
            <head><title>Financial Research Agent</title></head>
            <body>
                <h1>Financial Research Agent API</h1>
                <p>Endpoints:</p>
                <ul>
                    <li>POST /api/query - Query ChromaDB</li>
                    <li>POST /api/analyze - Trigger new analysis</li>
                    <li>POST /api/compare - Compare multiple companies</li>
                    <li>GET /api/companies - List analyzed companies</li>
                    <li>GET /docs - OpenAPI documentation</li>
                </ul>
            </body>
        </html>
        """

    @app.post("/api/query")
    async def query_analyses(req: QueryRequest):
        """Natural language query across all analyses."""
        try:
            results = rag.query(
                query=req.query,
                ticker=req.ticker,
                analysis_type=req.analysis_type,
                n_results=req.n_results
            )

            # Check if confidence is low (distance > 0.5)
            if results['distances'][0] and results['distances'][0][0] > 0.5:
                return {
                    "source": "low_confidence",
                    "message": "No relevant analyses found in database",
                    "results": results
                }

            return {
                "source": "chroma_db",
                "results": results
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/analyze")
    async def trigger_analysis(req: AnalysisRequest, background_tasks: BackgroundTasks):
        """
        Trigger new analysis for a company (async).

        Users can optionally provide their own API keys. If keys are provided,
        the analysis runs with their keys (they pay for compute/API costs).
        Otherwise, uses admin keys from Modal secrets (you pay).
        """
        # Determine who's paying
        using_user_keys = bool(req.openai_api_key)

        # Run analysis in background
        background_tasks.add_task(
            analyze_company.remote,
            ticker=req.ticker,
            force_refresh=req.force_refresh,
            user_openai_key=req.openai_api_key,
            user_brave_key=req.brave_api_key
        )

        return {
            "status": "queued",
            "ticker": req.ticker,
            "using_user_keys": using_user_keys,
            "message": f"Analysis for {req.ticker} queued. Check back in 5-10 minutes.",
            "cost_note": "Using your API keys" if using_user_keys else "Using admin keys (limited analyses available)"
        }

    @app.post("/api/compare")
    async def compare_companies(req: CompareRequest):
        """Compare multiple companies on a specific aspect."""
        try:
            results = rag.compare_peers(
                tickers=req.tickers,
                query=req.query,
                n_results_per_company=req.n_results_per_company
            )
            return {
                "query": req.query,
                "companies": results
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/companies")
    async def list_companies():
        """List all companies with analyses in ChromaDB."""
        try:
            companies = rag.list_companies()
            return {
                "total": len(companies),
                "companies": companies
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


# CLI for local testing
@app.local_entrypoint()
def main(ticker: str = "TSLA"):
    """Run analysis locally for testing."""
    result = analyze_company.remote(ticker=ticker, force_refresh=True)
    print(f"✅ Result: {result}")
