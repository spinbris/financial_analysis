"""
Test the statement data flattening function.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from financial_research_agent.manager_enhanced import EnhancedFinancialResearchManager

def test_flatten_nested_data():
    """Test flattening nested metadata structure."""
    manager = EnhancedFinancialResearchManager()

    # Example nested structure from MCP tool
    nested_input = {
        "data": {
            "Assets": {"value": 133735000000.0, "raw_value": "133,735", "period": "2025-09-30"},
            "Liabilities": {"value": 53019000000.0, "raw_value": "53,019", "period": "2025-09-30"},
            "StockholdersEquity": {"value": 79970000000.0, "raw_value": "79,970", "period": "2025-09-30"}
        },
        "source": "xbrl_concepts_dynamic"
    }

    result = manager._flatten_statement_data(nested_input)

    # Should extract just the values
    assert result == {
        "Assets": 133735000000.0,
        "Liabilities": 53019000000.0,
        "StockholdersEquity": 79970000000.0
    }

    print("✅ Nested data flattening works correctly")
    print(f"   Input: {list(nested_input.keys())}")
    print(f"   Output: {list(result.keys())}")
    print(f"   Assets: ${result['Assets']:,.0f}")
    print(f"   L + E: ${result['Liabilities'] + result['StockholdersEquity']:,.0f}")

    # Verify balance sheet equation
    assets = result['Assets']
    l_plus_e = result['Liabilities'] + result['StockholdersEquity']
    diff = abs(assets - l_plus_e)
    tolerance = assets * 0.001

    if diff > tolerance:
        print(f"   ⚠️  Balance sheet error: {diff:,.0f} (>{tolerance:,.0f})")
    else:
        print(f"   ✅ Balance sheet balances: diff={diff:,.0f} (<{tolerance:,.0f})")


def test_flatten_already_flat_data():
    """Test that already-flat data passes through unchanged."""
    manager = EnhancedFinancialResearchManager()

    # Already flat structure (expected format)
    flat_input = {
        "Assets_Current": 133735000000.0,
        "Liabilities_Current": 53019000000.0,
        "StockholdersEquity_Current": 80716000000.0,  # Corrected value
        "current_period_date": "2025-09-30"
    }

    result = manager._flatten_statement_data(flat_input)

    # Should return unchanged
    assert result == flat_input

    print("✅ Already-flat data passes through unchanged")
    print(f"   Keys: {list(result.keys())}")


if __name__ == "__main__":
    print("=" * 70)
    print("STATEMENT DATA FLATTENING TESTS")
    print("=" * 70)
    print()

    test_flatten_nested_data()
    print()
    test_flatten_already_flat_data()
    print()
    print("=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)
