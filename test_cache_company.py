"""Test caching multiple companies."""

import time
from financial_research_agent.cache.sec_financial_cache import SecFinancialCache

def test_cache_companies():
    """Test caching multiple companies."""
    
    print("=" * 60)
    print("Testing Multi-Company Caching")
    print("=" * 60)
    
    cache = SecFinancialCache()
    
    # Companies to test (mix of US and foreign)
    companies = [
        ("AAPL", "Apple - US Tech"),
        ("MSFT", "Microsoft - US Tech"),
        ("BHP", "BHP Group - Australian Mining (20-F)"),
    ]
    
    results = []
    
    for ticker, description in companies:
        print(f"\n📦 Caching {ticker} ({description})...")
        
        result = cache.cache_company(ticker)
        results.append(result)
        
        if result.get('from_cache'):
            print(f"   ⚡ Already cached! {result['total_items']} items available")
        elif result.get('error'):
            print(f"   ❌ Error: {result['error']}")
        else:
            print(f"   ✅ Cached {result['filings_cached']} filings")
            print(f"   📊 Total items: {result['total_items']}")
            print(f"   ⏱️  Time: {result['cache_time_seconds']}s")
            print(f"   🌍 Foreign: {result['is_foreign']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 CACHE SUMMARY")
    print("=" * 60)
    
    stats = cache.get_cache_stats()
    print(f"   Total filings: {stats['total_filings']}")
    print(f"   Unique companies: {stats['unique_companies']}")
    print(f"   Database size: {stats['database_size_mb']} MB")
    
    # Test retrieval speed
    print("\n⚡ Testing retrieval speed...")
    start = time.time()
    for ticker, _ in companies:
        data = cache.get_cached_financials(ticker)
    elapsed = time.time() - start
    
    print(f"   Retrieved {len(companies)} companies in {elapsed*1000:.2f}ms")
    print(f"   Average: {elapsed*1000/len(companies):.2f}ms per company")
    
    cache.close()
    
    print("\n✅ Multi-company caching complete!")
    
    return results

if __name__ == "__main__":
    test_cache_companies()