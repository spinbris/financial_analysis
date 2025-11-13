#!/usr/bin/env python3
"""
Comprehensive example of fetching and analyzing Apple's financial statements using edgartools.
This demonstrates the key features for extracting financial data from SEC EDGAR filings.
"""

from edgar import Company, set_identity

# Set identity (required by SEC EDGAR)
set_identity("stephen.parton@sjpconsulting.com")

print("="*80)
print("Apple Inc. (AAPL) Financial Analysis using EdgarTools")
print("="*80)

# 1. Get company information
print("\n1. Fetching Company Information...")
company = Company("AAPL")
print(f"   ✓ Company: {company.name}")
print(f"   ✓ CIK: {company.cik}")
print(f"   ✓ SIC: {company.sic}")
print(f"   ✓ Business Address: {company.business_address}")

# 2. Get recent filings
print("\n2. Recent 10-K and 10-Q Filings:")
latest_10k = company.get_filings(form="10-K").latest(1)
latest_10q = company.get_filings(form="10-Q").latest(1)
print(f"   Latest 10-K: {latest_10k.filing_date} - {latest_10k.accession_number}")
print(f"   Latest 10-Q: {latest_10q.filing_date} - {latest_10q.accession_number}")

# 3. Get financials from latest 10-K
print("\n3. Extracting Financial Statements from Latest 10-K...")
financials = latest_10k.obj()

# Check if XBRL data is available
if hasattr(financials, 'financials'):
    print("   ✓ XBRL financials available")

    # 4. Balance Sheet Analysis
    print("\n4. BALANCE SHEET (Most Recent Period):")
    print("-" * 80)
    bs = financials.financials.balance_sheet()

    # Get the dataframe from the Statement object
    if bs is not None:
        bs_df = bs.to_dataframe()

        if bs_df is not None and not bs_df.empty:
            # Find date columns (skip 'concept', 'label', 'level', etc.)
            date_cols = [col for col in bs_df.columns if col not in ['concept', 'label', 'level']]
            if date_cols:
                latest_col = date_cols[0]  # Most recent period
                print(f"   Period: {latest_col}\n")

                # Create a mapping from concept to value
                bs_df_indexed = bs_df.set_index('concept')

                # Key balance sheet items (using actual XBRL concept names)
                key_items = {
                    'us-gaap_Assets': 'Total Assets',
                    'us-gaap_AssetsCurrent': 'Total Current Assets',
                    'us-gaap_CashAndCashEquivalentsAtCarryingValue': 'Cash and Cash Equivalents',
                    'us-gaap_Liabilities': 'Total Liabilities',
                    'us-gaap_LiabilitiesCurrent': 'Total Current Liabilities',
                    'us-gaap_StockholdersEquity': 'Total Stockholders\' Equity'
                }

                for concept, label in key_items.items():
                    if concept in bs_df_indexed.index:
                        value = bs_df_indexed.loc[concept, latest_col]
                        if value is not None and str(value) != 'nan':
                            print(f"   {label:35s}: ${float(value):>20,.0f}")

    # 5. Income Statement Analysis
    print("\n5. INCOME STATEMENT (Most Recent Period):")
    print("-" * 80)
    income = financials.financials.income_statement()

    if income is not None:
        income_df = income.to_dataframe()

        if income_df is not None and not income_df.empty:
            date_cols = [col for col in income_df.columns if col not in ['concept', 'label', 'level']]
            if date_cols:
                latest_col = date_cols[0]
                print(f"   Period: {latest_col}\n")

                income_df_indexed = income_df.set_index('concept')

                key_items = {
                    'us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax': 'Total Revenues',
                    'us-gaap_CostOfGoodsAndServicesSold': 'Cost of Revenue',
                    'us-gaap_GrossProfit': 'Gross Profit',
                    'us-gaap_OperatingIncomeLoss': 'Operating Income',
                    'us-gaap_NetIncomeLoss': 'Net Income',
                    'us-gaap_EarningsPerShareBasic': 'EPS (Basic)',
                    'us-gaap_EarningsPerShareDiluted': 'EPS (Diluted)'
                }

                for concept, label in key_items.items():
                    if concept in income_df_indexed.index:
                        value = income_df_indexed.loc[concept, latest_col]
                        # Handle duplicate concepts by taking the first value if it's a Series
                        if hasattr(value, 'iloc'):
                            value = value.iloc[0] if len(value) > 0 else None
                        if value is not None and str(value) != 'nan':
                            # EPS values are small, others are in millions
                            if 'EarningsPerShare' in concept:
                                print(f"   {label:35s}: ${float(value):>20,.2f}")
                            else:
                                print(f"   {label:35s}: ${float(value):>20,.0f}")

    # 6. Cash Flow Statement Analysis
    print("\n6. CASH FLOW STATEMENT (Most Recent Period):")
    print("-" * 80)
    cf = financials.financials.cashflow_statement()

    if cf is not None:
        cf_df = cf.to_dataframe()

        if cf_df is not None and not cf_df.empty:
            date_cols = [col for col in cf_df.columns if col not in ['concept', 'label', 'level']]
            if date_cols:
                latest_col = date_cols[0]
                print(f"   Period: {latest_col}\n")

                cf_df_indexed = cf_df.set_index('concept')

                key_items = {
                    'us-gaap_NetCashProvidedByUsedInOperatingActivities': 'Operating Cash Flow',
                    'us-gaap_NetCashProvidedByUsedInInvestingActivities': 'Investing Cash Flow',
                    'us-gaap_NetCashProvidedByUsedInFinancingActivities': 'Financing Cash Flow',
                    'us-gaap_CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents': 'Cash & Equivalents (End of Period)'
                }

                for concept, label in key_items.items():
                    if concept in cf_df_indexed.index:
                        value = cf_df_indexed.loc[concept, latest_col]
                        # Handle duplicate concepts by taking the first value if it's a Series
                        if hasattr(value, 'iloc'):
                            value = value.iloc[0] if len(value) > 0 else None
                        if value is not None and str(value) != 'nan':
                            print(f"   {label:45s}: ${float(value):>20,.0f}")

    # 7. Calculate Key Financial Ratios
    print("\n7. KEY FINANCIAL RATIOS:")
    print("-" * 80)

    if bs is not None and income is not None:
        try:
            bs_df = bs.to_dataframe().set_index('concept')
            income_df = income.to_dataframe().set_index('concept')

            # Get date columns
            bs_date_cols = [col for col in bs_df.columns if col not in ['label', 'level']]
            income_date_cols = [col for col in income_df.columns if col not in ['label', 'level']]

            if bs_date_cols and income_date_cols:
                bs_col = bs_date_cols[0]
                income_col = income_date_cols[0]

                # Current Ratio
                if 'us-gaap_AssetsCurrent' in bs_df.index and 'us-gaap_LiabilitiesCurrent' in bs_df.index:
                    current_assets = float(bs_df.loc['us-gaap_AssetsCurrent', bs_col])
                    current_liabilities = float(bs_df.loc['us-gaap_LiabilitiesCurrent', bs_col])
                    current_ratio = current_assets / current_liabilities
                    print(f"   Current Ratio: {current_ratio:.2f}")

                # Profit Margin
                if 'us-gaap_NetIncomeLoss' in income_df.index:
                    net_income_val = income_df.loc['us-gaap_NetIncomeLoss', income_col]
                    net_income = float(net_income_val.iloc[0] if hasattr(net_income_val, 'iloc') else net_income_val)

                    # Revenue might be under different concept, try both
                    revenue_concept = None
                    if 'us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax' in income_df.index:
                        revenue_concept = 'us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax'
                    elif 'us-gaap_Revenues' in income_df.index:
                        revenue_concept = 'us-gaap_Revenues'

                    if revenue_concept:
                        revenue_val = income_df.loc[revenue_concept, income_col]
                        revenue = float(revenue_val.iloc[0] if hasattr(revenue_val, 'iloc') else revenue_val)
                        profit_margin = (net_income / revenue) * 100
                        print(f"   Net Profit Margin: {profit_margin:.2f}%")

                # ROE (Return on Equity)
                if 'us-gaap_StockholdersEquity' in bs_df.index and 'us-gaap_NetIncomeLoss' in income_df.index:
                    equity = float(bs_df.loc['us-gaap_StockholdersEquity', bs_col])
                    net_income_val = income_df.loc['us-gaap_NetIncomeLoss', income_col]
                    net_income = float(net_income_val.iloc[0] if hasattr(net_income_val, 'iloc') else net_income_val)
                    roe = (net_income / equity) * 100
                    print(f"   Return on Equity (ROE): {roe:.2f}%")

                # Debt to Equity
                if 'us-gaap_Liabilities' in bs_df.index and 'us-gaap_StockholdersEquity' in bs_df.index:
                    total_liabilities = float(bs_df.loc['us-gaap_Liabilities', bs_col])
                    equity = float(bs_df.loc['us-gaap_StockholdersEquity', bs_col])
                    debt_to_equity = total_liabilities / equity
                    print(f"   Debt to Equity Ratio: {debt_to_equity:.2f}")

        except (KeyError, ZeroDivisionError, AttributeError, ValueError) as e:
            print(f"   ⚠ Could not calculate some ratios: {e}")

else:
    print("   ⚠ XBRL financials not available in this format")
    print("   Try accessing raw XBRL data directly from the filing")

print("\n" + "="*80)
print("✅ Analysis Complete!")
print("="*80)