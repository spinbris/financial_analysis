#!/usr/bin/env python3
"""
Examples of querying the ChromaDB knowledge base for semantic search.

This demonstrates how to query financial analyses stored in ChromaDB
both locally and via Modal's API.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from financial_research_agent.rag.chroma_manager import FinancialRAGManager


def example_1_basic_query():
    """Example 1: Basic semantic search across all companies."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Semantic Search")
    print("="*70)

    rag = FinancialRAGManager(persist_directory="./chroma_db")

    # Natural language query - finds most relevant chunks across ALL indexed analyses
    query = "What are the main revenue sources?"

    results = rag.query(
        query=query,
        n_results=5  # Top 5 most relevant chunks
    )

    print(f"\nQuery: '{query}'")
    print(f"Found {len(results['documents'][0])} results\n")

    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        print(f"\n--- Result {i+1} (Similarity: {1-distance:.2%}) ---")
        print(f"Company: {metadata.get('company', 'Unknown')} ({metadata['ticker']})")
        print(f"Section: {metadata['section']}")
        print(f"Analysis Type: {metadata['analysis_type']}")
        print(f"\nContent Preview:")
        print(doc[:300] + "...")


def example_2_ticker_filtered():
    """Example 2: Query specific company only."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Company-Specific Query")
    print("="*70)

    rag = FinancialRAGManager(persist_directory="./chroma_db")

    query = "What are the key risk factors?"
    ticker = "AAPL"

    results = rag.query(
        query=query,
        ticker=ticker,  # Filter to only Apple
        n_results=3
    )

    print(f"\nQuery: '{query}' for {ticker}")
    print(f"Found {len(results['documents'][0])} results\n")

    for i, (doc, metadata) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0]
    )):
        print(f"\n--- Result {i+1} ---")
        print(f"Section: {metadata['section']}")
        print(f"Period: {metadata.get('period', 'N/A')}")
        print(f"\nContent:")
        print(doc[:400] + "...")


def example_3_analysis_type_filter():
    """Example 3: Query specific type of analysis."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Analysis Type Filter")
    print("="*70)

    rag = FinancialRAGManager(persist_directory="./chroma_db")

    # Only search risk analyses
    query = "regulatory challenges"

    results = rag.query(
        query=query,
        analysis_type="risk",  # Only search risk analysis documents
        n_results=5
    )

    print(f"\nQuery: '{query}' in risk analyses")
    print(f"Found {len(results['documents'][0])} results\n")

    for i, (doc, metadata) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0]
    )):
        print(f"\n--- Result {i+1}: {metadata['ticker']} ---")
        print(f"Company: {metadata.get('company', 'Unknown')}")
        print(f"Section: {metadata['section']}")
        print(doc[:300] + "...")


def example_4_peer_comparison():
    """Example 4: Compare multiple companies on same topic."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Peer Comparison")
    print("="*70)

    rag = FinancialRAGManager(persist_directory="./chroma_db")

    tickers = ["AAPL", "MSFT", "GOOGL"]
    query = "cloud services and AI strategy"

    comparison = rag.compare_peers(
        tickers=tickers,
        query=query,
        n_results_per_company=2
    )

    print(f"\nQuery: '{query}'")
    print(f"Comparing: {', '.join(tickers)}\n")

    for ticker, results in comparison.items():
        print(f"\n{'='*50}")
        print(f"{ticker}")
        print('='*50)

        for i, (doc, metadata) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0]
        )):
            print(f"\n  Match {i+1}: {metadata['section']}")
            print(f"  {doc[:250]}...")


def example_5_list_companies():
    """Example 5: List all indexed companies."""
    print("\n" + "="*70)
    print("EXAMPLE 5: List All Indexed Companies")
    print("="*70)

    rag = FinancialRAGManager(persist_directory="./chroma_db")

    companies = rag.list_companies()

    print(f"\nTotal companies indexed: {len(companies)}\n")

    for company in companies:
        print(f"{company['ticker']:6} - {company['company']}")
        print(f"        Latest: {company['latest_period']} ({company['filing_type']})")


def example_6_financial_metrics_query():
    """Example 6: Query for specific financial metrics."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Financial Metrics Search")
    print("="*70)

    rag = FinancialRAGManager(persist_directory="./chroma_db")

    # Search for profitability metrics
    query = "profit margins and return on equity"

    results = rag.query(
        query=query,
        analysis_type="financial_metrics",  # Only search metrics documents
        n_results=3
    )

    print(f"\nQuery: '{query}' in financial metrics")
    print(f"Found {len(results['documents'][0])} results\n")

    for i, (doc, metadata) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0]
    )):
        print(f"\n--- {metadata['ticker']} ---")
        print(f"Section: {metadata['section']}")
        print(doc[:400] + "...")


def main():
    """Run all examples."""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                                                               ║")
    print("║     ChromaDB Semantic Query Examples                         ║")
    print("║     Financial Analysis Knowledge Base                        ║")
    print("║                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════╝")

    # Check if ChromaDB exists
    if not Path("./chroma_db").exists():
        print("\n❌ ChromaDB not found at ./chroma_db")
        print("   Run some analyses first or use Modal's API endpoint\n")
        return 1

    try:
        # Run examples
        example_5_list_companies()  # Start with this to see what's available
        example_1_basic_query()
        example_2_ticker_filtered()
        example_3_analysis_type_filter()
        example_4_peer_comparison()
        example_6_financial_metrics_query()

        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70)
        print("\nTip: You can also query via Modal's REST API:")
        print("  curl https://YOUR-USERNAME--financial-research-agent-web-app.modal.run/api/query \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{\"query\": \"your question here\", \"n_results\": 5}'")
        print()

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
