"""
Test that financial statement line items preserve XBRL presentation order.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

from financial_research_agent.edgar_tools import extract_financial_data_deterministic
from financial_research_agent.formatters import format_financial_statements
import asyncio

async def main():
    print("Testing XBRL presentation order preservation...")
    print("=" * 80)

    # Extract statements using edgartools
    statements = await extract_financial_data_deterministic(None, "Apple")

    balance_sheet = statements['balance_sheet']

    print(f"\nBalance Sheet items (first 15):")
    print("-" * 80)

    count = 0
    for key in balance_sheet.keys():
        if count >= 15:
            break
        # Only show _Current items to avoid duplication
        if key.endswith("_Current"):
            base_name = key.replace("_Current", "")
            print(f"{count+1:3d}. {base_name}")
            count += 1

    print("\n" + "=" * 80)
    print("Expected order (from edgartools DataFrame):")
    print("-" * 80)
    print("  1. CashAndCashEquivalents")
    print("  2. CurrentMarketableSecurities")
    print("  3. AccountsReceivable")
    print("  4. Vendor non-trade receivables")
    print("  5. Inventory")
    print("  6. OtherCurrentAssets")
    print("  7. TotalCurrentAssets")
    print("  8. NonCurrentMarketableSecurities")
    print("  9. PropertyPlantAndEquipment")
    print(" 10. OtherNonCurrentAssets")
    print(" 11. TotalNonCurrentAssets")
    print(" 12. TotalAssets")
    print(" 13. AccountsPayable")
    print(" 14. OtherCurrentLiabilities")
    print(" 15. CommercialPaper")

    print("\n" + "=" * 80)
    print("\nFormatted output (first 20 lines):")
    print("-" * 80)

    formatted = format_financial_statements(
        balance_sheet=balance_sheet,
        income_statement=statements['income_statement'],
        cash_flow_statement=statements['cash_flow_statement'],
        company_name="Apple Inc",
        period=statements['period'],
        filing_reference=statements['filing_reference']
    )

    # Print first 40 lines of formatted output
    lines = formatted.split('\n')
    for i, line in enumerate(lines[:40]):
        print(line)

    print("\n" + "=" * 80)
    print("✓ Test complete - verify order matches XBRL presentation above")

if __name__ == "__main__":
    asyncio.run(main())
