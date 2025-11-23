# EdgarTools Integration Wrapper
# Uses Entity Facts API for reliable, pre-aggregated financial data

from edgar import Company, set_identity
import pandas as pd
from typing import Dict, Optional, Any
import os

class EdgarToolsWrapper:
    """
    Wrapper around edgartools using Entity Facts API.

    Uses company.income_statement(), company.balance_sheet(), etc.
    which automatically handle:
    - Segmented company presentations (Disney, JP Morgan, etc.)
    - Consolidated totals pre-aggregated by SEC
    - Multi-period comparison

    This is faster and more reliable than parsing XBRL DataFrames.
    """

    def __init__(self, identity: Optional[str] = None):
        if identity is None:
            identity = os.getenv("SEC_EDGAR_USER_AGENT", "FinancialResearchAgent/1.0 (user@example.com)")
        set_identity(identity)

    def _extract_statement_data(self, statement_obj: Any, period_index: int = 0) -> Dict[str, float]:
        """
        Extract key line items from a Statement object.

        Args:
            statement_obj: Statement object from edgartools (income_statement(), balance_sheet(), etc.)
            period_index: Which period to extract (0=most recent, 1=prior, etc.)

        Returns:
            Dict mapping standardized keys to values
        """
        # Convert statement to DataFrame for easier extraction
        # Use include_dimensions=False to get clean P&L without segment data mixed in
        df = statement_obj.to_dataframe(include_dimensions=False)

        # Entity Facts API DataFrame structure:
        # - Index: concept (e.g., 'Assets', 'Revenues')
        # - Columns: 'label', 'depth', 'is_abstract', 'is_total', 'section', 'confidence', 'FY 2025', 'FY 2024', etc.

        # Get date columns (exclude metadata columns)
        metadata_cols = ['label', 'depth', 'is_abstract', 'is_total', 'section', 'confidence']
        date_cols = [col for col in df.columns if col not in metadata_cols]

        if not date_cols or period_index >= len(date_cols):
            return {}

        date_col = date_cols[period_index]

        # Extract data by searching for standardized labels
        def get_value_by_label(label_keywords: list, prefer_total: bool = True) -> Optional[float]:
            """
            Find value by searching for label containing keywords (case-insensitive).

            Args:
                label_keywords: List of keywords to search for in label
                prefer_total: If True, prioritize items with is_total=True
            """
            # First pass: try to find item with is_total=True
            if prefer_total:
                for concept, row in df.iterrows():
                    if row.get('is_abstract', False):
                        continue
                    if not row.get('is_total', False):
                        continue
                    label = str(row.get('label', '')).lower()
                    if any(keyword.lower() in label for keyword in label_keywords):
                        value = row.get(date_col)
                        if pd.notna(value):
                            return float(value)

            # Second pass: any non-abstract item matching label
            for concept, row in df.iterrows():
                if row.get('is_abstract', False):
                    continue
                label = str(row.get('label', '')).lower()
                if any(keyword.lower() in label for keyword in label_keywords):
                    value = row.get(date_col)
                    if pd.notna(value):
                        return float(value)
            return None

        # Also try by concept suffix for fallback
        def get_value_by_concept(concept_suffixes: list, prefer_total: bool = True) -> Optional[float]:
            """
            Find value by concept (index) that ends with suffix.

            Args:
                concept_suffixes: List of concept suffixes to match
                prefer_total: If True, prioritize items with is_total=True
            """
            # First pass: try to find item with is_total=True
            if prefer_total:
                for suffix in concept_suffixes:
                    for concept, row in df.iterrows():
                        if row.get('is_abstract', False):
                            continue
                        if not row.get('is_total', False):
                            continue
                        concept_str = str(concept)
                        if concept_str.endswith(suffix):
                            value = row.get(date_col)
                            if pd.notna(value):
                                return float(value)

            # Second pass: any non-abstract item matching concept
            for suffix in concept_suffixes:
                for concept, row in df.iterrows():
                    if row.get('is_abstract', False):
                        continue
                    concept_str = str(concept)
                    if concept_str.endswith(suffix):
                        value = row.get(date_col)
                        if pd.notna(value):
                            return float(value)
            return None

        return {
            'date_col': date_col,
            'get_value_by_label': get_value_by_label,
            'get_value_by_concept': get_value_by_concept,
            'df': df
        }

    def get_balance_sheet_data(self, ticker: str) -> Dict:
        """
        Extract key balance sheet items using Entity Facts API.

        Automatically handles segmented presentations.
        """
        company = Company(ticker)

        # Get balance sheet - periods=2 for current + prior
        balance_sheet = company.balance_sheet(periods=2)

        # Extract current period (index 0)
        current_helper = self._extract_statement_data(balance_sheet, period_index=0)
        current = {}
        if current_helper:
            # For critical balance sheet items, try exact concept match first
            df = current_helper['df']
            date_col = current_helper['date_col']

            def get_exact_concept(concept_name: str) -> Optional[float]:
                """Get value for exact concept name."""
                if concept_name in df.index:
                    row = df.loc[concept_name]
                    # If multiple rows, get first one with is_total=True
                    if isinstance(row, pd.DataFrame):
                        total_rows = row[row.get('is_total', False) == True]
                        if not total_rows.empty:
                            value = total_rows.iloc[0][date_col]
                        else:
                            value = row.iloc[0][date_col]
                    else:
                        value = row[date_col]
                    if pd.notna(value):
                        return float(value)
                return None

            # Extract values
            total_assets = get_exact_concept('Assets') or current_helper['get_value_by_concept'](['Assets'])
            total_liabilities = get_exact_concept('Liabilities') or current_helper['get_value_by_concept'](['Liabilities'])
            stockholders_equity = get_exact_concept('StockholdersEquity') or current_helper['get_value_by_concept'](['StockholdersEquity'])

            # Fallback: If Liabilities is missing/NaN, calculate from Assets - Equity
            if not total_liabilities and total_assets and stockholders_equity:
                total_liabilities = total_assets - stockholders_equity

            current = {
                'total_assets': total_assets,
                'current_assets': (
                    get_exact_concept('AssetsCurrent') or
                    current_helper['get_value_by_concept'](['AssetsCurrent'])
                ),
                'total_liabilities': total_liabilities,
                'current_liabilities': (
                    get_exact_concept('LiabilitiesCurrent') or
                    current_helper['get_value_by_concept'](['LiabilitiesCurrent'])
                ),
                'stockholders_equity': stockholders_equity,
                'cash': (
                    get_exact_concept('CashAndCashEquivalentsAtCarryingValue') or
                    current_helper['get_value_by_concept'](['CashAndCashEquivalentsAtCarryingValue', 'Cash'])
                ),
                'ppe_net': (
                    get_exact_concept('PropertyPlantAndEquipmentNet') or
                    current_helper['get_value_by_concept'](['PropertyPlantAndEquipmentNet'])
                ),
            }
            current_date = current_helper['date_col']
        else:
            current_date = None

        # Extract prior period (index 1)
        prior_helper = self._extract_statement_data(balance_sheet, period_index=1)
        prior = {}
        if prior_helper:
            df_prior = prior_helper['df']
            date_col_prior = prior_helper['date_col']

            def get_exact_concept_prior(concept_name: str) -> Optional[float]:
                """Get value for exact concept name from prior period."""
                if concept_name in df_prior.index:
                    row = df_prior.loc[concept_name]
                    if isinstance(row, pd.DataFrame):
                        total_rows = row[row.get('is_total', False) == True]
                        if not total_rows.empty:
                            value = total_rows.iloc[0][date_col_prior]
                        else:
                            value = row.iloc[0][date_col_prior]
                    else:
                        value = row[date_col_prior]
                    if pd.notna(value):
                        return float(value)
                return None

            # Extract values
            total_assets_prior = get_exact_concept_prior('Assets') or prior_helper['get_value_by_concept'](['Assets'])
            total_liabilities_prior = get_exact_concept_prior('Liabilities') or prior_helper['get_value_by_concept'](['Liabilities'])
            stockholders_equity_prior = get_exact_concept_prior('StockholdersEquity') or prior_helper['get_value_by_concept'](['StockholdersEquity'])

            # Fallback: If Liabilities is missing/NaN, calculate from Assets - Equity
            if not total_liabilities_prior and total_assets_prior and stockholders_equity_prior:
                total_liabilities_prior = total_assets_prior - stockholders_equity_prior

            prior = {
                'total_assets': total_assets_prior,
                'current_assets': (
                    get_exact_concept_prior('AssetsCurrent') or
                    prior_helper['get_value_by_concept'](['AssetsCurrent'])
                ),
                'total_liabilities': total_liabilities_prior,
                'current_liabilities': (
                    get_exact_concept_prior('LiabilitiesCurrent') or
                    prior_helper['get_value_by_concept'](['LiabilitiesCurrent'])
                ),
                'stockholders_equity': stockholders_equity_prior,
                'cash': (
                    get_exact_concept_prior('CashAndCashEquivalentsAtCarryingValue') or
                    prior_helper['get_value_by_concept'](['CashAndCashEquivalentsAtCarryingValue'])
                ),
                'ppe_net': (
                    get_exact_concept_prior('PropertyPlantAndEquipmentNet') or
                    prior_helper['get_value_by_concept'](['PropertyPlantAndEquipmentNet'])
                ),
            }
            prior_date = prior_helper['date_col']
        else:
            prior_date = None

        return {
            'current_period': current,
            'prior_period': prior,
            'current_date': current_date,
            'prior_date': prior_date,
            'raw_dataframe': balance_sheet.to_dataframe() if balance_sheet else None,
        }

    def get_income_statement_data(self, ticker: str) -> Dict:
        """
        Extract key income statement items using Entity Facts API.

        Automatically handles segmented presentations (e.g., Disney's segment revenue).
        """
        company = Company(ticker)

        # Get income statement - periods=2 for current + prior
        income_statement = company.income_statement(periods=2)

        # Extract current period
        current_helper = self._extract_statement_data(income_statement, period_index=0)
        current = {}
        if current_helper:
            current = {
                'revenue': (
                    current_helper['get_value_by_label'](['Total Revenue', 'Revenue', 'Net Sales']) or
                    current_helper['get_value_by_concept'](['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax'])
                ),
                'cost_of_revenue': (
                    current_helper['get_value_by_label'](['Cost of Revenue', 'Cost of Sales', 'Cost of Goods']) or
                    current_helper['get_value_by_concept'](['CostOfRevenue', 'CostOfGoodsAndServicesSold'])
                ),
                'gross_profit': (
                    current_helper['get_value_by_label'](['Gross Profit']) or
                    current_helper['get_value_by_concept'](['GrossProfit'])
                ),
                'operating_income': (
                    current_helper['get_value_by_label'](['Operating Income', 'Income from Operations']) or
                    current_helper['get_value_by_concept'](['OperatingIncomeLoss'])
                ),
                'net_income': (
                    current_helper['get_value_by_label'](['Net Income', 'Net Income Attributable to Parent']) or
                    current_helper['get_value_by_concept'](['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic'])
                ),
                'eps_basic': (
                    current_helper['get_value_by_label'](['Earnings Per Share, Basic', 'EPS Basic']) or
                    current_helper['get_value_by_concept'](['EarningsPerShareBasic'])
                ),
                'eps_diluted': (
                    current_helper['get_value_by_label'](['Earnings Per Share, Diluted', 'EPS Diluted']) or
                    current_helper['get_value_by_concept'](['EarningsPerShareDiluted'])
                ),
            }
            current_date = current_helper['date_col']
        else:
            current_date = None

        # Extract prior period
        prior_helper = self._extract_statement_data(income_statement, period_index=1)
        prior = {}
        if prior_helper:
            prior = {
                'revenue': (
                    prior_helper['get_value_by_label'](['Total Revenue', 'Revenue', 'Net Sales']) or
                    prior_helper['get_value_by_concept'](['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax'])
                ),
                'cost_of_revenue': (
                    prior_helper['get_value_by_label'](['Cost of Revenue', 'Cost of Sales']) or
                    prior_helper['get_value_by_concept'](['CostOfRevenue'])
                ),
                'gross_profit': (
                    prior_helper['get_value_by_label'](['Gross Profit']) or
                    prior_helper['get_value_by_concept'](['GrossProfit'])
                ),
                'operating_income': (
                    prior_helper['get_value_by_label'](['Operating Income']) or
                    prior_helper['get_value_by_concept'](['OperatingIncomeLoss'])
                ),
                'net_income': (
                    prior_helper['get_value_by_label'](['Net Income']) or
                    prior_helper['get_value_by_concept'](['NetIncomeLoss'])
                ),
                'eps_basic': (
                    prior_helper['get_value_by_label'](['Earnings Per Share, Basic']) or
                    prior_helper['get_value_by_concept'](['EarningsPerShareBasic'])
                ),
                'eps_diluted': (
                    prior_helper['get_value_by_label'](['Earnings Per Share, Diluted']) or
                    prior_helper['get_value_by_concept'](['EarningsPerShareDiluted'])
                ),
            }
            prior_date = prior_helper['date_col']
        else:
            prior_date = None

        return {
            'current_period': current,
            'prior_period': prior,
            'current_date': current_date,
            'prior_date': prior_date,
            'raw_dataframe': income_statement.to_dataframe() if income_statement else None,
        }

    def get_cashflow_data(self, ticker: str) -> Dict:
        """
        Extract key cash flow items using Entity Facts API.
        """
        company = Company(ticker)

        # Get cash flow statement - periods=2 for current + prior
        cash_flow = company.cash_flow(periods=2)

        # Extract current period
        current_helper = self._extract_statement_data(cash_flow, period_index=0)
        current = {}
        if current_helper:
            current = {
                'operating_cash_flow': (
                    current_helper['get_value_by_label'](['Net Cash Provided by Operating', 'Operating Cash Flow', 'Cash from Operations']) or
                    current_helper['get_value_by_concept'](['NetCashProvidedByUsedInOperatingActivities'])
                ),
                'investing_cash_flow': (
                    current_helper['get_value_by_label'](['Net Cash Used in Investing', 'Investing Cash Flow']) or
                    current_helper['get_value_by_concept'](['NetCashProvidedByUsedInInvestingActivities'])
                ),
                'financing_cash_flow': (
                    current_helper['get_value_by_label'](['Net Cash Used in Financing', 'Financing Cash Flow']) or
                    current_helper['get_value_by_concept'](['NetCashProvidedByUsedInFinancingActivities'])
                ),
                'capex': (
                    current_helper['get_value_by_label'](['Capital Expenditures', 'Payments to Acquire Property', 'CapEx']) or
                    current_helper['get_value_by_concept'](['PaymentsToAcquirePropertyPlantAndEquipment'])
                ),
            }
            current_date = current_helper['date_col']
        else:
            current_date = None

        # Extract prior period
        prior_helper = self._extract_statement_data(cash_flow, period_index=1)
        prior = {}
        if prior_helper:
            prior = {
                'operating_cash_flow': (
                    prior_helper['get_value_by_label'](['Net Cash Provided by Operating']) or
                    prior_helper['get_value_by_concept'](['NetCashProvidedByUsedInOperatingActivities'])
                ),
                'investing_cash_flow': (
                    prior_helper['get_value_by_label'](['Net Cash Used in Investing']) or
                    prior_helper['get_value_by_concept'](['NetCashProvidedByUsedInInvestingActivities'])
                ),
                'financing_cash_flow': (
                    prior_helper['get_value_by_label'](['Net Cash Used in Financing']) or
                    prior_helper['get_value_by_concept'](['NetCashProvidedByUsedInFinancingActivities'])
                ),
                'capex': (
                    prior_helper['get_value_by_label'](['Capital Expenditures']) or
                    prior_helper['get_value_by_concept'](['PaymentsToAcquirePropertyPlantAndEquipment'])
                ),
            }
            prior_date = prior_helper['date_col']
        else:
            prior_date = None

        return {
            'current_period': current,
            'prior_period': prior,
            'current_date': current_date,
            'prior_date': prior_date,
            'raw_dataframe': cash_flow.to_dataframe() if cash_flow else None,
        }

    def get_all_data(self, ticker: str) -> Dict:
        """
        Get all financial data in format compatible with your current pipeline.

        Uses Entity Facts API for pre-aggregated, reliable data.
        """
        company = Company(ticker)

        return {
            'balance_sheet': self.get_balance_sheet_data(ticker),
            'income_statement': self.get_income_statement_data(ticker),
            'cashflow': self.get_cashflow_data(ticker),
            'ticker': ticker,
            'company_name': company.name,
            'sic_code': getattr(company, 'sic', None),  # Correct attribute is 'sic' not 'sic_code'
            'cik': company.cik,
        }

    def verify_balance_sheet_equation(self, ticker: str, tolerance: float = 0.001) -> Dict:
        """
        Verify Assets = Liabilities + Equity within tolerance.

        Args:
            ticker: Stock ticker
            tolerance: Acceptable difference as fraction (0.001 = 0.1%)

        Returns:
            Dict with verification results
        """
        bs_data = self.get_balance_sheet_data(ticker)
        current = bs_data['current_period']

        assets = current.get('total_assets', 0) or 0
        liabilities = current.get('total_liabilities', 0) or 0
        equity = current.get('stockholders_equity', 0) or 0

        if assets == 0:
            return {
                'passed': False,
                'error': 'Total assets is zero or missing',
                'assets': assets,
                'liabilities': liabilities,
                'equity': equity,
            }

        expected = liabilities + equity
        diff = abs(assets - expected)
        diff_pct = (diff / assets)  # As fraction, not percentage

        passed = diff_pct <= tolerance

        return {
            'passed': passed,
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'expected_assets': expected,
            'difference': diff,
            'difference_pct': diff_pct * 100,  # Convert to percentage for display
            'tolerance_pct': tolerance * 100,
        }


if __name__ == "__main__":
    # Test with multiple companies
    edgar = EdgarToolsWrapper(identity="Steve Parton steve@sjpconsulting.com")

    print("=" * 80)
    print("Testing EdgarTools Wrapper with Entity Facts API")
    print("=" * 80)

    # Test 1: Apple (consolidated presentation)
    print("\n1. APPLE (AAPL) - Consolidated Presentation")
    print("-" * 80)
    aapl_data = edgar.get_all_data("AAPL")
    print(f"Company: {aapl_data['company_name']}")
    print(f"Revenue: ${aapl_data['income_statement']['current_period'].get('revenue', 0)/1e9:.2f}B")
    print(f"Net Income: ${aapl_data['income_statement']['current_period'].get('net_income', 0)/1e9:.2f}B")

    aapl_verification = edgar.verify_balance_sheet_equation("AAPL")
    print(f"\nBalance Sheet Verification: {'✓ PASSED' if aapl_verification['passed'] else '✗ FAILED'}")
    print(f"  Assets: ${aapl_verification['assets']/1e9:.2f}B")
    print(f"  Liabilities: ${aapl_verification['liabilities']/1e9:.2f}B")
    print(f"  Equity: ${aapl_verification['equity']/1e9:.2f}B")
    print(f"  Difference: {aapl_verification['difference_pct']:.4f}% (tolerance: {aapl_verification['tolerance_pct']:.1f}%)")

    # Test 2: Disney (segmented presentation)
    print("\n2. DISNEY (DIS) - Segmented Presentation")
    print("-" * 80)
    dis_data = edgar.get_all_data("DIS")
    print(f"Company: {dis_data['company_name']}")
    revenue = dis_data['income_statement']['current_period'].get('revenue')
    if revenue:
        print(f"Revenue: ${revenue/1e9:.2f}B (auto-aggregated from segments!)")
    else:
        print("Revenue: NOT FOUND")

    net_income = dis_data['income_statement']['current_period'].get('net_income')
    if net_income:
        print(f"Net Income: ${net_income/1e9:.2f}B")

    dis_verification = edgar.verify_balance_sheet_equation("DIS")
    print(f"\nBalance Sheet Verification: {'✓ PASSED' if dis_verification['passed'] else '✗ FAILED'}")
    if not dis_verification.get('error'):
        print(f"  Assets: ${dis_verification['assets']/1e9:.2f}B")
        print(f"  Liabilities: ${dis_verification['liabilities']/1e9:.2f}B")
        print(f"  Equity: ${dis_verification['equity']/1e9:.2f}B")
        print(f"  Difference: {dis_verification['difference_pct']:.4f}% (tolerance: {dis_verification['tolerance_pct']:.1f}%)")
    else:
        print(f"  Error: {dis_verification.get('error')}")

    print("\n" + "=" * 80)
    print("✓ Entity Facts API wrapper refactoring complete!")
    print("=" * 80)
