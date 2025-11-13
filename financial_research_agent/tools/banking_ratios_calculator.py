"""
Banking-Specific Financial Ratios Calculator

Calculates banking-specific ratios (TIER 2 - simple calculations) from financial statements.
TIER 1 ratios (directly reported regulatory ratios) are extracted by the LLM agent.

This module focuses on "low-hanging fruit" calculations that can be derived from
standard financial statement line items.
"""

from typing import Dict, Optional
from financial_research_agent.tools.edgartools_wrapper import EdgarToolsWrapper


class BankingRatiosCalculator:
    """
    Calculate banking-specific financial ratios using edgartools.

    Focuses on TIER 2 ratios (calculated from statements):
    - Net Interest Margin (NIM)
    - Efficiency Ratio
    - Return on Tangible Common Equity (ROTCE)
    - Non-Performing Loan Ratio
    - Loan-to-Deposit Ratio
    - Other banking-specific metrics

    TIER 1 ratios (CET1, Tier 1, etc.) are extracted separately by LLM agent
    from regulatory disclosures.
    """

    def __init__(self, identity: str = "Steve Parton stephen.parton@sjpconsulting.com"):
        self.edgar = EdgarToolsWrapper(identity=identity)

    def calculate_all_banking_ratios(self, ticker: str) -> Dict:
        """
        Calculate comprehensive banking-specific ratios for a bank.

        Returns dict with:
        - profitability_ratios (banking-specific)
        - credit_quality_ratios
        - balance_sheet_composition

        Note: Regulatory capital ratios (CET1, Tier 1, etc.) must be extracted
        separately by the banking_ratios_agent from MD&A disclosures.
        """
        data = self.edgar.get_all_data(ticker)

        return {
            'ticker': ticker,
            'profitability': self._calculate_banking_profitability(data),
            'credit_quality': self._calculate_credit_quality(data),
            'balance_sheet_composition': self._calculate_balance_sheet_composition(data),
        }

    def _calculate_banking_profitability(self, data: Dict) -> Dict:
        """
        Banking-specific profitability ratios.

        Key metrics:
        - Net Interest Margin (NIM) - core lending profitability
        - Efficiency Ratio - operating cost management
        - Return on Tangible Common Equity (ROTCE) - key bank profitability metric
        """
        ratios = {}

        income = data['income_statement']['current_period']
        balance = data['balance_sheet']['current_period']

        # Net Interest Margin (NIM)
        # Formula: (Interest Income - Interest Expense) / Average Earning Assets * 100
        # Simplified: Use total assets as proxy for earning assets if specific data unavailable
        interest_income = income.get('interest_income')
        interest_expense = income.get('interest_expense')

        # Try to get interest income from various potential XBRL tags
        if not interest_income:
            interest_income = income.get('interest_and_dividend_income')
        if not interest_income:
            interest_income = income.get('interest_income_operating')

        # Calculate Net Interest Income
        if interest_income and interest_expense:
            net_interest_income = interest_income - interest_expense

            # Use total assets as proxy for earning assets
            avg_assets = balance.get('total_assets')
            if avg_assets and avg_assets > 0:
                ratios['net_interest_margin'] = (net_interest_income / avg_assets) * 100

        # Efficiency Ratio
        # Formula: Non-Interest Expense / (Net Interest Income + Non-Interest Income) * 100
        # Lower is better (indicates cost control)
        non_interest_expense = income.get('operating_expenses')
        if not non_interest_expense:
            non_interest_expense = income.get('noninterest_expense')

        non_interest_income = income.get('noninterest_income')

        if non_interest_expense and interest_income and interest_expense:
            net_interest_income = interest_income - interest_expense

            if non_interest_income:
                total_revenue = net_interest_income + non_interest_income
            else:
                # Fallback: Use total revenue
                total_revenue = income.get('revenue')

            if total_revenue and total_revenue > 0:
                ratios['efficiency_ratio'] = (non_interest_expense / total_revenue) * 100

        # Return on Tangible Common Equity (ROTCE)
        # Formula: Net Income / (Total Equity - Intangible Assets) * 100
        # Preferred over ROE for banks due to intangible assets from acquisitions
        net_income = income.get('net_income')
        stockholders_equity = balance.get('stockholders_equity')
        intangible_assets = balance.get('intangible_assets')
        if not intangible_assets:
            intangible_assets = balance.get('goodwill_and_intangible_assets')

        if net_income and stockholders_equity:
            if intangible_assets:
                tangible_equity = stockholders_equity - intangible_assets
            else:
                # If no intangibles data, fall back to ROE
                tangible_equity = stockholders_equity

            if tangible_equity > 0:
                ratios['return_on_tangible_equity'] = (net_income / tangible_equity) * 100

        return ratios

    def _calculate_credit_quality(self, data: Dict) -> Dict:
        """
        Credit quality and loan portfolio health ratios.

        Key metrics:
        - Non-Performing Loan (NPL) Ratio - credit risk indicator
        - Provision Coverage Ratio - adequacy of loan loss reserves
        - Net Charge-Off Rate - actual loan losses
        - Allowance for Loan Losses ratio
        """
        ratios = {}

        balance = data['balance_sheet']['current_period']
        income = data['income_statement']['current_period']

        # Non-Performing Loan Ratio
        # Formula: Non-Performing Loans / Total Loans * 100
        # NPLs = loans 90+ days past due + nonaccrual loans
        # Note: NPL data often not in standard XBRL, would need detailed notes
        # This is a placeholder - actual extraction would need LLM agent for notes
        non_performing_loans = balance.get('nonperforming_loans')
        total_loans = balance.get('loans_and_leases')
        if not total_loans:
            total_loans = balance.get('loans_receivable')
        if not total_loans:
            total_loans = balance.get('net_loans')

        if non_performing_loans and total_loans and total_loans > 0:
            ratios['npl_ratio'] = (non_performing_loans / total_loans) * 100

        # Allowance for Loan Losses (ALL) ratio
        # Formula: Allowance for Loan Losses / Total Loans * 100
        allowance_for_loan_losses = balance.get('allowance_for_loan_losses')
        if not allowance_for_loan_losses:
            allowance_for_loan_losses = balance.get('allowance_for_credit_losses')

        if allowance_for_loan_losses and total_loans and total_loans > 0:
            ratios['allowance_for_loan_losses'] = (allowance_for_loan_losses / total_loans) * 100

        # Provision Coverage Ratio
        # Formula: Allowance for Loan Losses / Non-Performing Loans * 100
        # Indicates adequacy of reserves (>80% is generally adequate)
        if allowance_for_loan_losses and non_performing_loans and non_performing_loans > 0:
            ratios['provision_coverage_ratio'] = (allowance_for_loan_losses / non_performing_loans) * 100

        # Net Charge-Off Rate
        # Formula: Net Charge-Offs / Average Total Loans * 100
        # Represents actual loan losses (written off - recoveries)
        net_charge_offs = income.get('net_charge_offs')
        if not net_charge_offs:
            # Try to calculate from provision and change in allowance
            provision = income.get('provision_for_loan_losses')
            if not provision:
                provision = income.get('provision_for_credit_losses')

            # Note: Net charge-offs = Beginning allowance + Provision - Ending allowance
            # Would need prior period data for accurate calculation
            # This is simplified
            if provision and total_loans and total_loans > 0:
                # Use provision as proxy (not perfectly accurate)
                ratios['net_charge_off_rate'] = (provision / total_loans) * 100
        elif total_loans and total_loans > 0:
            ratios['net_charge_off_rate'] = (net_charge_offs / total_loans) * 100

        return ratios

    def _calculate_balance_sheet_composition(self, data: Dict) -> Dict:
        """
        Balance sheet composition and funding structure ratios.

        Key metrics:
        - Loan-to-Deposit Ratio - primary banking metric
        - Loan-to-Assets Ratio - concentration in lending
        - Deposits-to-Assets Ratio - funding composition
        """
        ratios = {}

        balance = data['balance_sheet']['current_period']

        # Loan-to-Deposit Ratio (LTD)
        # Formula: Total Loans / Total Deposits * 100
        # <100% means excess deposits (good for liquidity)
        # >100% means bank needs other funding sources
        total_loans = balance.get('loans_and_leases')
        if not total_loans:
            total_loans = balance.get('loans_receivable')
        if not total_loans:
            total_loans = balance.get('net_loans')

        total_deposits = balance.get('deposits')
        if not total_deposits:
            total_deposits = balance.get('total_deposits')

        if total_loans and total_deposits and total_deposits > 0:
            ratios['loan_to_deposit_ratio'] = (total_loans / total_deposits) * 100

        # Loan-to-Assets Ratio
        # Formula: Total Loans / Total Assets * 100
        # Indicates concentration in lending business
        total_assets = balance.get('total_assets')
        if total_loans and total_assets and total_assets > 0:
            ratios['loan_to_assets_ratio'] = (total_loans / total_assets) * 100

        # Deposits-to-Assets Ratio
        # Formula: Total Deposits / Total Assets * 100
        # Higher indicates more stable funding from deposits
        if total_deposits and total_assets and total_assets > 0:
            ratios['deposits_to_assets_ratio'] = (total_deposits / total_assets) * 100

        return ratios

    def get_banking_ratio_summary(self, ticker: str) -> str:
        """
        Get formatted summary of banking-specific ratios.
        Useful for LLM agents and reporting.
        """
        ratios = self.calculate_all_banking_ratios(ticker)

        summary = [
            f"\n{'='*60}",
            f"BANKING RATIOS SUMMARY: {ticker}",
            f"{'='*60}",
            "",
            "BANKING PROFITABILITY:",
        ]

        for name, value in ratios['profitability'].items():
            if value is not None:
                summary.append(f"  {name.replace('_', ' ').title()}: {value:.2f}%")

        summary.append("\nCREDIT QUALITY:")
        for name, value in ratios['credit_quality'].items():
            if value is not None:
                summary.append(f"  {name.replace('_', ' ').title()}: {value:.2f}%")

        summary.append("\nBALANCE SHEET COMPOSITION:")
        for name, value in ratios['balance_sheet_composition'].items():
            if value is not None:
                summary.append(f"  {name.replace('_', ' ').title()}: {value:.2f}%")

        summary.append("")
        summary.append("Note: Regulatory capital ratios (CET1, Tier 1, Total Capital, etc.)")
        summary.append("must be extracted from MD&A disclosures using banking_ratios_agent.")
        summary.append(f"{'='*60}")

        return "\n".join(summary)


# Usage example
if __name__ == "__main__":
    calculator = BankingRatiosCalculator()

    # Test with JPMorgan Chase
    ratios = calculator.calculate_all_banking_ratios("JPM")
    print("Banking Ratios:", ratios)

    # Get formatted summary
    summary = calculator.get_banking_ratio_summary("JPM")
    print(summary)
