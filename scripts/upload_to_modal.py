#!/usr/bin/env python3
"""
Upload a local analysis directory to Modal ChromaDB.

Usage:
    python scripts/upload_to_modal.py --ticker AAPL --analysis-dir financial_research_agent/output/20251106_115436
"""
import argparse
from pathlib import Path
import sys
import modal

# Add project root to Python path to import modal_app
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the Modal app
from modal_app import app, index_local_analysis

def main():
    parser = argparse.ArgumentParser(description="Upload local analysis to Modal ChromaDB")
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

    if not local_path.is_dir():
        print(f"❌ Error: Not a directory: {local_path}")
        return 1

    # Check for required files
    required_files = [
        "07_comprehensive_report.md",
        "03_financial_statements.md",
        "04_financial_metrics.md"
    ]

    missing = [f for f in required_files if not (local_path / f).exists()]
    if missing:
        print(f"⚠️  Warning: Missing files: {', '.join(missing)}")
        print("   Continuing anyway, but indexing may be incomplete...")

    print(f"📤 Uploading {args.ticker} analysis from {local_path.name}...")

    try:
        # Use Modal CLI to run the function
        # This is more reliable than calling .remote() directly
        import subprocess

        cmd = [
            ".venv/bin/modal", "run", "modal_app.py::index_local_analysis",
            "--output-dir-path", str(local_path),
            "--ticker", args.ticker
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Print the output from Modal
        if result.stdout:
            print(result.stdout)

        print(f"\n✅ Upload successful for {args.ticker}!")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Upload failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return 1
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
