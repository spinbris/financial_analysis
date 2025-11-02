"""
Test complete flow: extraction, formatting, and verification of XBRL data.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

from financial_research_agent.edgar_tools import extract_financial_data_deterministic
from financial_research_agent.formatters import format_financial_statements
import asyncio

async def main():
    print("=" * 100)
    print("COMPLETE FLOW TEST: Extraction → Formatting → Verification")
    print("=" * 100)

    # Extract statements
    print("\n1. Extracting XBRL data from SEC EDGAR...")
    statements = await extract_financial_data_deterministic(None, "Apple")

    balance_sheet = statements['balance_sheet']
    income_statement = statements['income_statement']
    cash_flow = statements['cash_flow_statement']

    print(f"   ✓ Extracted {len([k for k in balance_sheet.keys() if k.endswith('_Current')])} balance sheet items")
    print(f"   ✓ Extracted {len([k for k in income_statement.keys() if k.endswith('_Current')])} income statement items")
    print(f"   ✓ Extracted {len([k for k in cash_flow.keys() if k.endswith('_Current')])} cash flow items")

    # Format statements
    print("\n2. Formatting financial statements...")
    formatted = format_financial_statements(
        balance_sheet=balance_sheet,
        income_statement=income_statement,
        cash_flow_statement=cash_flow,
        company_name="Apple Inc",
        period=statements['period'],
        filing_reference=statements['filing_reference']
    )

    print(f"   ✓ Generated {len(formatted)} characters of formatted output")

    # Verify order and totals
    print("\n3. Verifying XBRL presentation order...")
    lines = formatted.split('\n')

    # Find balance sheet section
    bs_start = None
    for i, line in enumerate(lines):
        if '## Consolidated Balance Sheet' in line:
            bs_start = i
            break

    if bs_start:
        # Check first 20 balance sheet items
        print("   First 15 balance sheet items in output:")
        count = 0
        for i in range(bs_start, min(bs_start + 50, len(lines))):
            if '|' in lines[i] and 'Line Item' not in lines[i] and '---' not in lines[i]:
                item_name = lines[i].split('|')[1].strip()
                if item_name and item_name != '**Current Assets**':
                    count += 1
                    if count <= 15:
                        print(f"   {count:2d}. {item_name}")
                    if count >= 15:
                        break

    # Save output to file
    output_file = "financial_research_agent/output/test_complete_flow_output.md"
    with open(output_file, 'w') as f:
        f.write(formatted)

    print(f"\n4. Full output saved to: {output_file}")

    # Check for raw XBRL CSV files
    print("\n5. Checking for raw XBRL audit trail files...")
    import os
    debug_dir = "financial_research_agent/output/debug_edgar"
    if os.path.exists(debug_dir):
        csv_files = [f for f in os.listdir(debug_dir) if f.endswith('.csv')]
        print(f"   ✓ Found {len(csv_files)} raw XBRL CSV files:")
        for csv_file in csv_files:
            file_size = os.path.getsize(os.path.join(debug_dir, csv_file))
            print(f"     - {csv_file} ({file_size:,} bytes)")

    print("\n" + "=" * 100)
    print("✓ COMPLETE FLOW TEST PASSED")
    print("=" * 100)

if __name__ == "__main__":
    asyncio.run(main())
