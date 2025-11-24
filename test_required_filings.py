"""Test filing detection logic."""

from financial_research_agent.cache.sec_financial_cache import SecFinancialCache

def test_required_filings():
    """Test detecting required filings."""
    
    print("Testing get_required_filings()...")
    
    cache = SecFinancialCache()
    
    # Test US company
    print("\n📄 Testing US Company (AAPL):")
    aapl_filings = cache.get_required_filings("AAPL")
    
    print(f"   Annual: {aapl_filings['annual_type']}")
    print(f"   Date: {aapl_filings['annual']['filing_date']}")
    print(f"   Quarterlies: {len(aapl_filings['quarterlies'])}")
    print(f"   Standard: {aapl_filings['accounting_standard']}")
    print(f"   Foreign: {aapl_filings['is_foreign']}")
    
    # Test foreign company
    print("\n📄 Testing Foreign Company (BHP):")
    bhp_filings = cache.get_required_filings("BHP")
    
    print(f"   Annual: {bhp_filings['annual_type']}")
    print(f"   Date: {bhp_filings['annual']['filing_date']}")
    print(f"   Quarterlies: {len(bhp_filings['quarterlies'])}")
    print(f"   Standard: {bhp_filings['accounting_standard']}")
    print(f"   Foreign: {bhp_filings['is_foreign']}")
    
    if aapl_filings['annual_type'] == '10-K' and bhp_filings['annual_type'] == '20-F':
        print("\n✅ Filing detection working correctly!")
    
    cache.close()
    
    return True

if __name__ == "__main__":
    test_required_filings()