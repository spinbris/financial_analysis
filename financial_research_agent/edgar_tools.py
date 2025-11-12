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
    from edgar import Company, set_identity, find_company

    # Set SEC identity (required)
    user_agent = os.getenv("SEC_EDGAR_USER_AGENT", "FinancialResearchAgent/1.0 (test@example.com)")
    # Extract email from user agent
    if "(" in user_agent and ")" in user_agent:
        email = user_agent.split("(")[1].split(")")[0]
        set_identity(email)
    else:
        set_identity("test@example.com")

    # Step 1: Search for company using edgartools' find_company
    # This searches SEC's database and works for any public company
    try:
        search_results = find_company(company_name)

        if not search_results or len(search_results) == 0:
            raise ValueError(f"No companies found matching: {company_name}")

        # Get the first (most relevant) result
        first_result = search_results[0]
        ticker = first_result.ticker if hasattr(first_result, 'ticker') else first_result.tickers
        cik = first_result.cik

        # Handle case where ticker might be a list
        if isinstance(ticker, list):
            ticker = ticker[0] if ticker else None

        if not ticker:
            # If no ticker, use CIK directly
            ticker = str(cik)

    except Exception as e:
        raise ValueError(f"Failed to find company '{company_name}': {e}")

    # Step 2: Get latest filing using edgartools
    # Try in order: 10-Q (quarterly), 10-K (annual), 20-F (foreign annual)
    try:
        company = Company(ticker)
        filing = None
        form_type = None

        # Try to get the most recent financial filing in order of preference
        for form in ["10-Q", "10-K", "20-F"]:
            try:
                filings = company.get_filings(form=form)
                if filings and len(filings) > 0:
                    filing = filings.latest(1)
                    form_type = form
                    break
            except Exception:
                continue

        if not filing:
            raise RuntimeError(f"No 10-Q, 10-K, or 20-F filings found for {ticker}")

        # Get financials object from the filing
        financials = filing.obj().financials

    except Exception as e:
        raise RuntimeError(f"Failed to get financials for {ticker}: {e}")

    # Step 3: Extract financial statements as DataFrames
    try:
        bs_df = financials.balance_sheet().to_dataframe()
        is_df = financials.income_statement().to_dataframe()
        cf_df = financials.cashflow_statement().to_dataframe()

        # Filter to keep only the first 2 date columns (most recent filing periods)
        # This ensures the financial statements match the format of the most recent filing
        def filter_to_recent_periods(df):
            """Keep only the first 2 date columns from the DataFrame."""
            # Get all date columns
            date_cols = [col for col in df.columns if isinstance(col, str) and '-' in col and col[0].isdigit()]

            # Get non-date columns (like 'label', 'concept', 'abstract', etc.)
            non_date_cols = [col for col in df.columns if col not in date_cols]

            # Keep only first 2 date columns (current and prior period from latest filing)
            cols_to_keep = non_date_cols + date_cols[:2]

            return df[cols_to_keep].copy()

        bs_df = filter_to_recent_periods(bs_df)
        is_df = filter_to_recent_periods(is_df)
        cf_df = filter_to_recent_periods(cf_df)

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

    # Step 4: Return DataFrames with metadata (no conversion to dict)
    # Get filing metadata
    filing_date = str(filing.filing_date) if hasattr(filing, 'filing_date') else 'Unknown'
    form_type = str(filing.form) if hasattr(filing, 'form') else 'Unknown'

    # Get period from DataFrame columns
    date_cols = [col for col in bs_df.columns if isinstance(col, str) and '-' in col and col[0].isdigit()]
    current_period = date_cols[0] if len(date_cols) >= 1 else 'Unknown'
    prior_period = date_cols[1] if len(date_cols) >= 2 else None

    # Find XBRL calculation linkbase URL (_cal.xml) for validation
    filing_url = None
    try:
        if hasattr(filing, 'attachments'):
            for att in filing.attachments:
                if hasattr(att, 'document') and '_cal.xml' in att.document:
                    # Construct full URL from attachment path
                    if hasattr(att, 'path'):
                        path = att.path
                        filing_url = f"https://www.sec.gov{path}" if not path.startswith('http') else path
                        break
    except Exception:
        # If we can't get the filing URL, continue without it
        pass

    # Extract fiscal year-end date from the filing
    # For 20-F filers, this is particularly important as they may have non-calendar year-ends
    fiscal_year_end = None
    try:
        # Try to get fiscal year end from the filing object
        if hasattr(filing, 'fiscal_year_end'):
            fiscal_year_end = str(filing.fiscal_year_end)
        elif hasattr(filing, 'period_of_report'):
            fiscal_year_end = str(filing.period_of_report)
        else:
            # Fall back to the current period end date
            fiscal_year_end = current_period
    except Exception:
        fiscal_year_end = current_period

    # Get company name from Company object
    company_name_official = company.name if hasattr(company, 'name') else ticker

    # Return structure with DataFrames instead of dicts
    return {
        'balance_sheet_df': bs_df,
        'income_statement_df': is_df,
        'cash_flow_statement_df': cf_df,
        'current_period': current_period,
        'prior_period': prior_period,
        'filing_date': filing_date,
        'form_type': form_type,
        'filing_reference': f"{form_type} filed {filing_date}",
        'filing_url': filing_url,
        'ticker': ticker,
        'cik': cik,
        'company_name': company_name_official,  # Official name from SEC
        'fiscal_year_end': fiscal_year_end,
        'is_foreign_filer': form_type == '20-F',
    }


def dataframes_to_dict_format(
    balance_sheet_df: Any,
    income_statement_df: Any,
    cash_flow_statement_df: Any,
) -> dict[str, dict[str, Any]]:
    """
    Convert DataFrames to dictionary format for verification tools.

    This is a helper function that converts DataFrames to the dict format
    expected by verification_tools.py.

    Args:
        balance_sheet_df: Balance sheet DataFrame
        income_statement_df: Income statement DataFrame
        cash_flow_statement_df: Cash flow statement DataFrame

    Returns:
        Dictionary with 'balance_sheet', 'income_statement', 'cash_flow_statement' keys,
        each containing a dict with '_Current' and '_Prior' suffixed line items.
    """

    def df_to_dict(df: Any) -> dict[str, Any]:
        """Convert a single statement DataFrame to dictionary with _Current and _Prior."""
        line_items = {}

        # Get column names (dates)
        date_cols = [col for col in df.columns if isinstance(col, str) and '-' in col and col[0].isdigit()]

        if len(date_cols) < 1:
            return line_items

        current_col = date_cols[0] if len(date_cols) >= 1 else None
        prior_col = date_cols[1] if len(date_cols) >= 2 else None

        # Iterate through rows
        for idx, row in df.iterrows():
            # Skip abstract (header) rows
            if row.get('abstract', False):
                continue

            # Get label (human-readable)
            label = row.get('label', row.get('concept', f'Item_{idx}'))

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

        return line_items

    return {
        'balance_sheet': df_to_dict(balance_sheet_df),
        'income_statement': df_to_dict(income_statement_df),
        'cash_flow_statement': df_to_dict(cash_flow_statement_df),
    }


def _extract_statements_from_dataframes(
    bs_df: Any,
    is_df: Any,
    cf_df: Any,
    filing: Any
) -> dict[str, Any]:
    """
    DEPRECATED: Use dataframes_to_dict_format() instead.

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

    # Find XBRL calculation linkbase URL (_cal.xml) for validation
    filing_url = None
    try:
        if hasattr(filing, 'attachments'):
            for att in filing.attachments:
                if hasattr(att, 'document') and '_cal.xml' in att.document:
                    # Construct full URL from attachment path
                    if hasattr(att, 'path'):
                        path = att.path
                        filing_url = f"https://www.sec.gov{path}" if not path.startswith('http') else path
                        break
    except Exception:
        # If we can't get the filing URL, continue without it
        pass

    return {
        'balance_sheet': balance_sheet,
        'income_statement': income_statement,
        'cash_flow_statement': cash_flow_statement,
        'period': period,
        'filing_reference': f"SEC Filing {form_type} dated {filing_date}",
        'form_type': form_type,
        'filing_url': filing_url
    }
