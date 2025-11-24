"""Test SecFinancialCache class initialization."""

from financial_research_agent.cache.sec_financial_cache import SecFinancialCache

def test_cache_initialization():
    """Test cache initializes correctly."""
    
    print("Testing SecFinancialCache initialization...")
    
    # Initialize cache
    cache = SecFinancialCache()
    
    # Get stats
    stats = cache.get_cache_stats()
    
    print(f"\n✅ Cache initialized successfully!")
    print(f"   Database: {stats['database_path']}")
    print(f"   Size: {stats['database_size_mb']} MB")
    print(f"   Total filings: {stats['total_filings']}")
    print(f"   Unique companies: {stats['unique_companies']}")
    
    cache.close()
    
    return True

if __name__ == "__main__":
    test_cache_initialization()