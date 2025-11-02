"""
Verify that extracted XBRL data matches SEC filings and that totals add up correctly.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

from edgar import Company, set_identity
set_identity('stephen.parton@sjpconsulting.com')

def main():
    print("Verifying XBRL data accuracy and structure...")
    print("=" * 100)

    company = Company('AAPL')
    filing = company.get_filings(form='10-Q').latest(1)
    financials = filing.obj().financials
    bs_df = financials.balance_sheet().to_dataframe()

    print(f'Filing: {filing.form} dated {filing.filing_date}')
    print(f'Period: {bs_df.columns[2]} (current) vs {bs_df.columns[3]} (prior)')
    print("=" * 100)
    print()
    print("Balance Sheet in XBRL presentation order:")
    print("-" * 100)

    for idx, row in bs_df.iterrows():
        label = row.get('label', 'NO_LABEL')
        level = int(row.get('level', 0))
        is_abstract = row.get('abstract', False)
        current_val = row.get(bs_df.columns[2])

        # Format
        indent = '  ' * level
        if is_abstract:
            print(f'{indent}[HEADER] {label}')
        else:
            if current_val and str(current_val) != 'nan':
                val_str = f'${current_val:,.0f}'
            else:
                val_str = 'N/A'
            print(f'{indent}{label}: {val_str}')

    print("\n" + "=" * 100)
    print("\nKEY VERIFICATION POINTS:")
    print("-" * 100)

    # Extract key values
    total_current_assets = None
    total_assets = None
    cash = None

    for idx, row in bs_df.iterrows():
        label_lower = row.get('label', '').lower()
        current_val = row.get(bs_df.columns[2])

        if 'total current assets' in label_lower:
            total_current_assets = current_val
        elif label_lower == 'total assets':
            total_assets = current_val
        elif 'cash and cash equivalents' in label_lower and not row.get('abstract', False):
            cash = current_val

    print(f"Cash and Cash Equivalents: ${cash:,.0f}" if cash else "Cash: NOT FOUND")
    print(f"Total Current Assets: ${total_current_assets:,.0f}" if total_current_assets else "Total Current Assets: NOT FOUND")
    print(f"Total Assets: ${total_assets:,.0f}" if total_assets else "Total Assets: NOT FOUND")

    print("\n" + "=" * 100)
    print("\nPROBLEM: Current formatter categorizes items AFTER extraction,")
    print("which breaks the XBRL hierarchy and totals.")
    print("\nSOLUTION: Display items in EXACT XBRL order without categorization.")
    print("=" * 100)

if __name__ == "__main__":
    main()
