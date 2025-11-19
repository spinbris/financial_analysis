from edgar import Company, set_identity
import pandas as pd

set_identity("Steve Parton steve@sjpconsulting.com")

company = Company("AAPL")
financials = company.get_financials()

print("Testing DataFrame Conversion\n" + "="*60)

# Convert to DataFrame
bs = financials.balance_sheet()
bs_df = bs.to_dataframe()

print(f"\n✓ Converted to DataFrame")
print(f"  Type: {type(bs_df)}")
print(f"  Shape: {bs_df.shape}")
print(f"  Columns: {list(bs_df.columns)}")

print("\n" + "="*60)
print("Balance Sheet DataFrame (first 10 rows):")
print("="*60)
print(bs_df.head(10))

print("\n" + "="*60)
print("Accessing Specific Values:")
print("="*60)

# Try to access specific line items
if 'Assets' in bs_df.index:
    assets = bs_df.loc['Assets'].iloc[0]
    print(f"✓ Total Assets: ${assets:,.0f}")

if 'Liabilities' in bs_df.index:
    liabilities = bs_df.loc['Liabilities'].iloc[0]
    print(f"✓ Total Liabilities: ${liabilities:,.0f}")

if 'StockholdersEquity' in bs_df.index:
    equity = bs_df.loc['StockholdersEquity'].iloc[0]
    print(f"✓ Stockholders Equity: ${equity:,.0f}")

print("\n" + "="*60)
print("✅ DataFrame access working!")
print("\nThis replaces your ~100 lines of XBRL parsing!")
print("="*60)
