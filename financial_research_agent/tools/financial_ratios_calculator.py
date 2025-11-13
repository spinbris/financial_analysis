"""
Enhanced Financial Ratios Calculator
Uses edgartools wrapper for clean data extraction and comprehensive ratio calculations.
"""

from typing import Dict, Optional
from edgartools_wrapper import EdgarToolsWrapper


class FinancialRatiosCalculator:
    """
    Calculate comprehensive financial ratios using edgartools.
    
    Replaces manual XBRL parsing with clean DataFrame-based extraction.
    """
    
    def __init__(self, identity: str = "Steve Parton stephen.parton@sjpconsulting.com"):
        self.edgar = EdgarToolsWrapper(identity=identity)
    
    def calculate_all_ratios(self, ticker: str) -> Dict:
        """
        Calculate comprehensive financial ratios for a company.
        
        Returns dict with:
        - profitability_ratios
        - liquidity_ratios
        - leverage_ratios
        - efficiency_ratios
        - market_ratios (if available)
        """
        data = self.edgar.get_all_data(ticker)
        
        return {
            'ticker': ticker,
            'profitability': self._calculate_profitability_ratios(data),
            'liquidity': self._calculate_liquidity_ratios(data),
            'leverage': self._calculate_leverage_ratios(data),
            'efficiency': self._calculate_efficiency_ratios(data),
            'cash_flow': self._calculate_cashflow_ratios(data),
        }
    
    def _calculate_profitability_ratios(self, data: Dict) -> Dict:
        """Profitability ratios: margins and returns"""
        ratios = {}
        
        # Get current period
        income = data['income_statement']['current_period']
        balance = data['balance_sheet']['current_period']
        
        # Profit Margins
        if income.get('revenue') and income.get('gross_profit'):
            ratios['gross_profit_margin'] = income['gross_profit'] / income['revenue']
        
        if income.get('revenue') and income.get('operating_income'):
            ratios['operating_margin'] = income['operating_income'] / income['revenue']
        
        if income.get('revenue') and income.get('net_income'):
            ratios['net_profit_margin'] = income['net_income'] / income['revenue']
        
        # Return Ratios
        if income.get('net_income') and balance.get('total_assets'):
            ratios['return_on_assets'] = income['net_income'] / balance['total_assets']
        
        if income.get('net_income') and balance.get('stockholders_equity'):
            ratios['return_on_equity'] = income['net_income'] / balance['stockholders_equity']
        
        # Asset Efficiency
        if income.get('revenue') and balance.get('total_assets'):
            ratios['asset_turnover'] = income['revenue'] / balance['total_assets']
        
        return ratios
    
    def _calculate_liquidity_ratios(self, data: Dict) -> Dict:
        """Liquidity ratios: ability to meet short-term obligations"""
        ratios = {}
        
        balance = data['balance_sheet']['current_period']
        
        if balance.get('current_assets') and balance.get('current_liabilities'):
            ratios['current_ratio'] = balance['current_assets'] / balance['current_liabilities']
        
        # Quick Ratio (if we had inventory and receivables)
        # For now, simplified version
        if balance.get('cash') and balance.get('current_liabilities'):
            ratios['cash_ratio'] = balance['cash'] / balance['current_liabilities']
        
        # Working Capital
        if balance.get('current_assets') and balance.get('current_liabilities'):
            ratios['working_capital'] = balance['current_assets'] - balance['current_liabilities']
        
        return ratios
    
    def _calculate_leverage_ratios(self, data: Dict) -> Dict:
        """Leverage ratios: debt and solvency"""
        ratios = {}
        
        balance = data['balance_sheet']['current_period']
        
        if balance.get('total_liabilities') and balance.get('total_assets'):
            ratios['debt_to_assets'] = balance['total_liabilities'] / balance['total_assets']
        
        if balance.get('total_liabilities') and balance.get('stockholders_equity'):
            ratios['debt_to_equity'] = balance['total_liabilities'] / balance['stockholders_equity']
        
        if balance.get('stockholders_equity') and balance.get('total_assets'):
            ratios['equity_ratio'] = balance['stockholders_equity'] / balance['total_assets']
        
        return ratios
    
    def _calculate_efficiency_ratios(self, data: Dict) -> Dict:
        """Efficiency ratios: asset utilization"""
        ratios = {}
        
        income = data['income_statement']['current_period']
        balance = data['balance_sheet']['current_period']
        
        # Revenue per Asset Dollar
        if income.get('revenue') and balance.get('total_assets'):
            ratios['asset_turnover'] = income['revenue'] / balance['total_assets']
        
        # Revenue per Equity Dollar
        if income.get('revenue') and balance.get('stockholders_equity'):
            ratios['equity_turnover'] = income['revenue'] / balance['stockholders_equity']
        
        return ratios
    
    def _calculate_cashflow_ratios(self, data: Dict) -> Dict:
        """Cash flow ratios: cash generation quality"""
        ratios = {}
        
        income = data['income_statement']['current_period']
        cashflow = data['cashflow']['current_period']
        balance = data['balance_sheet']['current_period']
        
        # Operating Cash Flow ratios
        if cashflow.get('operating_cash_flow') and income.get('net_income'):
            ratios['ocf_to_net_income'] = cashflow['operating_cash_flow'] / income['net_income']
        
        if cashflow.get('operating_cash_flow') and income.get('revenue'):
            ratios['ocf_margin'] = cashflow['operating_cash_flow'] / income['revenue']
        
        if cashflow.get('operating_cash_flow') and balance.get('current_liabilities'):
            ratios['ocf_to_current_liabilities'] = cashflow['operating_cash_flow'] / balance['current_liabilities']
        
        # Free Cash Flow (Operating CF - CapEx)
        if cashflow.get('operating_cash_flow') and cashflow.get('capex'):
            ratios['free_cash_flow'] = cashflow['operating_cash_flow'] + cashflow['capex']  # CapEx is negative
        
        return ratios
    
    def calculate_growth_rates(self, ticker: str) -> Dict:
        """
        Calculate year-over-year growth rates.
        Compares current period to prior period.
        """
        data = self.edgar.get_all_data(ticker)
        
        growth = {}
        
        # Income statement growth
        income_current = data['income_statement']['current_period']
        income_prior = data['income_statement']['prior_period']
        
        if income_current.get('revenue') and income_prior.get('revenue'):
            growth['revenue_growth'] = (
                (income_current['revenue'] - income_prior['revenue']) / 
                income_prior['revenue']
            )
        
        if income_current.get('net_income') and income_prior.get('net_income'):
            growth['net_income_growth'] = (
                (income_current['net_income'] - income_prior['net_income']) / 
                income_prior['net_income']
            )
        
        # Balance sheet growth
        balance_current = data['balance_sheet']['current_period']
        balance_prior = data['balance_sheet']['prior_period']
        
        if balance_current.get('total_assets') and balance_prior.get('total_assets'):
            growth['asset_growth'] = (
                (balance_current['total_assets'] - balance_prior['total_assets']) / 
                balance_prior['total_assets']
            )
        
        return growth
    
    def get_ratio_summary(self, ticker: str) -> str:
        """
        Get formatted summary of all ratios.
        Useful for LLM agents.
        """
        ratios = self.calculate_all_ratios(ticker)
        growth = self.calculate_growth_rates(ticker)
        
        summary = [
            f"\n{'='*60}",
            f"FINANCIAL RATIOS SUMMARY: {ticker}",
            f"{'='*60}",
            "",
            "PROFITABILITY:",
        ]
        
        for name, value in ratios['profitability'].items():
            if value is not None:
                pct = value * 100 if abs(value) < 10 else value
                summary.append(f"  {name.replace('_', ' ').title()}: {pct:.2f}%")
        
        summary.append("\nLIQUIDITY:")
        for name, value in ratios['liquidity'].items():
            if value is not None:
                summary.append(f"  {name.replace('_', ' ').title()}: {value:.2f}")
        
        summary.append("\nLEVERAGE:")
        for name, value in ratios['leverage'].items():
            if value is not None:
                summary.append(f"  {name.replace('_', ' ').title()}: {value:.2f}")
        
        summary.append("\nCASH FLOW:")
        for name, value in ratios['cash_flow'].items():
            if value is not None:
                if 'margin' in name:
                    summary.append(f"  {name.replace('_', ' ').title()}: {value*100:.2f}%")
                else:
                    summary.append(f"  {name.replace('_', ' ').title()}: {value:.2f}")
        
        summary.append("\nGROWTH RATES (YoY):")
        for name, value in growth.items():
            if value is not None:
                summary.append(f"  {name.replace('_', ' ').title()}: {value*100:.2f}%")
        
        summary.append(f"\n{'='*60}")
        
        return "\n".join(summary)


# Usage example
if __name__ == "__main__":
    calculator = FinancialRatiosCalculator()
    
    # Get all ratios
    ratios = calculator.calculate_all_ratios("AAPL")
    print("Profitability Ratios:", ratios['profitability'])
    
    # Get formatted summary
    summary = calculator.get_ratio_summary("AAPL")
    print(summary)
