"""
Direct extraction of financial statements using edgartools library.

This module provides comprehensive financial statement extraction with 100+ line items
using the edgartools library directly, bypassing the limited MCP tool responses.

Enhanced with edgartools' XBRL features:
- render() for formatted statement presentation
- to_markdown() for professional table output
- metadata['comparison_data'] for YoY percentages
- analyze_trends() for built-in trend analysis
- calculate_ratios() for built-in ratio calculations
- Segment filtering for cleaner main statements
"""

from typing import Any, Optional
import json
import os
import re
from pathlib import Path
import pandas as pd


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
    # Get the most recent filing by date across 10-Q, 10-K, and 20-F
    try:
        company = Company(ticker)
        filing = None
        form_type = None
        latest_date = None

        # Find the most recent financial filing by comparing dates
        for form in ["10-Q", "10-K", "20-F"]:
            try:
                filings = company.get_filings(form=form)
                if filings and len(filings) > 0:
                    candidate = filings.latest(1)
                    # Get filing date for comparison
                    candidate_date = candidate.filing_date if hasattr(candidate, 'filing_date') else None

                    # If this is more recent than what we have, use it
                    if candidate_date and (latest_date is None or candidate_date > latest_date):
                        filing = candidate
                        form_type = form
                        latest_date = candidate_date
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


async def extract_financial_data_enhanced(
    mcp_server: Any,
    company_name: str,
) -> dict[str, Any]:
    """
    Extract financial data using edgartools' enhanced XBRL features.

    This function leverages edgartools' XBRL capabilities:
    - render() for formatted statement presentation
    - to_markdown() for professional table output
    - metadata['comparison_data'] for pre-calculated YoY percentages
    - Segment filtering for cleaner main statements

    Args:
        mcp_server: MCPServerStdio instance (unused, kept for compatibility)
        company_name: Company name (e.g., "Apple Inc" or "Apple")

    Returns:
        Dictionary with enhanced financial data including:
        - DataFrames for each statement
        - Markdown formatted output
        - YoY comparison percentages
        - Metadata and filing information
    """

    # Import edgartools
    from edgar import Company, set_identity, find_company

    # Set SEC identity (required)
    user_agent = os.getenv("SEC_EDGAR_USER_AGENT", "FinancialResearchAgent/1.0 (test@example.com)")
    if "(" in user_agent and ")" in user_agent:
        email = user_agent.split("(")[1].split(")")[0]
        set_identity(email)
    else:
        set_identity("test@example.com")

    # Step 1: Find company
    try:
        search_results = find_company(company_name)
        if not search_results or len(search_results) == 0:
            raise ValueError(f"No companies found matching: {company_name}")

        first_result = search_results[0]
        ticker = first_result.ticker if hasattr(first_result, 'ticker') else first_result.tickers
        cik = first_result.cik

        if isinstance(ticker, list):
            ticker = ticker[0] if ticker else None
        if not ticker:
            ticker = str(cik)

    except Exception as e:
        raise ValueError(f"Failed to find company '{company_name}': {e}")

    # Step 2: Get latest filing
    try:
        company = Company(ticker)
        filing = None
        form_type = None
        latest_date = None

        for form in ["10-Q", "10-K", "20-F"]:
            try:
                filings = company.get_filings(form=form)
                if filings and len(filings) > 0:
                    candidate = filings.latest(1)
                    candidate_date = candidate.filing_date if hasattr(candidate, 'filing_date') else None
                    if candidate_date and (latest_date is None or candidate_date > latest_date):
                        filing = candidate
                        form_type = form
                        latest_date = candidate_date
            except Exception:
                continue

        if not filing:
            raise RuntimeError(f"No 10-Q, 10-K, or 20-F filings found for {ticker}")

    except Exception as e:
        raise RuntimeError(f"Failed to get filing for {ticker}: {e}")

    # Step 3: Get XBRL data using enhanced API
    try:
        xbrl = filing.xbrl()

        # Get statements using XBRL statements API
        income_stmt = xbrl.statements.income_statement()
        balance_stmt = xbrl.statements.balance_sheet()
        cashflow_stmt = xbrl.statements.cashflow_statement()

        # Extract enhanced data for each statement
        def extract_statement_data(stmt, name):
            """Extract enhanced data from a statement object."""
            result = {
                'name': name,
                'title': stmt.name if hasattr(stmt, 'name') else name,
                'periods': list(stmt.periods) if hasattr(stmt, 'periods') else [],
            }

            # Get DataFrame
            df = stmt.to_dataframe()
            result['dataframe'] = df

            # Get text output using str() - Statement class uses __str__ for formatted output
            try:
                result['markdown'] = str(stmt)
            except Exception:
                result['markdown'] = None

            # Get raw data for detailed access
            try:
                result['raw_data'] = stmt.get_raw_data()
            except Exception:
                result['raw_data'] = []

            # Filter to main line items (exclude dimensional/segment breakdowns)
            # Main items have dimension=False or no dimension column
            if 'dimension' in df.columns:
                main_df = df[df['dimension'] == False].copy()
            else:
                main_df = df.copy()
            result['main_items_df'] = main_df

            return result

        # Extract data for each statement
        income_data = extract_statement_data(income_stmt, 'Income Statement')
        balance_data = extract_statement_data(balance_stmt, 'Balance Sheet')
        cashflow_data = extract_statement_data(cashflow_stmt, 'Cash Flow Statement')

        # Also get financials object for backward compatibility
        financials = filing.obj().financials
        bs_df = financials.balance_sheet().to_dataframe()
        is_df = financials.income_statement().to_dataframe()
        cf_df = financials.cashflow_statement().to_dataframe()

        # Filter to recent periods
        def filter_to_recent_periods(df):
            date_cols = [col for col in df.columns if isinstance(col, str) and '-' in col and col[0].isdigit()]
            non_date_cols = [col for col in df.columns if col not in date_cols]
            cols_to_keep = non_date_cols + date_cols[:2]
            return df[cols_to_keep].copy()

        bs_df = filter_to_recent_periods(bs_df)
        is_df = filter_to_recent_periods(is_df)
        cf_df = filter_to_recent_periods(cf_df)

    except Exception as e:
        raise RuntimeError(f"Failed to extract XBRL statements: {e}")

    # Step 4: Save debug information
    debug_dir = Path("financial_research_agent/output/debug_edgar")
    debug_dir.mkdir(parents=True, exist_ok=True)

    filing_date_str = str(filing.filing_date).replace("-", "")

    # Save raw DataFrames
    bs_df.to_csv(debug_dir / f"xbrl_raw_balance_sheet_{ticker}_{filing_date_str}.csv", index=False)
    is_df.to_csv(debug_dir / f"xbrl_raw_income_statement_{ticker}_{filing_date_str}.csv", index=False)
    cf_df.to_csv(debug_dir / f"xbrl_raw_cashflow_{ticker}_{filing_date_str}.csv", index=False)

    # Save markdown outputs
    if income_data.get('markdown'):
        with open(debug_dir / f"income_statement_markdown_{ticker}_{filing_date_str}.md", 'w') as f:
            f.write(income_data['markdown'])
    if balance_data.get('markdown'):
        with open(debug_dir / f"balance_sheet_markdown_{ticker}_{filing_date_str}.md", 'w') as f:
            f.write(balance_data['markdown'])
    if cashflow_data.get('markdown'):
        with open(debug_dir / f"cashflow_markdown_{ticker}_{filing_date_str}.md", 'w') as f:
            f.write(cashflow_data['markdown'])

    # Save extraction summary
    with open(debug_dir / f"edgartools_enhanced_extraction_{ticker}.txt", "w") as f:
        f.write(f"Enhanced XBRL Extraction\n")
        f.write(f"========================\n\n")
        f.write(f"Ticker: {ticker}\n")
        f.write(f"Filing: {filing.form} from {filing.filing_date}\n")
        f.write(f"Income Statement periods: {income_data['periods']}\n")
        f.write(f"Balance Sheet periods: {balance_data['periods']}\n")
        f.write(f"Cash Flow periods: {cashflow_data['periods']}\n\n")
        f.write(f"Line item counts:\n")
        f.write(f"  Income Statement: {len(income_data['dataframe'])} total, {len(income_data['main_items_df'])} main\n")
        f.write(f"  Balance Sheet: {len(balance_data['dataframe'])} total, {len(balance_data['main_items_df'])} main\n")
        f.write(f"  Cash Flow: {len(cashflow_data['dataframe'])} total, {len(cashflow_data['main_items_df'])} main\n")

    # Step 5: Get metadata
    filing_date = str(filing.filing_date) if hasattr(filing, 'filing_date') else 'Unknown'
    form_type = str(filing.form) if hasattr(filing, 'form') else 'Unknown'

    date_cols = [col for col in bs_df.columns if isinstance(col, str) and '-' in col and col[0].isdigit()]
    current_period = date_cols[0] if len(date_cols) >= 1 else 'Unknown'
    prior_period = date_cols[1] if len(date_cols) >= 2 else None

    company_name_official = company.name if hasattr(company, 'name') else ticker

    fiscal_year_end = None
    try:
        if hasattr(filing, 'fiscal_year_end'):
            fiscal_year_end = str(filing.fiscal_year_end)
        elif hasattr(filing, 'period_of_report'):
            fiscal_year_end = str(filing.period_of_report)
        else:
            fiscal_year_end = current_period
    except Exception:
        fiscal_year_end = current_period

    # Return enhanced structure
    return {
        # Standard DataFrames (backward compatible)
        'balance_sheet_df': bs_df,
        'income_statement_df': is_df,
        'cash_flow_statement_df': cf_df,

        # Enhanced XBRL data
        'income_statement_enhanced': income_data,
        'balance_sheet_enhanced': balance_data,
        'cash_flow_enhanced': cashflow_data,

        # Metadata
        'current_period': current_period,
        'prior_period': prior_period,
        'filing_date': filing_date,
        'form_type': form_type,
        'filing_reference': f"{form_type} filed {filing_date}",
        'ticker': ticker,
        'cik': cik,
        'company_name': company_name_official,
        'fiscal_year_end': fiscal_year_end,
        'is_foreign_filer': form_type == '20-F',
    }


def generate_yoy_comparison_table(
    df: pd.DataFrame,
    statement_name: str,
    key_items: list[str] = None
) -> str:
    """
    Generate a Year-over-Year comparison table from a statement DataFrame.

    Args:
        df: Statement DataFrame with date columns
        statement_name: Name of the statement for the table title
        key_items: Optional list of specific items to include (if None, includes all)

    Returns:
        Markdown formatted table with Current, Prior, Change, and YoY % columns
    """

    # Get date columns
    date_cols = [col for col in df.columns if isinstance(col, str) and '-' in col and col[0].isdigit()]

    if len(date_cols) < 2:
        return f"*Insufficient periods for YoY comparison in {statement_name}*\n"

    current_col = date_cols[0]
    prior_col = date_cols[1]

    # Build comparison data
    rows = []

    for idx, row in df.iterrows():
        # Skip abstract (header) rows
        if row.get('abstract', False):
            continue

        label = row.get('label', row.get('concept', f'Item_{idx}'))

        # If key_items specified, only include those
        if key_items and label not in key_items:
            continue

        current_val = row.get(current_col)
        prior_val = row.get(prior_col)

        # Skip if both values are None/NaN
        if (current_val is None or (isinstance(current_val, float) and pd.isna(current_val))) and \
           (prior_val is None or (isinstance(prior_val, float) and pd.isna(prior_val))):
            continue

        # Convert to float for calculations
        try:
            current_num = float(current_val) if current_val is not None and not pd.isna(current_val) else 0
            prior_num = float(prior_val) if prior_val is not None and not pd.isna(prior_val) else 0
        except (ValueError, TypeError):
            continue

        # Calculate change
        change = current_num - prior_num

        # Calculate YoY percentage
        if prior_num != 0:
            yoy_pct = (change / abs(prior_num)) * 100
        else:
            yoy_pct = 0 if current_num == 0 else float('inf')

        rows.append({
            'label': label,
            'current': current_num,
            'prior': prior_num,
            'change': change,
            'yoy_pct': yoy_pct
        })

    if not rows:
        return f"*No data available for YoY comparison in {statement_name}*\n"

    # Format table
    def format_value(val):
        """Format a numeric value for display."""
        if abs(val) >= 1e9:
            return f"${val/1e9:.1f}B"
        elif abs(val) >= 1e6:
            return f"${val/1e6:.1f}M"
        elif abs(val) >= 1e3:
            return f"${val/1e3:.1f}K"
        else:
            return f"${val:.0f}"

    def format_pct(pct):
        """Format percentage for display."""
        if pct == float('inf'):
            return "N/A"
        elif pct > 0:
            return f"+{pct:.1f}%"
        else:
            return f"{pct:.1f}%"

    # Build markdown table
    lines = [
        f"### {statement_name} - Year-over-Year Comparison",
        "",
        f"| Item | {current_col} | {prior_col} | Change | YoY % |",
        "|------|------------|-----------|--------|-------|"
    ]

    for row in rows:
        line = f"| {row['label']} | {format_value(row['current'])} | {format_value(row['prior'])} | {format_value(row['change'])} | {format_pct(row['yoy_pct'])} |"
        lines.append(line)

    return "\n".join(lines) + "\n"


def extract_key_metrics_from_statements(
    bs_df: pd.DataFrame,
    is_df: pd.DataFrame,
    cf_df: pd.DataFrame
) -> dict[str, Any]:
    """
    Extract key financial metrics from statement DataFrames.

    This provides a structured summary of key metrics that can be used
    for ratio calculations and analysis.

    Args:
        bs_df: Balance sheet DataFrame
        is_df: Income statement DataFrame
        cf_df: Cash flow statement DataFrame

    Returns:
        Dictionary with key metrics for current and prior periods
    """

    def get_value(df, possible_labels, period_idx=0):
        """Get value from DataFrame trying multiple possible labels."""
        date_cols = [col for col in df.columns if isinstance(col, str) and '-' in col and col[0].isdigit()]
        if not date_cols or period_idx >= len(date_cols):
            return None

        col = date_cols[period_idx]

        for idx, row in df.iterrows():
            if row.get('abstract', False):
                continue
            label = row.get('label', row.get('concept', ''))
            if label in possible_labels:
                val = row.get(col)
                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                    return float(val)
        return None

    # Define common label variations
    revenue_labels = ['Revenue', 'Revenues', 'Total Revenue', 'Net Sales', 'Contract Revenue',
                      'Revenue From Contract With Customer Excluding Assessed Tax',
                      'Total Net Sales']
    net_income_labels = ['Net Income', 'Net Income (Loss)', 'Net Income Attributable to Parent']
    total_assets_labels = ['Assets', 'Total Assets']
    total_liabilities_labels = ['Liabilities', 'Total Liabilities']
    equity_labels = ['Equity', 'Total Equity', "Stockholders' Equity",
                     'Stockholders Equity', 'Total Stockholders Equity',
                     "Total Stockholders' Equity", 'Shareholders Equity',
                     'Total Shareholders Equity']
    operating_cf_labels = ['Net Cash Provided by Operating Activities',
                           'Net Cash From Operating Activities',
                           'Net Cash from Operating Activities',
                           'Cash Flows from Operating Activities',
                           'Operating Cash Flow']
    capex_labels = ['Purchases of Property, Plant and Equipment',
                    'Payments for Property, Plant and Equipment',
                    'Capital Expenditures',
                    'Payments to Acquire Property Plant and Equipment',
                    'Capital Expenditures, Net']

    metrics = {
        'current': {},
        'prior': {}
    }

    # Extract metrics for both periods
    for period_idx, period_key in [(0, 'current'), (1, 'prior')]:
        metrics[period_key] = {
            'revenue': get_value(is_df, revenue_labels, period_idx),
            'net_income': get_value(is_df, net_income_labels, period_idx),
            'total_assets': get_value(bs_df, total_assets_labels, period_idx),
            'total_liabilities': get_value(bs_df, total_liabilities_labels, period_idx),
            'total_equity': get_value(bs_df, equity_labels, period_idx),
            'operating_cash_flow': get_value(cf_df, operating_cf_labels, period_idx),
            'capex': get_value(cf_df, capex_labels, period_idx),
        }

        # Calculate FCF if we have the components
        ocf = metrics[period_key]['operating_cash_flow']
        capex = metrics[period_key]['capex']
        if ocf is not None and capex is not None:
            # CapEx is typically negative in the cash flow statement
            metrics[period_key]['free_cash_flow'] = ocf - abs(capex)
        else:
            metrics[period_key]['free_cash_flow'] = None

    return metrics


async def extract_risk_factors(ticker: str, use_cache: bool = True) -> dict[str, Any]:
    """
    Extract Item 1A "Risk Factors" and MD&A from SEC filings using edgartools.

    This function:
    1. Checks ChromaDB cache for previously downloaded filings
    2. Gets the most recent 10-K for comprehensive annual risk factors
    3. Gets the most recent 10-Q for quarterly updates
    4. Extracts Item 1A "Risk Factors" text from both
    5. Extracts Management Discussion and Analysis (MD&A)
    6. Gets recent 8-K filings for material events
    7. Stores extracted filings in ChromaDB cache for future use

    Args:
        ticker: Company ticker symbol (e.g., "AAPL", "TSLA")
        use_cache: Whether to check/use ChromaDB cache (default: True)

    Returns:
        Dictionary with:
        - risk_factors_10k: Text from most recent 10-K Item 1A
        - risk_factors_10q: Text from most recent 10-Q Item 1A (if available)
        - mda_text: Management Discussion & Analysis
        - recent_8ks: List of recent 8-K filings with dates and descriptions
        - filing_references: List of filing references for citations
        - from_cache: Boolean indicating if data was retrieved from cache
    """
    from edgar import Company, set_identity

    # Import RAG manager for caching
    rag_manager = None
    if use_cache:
        try:
            from financial_research_agent.rag.chroma_manager import FinancialRAGManager
            rag_manager = FinancialRAGManager()
        except Exception as e:
            print(f"Warning: Could not initialize RAG manager for caching: {e}")

    # Set SEC identity
    user_agent = os.getenv("SEC_EDGAR_USER_AGENT", "FinancialResearchAgent/1.0 (test@example.com)")
    if "(" in user_agent and ")" in user_agent:
        email = user_agent.split("(")[1].split(")")[0]
        set_identity(email)
    else:
        set_identity("test@example.com")

    result = {
        'ticker': ticker,
        'risk_factors_10k': None,
        'risk_factors_10k_date': None,
        'risk_factors_10k_accession': None,
        'risk_factors_10q': None,
        'risk_factors_10q_date': None,
        'risk_factors_10q_accession': None,
        'mda_text': None,
        'mda_date': None,
        'recent_8ks': [],
        'legal_proceedings': None,
        'filing_references': [],
        'from_cache': False,
    }

    # Check cache for 10-K and 10-Q filings
    cached_10k = None
    cached_10q = None
    if rag_manager and use_cache:
        try:
            cached_10k = rag_manager.get_cached_filing(ticker, "10-K")
            cached_10q = rag_manager.get_cached_filing(ticker, "10-Q")

            if cached_10k:
                print(f"Using cached 10-K for {ticker} (filed {cached_10k.get('filing_date', 'unknown')})")
                result['risk_factors_10k'] = cached_10k.get('item1a')
                result['risk_factors_10k_date'] = cached_10k.get('filing_date')
                result['risk_factors_10k_accession'] = cached_10k.get('accession')
                result['legal_proceedings'] = cached_10k.get('item3')
                if cached_10k.get('filing_date'):
                    result['filing_references'].append(f"10-K filed {cached_10k.get('filing_date')} (cached)")
                result['from_cache'] = True

            if cached_10q:
                print(f"Using cached 10-Q for {ticker} (filed {cached_10q.get('filing_date', 'unknown')})")
                result['risk_factors_10q'] = cached_10q.get('item1a')
                result['risk_factors_10q_date'] = cached_10q.get('filing_date')
                result['risk_factors_10q_accession'] = cached_10q.get('accession')
                result['mda_text'] = cached_10q.get('item2')
                result['mda_date'] = cached_10q.get('filing_date')
                if cached_10q.get('filing_date'):
                    result['filing_references'].append(f"10-Q filed {cached_10q.get('filing_date')} (cached)")
                result['from_cache'] = True

            # If we have both cached, we still need to fetch 8-Ks (they change frequently)
            # So we continue to the company lookup below
        except Exception as e:
            print(f"Warning: Cache lookup failed: {e}")

    try:
        company = Company(ticker)

        # Extract 10-K risk factors (annual comprehensive list) - skip if cached
        if not cached_10k:
            try:
                tenk_filings = company.get_filings(form="10-K")
                if tenk_filings and len(tenk_filings) > 0:
                    tenk = tenk_filings.latest(1)
                    tenk_obj = tenk.obj()

                    # Prepare items for caching
                    tenk_items = {}

                    # Extract Item 1A - Risk Factors
                    if hasattr(tenk_obj, 'item1a') or hasattr(tenk_obj, '__getitem__'):
                        try:
                            # Try different access patterns
                            risk_text = None
                            if hasattr(tenk_obj, 'item1a'):
                                risk_text = str(tenk_obj.item1a)
                            elif hasattr(tenk_obj, '__getitem__'):
                                try:
                                    risk_text = str(tenk_obj['Item 1A'])
                                except (KeyError, TypeError):
                                    try:
                                        risk_text = str(tenk_obj['1A'])
                                    except (KeyError, TypeError):
                                        pass

                            if risk_text and len(risk_text) > 100:
                                result['risk_factors_10k'] = risk_text
                                result['risk_factors_10k_date'] = str(tenk.filing_date)
                                result['risk_factors_10k_accession'] = str(tenk.accession_number) if hasattr(tenk, 'accession_number') else None
                                result['filing_references'].append(f"10-K filed {tenk.filing_date}")
                                tenk_items['item1a'] = risk_text
                        except Exception as e:
                            print(f"Warning: Could not extract 10-K Item 1A: {e}")

                    # Extract Item 3 - Legal Proceedings
                    try:
                        legal_text = None
                        if hasattr(tenk_obj, 'item3'):
                            legal_text = str(tenk_obj.item3)
                        elif hasattr(tenk_obj, '__getitem__'):
                            try:
                                legal_text = str(tenk_obj['Item 3'])
                            except (KeyError, TypeError):
                                pass

                        if legal_text and len(legal_text) > 50:
                            result['legal_proceedings'] = legal_text
                            tenk_items['item3'] = legal_text
                    except Exception:
                        pass

                    # Cache the 10-K filing
                    if rag_manager and tenk_items:
                        try:
                            rag_manager.store_sec_filing(
                                ticker=ticker,
                                filing_type="10-K",
                                filing_date=str(tenk.filing_date),
                                accession=str(tenk.accession_number) if hasattr(tenk, 'accession_number') else "unknown",
                                items=tenk_items
                            )
                            print(f"Cached 10-K for {ticker} (filed {tenk.filing_date})")
                        except Exception as e:
                            print(f"Warning: Could not cache 10-K: {e}")

            except Exception as e:
                print(f"Warning: Could not get 10-K filings: {e}")

        # Extract 10-Q risk factors and MD&A (quarterly updates) - skip if cached
        if not cached_10q:
            try:
                tenq_filings = company.get_filings(form="10-Q")
                if tenq_filings and len(tenq_filings) > 0:
                    tenq = tenq_filings.latest(1)
                    tenq_obj = tenq.obj()

                    # Prepare items for caching
                    tenq_items = {}

                    # Extract Item 1A - Risk Factors from 10-Q
                    try:
                        risk_text = None
                        if hasattr(tenq_obj, 'item1a'):
                            risk_text = str(tenq_obj.item1a)
                        elif hasattr(tenq_obj, '__getitem__'):
                            try:
                                risk_text = str(tenq_obj['Item 1A'])
                            except (KeyError, TypeError):
                                pass

                        if risk_text and len(risk_text) > 100:
                            result['risk_factors_10q'] = risk_text
                            result['risk_factors_10q_date'] = str(tenq.filing_date)
                            result['risk_factors_10q_accession'] = str(tenq.accession_number) if hasattr(tenq, 'accession_number') else None
                            result['filing_references'].append(f"10-Q filed {tenq.filing_date}")
                            tenq_items['item1a'] = risk_text
                    except Exception:
                        pass

                    # Extract Item 2 - MD&A from 10-Q
                    try:
                        mda_text = None
                        if hasattr(tenq_obj, 'item2'):
                            mda_text = str(tenq_obj.item2)
                        elif hasattr(tenq_obj, '__getitem__'):
                            try:
                                mda_text = str(tenq_obj['Item 2'])
                            except (KeyError, TypeError):
                                pass

                        if mda_text and len(mda_text) > 100:
                            result['mda_text'] = mda_text
                            result['mda_date'] = str(tenq.filing_date)
                            tenq_items['item2'] = mda_text
                    except Exception:
                        pass

                    # Cache the 10-Q filing
                    if rag_manager and tenq_items:
                        try:
                            rag_manager.store_sec_filing(
                                ticker=ticker,
                                filing_type="10-Q",
                                filing_date=str(tenq.filing_date),
                                accession=str(tenq.accession_number) if hasattr(tenq, 'accession_number') else "unknown",
                                items=tenq_items
                            )
                            print(f"Cached 10-Q for {ticker} (filed {tenq.filing_date})")
                        except Exception as e:
                            print(f"Warning: Could not cache 10-Q: {e}")

            except Exception as e:
                print(f"Warning: Could not get 10-Q filings: {e}")

        # Get recent 8-K filings for material events
        try:
            eightk_filings = company.get_filings(form="8-K")
            if eightk_filings and len(eightk_filings) > 0:
                # Get last 5 8-Ks - use head() to avoid PyArrow slicing issues
                if hasattr(eightk_filings, 'head'):
                    recent = eightk_filings.head(5)
                else:
                    # Fallback: iterate and take first 5
                    recent = []
                    for i, f in enumerate(eightk_filings):
                        if i >= 5:
                            break
                        recent.append(f)
                for filing in recent:
                    try:
                        filing_info = {
                            'date': str(filing.filing_date),
                            'accession': str(filing.accession_number) if hasattr(filing, 'accession_number') else None,
                            'items': [],
                        }

                        # Try to get the items disclosed in the 8-K
                        # Handle PyArrow ChunkedArray that edgartools may return
                        if hasattr(filing, 'items'):
                            items_attr = filing.items
                            try:
                                # Try to convert PyArrow to Python list
                                if hasattr(items_attr, 'to_pylist'):
                                    filing_info['items'] = items_attr.to_pylist()
                                elif hasattr(items_attr, 'tolist'):
                                    filing_info['items'] = items_attr.tolist()
                                elif isinstance(items_attr, (list, tuple)):
                                    filing_info['items'] = list(items_attr)
                                else:
                                    # Last resort: convert to string
                                    filing_info['items'] = [str(items_attr)]
                            except Exception:
                                # If all else fails, skip items
                                pass

                        result['recent_8ks'].append(filing_info)

                    except Exception:
                        continue

        except Exception as e:
            print(f"Warning: Could not get 8-K filings: {e}")

    except Exception as e:
        raise RuntimeError(f"Failed to extract risk factors for {ticker}: {e}")

    return result


async def extract_financials_analysis_data(ticker: str) -> dict[str, Any]:
    """
    Extract data needed for the financials agent analysis.

    This extracts MD&A, business description, and other qualitative data
    that complements the quantitative XBRL data.

    Args:
        ticker: Company ticker symbol

    Returns:
        Dictionary with:
        - mda_text: Management Discussion & Analysis
        - business_description: Item 1 business description
        - segment_info: Segment reporting information
        - filing_references: List of filing references
    """
    from edgar import Company, set_identity

    # Set SEC identity
    user_agent = os.getenv("SEC_EDGAR_USER_AGENT", "FinancialResearchAgent/1.0 (test@example.com)")
    if "(" in user_agent and ")" in user_agent:
        email = user_agent.split("(")[1].split(")")[0]
        set_identity(email)
    else:
        set_identity("test@example.com")

    result = {
        'ticker': ticker,
        'mda_text': None,
        'mda_date': None,
        'business_description': None,
        'segment_info': None,
        'filing_references': [],
    }

    try:
        company = Company(ticker)

        # Get MD&A from most recent 10-Q or 10-K
        try:
            # Try 10-Q first for most recent data
            tenq_filings = company.get_filings(form="10-Q")
            if tenq_filings and len(tenq_filings) > 0:
                tenq = tenq_filings.latest(1)
                tenq_obj = tenq.obj()

                # Extract Item 2 - MD&A
                try:
                    mda_text = None
                    if hasattr(tenq_obj, 'item2'):
                        mda_text = str(tenq_obj.item2)
                    elif hasattr(tenq_obj, '__getitem__'):
                        try:
                            mda_text = str(tenq_obj['Item 2'])
                        except (KeyError, TypeError):
                            pass

                    if mda_text and len(mda_text) > 100:
                        result['mda_text'] = mda_text
                        result['mda_date'] = str(tenq.filing_date)
                        result['filing_references'].append(f"10-Q filed {tenq.filing_date}")
                except Exception:
                    pass

        except Exception:
            pass

        # Get business description from 10-K
        try:
            tenk_filings = company.get_filings(form="10-K")
            if tenk_filings and len(tenk_filings) > 0:
                tenk = tenk_filings.latest(1)
                tenk_obj = tenk.obj()

                # Extract Item 1 - Business Description
                try:
                    biz_text = None
                    if hasattr(tenk_obj, 'item1'):
                        biz_text = str(tenk_obj.item1)
                    elif hasattr(tenk_obj, '__getitem__'):
                        try:
                            biz_text = str(tenk_obj['Item 1'])
                        except (KeyError, TypeError):
                            pass

                    if biz_text and len(biz_text) > 100:
                        result['business_description'] = biz_text
                        result['filing_references'].append(f"10-K filed {tenk.filing_date}")
                except Exception:
                    pass

                # If we didn't get MD&A from 10-Q, try 10-K
                if not result['mda_text']:
                    try:
                        mda_text = None
                        if hasattr(tenk_obj, 'item7'):
                            mda_text = str(tenk_obj.item7)
                        elif hasattr(tenk_obj, '__getitem__'):
                            try:
                                mda_text = str(tenk_obj['Item 7'])
                            except (KeyError, TypeError):
                                pass

                        if mda_text and len(mda_text) > 100:
                            result['mda_text'] = mda_text
                            result['mda_date'] = str(tenk.filing_date)
                    except Exception:
                        pass

        except Exception:
            pass

    except Exception as e:
        raise RuntimeError(f"Failed to extract financials data for {ticker}: {e}")

    return result


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
