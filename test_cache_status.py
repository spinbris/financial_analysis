"""Test cache status detection."""

from financial_research_agent.cache.sec_financial_cache import SecFinancialCache

def test_cache_status():
    """Test checking cache status."""
    
    print("Testing cache_status()...")
    
    cache = SecFinancialCache()
    
    # Test with uncached ticker
    status = cache.check_cache_status("AAPL")
    
    print(f"\n📊 AAPL Cache Status:")
    print(f"   Cached: {status['cached']}")
    print(f"   Current: {status['current']}")
    print(f"   Needs update: {status['needs_update']}")
    print(f"   Filing count: {status['filing_count']}")
    
    if not status['cached']:
        print("\n✅ Correct! AAPL is not cached yet.")
    else:
        print(f"\n   Cache age: {status['cache_age_days']} days")
        print(f"   Latest filing: {status['latest_filing_date']}")
    
    cache.close()
    
    return True

if __name__ == "__main__":
    test_cache_status()