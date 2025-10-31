#!/usr/bin/env python3
import os
os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 stephen.parton@sjpconsulting.com"

from edgar import Company, set_identity

set_identity("stephen.parton@sjpconsulting.com")

company = Company("AAPL")
filing = company.get_filings(form="10-Q").latest(1)

print(f"Filing: {filing.form} from {filing.filing_date}\n")

# Get XBRL object
xbrl = filing.obj()

# Get balance sheet as DataFrame
print("=== BALANCE SHEET ===")
bs = xbrl.statements.balance_sheet()
bs_df = bs.to_dataframe()
print(f"Balance Sheet rows: {len(bs_df)}")
print(f"Balance Sheet columns: {list(bs_df.columns)}")
print(f"\nFirst 15 rows:")
print(bs_df.head(15))

# Get income statement
print("\n\n=== INCOME STATEMENT ===")
income = xbrl.statements.income_statement()
income_df = income.to_dataframe()
print(f"Income Statement rows: {len(income_df)}")
print(f"\nFirst 10 rows:")
print(income_df.head(10))

# Get cash flow
print("\n\n=== CASH FLOW ===")
cf = xbrl.statements.cash_flow_statement()
cf_df = cf.to_dataframe()
print(f"Cash Flow rows: {len(cf_df)}")
print(f"\nFirst 10 rows:")
print(cf_df.head(10))

print(f"\n\nTOTAL LINE ITEMS: {len(bs_df) + len(income_df) + len(cf_df)}")

