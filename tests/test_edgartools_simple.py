#!/usr/bin/env python3
"""
Simple edgartools exploration to understand the API structure.
"""

from edgar import Company, set_identity

# Set identity (required by SEC EDGAR)
set_identity("stephen.parton@sjpconsulting.com")

print("="*80)
print("Exploring EdgarTools API Structure")
print("="*80)

# Get company
company = Company("AAPL")
print(f"\n✓ Company: {company.name}")

# Get latest 10-K
latest_10k = company.get_filings(form="10-K").latest(1)
print(f"✓ Latest 10-K: {latest_10k.filing_date}")

# Get financials
print("\nExtracting financials...")
financials = latest_10k.obj()

# Explore the structure
print(f"\nFinancials object type: {type(financials)}")
print(f"Has 'financials' attribute: {hasattr(financials, 'financials')}")

if hasattr(financials, 'financials'):
    print(f"\nFinancials.financials type: {type(financials.financials)}")

    # Get balance sheet
    print("\n" + "="*80)
    print("BALANCE SHEET")
    print("="*80)
    bs = financials.financials.balance_sheet()
    print(f"Balance sheet type: {type(bs)}")
    print(f"Balance sheet attributes: {dir(bs)[:10]}...")  # Show first 10

    # Try different ways to access data
    if hasattr(bs, 'data'):
        print(f"\nbs.data type: {type(bs.data)}")
        if bs.data is not None:
            print(f"bs.data shape: {bs.data.shape}")
            print(f"bs.data columns: {list(bs.data.columns)[:5]}...")  # First 5 columns
            print(f"bs.data index (first 10 items): {list(bs.data.index)[:10]}")
            print("\nFirst few rows of balance sheet:")
            print(bs.data.head(10))

    if hasattr(bs, 'to_dataframe'):
        df = bs.to_dataframe()
        print(f"\nbs.to_dataframe() type: {type(df)}")
        if df is not None:
            print(f"DataFrame shape: {df.shape}")
            print(f"DataFrame columns: {list(df.columns)[:5]}...")

    # Try just printing the statement
    print("\n" + "="*80)
    print("Direct print of balance sheet:")
    print("="*80)
    print(bs)

print("\n" + "="*80)
print("Exploration Complete!")
print("="*80)
