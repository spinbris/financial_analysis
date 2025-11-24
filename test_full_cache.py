"""Test complete caching workflow with real AAPL data."""

import time
from financial_research_agent.cache.sec_financial_cache import SecFinancialCache

def test_full_cache_workflow():
    """Test complete cache workflow."""
    
    print("=" * 60)
    print("Testing Full Cache Workflow with AAPL")
    print("=" * 60)
    
    cache = SecFinancialCache()
    ticker = "AAPL"
    
    # Step 1: Check initial status
    print("\n1️⃣  Checking cache status...")
    status = cache.check_cache_status(ticker)
    print(f"   Cached: {status['cached']}")
    print(f"   Needs update: {status['needs_update']}")
    
    # Step 2: Get required filings
    print("\n2️⃣  Getting required filings...")
    start = time.time()
    filings = cache.get_required_filings(ticker)
    elapsed = time.time() - start
    print(f"   Found: {filings['annual_type']} + {len(filings['quarterlies'])} quarterlies")
    print(f"   Time: {elapsed:.2f}s")
    
    # Step 3: Cache the annual filing
    print("\n3️⃣  Caching annual filing...")
    start = time.time()
    filing_id = cache.cache_filing(ticker, filings['annual'])
    elapsed = time.time() - start
    print(f"   Cached filing ID: {filing_id}")
    print(f"   Time: {elapsed:.2f}s")
    
    # Step 4: Retrieve from cache
    print("\n4️⃣  Retrieving from cache...")
    start = time.time()
    cached_data = cache.get_cached_financials(ticker, periods=1)
    elapsed = time.time() - start
    
    if cached_data:
        period = cached_data['periods'][0]
        print(f"   ✅ Retrieved successfully!")
        print(f"   Time: {elapsed:.4f}s ({elapsed*1000:.2f}ms)")
        print(f"   Balance sheet items: {len(period['balance_sheet'])}")
        print(f"   Income statement items: {len(period['income_statement'])}")
        print(f"   Cash flow items: {len(period['cash_flow'])}")
        
        # Show sample data
        if period['balance_sheet']:
            print(f"\n   📊 Sample Balance Sheet Items:")
            for item in period['balance_sheet'][:3]:
                print(f"      {item['label']}: ${item['value']:,.0f}")
    
    # Step 5: Check updated status
    print("\n5️⃣  Checking updated cache status...")
    status = cache.check_cache_status(ticker)
    print(f"   Cached: {status['cached']}")
    print(f"   Current: {status['current']}")
    print(f"   Age: {status['cache_age_days']} days")
    print(f"   Filings: {status['filing_count']}")
    
    # Step 6: Get cache stats
    print("\n6️⃣  Cache Statistics:")
    stats = cache.get_cache_stats()
    print(f"   Total filings: {stats['total_filings']}")
    print(f"   Unique companies: {stats['unique_companies']}")
    print(f"   Database size: {stats['database_size_mb']} MB")
    
    cache.close()
    
    print("\n" + "=" * 60)
    print("✅ Full cache workflow complete!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_full_cache_workflow()