from edgar import Company, set_identity

# Set identity (required by SEC)
set_identity("Steve Parton steve@sjpconsulting.com")

print("Testing EdgarTools API\n" + "="*60)

# Get company
print("\n1. Loading company...")
company = Company("AAPL")
print(f"   ✓ Company: {company.name}")
print(f"   ✓ CIK: {company.cik}")

# Get financials
print("\n2. Fetching financials from SEC EDGAR...")
financials = company.get_financials()
print(f"   ✓ Financials loaded")

# Get balance sheet - it's a Statement object
print("\n3. Balance Sheet Statement:")
bs = financials.balance_sheet()
print(f"   Type: {type(bs)}")

# Convert to DataFrame to see the data
print("\n4. Converting to DataFrame...")
try:
    # Try to convert to DataFrame
    bs_df = bs.to_dataframe() if hasattr(bs, 'to_dataframe') else bs
    print(bs_df.head(10))
except Exception as e:
    # Or just print the Statement object
    print(f"   Statement object: {bs}")
    print(f"\n   Let's see what methods are available:")
    print(f"   Methods: {[m for m in dir(bs) if not m.startswith('_')][:10]}")

print("\n" + "="*60)
print("✅ API test complete!")
print("\nNext: We need to understand the Statement API")
print("="*60)
