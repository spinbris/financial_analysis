from edgar.ai.helpers import (
    get_revenue_trend,
    get_filing_statement,
    compare_companies_revenue,
)

# Test 1: Revenue trend
print("=== get_revenue_trend('AAPL', periods=3) ===")
income = get_revenue_trend("AAPL", periods=3)
print(type(income))
print(income)

# Test 2: Compare companies
print("\n=== compare_companies_revenue(['AAPL', 'MSFT'], periods=2) ===")
comparison = compare_companies_revenue(["AAPL", "MSFT"], periods=2)
for ticker, data in comparison.items():
    print(f"\n{ticker}:")
    print(data)

# Test 3: to_context for LLM
print("\n=== Company.to_context() ===")
from edgar import Company
company = Company("AAPL")
context = company.to_context(detail='standard')
print(context[:1000])

# Test 4: Statement find_item
print("\n=== stmt.find_item() ===")
stmt = company.income_statement(periods=2)
revenue = stmt.find_item('Revenue')
print(f"Revenue item: {revenue}")
if revenue:
    print(f"Values: {revenue.values}")
