"""
Utility functions for extracting structured data from financial reports.

These functions parse markdown reports and structured data to prepare
chart-ready data dictionaries.
"""

import re
from typing import Dict, List, Any, Optional
from pathlib import Path


def extract_revenue_trend_data(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract revenue trend data from structured financial data.

    Args:
        financial_data: Dictionary with income statement data

    Returns:
        Dictionary ready for create_revenue_trend_chart()
    """
    # This is a template - actual implementation depends on data structure
    # from the financial analyst agent
    chart_data = {
        'periods': [],
        'revenue': [],
        'gross_profit': [],
        'operating_income': [],
        'gross_margin_pct': [],
        'operating_margin_pct': []
    }

    # Example extraction logic (adapt based on actual data structure)
    if 'income_statement' in financial_data:
        income_stmt = financial_data['income_statement']

        # Extract current period
        if 'current' in income_stmt:
            current = income_stmt['current']
            chart_data['periods'].append(current.get('period', 'Current'))
            chart_data['revenue'].append(current.get('revenue', 0))
            chart_data['gross_profit'].append(current.get('gross_profit', 0))
            chart_data['operating_income'].append(current.get('operating_income', 0))

            # Calculate margins
            revenue = current.get('revenue', 1)  # Avoid division by zero
            gross_profit = current.get('gross_profit', 0)
            operating_income = current.get('operating_income', 0)

            chart_data['gross_margin_pct'].append((gross_profit / revenue * 100) if revenue else 0)
            chart_data['operating_margin_pct'].append((operating_income / revenue * 100) if revenue else 0)

        # Extract prior period
        if 'prior' in income_stmt:
            prior = income_stmt['prior']
            chart_data['periods'].insert(0, prior.get('period', 'Prior'))
            chart_data['revenue'].insert(0, prior.get('revenue', 0))
            chart_data['gross_profit'].insert(0, prior.get('gross_profit', 0))
            chart_data['operating_income'].insert(0, prior.get('operating_income', 0))

            # Calculate margins
            revenue = prior.get('revenue', 1)
            gross_profit = prior.get('gross_profit', 0)
            operating_income = prior.get('operating_income', 0)

            chart_data['gross_margin_pct'].insert(0, (gross_profit / revenue * 100) if revenue else 0)
            chart_data['operating_margin_pct'].insert(0, (operating_income / revenue * 100) if revenue else 0)

    return chart_data


def extract_margin_comparison_data(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract margin comparison data from structured financial data.

    Args:
        financial_data: Dictionary with income statement data

    Returns:
        Dictionary ready for create_margin_comparison_chart()
    """
    chart_data = {
        'current': {},
        'prior': {},
        'current_period': 'Current Period',
        'prior_period': 'Prior Period'
    }

    if 'income_statement' in financial_data:
        income_stmt = financial_data['income_statement']

        # Current period margins
        if 'current' in income_stmt:
            current = income_stmt['current']
            revenue = current.get('revenue', 1)
            gross_profit = current.get('gross_profit', 0)
            operating_income = current.get('operating_income', 0)
            net_income = current.get('net_income', 0)

            chart_data['current'] = {
                'gross_margin': (gross_profit / revenue * 100) if revenue else 0,
                'operating_margin': (operating_income / revenue * 100) if revenue else 0,
                'net_margin': (net_income / revenue * 100) if revenue else 0
            }
            chart_data['current_period'] = current.get('period', 'Current Period')

        # Prior period margins
        if 'prior' in income_stmt:
            prior = income_stmt['prior']
            revenue = prior.get('revenue', 1)
            gross_profit = prior.get('gross_profit', 0)
            operating_income = prior.get('operating_income', 0)
            net_income = prior.get('net_income', 0)

            chart_data['prior'] = {
                'gross_margin': (gross_profit / revenue * 100) if revenue else 0,
                'operating_margin': (operating_income / revenue * 100) if revenue else 0,
                'net_margin': (net_income / revenue * 100) if revenue else 0
            }
            chart_data['prior_period'] = prior.get('period', 'Prior Period')

    return chart_data


def extract_cash_flow_waterfall_data(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract cash flow waterfall data from structured financial data.

    Args:
        financial_data: Dictionary with cash flow statement data

    Returns:
        Dictionary ready for create_cash_flow_waterfall()
    """
    chart_data = {
        'operating_cf': 0,
        'investing_cf': 0,
        'financing_cf': 0,
        'net_change': 0,
        'period': 'Current Period'
    }

    if 'cash_flow' in financial_data:
        cf_stmt = financial_data['cash_flow']

        if 'current' in cf_stmt:
            current = cf_stmt['current']
            chart_data['operating_cf'] = current.get('operating_cash_flow', 0)
            chart_data['investing_cf'] = current.get('investing_cash_flow', 0)
            chart_data['financing_cf'] = current.get('financing_cash_flow', 0)
            chart_data['net_change'] = current.get('net_change_in_cash', 0)
            chart_data['period'] = current.get('period', 'Current Period')

    return chart_data


def extract_key_metrics_data(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key metrics data from structured financial data.

    Args:
        financial_data: Dictionary with financial metrics data

    Returns:
        Dictionary ready for create_key_metrics_dashboard()
    """
    chart_data = {
        'roe': 0,
        'roa': 0,
        'current_ratio': 0,
        'debt_to_equity': 0,
        'roe_prior': None,
        'roa_prior': None,
        'current_ratio_prior': None,
        'debt_to_equity_prior': None
    }

    if 'metrics' in financial_data:
        metrics = financial_data['metrics']

        # Current period metrics
        if 'current' in metrics:
            current = metrics['current']
            chart_data['roe'] = current.get('return_on_equity', 0)
            chart_data['roa'] = current.get('return_on_assets', 0)
            chart_data['current_ratio'] = current.get('current_ratio', 0)
            chart_data['debt_to_equity'] = current.get('debt_to_equity', 0)

        # Prior period metrics (for delta indicators)
        if 'prior' in metrics:
            prior = metrics['prior']
            chart_data['roe_prior'] = prior.get('return_on_equity', 0)
            chart_data['roa_prior'] = prior.get('return_on_assets', 0)
            chart_data['current_ratio_prior'] = prior.get('current_ratio', 0)
            chart_data['debt_to_equity_prior'] = prior.get('debt_to_equity', 0)

    return chart_data


def parse_financial_statements_markdown(markdown_path: Path) -> Dict[str, Any]:
    """
    Parse financial statements markdown file to extract structured data.

    This is a fallback method if structured JSON data is not available.

    Args:
        markdown_path: Path to financial statements markdown file

    Returns:
        Dictionary with extracted financial data
    """
    if not markdown_path.exists():
        return {}

    content = markdown_path.read_text()

    # Extract data using regex patterns
    # This is a simplified parser - can be enhanced based on actual markdown structure

    data = {
        'income_statement': {},
        'balance_sheet': {},
        'cash_flow': {}
    }

    # Example: Extract revenue from markdown table
    revenue_pattern = r'Revenue.*?\|\s*\$?\s*([\d,]+(?:\.\d+)?)\s*[MB]?'
    revenue_match = re.search(revenue_pattern, content, re.IGNORECASE)
    if revenue_match:
        # Parse revenue value (handle millions/billions notation)
        # This is placeholder logic - actual implementation depends on format
        pass

    return data


def convert_financial_value(value_str: str) -> float:
    """
    Convert financial value string to float.

    Handles formats like:
    - "$123.4M" -> 123400000
    - "45.6B" -> 45600000000
    - "1,234.56" -> 1234.56

    Args:
        value_str: String representation of financial value

    Returns:
        Float value
    """
    # Remove $ and commas
    cleaned = value_str.replace('$', '').replace(',', '').strip()

    # Handle millions/billions
    multiplier = 1
    if cleaned.endswith('M'):
        multiplier = 1e6
        cleaned = cleaned[:-1]
    elif cleaned.endswith('B'):
        multiplier = 1e9
        cleaned = cleaned[:-1]

    try:
        return float(cleaned) * multiplier
    except ValueError:
        return 0.0
