#!/usr/bin/env python3
"""
Upload locally-generated analyses directly to ChromaDB.

This script runs locally and indexes analysis files into ChromaDB,
which can then be synced to Modal's persistent volume.

Usage:
    python scripts/upload_local_to_chroma.py --ticker AAPL --analysis-dir financial_research_agent/output/20251106_115436
"""
import argparse
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from financial_research_agent.rag.chroma_manager import FinancialRAGManager


def main():
    parser = argparse.ArgumentParser(description="Upload local analysis to ChromaDB")
    parser.add_argument("--ticker", required=True, help="Stock ticker symbol (e.g., AAPL)")
    parser.add_argument(
        "--analysis-dir",
        required=True,
        help="Path to local analysis directory (e.g., financial_research_agent/output/20251106_115436)"
    )

    args = parser.parse_args()

    # Resolve to absolute path
    local_path = Path(args.analysis_dir).resolve()

    if not local_path.exists():
        print(f"❌ Error: Directory not found: {local_path}")
        return 1

    # Verify required files exist (based on chroma_manager.py expected filenames)
    required_files = [
        "07_comprehensive_report.md",
        "03_financial_statements.md",
        "04_financial_metrics.md",
        "05_financial_analysis.md",
        "06_risk_analysis.md"
    ]

    missing = [f for f in required_files if not (local_path / f).exists()]
    if missing:
        print(f"⚠️  Warning: Missing files: {', '.join(missing)}")
        print("   Continuing anyway, but indexing may be incomplete...")

    print(f"📤 Indexing {args.ticker} analysis from {local_path.name}...")

    try:
        # Initialize ChromaDB manager
        # Use local persistent directory for ChromaDB
        chroma_path = project_root / "chroma_db"
        chroma_path.mkdir(exist_ok=True)

        rag_manager = FinancialRAGManager(
            persist_directory=str(chroma_path)
        )

        # Index the analysis
        result = rag_manager.index_analysis_from_directory(
            output_dir=str(local_path),
            ticker=args.ticker
        )

        print(f"\n✅ Indexing successful!")
        print(f"   Ticker: {args.ticker}")
        print(f"   Chunks indexed: {result['total_chunks']}")
        print(f"   Files indexed: {', '.join(result['indexed_files'])}")
        print(f"   ChromaDB location: {chroma_path}")

        return 0

    except Exception as e:
        print(f"\n❌ Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
