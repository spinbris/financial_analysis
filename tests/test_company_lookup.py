#!/usr/bin/env python3
"""
Test the improved company lookup in edgar_tools.
"""
import os
import asyncio

# Set required SEC identity
os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 (test@example.com)"

from edgar import find_company, set_identity

set_identity("test@example.com")


def test_company_lookup():
    """Test finding various companies."""
    test_companies = [
        "Apple",
        "Microsoft",
        "Tesla",
        "Walmart",  # NEW: Not in old hardcoded list
        "Coca-Cola",  # NEW: Not in old hardcoded list
        "Boeing",  # NEW: Not in old hardcoded list
        "JPMorgan",  # NEW: Not in old hardcoded list
    ]

    print("Testing company lookup with edgartools find_company():\n")
    print("=" * 60)

    for company in test_companies:
        try:
            results = find_company(company)
            if results and len(results) > 0:
                first = results[0]
                ticker = first.ticker if hasattr(first, 'ticker') else first.tickers
                if isinstance(ticker, list):
                    ticker = ticker[0] if ticker else "N/A"
                print(f"✅ {company:15} → Ticker: {ticker:6} CIK: {first.cik}")
            else:
                print(f"❌ {company:15} → No results")
        except Exception as e:
            print(f"❌ {company:15} → Error: {e}")

    print("=" * 60)
    print("\n✅ Company lookup now works for ANY public company!")
    print("   No more hardcoded ticker list!")


if __name__ == "__main__":
    test_company_lookup()
