from edgar import Company, set_identity

# Set identity (required by SEC)
set_identity("Steve Parton steve@sjpconsulting.com")

print("Fetching Apple financials...\n")

# Get company
company = Company("AAPL")
print(f"Company loaded: {company}")

# Get financials - THIS IS THE KEY TEST
print("\nFetching financial statements...")
financials = company.get_financials()

# Get balance sheet
print("\nBalance Sheet:")
bs = financials.balance_sheet()
print(bs.head())  # Show first 5 rows

print("\n" + "="*60)
print("✅ EdgarTools is working!")
print("="*60)
