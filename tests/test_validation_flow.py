"""
Test the complete validation flow: flattening -> formatting -> validation.
"""

import sys
import os
from pathlib import Path
import tempfile
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from financial_research_agent.manager_enhanced import EnhancedFinancialResearchManager
from financial_research_agent.formatters import format_financial_statements

def test_complete_validation_flow():
    """Test the complete flow from nested data to validation."""

    print("=" * 70)
    print("COMPLETE VALIDATION FLOW TEST")
    print("=" * 70)
    print()

    # Step 1: Simulate nested data from MCP tool
    print("Step 1: Nested data from MCP tool")
    nested_balance_sheet = {
        "data": {
            "Assets": {"value": 133735000000.0, "raw_value": "133,735"},
            "AssetsCurrent": {"value": 64653000000.0, "raw_value": "64,653"},
            "Liabilities": {"value": 53019000000.0, "raw_value": "53,019"},
            "LiabilitiesCurrent": {"value": 31290000000.0, "raw_value": "31,290"},
            "StockholdersEquity": {"value": 80716000000.0, "raw_value": "80,716"}  # Corrected!
        },
        "source": "xbrl_concepts_dynamic"
    }
    print(f"   Nested structure with {len(nested_balance_sheet)} top-level keys")
    print()

    # Step 2: Flatten the data
    print("Step 2: Flatten the data")
    manager = EnhancedFinancialResearchManager()
    flat_balance_sheet = manager._flatten_statement_data(nested_balance_sheet)
    print(f"   Flattened to {len(flat_balance_sheet)} line items")
    print(f"   Assets: ${flat_balance_sheet['Assets']:,.0f}")
    print(f"   Liabilities: ${flat_balance_sheet['Liabilities']:,.0f}")
    print(f"   Equity: ${flat_balance_sheet['StockholdersEquity']:,.0f}")
    print()

    # Step 3: Format as markdown table
    print("Step 3: Format as markdown table")
    markdown = format_financial_statements(
        balance_sheet=flat_balance_sheet,
        income_statement={},
        cash_flow_statement={},
        company_name="Tesla",
        period="2025-09-30",
        filing_reference="10-Q filed 2025-10-23, Accession: 0001628280-25-045968"
    )

    # Extract just the balance sheet section for display
    bs_section = markdown.split("## Consolidated Statement")[0]
    print("   Generated markdown (first 500 chars):")
    print("   " + bs_section[:500].replace("\n", "\n   "))
    print()

    # Step 4: Save to temp file and run validation
    print("Step 4: Run validation on formatted output")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        statements_file = tmpdir_path / "03_financial_statements.md"
        statements_file.write_text(markdown, encoding='utf-8')

        # Temporarily set session_dir to temp directory
        original_session_dir = manager.session_dir
        manager.session_dir = tmpdir_path

        # Run validation
        errors = manager._validate_financial_statements()

        # Restore original session_dir
        manager.session_dir = original_session_dir

        if errors:
            print("   ❌ Validation FAILED")
            for error in errors:
                print(f"   {error}")
        else:
            print("   ✅ Validation PASSED - Balance sheet arithmetic is correct!")
        print()

    # Step 5: Verify the numbers manually
    print("Step 5: Manual verification")
    assets = flat_balance_sheet['Assets']
    liabilities = flat_balance_sheet['Liabilities']
    equity = flat_balance_sheet['StockholdersEquity']
    total = liabilities + equity
    diff = abs(assets - total)
    tolerance = assets * 0.001

    print(f"   Assets:              ${assets:>15,.0f}")
    print(f"   Liabilities + Equity: ${total:>15,.0f}")
    print(f"   Difference:          ${diff:>15,.0f}")
    print(f"   Tolerance (0.1%):    ${tolerance:>15,.0f}")

    if diff <= tolerance:
        print(f"   ✅ PASS: Difference within tolerance")
    else:
        print(f"   ❌ FAIL: Difference exceeds tolerance")
        print(f"   Error: {diff/assets*100:.2f}% of total assets")

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_complete_validation_flow()
