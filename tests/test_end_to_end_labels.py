"""
Test end-to-end flow with human-readable labels.
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from financial_research_agent.edgar_tools import extract_financial_data_deterministic
from financial_research_agent.formatters import format_financial_statements


async def test_deterministic_extraction_to_format():
    """Test that deterministic extraction produces human-readable labels in final output."""

    print("="*80)
    print("TESTING: Deterministic Extraction → Formatter with Human-Readable Labels")
    print("="*80)

    # Extract data for Tesla (will use edgartools to get latest 10-Q)
    print("\n1. Extracting financial data from SEC EDGAR...")
    statements_data = await extract_financial_data_deterministic(None, "Tesla")

    # Check structure
    print("\n2. Checking data structure...")
    assert 'balance_sheet' in statements_data
    assert 'income_statement' in statements_data
    assert 'cash_flow_statement' in statements_data

    bs = statements_data['balance_sheet']
    print(f"   Balance sheet type: {type(bs)}")

    # Check if it has the new structure
    if isinstance(bs, dict) and 'line_items' in bs:
        print("   ✅ New structure detected: {'line_items': ..., 'xbrl_concepts': ...}")
        line_items = bs['line_items']
        xbrl_concepts = bs['xbrl_concepts']

        # Show a few examples
        sample_keys = list(line_items.keys())[:3]
        print(f"\n   Sample line item keys:")
        for key in sample_keys:
            print(f"      - {key}")
            # Find the base label (without _Current/_Prior)
            base_label = key.replace('_Current', '').replace('_Prior', '')
            if base_label in xbrl_concepts:
                print(f"        XBRL concept: {xbrl_concepts[base_label]}")

        # Check for spaces in labels
        has_spaces = any(' ' in k for k in line_items.keys())
        print(f"\n   Human-readable labels (with spaces): {'✅ YES' if has_spaces else '❌ NO'}")
    else:
        print("   Old structure (flat dict)")
        sample_keys = list(bs.keys())[:3]
        print(f"   Sample keys: {sample_keys}")

    # Format the statements
    print("\n3. Formatting financial statements...")
    formatted_output = format_financial_statements(
        balance_sheet=statements_data['balance_sheet'],
        income_statement=statements_data['income_statement'],
        cash_flow_statement=statements_data['cash_flow_statement'],
        company_name="Tesla",
        period=statements_data.get('period', 'Unknown'),
        filing_reference=statements_data.get('filing_reference', 'Unknown')
    )

    # Check formatted output
    print("\n4. Checking formatted output...")

    # Should have human-readable labels with spaces
    has_readable_cash = 'Cash and cash equivalents' in formatted_output or 'Cash and Cash Equivalents' in formatted_output
    has_readable_accounts = 'Accounts receivable' in formatted_output or 'Accounts Receivable' in formatted_output

    print(f"   Contains 'Cash and cash equivalents': {'✅' if has_readable_cash else '❌'}")
    print(f"   Contains 'Accounts receivable': {'✅' if has_readable_accounts else '❌'}")

    # Should NOT have smashed-together labels
    has_smashed_cash = 'CashandCashEquivalents' in formatted_output or 'Cashandcashequivalents' in formatted_output
    has_smashed_accounts = 'AccountsReceivable' in formatted_output or 'Accountsreceivable' in formatted_output

    print(f"   Contains smashed 'CashandCashEquivalents': {'❌ BAD' if has_smashed_cash else '✅ GOOD'}")
    print(f"   Contains smashed 'AccountsReceivable': {'❌ BAD' if has_smashed_accounts else '✅ GOOD'}")

    # Show sample of formatted output
    print("\n5. Sample of formatted output:")
    print("-"*80)
    lines = formatted_output.split('\n')
    # Find balance sheet section
    bs_start = next((i for i, line in enumerate(lines) if 'Balance Sheet' in line), 0)
    sample_lines = lines[bs_start:bs_start+20]
    print('\n'.join(sample_lines))
    print("-"*80)

    # Final verdict
    print("\n" + "="*80)
    if has_readable_cash and has_readable_accounts and not has_smashed_cash and not has_smashed_accounts:
        print("✅ SUCCESS: Human-readable labels are preserved in formatted output!")
    else:
        print("❌ FAILURE: Labels are not properly formatted")
        print(f"   Readable labels found: {has_readable_cash and has_readable_accounts}")
        print(f"   Smashed labels avoided: {not has_smashed_cash and not has_smashed_accounts}")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_deterministic_extraction_to_format())
