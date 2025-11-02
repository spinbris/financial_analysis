"""
Test Brave Search API integration.
"""

import os
import sys
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from financial_research_agent.tools.brave_search import _brave_search_impl

async def main():
    print("=" * 80)
    print("BRAVE SEARCH API TEST")
    print("=" * 80)

    # Test query
    query = "Apple Inc Q3 2025 earnings report"

    print(f"\nSearching for: {query}")
    print("-" * 80)

    try:
        results = await _brave_search_impl(query, count=5)
        print(results)
        print("\n" + "=" * 80)
        print("✅ Brave Search API test successful!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease check:")
        print("1. BRAVE_API_KEY is set in .env file")
        print("2. API key is valid")
        print("3. You have remaining quota")
        print("\nGet your API key at: https://brave.com/search/api/")

if __name__ == "__main__":
    asyncio.run(main())
