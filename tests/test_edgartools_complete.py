#!/usr/bin/env python3
import os
os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 stephen.parton@sjpconsulting.com"

from edgar import Company, set_identity

set_identity("stephen.parton@sjpconsulting.com")

company = Company("AAPL")
filing = company.get_filings(form="10-Q").latest(1)

print(f"Filing: {filing.form} from {filing.filing_date}\n")

# Get financials object
financials = filing.obj().financials

# Get balance sheet
print("=== BALANCE SHEET ===")
bs = financials.balance_sheet()
bs_df = bs.to_dataframe()
print(f"Balance Sheet rows: {len(bs_df)}")
print(f"Columns: {list(bs_df.columns)}")
print(f"\nFirst 15 line items:")
print(bs_df.head(15).to_string())

# Get income statement  
print("\n\n=== INCOME STATEMENT ===")
income = financials.income_statement()
income_df = income.to_dataframe()
print(f"Income Statement rows: {len(income_df)}")
print(f"\nFirst 10 line items:")
print(income_df.head(10).to_string())

# Get cash flow
print("\n\n=== CASH FLOW ===")
cf = financials.cash_flow_statement()
cf_df = cf.to_dataframe()
print(f"Cash Flow rows: {len(cf_df)}")
print(f"\nFirst 10 line items:")
print(cf_df.head(10).to_string())

print(f"\n\n✓ TOTAL LINE ITEMS: {len(bs_df) + len(income_df) + len(cf_df)}")

