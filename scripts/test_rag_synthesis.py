#!/usr/bin/env python3
"""
Test script for RAG synthesis functionality.

Demonstrates how to query the indexed financial analyses and get synthesized responses.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from financial_research_agent.rag.chroma_manager import FinancialRAGManager


def print_response(response):
    """Pretty print a RAGResponse object."""
    print("\n" + "="*80)
    print("ANSWER")
    print("="*80)
    print(response.answer)

    print("\n" + "-"*80)
    print(f"CONFIDENCE: {response.confidence.upper()}")
    print("-"*80)

    if response.sources_cited:
        print("\nSOURCES CITED:")
        for i, source in enumerate(response.sources_cited, 1):
            print(f"  {i}. {source}")

    if response.limitations:
        print("\nLIMITATIONS:")
        print(f"  {response.limitations}")

    if response.suggested_followup:
        print("\nSUGGESTED FOLLOW-UP QUESTIONS:")
        for i, question in enumerate(response.suggested_followup, 1):
            print(f"  {i}. {question}")

    print("\n" + "="*80 + "\n")


def main():
    """Run example queries against the indexed knowledge base."""

    print("\n" + "🔍 RAG Synthesis Test - Financial Research Knowledge Base" + "\n")

    # Initialize ChromaDB manager
    chroma_path = project_root / "chroma_db"

    if not chroma_path.exists():
        print("❌ ChromaDB not found. Please run upload_local_to_chroma.py first.")
        return 1

    print(f"📂 Loading ChromaDB from: {chroma_path}")
    rag_manager = FinancialRAGManager(persist_directory=str(chroma_path))

    # List available companies
    companies = rag_manager.list_companies()
    print(f"\n✅ Found {len(companies)} companies in knowledge base:")
    for company in companies:
        ticker = company['ticker']
        name = company.get('company', 'Unknown')
        period = company.get('latest_period', 'Unknown')
        print(f"   • {ticker} - {name} ({period})")

    # Example queries to test
    example_queries = [
        {
            "query": "What was Apple's revenue in Q3 2024?",
            "ticker": "AAPL",
            "description": "Simple factual query"
        },
        {
            "query": "What are the main risks facing Tesla?",
            "ticker": "TSLA",
            "description": "Risk assessment query"
        },
        {
            "query": "How did Microsoft's operating margin change?",
            "ticker": "MSFT",
            "description": "Trend analysis query"
        },
        {
            "query": "Compare Apple and Microsoft's profitability",
            "ticker": None,
            "description": "Multi-company comparison"
        },
    ]

    print("\n" + "="*80)
    print("RUNNING EXAMPLE QUERIES")
    print("="*80)

    for i, example in enumerate(example_queries, 1):
        print(f"\n\n{'='*80}")
        print(f"QUERY {i}: {example['description']}")
        print(f"{'='*80}")
        print(f"Question: {example['query']}")
        if example['ticker']:
            print(f"Filter: ticker={example['ticker']}")

        try:
            # Query with synthesis
            response = rag_manager.query_with_synthesis(
                query=example['query'],
                ticker=example['ticker'],
                n_results=5
            )

            # Print the response
            print_response(response)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    # Interactive mode
    print("\n" + "="*80)
    print("INTERACTIVE MODE")
    print("="*80)
    print("Enter your questions below (or 'quit' to exit)")
    print("Optional: Add 'ticker=AAPL' at the end to filter by company")
    print()

    while True:
        try:
            user_input = input("\n💬 Your question: ").strip()

            if not user_input or user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            # Check for ticker filter
            ticker = None
            if 'ticker=' in user_input.lower():
                parts = user_input.rsplit('ticker=', 1)
                user_input = parts[0].strip()
                ticker = parts[1].strip().upper()
                print(f"   (Filtering by ticker: {ticker})")

            # Query with synthesis
            response = rag_manager.query_with_synthesis(
                query=user_input,
                ticker=ticker,
                n_results=5
            )

            # Print the response
            print_response(response)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    return 0


if __name__ == "__main__":
    exit(main())
