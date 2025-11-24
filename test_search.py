"""Test search functionality."""

from financial_research_agent.cache.sec_financial_cache import SecFinancialCache

def test_search():
    print("=" * 60)
    print("Testing Search Functionality")
    print("=" * 60)
    
    cache = SecFinancialCache()
    
    # Test 1: Search for "Revenue"
    print("\n🔍 Searching for 'Revenue'...")
    results = cache.search_line_items("Revenue", limit=10)
    print(f"   Found {len(results)} matches:")
    for r in results[:5]:
        print(f"   - {r['ticker']}: {r['label'][:40]}... = ${r['value']:,.0f}")
    
    # Test 2: Search for "Cash" in AAPL
    print("\n🔍 Searching for 'Cash' in AAPL...")
    results = cache.search_line_items("Cash", ticker="AAPL", limit=10)
    print(f"   Found {len(results)} matches:")
    for r in results[:5]:
        print(f"   - {r['label'][:50]}: ${r['value']:,.0f}")
    
    # Test 3: Compare Assets across companies
    print("\n📊 Comparing Total Assets...")
    comparison = cache.compare_companies(
        tickers=["AAPL", "MSFT", "BHP"],
        concepts=['us-gaap_Assets']
    )
    for ticker, values in comparison.items():
        assets = values.get('us-gaap_Assets')
        if assets:
            print(f"   {ticker}: ${assets:,.0f}")
    
    cache.close()
    print("\n✅ Search tests complete!")

if __name__ == "__main__":
    test_search()