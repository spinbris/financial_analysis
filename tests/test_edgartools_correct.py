from edgar import Company, set_identity

set_identity("Steve Parton steve@sjpconsulting.com")

print("Fetching Apple financials...\n")

company = Company("AAPL")
financials = company.get_financials()

print("Balance Sheet:")
print("="*60)
bs = financials.balance_sheet()
print(bs)

print("\n" + "="*60)
print("\nIncome Statement:")
print("="*60)
income = financials.income_statement()
print(income)

print("\n" + "="*60)
print("\nCash Flow:")
print("="*60)
cf = financials.cashflow_statement()  # Fixed: cashflow not cash_flow
print(cf)

print("\n" + "="*60)
print("✅ EdgarTools is working!")
print("="*60)
