"""
Test that XBRL labels are preserved with human-readable formatting.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from financial_research_agent.formatters import format_financial_statements


def test_format_with_readable_labels():
    """Test that human-readable labels are preserved in formatted output."""

    # Simulate the new structure from edgar_tools.py
    balance_sheet = {
        'line_items': {
            'Cash and cash equivalents_Current': 18289000000,
            'Cash and cash equivalents_Prior': 16139000000,
            'Accounts receivable_Current': 4703000000,
            'Accounts receivable_Prior': 4418000000,
            'Total assets_Current': 133735000000,
            'Total assets_Prior': 122070000000,
        },
        'xbrl_concepts': {
            'Cash and cash equivalents': 'us-gaap_CashAndCashEquivalentsAtCarryingValue',
            'Accounts receivable': 'us-gaap_AccountsReceivableNetCurrent',
            'Total assets': 'us-gaap_Assets',
        }
    }

    income_statement = {
        'line_items': {
            'Revenue_Current': 24680000000,
            'Revenue_Prior': 23350000000,
        },
        'xbrl_concepts': {
            'Revenue': 'us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax',
        }
    }

    cash_flow = {
        'line_items': {
            'Net cash from operating activities_Current': 10934000000,
            'Net cash from operating activities_Prior': 10109000000,
        },
        'xbrl_concepts': {
            'Net cash from operating activities': 'us-gaap_NetCashProvidedByUsedInOperatingActivities',
        }
    }

    result = format_financial_statements(
        balance_sheet=balance_sheet,
        income_statement=income_statement,
        cash_flow_statement=cash_flow,
        company_name="Tesla",
        period="Q3 2025",
        filing_reference="10-Q filed 2025-10-23"
    )

    # Check that human-readable labels appear in output
    assert 'Cash and cash equivalents' in result, "Should preserve spaces in labels"
    assert 'Accounts receivable' in result, "Should preserve lowercase and spaces"
    assert 'Net cash from operating activities' in result, "Should preserve full readable names"

    # Check that we don't see the old smashed-together format
    assert 'Cashandcashequivalents' not in result, "Should not smash words together"
    assert 'Accountsreceivable' not in result, "Should not remove spaces"

    # Check formatting
    assert '$18,289,000,000' in result, "Should format currency correctly"
    assert '| Current | Prior |' in result or '| Cash and cash equivalents | $18,289,000,000 | $16,139,000,000 |' in result, "Should have comparative columns"

    print("✅ Test passed: Human-readable labels are preserved")
    print("\nSample output:\n")
    print(result[:1000])


def test_backward_compatibility():
    """Test that old flat dictionary format still works."""

    # Old format - flat dict with cleaned-up keys
    balance_sheet = {
        'CashandCashEquivalents_Current': 18289000000,
        'AccountsReceivable_Current': 4703000000,
    }

    income_statement = {
        'Revenue_Current': 24680000000,
    }

    cash_flow = {
        'NetCashfromOperatingActivities_Current': 10934000000,
    }

    result = format_financial_statements(
        balance_sheet=balance_sheet,
        income_statement=income_statement,
        cash_flow_statement=cash_flow,
        company_name="Tesla",
        period="Q3 2025",
        filing_reference="10-Q filed 2025-10-23"
    )

    # Should still work with old format
    assert 'CashandCashEquivalents' in result or 'Cash and Cash Equivalents' in result
    assert 'Revenue' in result
    assert '$' in result

    print("✅ Test passed: Backward compatibility maintained")


if __name__ == "__main__":
    test_format_with_readable_labels()
    print("\n" + "="*80 + "\n")
    test_backward_compatibility()
