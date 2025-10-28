"""
Enhanced Financial Research Agent - Entry Point

This version produces comprehensive 3-5 page research reports with:
- 800-1200 word specialist analysis (financials & risk)
- SEC EDGAR integration for authoritative data
- Investment-grade quality suitable for institutional investors

Usage:
    python -m financial_research_agent.main_enhanced

Or:
    python financial_research_agent/main_enhanced.py
"""

import asyncio
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # ImportError or any other import-time issue
    load_dotenv = None
    # Helpful runtime guidance when dotenv isn't available
    print("\n⚠️  Optional package 'python-dotenv' (module name: dotenv) is not installed.")
    print("If you want to load environment variables from a .env file, install it into your environment.")
    print("Preferred (project workflow):")
    print("  uv pip install python-dotenv")
    print("")
    print("Or using the project's virtualenv:")
    print("  # activate venv (recommended)")
    print("  source .venv/bin/activate")
    print("  pip install python-dotenv")
    print("")
    print("Or install without activating: ./.venv/bin/python -m pip install python-dotenv")
    print("")
    print("You can also run the script with the project's venv Python explicitly:")
    print("  ./.venv/bin/python -m financial_research_agent.main_enhanced\n")

# Load environment variables from .env file
# Look for .env in the financial_research_agent directory
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    if load_dotenv:
        load_dotenv(env_path, override=True)
        print(f"✓ Loaded environment from: {env_path}")
    else:
        print(f"⚠️  Found .env at {env_path} but 'python-dotenv' is not installed, skipping load.")
else:
    # Try parent directory
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        if load_dotenv:
            load_dotenv(env_path, override=True)
            print(f"✓ Loaded environment from: {env_path}")
        else:
            print(f"⚠️  Found .env at {env_path} but 'python-dotenv' is not installed, skipping load.")
    else:
        print("⚠️  Warning: No .env file found. Using environment variables only.")

# Verify OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("\n❌ Error: OPENAI_API_KEY not set!")
    print("Please set your OpenAI API key in the .env file or environment.")
    print(f"Looking for .env at: {Path(__file__).parent / '.env'}")
    sys.exit(1)

# Check EDGAR configuration if enabled
edgar_enabled = os.getenv("ENABLE_EDGAR_INTEGRATION", "false").lower() == "true"
if edgar_enabled:
    user_agent = os.getenv("SEC_EDGAR_USER_AGENT", "")
    if not user_agent or user_agent == "FinancialResearchAgent/1.0 (your-email@example.com)":
        print("\n⚠️  Warning: EDGAR integration is enabled but SEC_EDGAR_USER_AGENT is not properly configured.")
        print("Please set it to: 'YourCompany/Version (your-email@example.com)' in .env")
        print("See: https://www.sec.gov/os/accessing-edgar-data")
        print("\nContinuing without EDGAR integration...")
        os.environ["ENABLE_EDGAR_INTEGRATION"] = "false"
    else:
        print(f"✓ EDGAR integration enabled with User-Agent: {user_agent}")

from .manager_enhanced import EnhancedFinancialResearchManager


async def main() -> None:
    """Main entry point for enhanced financial research agent."""
    print("\n" + "=" * 70)
    print("  ENHANCED FINANCIAL RESEARCH AGENT")
    print("  Comprehensive 3-5 Page Investment-Grade Reports")
    print("=" * 70)
    print()
    print("This enhanced version produces:")
    print("  • 800-1200 word comprehensive financial analysis")
    print("  • 800-1200 word comprehensive risk assessment")
    print("  • 1500-2500 word synthesized research report (3-5 pages)")
    if edgar_enabled:
        print("  • SEC EDGAR integration for authoritative filing data")
    print()
    print("Example queries:")
    print("  • Analyze Apple's most recent quarterly performance")
    print("  • What are the key risks facing Tesla?")
    print("  • Compare Microsoft and Google's financial health")
    print()
    print("-" * 70)
    print()

    # Get query from user
    query = input("Enter your financial research query: ").strip()

    if not query:
        print("❌ No query provided. Exiting.")
        return

    print()
    print("Starting comprehensive research...")
    print()

    # Create and run the enhanced manager
    mgr = EnhancedFinancialResearchManager()

    try:
        await mgr.run(query)
    except KeyboardInterrupt:
        print("\n\n⚠️  Research interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error during research: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
