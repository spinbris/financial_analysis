"""
Direct extraction of financial statements using edgartools library.

This module provides comprehensive financial statement extraction with 100+ line items
using the edgartools library directly, bypassing the limited MCP tool responses.
"""

from typing import Any, Optional
import json
import os
import re
from pathlib import Path


async def extract_financial_data_deterministic(
    mcp_server: Any,
    company_name: str,
) -> dict[str, Any]:
    """
    Extract complete financial data using edgartools library directly.

    This function:
    1. Uses ticker symbol mapping to get company
    2. Uses edgartools library to get latest 10-Q filing
    3. Extracts ALL line items from balance sheet, income statement, and cash flow
    4. Returns structured data with _Current and _Prior suffixes for comparative analysis

    Args:
        mcp_server: MCPServerStdio instance (unused, kept for compatibility)
        company_name: Company name (e.g., "Apple Inc" or "Apple")

    Returns:
        Dictionary with balance_sheet, income_statement, and cash_flow_statement,
        each containing line items with _Current and _Prior suffixes.
        Provides 100+ total line items compared to 19 from MCP tool.
    """

    # Import edgartools
    from edgar import Company, set_identity

    # Set SEC identity (required)
    user_agent = os.getenv("SEC_EDGAR_USER_AGENT", "FinancialResearchAgent/1.0 (test@example.com)")
    # Extract email from user agent
    if "(" in user_agent and ")" in user_agent:
        email = user_agent.split("(")[1].split(")")[0]
        set_identity(email)
    else:
        set_identity("test@example.com")

    # Step 1: Get ticker symbol from company name
    ticker_mapping = {
        "apple": "AAPL",
        "microsoft": "MSFT",
        "tesla": "TSLA",
        "amazon": "AMZN",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "meta": "META",
        "facebook": "META",
        "nvidia": "NVDA",
        "nvda": "NVDA",
    }

    company_key = company_name.lower().split()[0]
    ticker = ticker_mapping.get(company_key)

    if not ticker:
        raise ValueError(f"Could not find ticker for company: {company_name}. Please add to ticker_mapping in edgar_tools.py")

    # Step 2: Get latest 10-Q filing using edgartools
    try:
        company = Company(ticker)
        filing = company.get_filings(form="10-Q").latest(1)

        # Get financials object from the filing
        financials = filing.obj().financials

    except Exception as e:
        raise RuntimeError(f"Failed to get financials for {ticker}: {e}")

    # Step 3: Extract financial statements as DataFrames
    try:
        bs_df = financials.balance_sheet().to_dataframe()
        is_df = financials.income_statement().to_dataframe()
        cf_df = financials.cashflow_statement().to_dataframe()

    except Exception as e:
        raise RuntimeError(f"Failed to extract statements from financials: {e}")

    # Save raw XBRL DataFrames as CSV for audit trail (will be copied to output folder later)
    debug_dir = Path("financial_research_agent/output/debug_edgar")
    debug_dir.mkdir(parents=True, exist_ok=True)

    # Export raw XBRL data to CSV for verification and audit trail
    filing_date_str = str(filing.filing_date).replace("-", "")
    bs_df.to_csv(debug_dir / f"xbrl_raw_balance_sheet_{ticker}_{filing_date_str}.csv", index=False)
    is_df.to_csv(debug_dir / f"xbrl_raw_income_statement_{ticker}_{filing_date_str}.csv", index=False)
    cf_df.to_csv(debug_dir / f"xbrl_raw_cashflow_{ticker}_{filing_date_str}.csv", index=False)

    # Save extraction summary
    debug_file = debug_dir / f"edgartools_extraction_{ticker}.txt"
    with open(debug_file, "w") as f:
        f.write(f"Ticker: {ticker}\n")
        f.write(f"Filing: {filing.form} from {filing.filing_date}\n")
        f.write(f"Period: {bs_df.columns[2]} (current) vs {bs_df.columns[3]} (prior)\n")
        f.write(f"Balance Sheet rows: {len(bs_df)}\n")
        f.write(f"Income Statement rows: {len(is_df)}\n")
        f.write(f"Cash Flow rows: {len(cf_df)}\n")
        f.write(f"Total line items: {len(bs_df) + len(is_df) + len(cf_df)}\n\n")
        f.write(f"Raw XBRL CSV files saved for audit trail:\n")
        f.write(f"  - xbrl_raw_balance_sheet_{ticker}_{filing_date_str}.csv\n")
        f.write(f"  - xbrl_raw_income_statement_{ticker}_{filing_date_str}.csv\n")
        f.write(f"  - xbrl_raw_cashflow_{ticker}_{filing_date_str}.csv\n\n")
        f.write(f"Balance Sheet columns: {list(bs_df.columns)}\n\n")
        f.write(f"Balance Sheet preview:\n{bs_df.head(20).to_string()}\n")

    # Step 4: Convert DataFrames to dictionaries with _Current and _Prior suffixes
    statements = _extract_statements_from_dataframes(bs_df, is_df, cf_df, filing)

    if not statements or not statements.get('balance_sheet'):
        raise RuntimeError(f"Failed to extract statements from DataFrames")

    return statements


def _extract_statements_from_dataframes(
    bs_df: Any,
    is_df: Any,
    cf_df: Any,
    filing: Any
) -> dict[str, Any]:
    """
    Convert DataFrames from edgartools to dictionaries with _Current and _Prior suffixes.

    The DataFrames have columns like:
    - concept: XBRL tag name
    - label: Human-readable label
    - 2025-06-28: Current period value
    - 2024-09-28: Prior period value
    - level: Hierarchy level
    - abstract: Whether this is a header row

    Returns flat dictionaries suitable for the FinancialMetrics agent.
    """

    def df_to_dict(df: Any) -> dict[str, Any]:
        """Convert a single statement DataFrame to dictionary with _Current and _Prior.

        Returns a dictionary with three sections:
        - 'line_items': Dict mapping human-readable labels to values
        - 'xbrl_concepts': Dict mapping same labels to XBRL concept names for citations
        - 'period_dates': Dict with 'current' and 'prior' period end dates
        """
        line_items = {}
        xbrl_concepts = {}

        # Get column names (dates)
        date_cols = [col for col in df.columns if isinstance(col, str) and '-' in col and col[0].isdigit()]

        if len(date_cols) < 1:
            return {'line_items': line_items, 'xbrl_concepts': xbrl_concepts, 'period_dates': {}}

        current_col = date_cols[0] if len(date_cols) >= 1 else None
        prior_col = date_cols[1] if len(date_cols) >= 2 else None

        # Store the actual period dates for column headers
        period_dates = {}
        if current_col:
            period_dates['current'] = current_col
        if prior_col:
            period_dates['prior'] = prior_col

        # Iterate through rows
        for idx, row in df.iterrows():
            # Skip abstract (header) rows
            if row.get('abstract', False):
                continue

            # Get both label (human-readable) and concept (XBRL technical ID)
            label = row.get('label', row.get('concept', f'Item_{idx}'))
            concept = row.get('concept', label)

            # Use the original label WITH spaces as the key (human-readable)
            # This preserves readability: "Depreciation, amortization and impairment"
            # instead of "Depreciationamortizationandimpairment"

            # Store XBRL concept for citation purposes
            xbrl_concepts[label] = concept

            # Get current period value
            if current_col and current_col in row:
                current_val = row[current_col]
                if current_val is not None and not (isinstance(current_val, float) and str(current_val) == 'nan'):
                    line_items[f"{label}_Current"] = current_val

            # Get prior period value
            if prior_col and prior_col in row:
                prior_val = row[prior_col]
                if prior_val is not None and not (isinstance(prior_val, float) and str(prior_val) == 'nan'):
                    line_items[f"{label}_Prior"] = prior_val

        return {'line_items': line_items, 'xbrl_concepts': xbrl_concepts, 'period_dates': period_dates}

    # Convert each statement
    balance_sheet = df_to_dict(bs_df)
    income_statement = df_to_dict(is_df)
    cash_flow_statement = df_to_dict(cf_df)

    # Get filing metadata
    filing_date = str(filing.filing_date) if hasattr(filing, 'filing_date') else 'Unknown'
    form_type = str(filing.form) if hasattr(filing, 'form') else 'Unknown'

    # Get period from DataFrame columns
    date_cols = [col for col in bs_df.columns if isinstance(col, str) and '-' in col and col[0].isdigit()]
    period = date_cols[0] if date_cols else 'Unknown'

    return {
        'balance_sheet': balance_sheet,
        'income_statement': income_statement,
        'cash_flow_statement': cash_flow_statement,
        'period': period,
        'filing_reference': f"SEC Filing {form_type} dated {filing_date}",
        'form_type': form_type
    }
