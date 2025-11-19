from edgar import Company, set_identity

# Required by SEC regulations
set_identity("Steve Parton steve@sjpconsulting.com")

print("Testing EdgarTools Simplified API\n" + "="*60)

# Get Apple - this replaces your 100+ lines!
print("\n1. Fetching company...")
company = Company("AAPL")
print(f"   ✓ Company: {company.name}")
print(f"   ✓ CIK: {company.cik}")

# Get financials
print("\n2. Loading financials...")
financials = company.get_financials()
print(f"   ✓ Financials loaded")

# Balance sheet
print("\n3. Balance Sheet (most recent):")
bs = financials.balance_sheet()
print(f"   • Total Assets: ${bs['Assets'].iloc[0]:,.0f}")
print(f"   • Total Liabilities: ${bs['Liabilities'].iloc[0]:,.0f}")
print(f"   • Stockholders Equity: ${bs['StockholdersEquity'].iloc[0]:,.0f}")

# Income statement
print("\n4. Income Statement (most recent):")
is_data = financials.income_statement()
print(f"   • Revenue: ${is_data['Revenues'].iloc[0]:,.0f}")
print(f"   • Net Income: ${is_data['NetIncomeLoss'].iloc[0]:,.0f}")

# Cash flow
print("\n5. Cash Flow (most recent):")
cf = financials.cash_flow_statement()
print(f"   • Operating Cash Flow: ${cf['NetCashProvidedByUsedInOperatingActivities'].iloc[0]:,.0f}")

print("\n" + "="*60)
print("✅ EdgarTools API working perfectly!")
print("\nCompare this ~20 line script to your current:")
print("  • edgar_tools.py (~100+ lines)")
print("  • financial_statements.py (~200+ lines)")
print("\nYou could replace 300+ lines with <50!")
print("="*60)
