#!/usr/bin/env python3
"""Test edgartools library directly to see how many line items we can extract."""

import os
os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 stephen.parton@sjpconsulting.com"

from edgar import Company, set_identity

# Set identity (required by SEC)
set_identity("stephen.parton@sjpconsulting.com")

# Get Apple
print("Fetching Apple financials...")
company = Company("AAPL")

# Get latest 10-Q filing
filing = company.get_filings(form="10-Q").latest(1)

print(f"Filing type: {type(filing)}")
print(f"Filing: {filing.form} from {filing.filing_date}")

# Get financials object
financials = filing.obj().financials

print(f"\nFinancials type: {type(financials)}")

# Get balance sheet
print("\n=== BALANCE SHEET ===")
bs = financials.balance_sheet
print(f"Balance sheet type: {type(bs)}")

# Try different attributes
for attr in ['data', 'df', 'to_dataframe', 'items', 'values']:
    if hasattr(bs, attr):
        val = getattr(bs, attr)
        if callable(val):
            try:
                result = val()
                print(f"{attr}(): {type(result)}, len={len(result) if hasattr(result, '__len__') else 'N/A'}")
            except:
                pass
        else:
            print(f"{attr}: {type(val)}, len={len(val) if hasattr(val, '__len__') else 'N/A'}")

# Show first few items
print(f"\nFirst items from balance sheet:")
print(bs)

