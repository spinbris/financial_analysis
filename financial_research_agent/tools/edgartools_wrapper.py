# EdgarTools Integration Wrapper
# Replaces ~400 lines of custom XBRL parsing with clean API

from edgar import Company, set_identity
import pandas as pd
from typing import Dict, Optional
import os

class EdgarToolsWrapper:
    """
    Simple wrapper around edgartools for your financial analysis pipeline.
    """
    
    def __init__(self, identity: Optional[str] = None):
        if identity is None:
            identity = os.getenv("EDGAR_IDENTITY", "User user@example.com")
        set_identity(identity)
    
    def get_financial_statements(self, ticker: str) -> Dict[str, pd.DataFrame]:
        """
        Get all financial statements as DataFrames.
        
        Args:
            ticker: Stock ticker (e.g., "AAPL")
            
        Returns:
            Dict with 'balance_sheet', 'income_statement', 'cashflow' as DataFrames
        """
        company = Company(ticker)
        financials = company.get_financials()  # No period argument
        
        return {
            'balance_sheet': financials.balance_sheet().to_dataframe(),
            'income_statement': financials.income_statement().to_dataframe(),
            'cashflow': financials.cashflow_statement().to_dataframe(),
            'metadata': {
                'ticker': ticker,
                'company_name': company.name,
                'cik': company.cik,
                'sic_code': getattr(company, 'sic_code', None),  # SIC code for sector detection
            }
        }
    
    def get_balance_sheet_data(self, ticker: str) -> Dict:
        """Extract key balance sheet items."""
        statements = self.get_financial_statements(ticker)
        bs_df = statements['balance_sheet']
        
        # Get date columns
        date_cols = [col for col in bs_df.columns if col not in 
                     ['concept', 'label', 'level', 'abstract', 'dimension', 'balance', 'weight', 'preferred_sign']]
        current_date = date_cols[0] if date_cols else None
        prior_date = date_cols[1] if len(date_cols) > 1 else None
        
        # Helper to find value by concept
        def get_value(concept_suffix: str, date_col: str) -> Optional[float]:
            """Find value by searching for concept that ends with suffix"""
            for idx, row in bs_df.iterrows():
                if row['concept'].endswith(concept_suffix):
                    return row[date_col]
            return None
        
        # Extract current period
        current = {}
        if current_date:
            current = {
                'total_assets': get_value('Assets', current_date),
                'current_assets': get_value('AssetsCurrent', current_date),
                'total_liabilities': get_value('Liabilities', current_date),
                'current_liabilities': get_value('LiabilitiesCurrent', current_date),
                'stockholders_equity': get_value('StockholdersEquity', current_date),
                'cash': get_value('CashAndCashEquivalentsAtCarryingValue', current_date),
                'ppe_net': get_value('PropertyPlantAndEquipmentNet', current_date),
            }
        
        # Extract prior period
        prior = {}
        if prior_date:
            prior = {
                'total_assets': get_value('Assets', prior_date),
                'current_assets': get_value('AssetsCurrent', prior_date),
                'total_liabilities': get_value('Liabilities', prior_date),
                'current_liabilities': get_value('LiabilitiesCurrent', prior_date),
                'stockholders_equity': get_value('StockholdersEquity', prior_date),
                'cash': get_value('CashAndCashEquivalentsAtCarryingValue', prior_date),
                'ppe_net': get_value('PropertyPlantAndEquipmentNet', prior_date),
            }
        
        return {
            'current_period': current,
            'prior_period': prior,
            'current_date': current_date,
            'prior_date': prior_date,
            'raw_dataframe': bs_df,
        }
    
    def get_income_statement_data(self, ticker: str) -> Dict:
        """Extract key income statement items."""
        statements = self.get_financial_statements(ticker)
        is_df = statements['income_statement']
        
        # Get date columns
        date_cols = [col for col in is_df.columns if col not in 
                     ['concept', 'label', 'level', 'abstract', 'dimension', 'balance', 'weight', 'preferred_sign']]
        current_date = date_cols[0] if date_cols else None
        prior_date = date_cols[1] if len(date_cols) > 1 else None
        
        def get_value(concept_suffix: str, date_col: str) -> Optional[float]:
            for idx, row in is_df.iterrows():
                if row['concept'].endswith(concept_suffix):
                    return row[date_col]
            return None
        
        current = {}
        if current_date:
            current = {
                'revenue': get_value('Revenues', current_date) or get_value('RevenueFromContractWithCustomerExcludingAssessedTax', current_date),
                'cost_of_revenue': get_value('CostOfRevenue', current_date),
                'gross_profit': get_value('GrossProfit', current_date),
                'operating_income': get_value('OperatingIncomeLoss', current_date),
                'net_income': get_value('NetIncomeLoss', current_date),
                'eps_basic': get_value('EarningsPerShareBasic', current_date),
                'eps_diluted': get_value('EarningsPerShareDiluted', current_date),
            }
        
        prior = {}
        if prior_date:
            prior = {
                'revenue': get_value('Revenues', prior_date) or get_value('RevenueFromContractWithCustomerExcludingAssessedTax', prior_date),
                'cost_of_revenue': get_value('CostOfRevenue', prior_date),
                'gross_profit': get_value('GrossProfit', prior_date),
                'operating_income': get_value('OperatingIncomeLoss', prior_date),
                'net_income': get_value('NetIncomeLoss', prior_date),
                'eps_basic': get_value('EarningsPerShareBasic', prior_date),
                'eps_diluted': get_value('EarningsPerShareDiluted', prior_date),
            }
        
        return {
            'current_period': current,
            'prior_period': prior,
            'current_date': current_date,
            'prior_date': prior_date,
            'raw_dataframe': is_df,
        }
    
    def get_cashflow_data(self, ticker: str) -> Dict:
        """Extract key cash flow items."""
        statements = self.get_financial_statements(ticker)
        cf_df = statements['cashflow']
        
        # Get date columns
        date_cols = [col for col in cf_df.columns if col not in 
                     ['concept', 'label', 'level', 'abstract', 'dimension', 'balance', 'weight', 'preferred_sign']]
        current_date = date_cols[0] if date_cols else None
        prior_date = date_cols[1] if len(date_cols) > 1 else None
        
        def get_value(concept_suffix: str, date_col: str) -> Optional[float]:
            for idx, row in cf_df.iterrows():
                if row['concept'].endswith(concept_suffix):
                    return row[date_col]
            return None
        
        current = {}
        if current_date:
            current = {
                'operating_cash_flow': get_value('NetCashProvidedByUsedInOperatingActivities', current_date),
                'investing_cash_flow': get_value('NetCashProvidedByUsedInInvestingActivities', current_date),
                'financing_cash_flow': get_value('NetCashProvidedByUsedInFinancingActivities', current_date),
                'capex': get_value('PaymentsToAcquirePropertyPlantAndEquipment', current_date),
            }
        
        prior = {}
        if prior_date:
            prior = {
                'operating_cash_flow': get_value('NetCashProvidedByUsedInOperatingActivities', prior_date),
                'investing_cash_flow': get_value('NetCashProvidedByUsedInInvestingActivities', prior_date),
                'financing_cash_flow': get_value('NetCashProvidedByUsedInFinancingActivities', prior_date),
                'capex': get_value('PaymentsToAcquirePropertyPlantAndEquipment', prior_date),
            }
        
        return {
            'current_period': current,
            'prior_period': prior,
            'current_date': current_date,
            'prior_date': prior_date,
            'raw_dataframe': cf_df,
        }
    
    def get_all_data(self, ticker: str) -> Dict:
        """
        Get all financial data in format compatible with your current pipeline.
        """
        # Get company metadata first
        from edgar import Company
        company = Company(ticker)

        return {
            'balance_sheet': self.get_balance_sheet_data(ticker),
            'income_statement': self.get_income_statement_data(ticker),
            'cashflow': self.get_cashflow_data(ticker),
            'ticker': ticker,
            'company_name': company.name,
            'sic_code': getattr(company, 'sic_code', None),
            'cik': company.cik,
        }
    
    def verify_balance_sheet_equation(self, ticker: str, tolerance: float = 0.001) -> Dict:
        """Verify Assets = Liabilities + Equity"""
        bs_data = self.get_balance_sheet_data(ticker)
        current = bs_data['current_period']
        
        assets = current.get('total_assets', 0) or 0
        liabilities = current.get('total_liabilities', 0) or 0
        equity = current.get('stockholders_equity', 0) or 0
        
        expected = liabilities + equity
        diff = abs(assets - expected)
        diff_pct = (diff / assets * 100) if assets > 0 else 0
        
        passed = diff_pct <= (tolerance * 100)
        
        return {
            'passed': passed,
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'expected_assets': expected,
            'difference': diff,
            'difference_pct': diff_pct,
        }


if __name__ == "__main__":
    edgar = EdgarToolsWrapper(identity="Steve Parton steve@sjpconsulting.com")
    data = edgar.get_all_data("AAPL")
    print("Balance Sheet:")
    print(f"  Total Assets: ${data['balance_sheet']['current_period'].get('total_assets', 0):,.0f}")
    verification = edgar.verify_balance_sheet_equation("AAPL")
    print(f"\nVerification: {'✓ PASSED' if verification['passed'] else '✗ FAILED'}")
