"""Formatting utilities for financial statements and metrics output."""

from typing import Any
import pandas as pd
from great_tables import GT, md, html


def format_currency(value: float | int | None) -> str:
    """Format a number as currency with thousands separators.

    Args:
        value: Numeric value to format

    Returns:
        Formatted string like "$1,234,567" or "N/A" if None
    """
    if value is None:
        return "N/A"
    return f"${value:,.0f}"


def format_percentage(value: float | None, decimals: int = 1) -> str:
    """Format a decimal as percentage.

    Args:
        value: Decimal value (e.g., 0.443 for 44.3%)
        decimals: Number of decimal places

    Returns:
        Formatted string like "44.3%" or "N/A" if None
    """
    if value is None:
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def format_ratio(value: float | None, decimals: int = 2) -> str:
    """Format a ratio value.

    Args:
        value: Ratio value
        decimals: Number of decimal places

    Returns:
        Formatted string like "1.05" or "N/A" if None
    """
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def format_multiplier(value: float | None, decimals: int = 1) -> str:
    """Format a multiplier value (e.g., turnover ratios).

    Args:
        value: Multiplier value
        decimals: Number of decimal places

    Returns:
        Formatted string like "36.4x" or "N/A" if None
    """
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}x"


def get_ratio_interpretation(ratio_name: str, value: float | None) -> str:
    """Get interpretation symbol for a ratio value.

    Args:
        ratio_name: Name of the ratio
        value: Ratio value

    Returns:
        Interpretation symbol: ✓ (healthy), ⚠ (moderate), ✗ (concerning), or - (N/A)
    """
    if value is None:
        return "-"

    # Liquidity ratios (higher is better)
    if ratio_name == "current_ratio":
        if value >= 1.5:
            return "✓"
        elif value >= 1.0:
            return "⚠"
        else:
            return "✗"

    if ratio_name == "quick_ratio":
        if value >= 1.0:
            return "✓"
        elif value >= 0.7:
            return "⚠"
        else:
            return "✗"

    if ratio_name == "cash_ratio":
        if value >= 0.3:
            return "✓"
        elif value >= 0.15:
            return "⚠"
        else:
            return "✗"

    # Solvency ratios
    if ratio_name == "debt_to_equity":
        if value <= 1.0:
            return "✓"
        elif value <= 2.0:
            return "⚠"
        else:
            return "✗"

    if ratio_name == "debt_to_assets":
        if value <= 0.3:
            return "✓"
        elif value <= 0.5:
            return "⚠"
        else:
            return "✗"

    if ratio_name == "interest_coverage":
        if value >= 5.0:
            return "✓"
        elif value >= 2.5:
            return "⚠"
        else:
            return "✗"

    if ratio_name == "equity_ratio":
        if value >= 0.5:
            return "✓"
        elif value >= 0.3:
            return "⚠"
        else:
            return "✗"

    # Profitability ratios (context-dependent, general guidelines)
    if ratio_name in ["gross_profit_margin", "operating_margin", "net_profit_margin"]:
        if value >= 0.20:
            return "✓"
        elif value >= 0.10:
            return "⚠"
        else:
            return "✗"

    if ratio_name in ["return_on_assets", "return_on_equity"]:
        if value >= 0.15:
            return "✓"
        elif value >= 0.08:
            return "⚠"
        else:
            return "✗"

    # Efficiency ratios (higher is generally better)
    if ratio_name in ["asset_turnover", "inventory_turnover", "receivables_turnover"]:
        if value >= 2.0:
            return "✓"
        elif value >= 1.0:
            return "⚠"
        else:
            return "✗"

    if ratio_name == "days_sales_outstanding":
        # Lower is better for DSO
        if value <= 45:
            return "✓"
        elif value <= 60:
            return "⚠"
        else:
            return "✗"

    return "-"


def format_financial_statements(
    balance_sheet: dict[str, Any],
    income_statement: dict[str, Any],
    cash_flow_statement: dict[str, Any],
    company_name: str,
    period: str,
    filing_reference: str,
) -> str:
    """Format complete financial statements as markdown with tables.

    Args:
        balance_sheet: Balance sheet line items (may include _Current and _Prior suffixed keys)
                      Can be either flat dict or {'line_items': {...}, 'xbrl_concepts': {...}}
        income_statement: Income statement line items (may include _Current and _Prior suffixed keys)
                         Can be either flat dict or {'line_items': {...}, 'xbrl_concepts': {...}}
        cash_flow_statement: Cash flow statement line items (may include _Current and _Prior suffixed keys)
                            Can be either flat dict or {'line_items': {...}, 'xbrl_concepts': {...}}
        company_name: Company name
        period: Reporting period
        filing_reference: Filing reference string

    Returns:
        Formatted markdown string with tables
    """
    # Handle new structure with line_items and xbrl_concepts
    # If the dict has 'line_items' key, extract it; otherwise use the dict as-is
    bs_items = balance_sheet.get('line_items', balance_sheet) if isinstance(balance_sheet, dict) else balance_sheet
    is_items = income_statement.get('line_items', income_statement) if isinstance(income_statement, dict) else income_statement
    cf_items = cash_flow_statement.get('line_items', cash_flow_statement) if isinstance(cash_flow_statement, dict) else cash_flow_statement

    # Get XBRL concepts if available (for future use in citations)
    bs_concepts = balance_sheet.get('xbrl_concepts', {}) if isinstance(balance_sheet, dict) and 'xbrl_concepts' in balance_sheet else {}
    is_concepts = income_statement.get('xbrl_concepts', {}) if isinstance(income_statement, dict) and 'xbrl_concepts' in income_statement else {}
    cf_concepts = cash_flow_statement.get('xbrl_concepts', {}) if isinstance(cash_flow_statement, dict) and 'xbrl_concepts' in cash_flow_statement else {}

    # Get actual period dates if available (from new structure)
    bs_dates = balance_sheet.get('period_dates', {}) if isinstance(balance_sheet, dict) and 'period_dates' in balance_sheet else {}
    is_dates = income_statement.get('period_dates', {}) if isinstance(income_statement, dict) and 'period_dates' in income_statement else {}
    cf_dates = cash_flow_statement.get('period_dates', {}) if isinstance(cash_flow_statement, dict) and 'period_dates' in cash_flow_statement else {}

    # Use the extracted line_items for processing
    balance_sheet = bs_items
    income_statement = is_items
    cash_flow_statement = cf_items
    output = f"# Financial Statements\n\n"
    output += f"**Company:** {company_name}  \n"
    output += f"**Period:** {period}  \n"
    output += f"**Filing:** {filing_reference}  \n\n"
    output += "---\n\n"

    # Check if we have comparative period data (keys ending with _Current and _Prior)
    has_comparative = any(k.endswith("_Current") or k.endswith("_Prior") for k in balance_sheet.keys())

    # Extract period dates - prefer actual dates from period_dates, fallback to old keys
    current_date = bs_dates.get('current', balance_sheet.get("current_period_date", "Current"))
    prior_date = bs_dates.get('prior', balance_sheet.get("prior_period_date", "Prior"))

    # Balance Sheet
    output += "## Consolidated Balance Sheet\n"
    output += "*All figures in USD (from XBRL, exact values)*\n"
    output += "*Items displayed in SEC XBRL presentation order (totals and subtotals in correct hierarchy)*\n\n"

    if balance_sheet:
        if has_comparative:
            output += f"| Line Item | {current_date} | {prior_date} |\n"
            output += "|:----------|----------:|----------:|\n"
        else:
            output += "| Line Item | Amount |\n"
            output += "|:----------|-------:|\n"

        # Collect unique base item names (without _Current/_Prior suffix)
        # Preserve insertion order from edgartools DataFrame (XBRL presentation order)
        base_items = []
        seen = set()
        for item in balance_sheet.keys():
            if item not in ["current_period_date", "prior_period_date"]:
                base_name = item.replace("_Current", "").replace("_Prior", "")
                if base_name not in seen:
                    base_items.append(base_name)
                    seen.add(base_name)

        # Display each item in XBRL presentation order WITHOUT categorization
        # This preserves the SEC-mandated hierarchy where totals appear in correct position
        for base_item in base_items:
            # Get current and prior values if available
            if has_comparative:
                current_val = balance_sheet.get(f"{base_item}_Current", balance_sheet.get(base_item))
                prior_val = balance_sheet.get(f"{base_item}_Prior")
                formatted_current = format_currency(current_val) if isinstance(current_val, (int, float)) else str(current_val) if current_val is not None else "—"
                formatted_prior = format_currency(prior_val) if isinstance(prior_val, (int, float)) else str(prior_val) if prior_val is not None else "—"

                # Bold key totals for readability
                if any(x in base_item.lower() for x in ["total", "liabilitiesandstockholders"]):
                    output += f"| **{base_item}** | **{formatted_current}** | **{formatted_prior}** |\n"
                else:
                    output += f"| {base_item} | {formatted_current} | {formatted_prior} |\n"
            else:
                value = balance_sheet.get(base_item)
                formatted_value = format_currency(value) if isinstance(value, (int, float)) else str(value) if value is not None else "—"

                # Bold key totals for readability
                if "total" in base_item.lower():
                    output += f"| **{base_item}** | **{formatted_value}** |\n"
                else:
                    output += f"| {base_item} | {formatted_value} |\n"
    else:
        output += "*No balance sheet data available*\n"

    output += "\n---\n\n"

    # Income Statement
    output += "## Consolidated Statement of Operations\n"
    output += f"*Period: {period} (from XBRL, exact values)*\n\n"

    has_comparative_income = any(k.endswith("_Current") or k.endswith("_Prior") for k in income_statement.keys())
    current_date_income = is_dates.get('current', income_statement.get("current_period_date", "Current"))
    prior_date_income = is_dates.get('prior', income_statement.get("prior_period_date", "Prior"))

    if income_statement:
        if has_comparative_income:
            output += f"| Line Item | {current_date_income} | {prior_date_income} |\n"
            output += "|:----------|----------:|----------:|\n"
        else:
            output += "| Line Item | Amount |\n"
            output += "|:----------|-------:|\n"

        # Collect unique base item names (preserving XBRL presentation order)
        base_items_income = []
        seen_income = set()
        for item in income_statement.keys():
            if item not in ["current_period_date", "prior_period_date"]:
                base_name = item.replace("_Current", "").replace("_Prior", "")
                if base_name not in seen_income:
                    base_items_income.append(base_name)
                    seen_income.add(base_name)

        # Process each item in XBRL presentation order
        for base_item in base_items_income:
            if has_comparative_income:
                current_val = income_statement.get(f"{base_item}_Current", income_statement.get(base_item))
                prior_val = income_statement.get(f"{base_item}_Prior")
                formatted_current = format_currency(current_val) if isinstance(current_val, (int, float)) else str(current_val) if current_val is not None else "—"
                formatted_prior = format_currency(prior_val) if isinstance(prior_val, (int, float)) else str(prior_val) if prior_val is not None else "—"

                # Bold key totals
                if any(x in base_item.lower() for x in ["revenue", "grossprofit", "operatingincome", "netincome", "ebit"]):
                    output += f"| **{base_item}** | **{formatted_current}** | **{formatted_prior}** |\n"
                else:
                    output += f"| {base_item} | {formatted_current} | {formatted_prior} |\n"
            else:
                value = income_statement.get(base_item)
                formatted_value = format_currency(value) if isinstance(value, (int, float)) else str(value) if value is not None else "—"
                # Bold key totals
                if any(x in base_item.lower() for x in ["revenue", "grossprofit", "operatingincome", "netincome", "ebit"]):
                    output += f"| **{base_item}** | **{formatted_value}** |\n"
                else:
                    output += f"| {base_item} | {formatted_value} |\n"
    else:
        output += "*No income statement data available*\n"

    output += "\n---\n\n"

    # Cash Flow Statement
    output += "## Consolidated Statement of Cash Flows\n"
    output += f"*Period: {period} (from XBRL, exact values)*\n"
    output += "*Items displayed in SEC XBRL presentation order (totals in correct hierarchy)*\n\n"

    has_comparative_cf = any(k.endswith("_Current") or k.endswith("_Prior") for k in cash_flow_statement.keys())
    current_date_cf = cf_dates.get('current', cash_flow_statement.get("current_period_date", "Current"))
    prior_date_cf = cf_dates.get('prior', cash_flow_statement.get("prior_period_date", "Prior"))

    if cash_flow_statement:
        if has_comparative_cf:
            output += f"| Line Item | {current_date_cf} | {prior_date_cf} |\n"
            output += "|:----------|----------:|----------:|\n"
        else:
            output += "| Line Item | Amount |\n"
            output += "|:----------|-------:|\n"

        # Collect unique base item names (preserving XBRL presentation order)
        base_items_cf = []
        seen_cf = set()
        for item in cash_flow_statement.keys():
            if item not in ["current_period_date", "prior_period_date"]:
                base_name = item.replace("_Current", "").replace("_Prior", "")
                if base_name not in seen_cf:
                    base_items_cf.append(base_name)
                    seen_cf.add(base_name)

        # Display each item in XBRL presentation order WITHOUT categorization
        for base_item in base_items_cf:
            if has_comparative_cf:
                current_val = cash_flow_statement.get(f"{base_item}_Current", cash_flow_statement.get(base_item))
                prior_val = cash_flow_statement.get(f"{base_item}_Prior")
                formatted_current = format_currency(current_val) if isinstance(current_val, (int, float)) else str(current_val) if current_val is not None else "—"
                formatted_prior = format_currency(prior_val) if isinstance(prior_val, (int, float)) else str(prior_val) if prior_val is not None else "—"

                # Bold key totals
                if any(x in base_item.lower() for x in ["total", "net", "cashequivalents"]):
                    output += f"| **{base_item}** | **{formatted_current}** | **{formatted_prior}** |\n"
                else:
                    output += f"| {base_item} | {formatted_current} | {formatted_prior} |\n"
            else:
                value = cash_flow_statement.get(base_item)
                formatted_value = format_currency(value) if isinstance(value, (int, float)) else str(value) if value is not None else "—"

                # Bold key totals
                if any(x in base_item.lower() for x in ["total", "net", "cashequivalents"]):
                    output += f"| **{base_item}** | **{formatted_value}** |\n"
                else:
                    output += f"| {base_item} | {formatted_value} |\n"
    else:
        output += "*No cash flow statement data available*\n"

    output += "\n---\n\n"
    output += "## Data Source\n\n"
    output += f"All financial data extracted from official SEC EDGAR filings using XBRL precision.  \n"
    output += f"**Filing Reference:** {filing_reference}  \n\n"
    output += "*Note: Values are typically in thousands of USD unless otherwise specified in the line item name.*\n"

    return output


def format_financial_statements_gt(
    balance_sheet_df: pd.DataFrame,
    income_statement_df: pd.DataFrame,
    cash_flow_statement_df: pd.DataFrame,
    company_name: str,
    current_period: str,
    prior_period: str | None,
    filing_reference: str,
) -> str:
    """
    Format complete financial statements as markdown from DataFrames.

    This is the modernized version using DataFrames directly.
    Significantly more concise and maintainable than the original 220-line manual formatter.

    Args:
        balance_sheet_df: Balance sheet DataFrame from edgartools
        income_statement_df: Income statement DataFrame from edgartools
        cash_flow_statement_df: Cash flow statement DataFrame from edgartools
        company_name: Company name
        current_period: Current period date (e.g., "2025-06-28")
        prior_period: Prior period date (e.g., "2024-09-28") or None
        filing_reference: Filing reference string

    Returns:
        Formatted markdown string with professionally styled tables
    """
    output = f"# Financial Statements\n\n"
    output += f"**Company:** {company_name}  \n"
    output += f"**Period:** {current_period}  \n"
    output += f"**Filing:** {filing_reference}  \n\n"
    output += "---\n\n"

    # Helper function to format a statement DataFrame as markdown
    def format_statement(df: pd.DataFrame, title: str, subtitle: str, bold_keywords: list[str]) -> str:
        """Format a single financial statement as markdown table."""
        # Filter out abstract rows (headers)
        df_filtered = df[~df.get('abstract', False)].copy()

        # Get date columns (numeric data columns)
        date_cols = [col for col in df_filtered.columns if isinstance(col, str) and '-' in col and col[0].isdigit()]

        if not date_cols or len(df_filtered) == 0:
            return f"## {title}\n{subtitle}\n\n*No data available*\n\n---\n\n"

        # Build markdown table manually
        markdown = f"## {title}\n{subtitle}\n\n"

        # Header row
        markdown += "| Line Item | " + " | ".join(date_cols) + " |\n"
        # Alignment row (left for line items, right for numbers)
        markdown += "|:----------|" + "----------:|" * len(date_cols) + "\n"

        # Data rows
        for idx, row in df_filtered.iterrows():
            label = row.get('label', row.get('concept', f'Item_{idx}'))

            # Check if this row should be bold (contains keywords)
            is_bold = any(keyword.lower() in str(label).lower() for keyword in bold_keywords)

            # Format label
            label_text = f"**{label}**" if is_bold else label

            # Format values
            values = []
            for col in date_cols:
                val = row.get(col)
                if pd.isna(val):
                    formatted_val = "—"
                else:
                    # Format as currency (handle both numeric and string types)
                    if isinstance(val, (int, float)):
                        formatted_val = f"${val:,.0f}"
                    else:
                        # Already a string, use as-is
                        formatted_val = str(val)
                    if is_bold:
                        formatted_val = f"**{formatted_val}**"
                values.append(formatted_val)

            markdown += f"| {label_text} | " + " | ".join(values) + " |\n"

        markdown += "\n---\n\n"
        return markdown

    # Format each statement
    output += format_statement(
        balance_sheet_df,
        "Consolidated Balance Sheet",
        "*All figures in USD (from XBRL, exact values)*  \n*Items displayed in SEC XBRL presentation order*",
        ["total", "liabilities", "equity", "assets"]
    )

    output += format_statement(
        income_statement_df,
        "Consolidated Statement of Operations",
        f"*Period: {current_period} (from XBRL, exact values)*",
        ["revenue", "gross profit", "operating income", "net income", "ebit"]
    )

    output += format_statement(
        cash_flow_statement_df,
        "Consolidated Statement of Cash Flows",
        f"*Period: {current_period} (from XBRL, exact values)*  \n*Items displayed in SEC XBRL presentation order*",
        ["total", "net", "cash equivalents", "operating activities", "investing activities", "financing activities"]
    )

    output += "## Data Source\n\n"
    output += f"All financial data extracted from official SEC EDGAR filings using XBRL precision.  \n"
    output += f"**Filing Reference:** {filing_reference}  \n\n"
    output += "*Note: Values are typically in thousands of USD unless otherwise specified in the line item name.*\n"

    return output


def _calculate_ratio_from_data(balance_sheet: dict, income_statement: dict, cash_flow: dict,
                                ratio_name: str, period_suffix: str) -> float | None:
    """Calculate a specific ratio from raw financial data for a given period.

    Args:
        balance_sheet: Balance sheet data dict
        income_statement: Income statement data dict
        cash_flow: Cash flow data dict
        ratio_name: Name of the ratio to calculate
        period_suffix: Either '_Current' or '_Prior'

    Returns:
        Calculated ratio value or None if cannot be calculated
    """
    # Extract line_items if using new structure, otherwise use dict directly
    bs = balance_sheet.get('line_items', balance_sheet) if isinstance(balance_sheet, dict) and 'line_items' in balance_sheet else balance_sheet
    inc = income_statement.get('line_items', income_statement) if isinstance(income_statement, dict) and 'line_items' in income_statement else income_statement
    cf = cash_flow.get('line_items', cash_flow) if isinstance(cash_flow, dict) and 'line_items' in cash_flow else cash_flow

    # Helper to find value by searching for key patterns
    def find_value(data: dict, patterns: list[str], suffix: str) -> float | None:
        for pattern in patterns:
            # Try exact match with suffix
            key_with_suffix = f"{pattern}{suffix}"
            if key_with_suffix in data:
                val = data[key_with_suffix]
                if isinstance(val, (int, float)) and val != 0:
                    return float(val)

            # Try case-insensitive search
            for key in data.keys():
                if pattern.lower() in key.lower() and key.endswith(suffix):
                    val = data[key]
                    if isinstance(val, (int, float)) and val != 0:
                        return float(val)
        return None

    try:
        if ratio_name == 'current_ratio':
            current_assets = find_value(bs, ['Assets Current', 'Current Assets', 'AssetsCurrent'], period_suffix)
            current_liabilities = find_value(bs, ['Liabilities Current', 'Current Liabilities', 'LiabilitiesCurrent'], period_suffix)
            if current_assets and current_liabilities:
                return current_assets / current_liabilities

        elif ratio_name == 'quick_ratio':
            current_assets = find_value(bs, ['Assets Current', 'Current Assets', 'AssetsCurrent'], period_suffix)
            inventory = find_value(bs, ['Inventory', 'InventoryNet'], period_suffix) or 0
            current_liabilities = find_value(bs, ['Liabilities Current', 'Current Liabilities', 'LiabilitiesCurrent'], period_suffix)
            if current_assets and current_liabilities:
                return (current_assets - inventory) / current_liabilities

        elif ratio_name == 'cash_ratio':
            cash = find_value(bs, ['Cash and cash equivalents', 'Cash and Cash Equivalents', 'CashAndCashEquivalents'], period_suffix)
            current_liabilities = find_value(bs, ['Liabilities Current', 'Current Liabilities', 'LiabilitiesCurrent'], period_suffix)
            if cash and current_liabilities:
                return cash / current_liabilities

        elif ratio_name == 'debt_to_equity':
            total_debt = find_value(bs, ['Long-term debt', 'Long-Term Debt', 'LongTermDebt', 'Total debt', 'Debt'], period_suffix)
            equity = find_value(bs, ["Stockholders' equity", 'Stockholders Equity', 'StockholdersEquity', 'Total equity'], period_suffix)
            if total_debt and equity:
                return total_debt / equity

        elif ratio_name == 'debt_to_assets':
            total_debt = find_value(bs, ['Long-term debt', 'Long-Term Debt', 'LongTermDebt', 'Total debt', 'Debt'], period_suffix)
            total_assets = find_value(bs, ['Total assets', 'Assets', 'Total Assets'], period_suffix)
            if total_debt and total_assets:
                return total_debt / total_assets

        elif ratio_name == 'equity_ratio':
            equity = find_value(bs, ["Stockholders' equity", 'Stockholders Equity', 'StockholdersEquity', 'Total equity'], period_suffix)
            total_assets = find_value(bs, ['Total assets', 'Assets', 'Total Assets'], period_suffix)
            if equity and total_assets:
                return equity / total_assets

        elif ratio_name == 'gross_profit_margin':
            gross_profit = find_value(inc, ['Gross profit', 'Gross Profit', 'GrossProfit'], period_suffix)
            revenue = find_value(inc, ['Revenue', 'Total revenue', 'Revenues'], period_suffix)
            if gross_profit and revenue:
                return gross_profit / revenue

        elif ratio_name == 'operating_margin':
            operating_income = find_value(inc, ['Operating income', 'Operating Income', 'OperatingIncome'], period_suffix)
            revenue = find_value(inc, ['Revenue', 'Total revenue', 'Revenues'], period_suffix)
            if operating_income and revenue:
                return operating_income / revenue

        elif ratio_name == 'net_profit_margin':
            net_income = find_value(inc, ['Net income', 'Net Income', 'NetIncome'], period_suffix)
            revenue = find_value(inc, ['Revenue', 'Total revenue', 'Revenues'], period_suffix)
            if net_income and revenue:
                return net_income / revenue

        elif ratio_name == 'return_on_assets':
            net_income = find_value(inc, ['Net income', 'Net Income', 'NetIncome'], period_suffix)
            total_assets = find_value(bs, ['Total assets', 'Assets', 'Total Assets'], period_suffix)
            if net_income and total_assets:
                return net_income / total_assets

        elif ratio_name == 'return_on_equity':
            net_income = find_value(inc, ['Net income', 'Net Income', 'NetIncome'], period_suffix)
            equity = find_value(bs, ["Stockholders' equity", 'Stockholders Equity', 'StockholdersEquity', 'Total equity'], period_suffix)
            if net_income and equity:
                return net_income / equity

    except (ZeroDivisionError, TypeError):
        pass

    return None


def format_financial_metrics(metrics: Any, company_name: str) -> str:
    """Format financial metrics and ratios as markdown with tables and analysis.

    Args:
        metrics: FinancialMetrics object
        company_name: Company name

    Returns:
        Formatted markdown string with ratio tables and interpretations
    """
    # Extract period dates from the balance sheet data
    bs_data = metrics.balance_sheet
    bs_dates = {}

    # Try to get date information from multiple possible formats
    if isinstance(bs_data, dict):
        # New structure with period_dates
        if 'period_dates' in bs_data:
            bs_dates = bs_data['period_dates']
        # Old structure with explicit date keys
        elif 'current_period_date' in bs_data:
            bs_dates = {
                'current': bs_data.get('current_period_date', 'Current'),
                'prior': bs_data.get('prior_period_date', 'Prior')
            }
        # Check for _Current/_Prior suffixed keys
        elif any(k.endswith('_Current') for k in bs_data.keys()):
            # Extract dates from the data structure
            current_keys = [k for k in bs_data.keys() if k.endswith('_Current')]
            prior_keys = [k for k in bs_data.keys() if k.endswith('_Prior')]
            if current_keys and prior_keys:
                bs_dates = {
                    'current': bs_data.get('current_period_date', metrics.period),
                    'prior': bs_data.get('prior_period_date', 'Prior Period')
                }

    current_date = bs_dates.get('current', metrics.period if metrics.period else 'Current')
    prior_date = bs_dates.get('prior', 'Prior')

    # Check if we have _Current/_Prior suffixed data (old format) or comparative data
    has_comparative = (prior_date not in ['Prior', 'Prior Period', None]) or \
                      (isinstance(bs_data, dict) and any(k.endswith('_Prior') for k in bs_data.keys()))

    output = f"# Financial Metrics & Ratio Analysis\n\n"
    output += f"**Company:** {company_name}  \n"
    output += f"**Period:** {metrics.period}  \n"
    output += f"**Analysis Date:** {metrics.filing_date}  \n"
    output += f"**Source Data:** See `03_financial_statements.md`  \n\n"
    output += "---\n\n"

    # Executive Summary
    output += "## Executive Summary\n\n"
    output += f"{metrics.executive_summary}\n\n"
    output += "---\n\n"

    # Liquidity Ratios
    output += "## Liquidity Ratios\n"
    output += "*Ability to meet short-term obligations*\n\n"

    if has_comparative:
        # Calculate prior period ratios
        current_ratio_prior = _calculate_ratio_from_data(metrics.balance_sheet, metrics.income_statement,
                                                         metrics.cash_flow_statement, 'current_ratio', '_Prior')
        quick_ratio_prior = _calculate_ratio_from_data(metrics.balance_sheet, metrics.income_statement,
                                                        metrics.cash_flow_statement, 'quick_ratio', '_Prior')
        cash_ratio_prior = _calculate_ratio_from_data(metrics.balance_sheet, metrics.income_statement,
                                                       metrics.cash_flow_statement, 'cash_ratio', '_Prior')

        output += f"| Ratio | {current_date} | {prior_date} | Change | % Change |\n"
        output += "|-------|------------|------------|--------|----------|\n"

        # Current Ratio
        change = (metrics.current_ratio - current_ratio_prior) if metrics.current_ratio and current_ratio_prior else None
        pct_change = (change / current_ratio_prior * 100) if change and current_ratio_prior else None
        trend = "↑" if change and change > 0 else "↓" if change and change < 0 else "→"
        output += f"| **Current Ratio** | {format_ratio(metrics.current_ratio)} | {format_ratio(current_ratio_prior)} | "
        output += f"{format_ratio(change) if change else '—'} | "
        output += f"{format_percentage(pct_change/100) if pct_change else '—'} {trend} |\n"

        # Quick Ratio
        change = (metrics.quick_ratio - quick_ratio_prior) if metrics.quick_ratio and quick_ratio_prior else None
        pct_change = (change / quick_ratio_prior * 100) if change and quick_ratio_prior else None
        trend = "↑" if change and change > 0 else "↓" if change and change < 0 else "→"
        output += f"| **Quick Ratio** | {format_ratio(metrics.quick_ratio)} | {format_ratio(quick_ratio_prior)} | "
        output += f"{format_ratio(change) if change else '—'} | "
        output += f"{format_percentage(pct_change/100) if pct_change else '—'} {trend} |\n"

        # Cash Ratio
        change = (metrics.cash_ratio - cash_ratio_prior) if metrics.cash_ratio and cash_ratio_prior else None
        pct_change = (change / cash_ratio_prior * 100) if change and cash_ratio_prior else None
        trend = "↑" if change and change > 0 else "↓" if change and change < 0 else "→"
        output += f"| **Cash Ratio** | {format_ratio(metrics.cash_ratio)} | {format_ratio(cash_ratio_prior)} | "
        output += f"{format_ratio(change) if change else '—'} | "
        output += f"{format_percentage(pct_change/100) if pct_change else '—'} {trend} |\n"

    else:
        # Single period format (fallback)
        output += "| Ratio | Value | Interpretation |\n"
        output += "|-------|-------|----------------|\n"

        output += f"| **Current Ratio** | {format_ratio(metrics.current_ratio)} | "
        if metrics.current_ratio and metrics.current_ratio >= 1.0:
            output += "✓ Healthy"
        elif metrics.current_ratio:
            output += "⚠ Below target"
        else:
            output += "Data unavailable"
        output += " |\n"

        output += f"| **Quick Ratio** | {format_ratio(metrics.quick_ratio)} | "
        if metrics.quick_ratio and metrics.quick_ratio >= 1.0:
            output += "✓ Strong"
        elif metrics.quick_ratio and metrics.quick_ratio >= 0.7:
            output += "✓ Adequate"
        elif metrics.quick_ratio:
            output += "⚠ Below target"
        else:
            output += "Data unavailable"
        output += " |\n"

        output += f"| **Cash Ratio** | {format_ratio(metrics.cash_ratio)} | "
        if metrics.cash_ratio and metrics.cash_ratio >= 0.2:
            output += "✓ Adequate"
        elif metrics.cash_ratio:
            output += "⚠ Low"
        else:
            output += "Data unavailable"
        output += " |\n"

    output += "\n**Formula Reference:**\n"
    output += "- Current Ratio = Current Assets ÷ Current Liabilities\n"
    output += "- Quick Ratio = (Current Assets - Inventory) ÷ Current Liabilities\n"
    output += "- Cash Ratio = Cash & Equivalents ÷ Current Liabilities\n\n"

    output += "---\n\n"

    # Solvency Ratios
    output += "## Solvency Ratios\n"
    output += "*Long-term financial stability and debt capacity*\n\n"

    if has_comparative:
        # Calculate prior period ratios
        debt_to_equity_prior = _calculate_ratio_from_data(metrics.balance_sheet, metrics.income_statement,
                                                          metrics.cash_flow_statement, 'debt_to_equity', '_Prior')
        debt_to_assets_prior = _calculate_ratio_from_data(metrics.balance_sheet, metrics.income_statement,
                                                          metrics.cash_flow_statement, 'debt_to_assets', '_Prior')
        equity_ratio_prior = _calculate_ratio_from_data(metrics.balance_sheet, metrics.income_statement,
                                                        metrics.cash_flow_statement, 'equity_ratio', '_Prior')

        output += f"| Ratio | {current_date} | {prior_date} | Change | % Change |\n"
        output += "|-------|------------|------------|--------|----------|\n"

        # Debt-to-Equity
        change = (metrics.debt_to_equity - debt_to_equity_prior) if metrics.debt_to_equity and debt_to_equity_prior else None
        pct_change = (change / debt_to_equity_prior * 100) if change and debt_to_equity_prior else None
        trend = "↓" if change and change < 0 else "↑" if change and change > 0 else "→"  # Lower is better for debt ratios
        output += f"| **Debt-to-Equity** | {format_ratio(metrics.debt_to_equity)} | {format_ratio(debt_to_equity_prior)} | "
        output += f"{format_ratio(change) if change else '—'} | "
        output += f"{format_percentage(pct_change/100) if pct_change else '—'} {trend} |\n"

        # Debt-to-Assets
        change = (metrics.debt_to_assets - debt_to_assets_prior) if metrics.debt_to_assets and debt_to_assets_prior else None
        pct_change = (change / debt_to_assets_prior * 100) if change and debt_to_assets_prior else None
        trend = "↓" if change and change < 0 else "↑" if change and change > 0 else "→"
        output += f"| **Debt-to-Assets** | {format_ratio(metrics.debt_to_assets)} | {format_ratio(debt_to_assets_prior)} | "
        output += f"{format_ratio(change) if change else '—'} | "
        output += f"{format_percentage(pct_change/100) if pct_change else '—'} {trend} |\n"

        # Equity Ratio
        change = (metrics.equity_ratio - equity_ratio_prior) if metrics.equity_ratio and equity_ratio_prior else None
        pct_change = (change / equity_ratio_prior * 100) if change and equity_ratio_prior else None
        trend = "↑" if change and change > 0 else "↓" if change and change < 0 else "→"  # Higher is better
        output += f"| **Equity Ratio** | {format_ratio(metrics.equity_ratio)} | {format_ratio(equity_ratio_prior)} | "
        output += f"{format_ratio(change) if change else '—'} | "
        output += f"{format_percentage(pct_change/100) if pct_change else '—'} {trend} |\n"

    else:
        # Single period format (fallback)
        output += "| Ratio | Value | Interpretation |\n"
        output += "|-------|-------|----------------|\n"

        output += f"| **Debt-to-Equity** | {format_ratio(metrics.debt_to_equity)} | "
        if metrics.debt_to_equity and metrics.debt_to_equity <= 1.0:
            output += "✓ Conservative"
        elif metrics.debt_to_equity and metrics.debt_to_equity <= 2.0:
            output += "Moderate"
        elif metrics.debt_to_equity:
            output += "⚠ High leverage"
        else:
            output += "Data unavailable"
        output += " |\n"

        output += f"| **Debt-to-Assets** | {format_ratio(metrics.debt_to_assets)} | "
        if metrics.debt_to_assets and metrics.debt_to_assets <= 0.3:
            output += "✓ Very conservative"
        elif metrics.debt_to_assets and metrics.debt_to_assets <= 0.5:
            output += "✓ Moderate"
        elif metrics.debt_to_assets:
            output += "⚠ High debt"
        else:
            output += "Data unavailable"
        output += " |\n"

        output += f"| **Equity Ratio** | {format_ratio(metrics.equity_ratio)} | "
        if metrics.equity_ratio and metrics.equity_ratio >= 0.5:
            output += "✓ Strong"
        elif metrics.equity_ratio and metrics.equity_ratio >= 0.3:
            output += "Moderate"
        elif metrics.equity_ratio:
            output += "⚠ Weak"
        else:
            output += "Data unavailable"
        output += " |\n"

    output += "\n**Formula Reference:**\n"
    output += "- Debt-to-Equity = Total Debt ÷ Total Shareholders' Equity\n"
    output += "- Debt-to-Assets = Total Debt ÷ Total Assets\n"
    output += "- Equity Ratio = Total Equity ÷ Total Assets\n\n"

    output += "---\n\n"

    # Profitability Ratios
    output += "## Profitability Ratios\n"
    output += "*Earnings generation and margins*\n\n"

    if has_comparative:
        # Calculate prior period ratios
        gross_margin_prior = _calculate_ratio_from_data(metrics.balance_sheet, metrics.income_statement,
                                                         metrics.cash_flow_statement, 'gross_profit_margin', '_Prior')
        operating_margin_prior = _calculate_ratio_from_data(metrics.balance_sheet, metrics.income_statement,
                                                             metrics.cash_flow_statement, 'operating_margin', '_Prior')
        net_margin_prior = _calculate_ratio_from_data(metrics.balance_sheet, metrics.income_statement,
                                                       metrics.cash_flow_statement, 'net_profit_margin', '_Prior')
        roa_prior = _calculate_ratio_from_data(metrics.balance_sheet, metrics.income_statement,
                                                metrics.cash_flow_statement, 'return_on_assets', '_Prior')
        roe_prior = _calculate_ratio_from_data(metrics.balance_sheet, metrics.income_statement,
                                                metrics.cash_flow_statement, 'return_on_equity', '_Prior')

        output += f"| Ratio | {current_date} | {prior_date} | Change | % Change |\n"
        output += "|-------|------------|------------|--------|----------|\n"

        # Gross Margin
        change = (metrics.gross_profit_margin - gross_margin_prior) if metrics.gross_profit_margin and gross_margin_prior else None
        pct_change = (change / gross_margin_prior * 100) if change and gross_margin_prior else None
        trend = "↑" if change and change > 0 else "↓" if change and change < 0 else "→"
        output += f"| **Gross Margin** | {format_percentage(metrics.gross_profit_margin)} | {format_percentage(gross_margin_prior)} | "
        output += f"{format_percentage(change) if change else '—'} | "
        output += f"{format_percentage(pct_change/100) if pct_change else '—'} {trend} |\n"

        # Operating Margin
        change = (metrics.operating_margin - operating_margin_prior) if metrics.operating_margin and operating_margin_prior else None
        pct_change = (change / operating_margin_prior * 100) if change and operating_margin_prior else None
        trend = "↑" if change and change > 0 else "↓" if change and change < 0 else "→"
        output += f"| **Operating Margin** | {format_percentage(metrics.operating_margin)} | {format_percentage(operating_margin_prior)} | "
        output += f"{format_percentage(change) if change else '—'} | "
        output += f"{format_percentage(pct_change/100) if pct_change else '—'} {trend} |\n"

        # Net Margin
        change = (metrics.net_profit_margin - net_margin_prior) if metrics.net_profit_margin and net_margin_prior else None
        pct_change = (change / net_margin_prior * 100) if change and net_margin_prior else None
        trend = "↑" if change and change > 0 else "↓" if change and change < 0 else "→"
        output += f"| **Net Margin** | {format_percentage(metrics.net_profit_margin)} | {format_percentage(net_margin_prior)} | "
        output += f"{format_percentage(change) if change else '—'} | "
        output += f"{format_percentage(pct_change/100) if pct_change else '—'} {trend} |\n"

        # ROA
        change = (metrics.return_on_assets - roa_prior) if metrics.return_on_assets and roa_prior else None
        pct_change = (change / roa_prior * 100) if change and roa_prior else None
        trend = "↑" if change and change > 0 else "↓" if change and change < 0 else "→"
        output += f"| **Return on Assets (ROA)** | {format_percentage(metrics.return_on_assets)} | {format_percentage(roa_prior)} | "
        output += f"{format_percentage(change) if change else '—'} | "
        output += f"{format_percentage(pct_change/100) if pct_change else '—'} {trend} |\n"

        # ROE
        change = (metrics.return_on_equity - roe_prior) if metrics.return_on_equity and roe_prior else None
        pct_change = (change / roe_prior * 100) if change and roe_prior else None
        trend = "↑" if change and change > 0 else "↓" if change and change < 0 else "→"
        output += f"| **Return on Equity (ROE)** | {format_percentage(metrics.return_on_equity)} | {format_percentage(roe_prior)} | "
        output += f"{format_percentage(change) if change else '—'} | "
        output += f"{format_percentage(pct_change/100) if pct_change else '—'} {trend} |\n"

    else:
        # Single period format (fallback)
        output += "| Ratio | Value | Interpretation |\n"
        output += "|-------|-------|----------------|\n"

        output += f"| **Gross Margin** | {format_percentage(metrics.gross_profit_margin)} | "
        if metrics.gross_profit_margin and metrics.gross_profit_margin >= 0.40:
            output += "✓ Excellent"
        elif metrics.gross_profit_margin and metrics.gross_profit_margin >= 0.20:
            output += "✓ Healthy"
        elif metrics.gross_profit_margin:
            output += "⚠ Low"
        else:
            output += "Data unavailable"
        output += " |\n"

        output += f"| **Operating Margin** | {format_percentage(metrics.operating_margin)} | "
        if metrics.operating_margin and metrics.operating_margin >= 0.20:
            output += "✓ Strong"
        elif metrics.operating_margin and metrics.operating_margin >= 0.10:
            output += "✓ Moderate"
        elif metrics.operating_margin:
            output += "⚠ Low"
        else:
            output += "Data unavailable"
        output += " |\n"

        output += f"| **Net Margin** | {format_percentage(metrics.net_profit_margin)} | "
        if metrics.net_profit_margin and metrics.net_profit_margin >= 0.15:
            output += "✓ Excellent"
        elif metrics.net_profit_margin and metrics.net_profit_margin >= 0.08:
            output += "✓ Healthy"
        elif metrics.net_profit_margin:
            output += "⚠ Low"
        else:
            output += "Data unavailable"
        output += " |\n"

        output += f"| **Return on Assets (ROA)** | {format_percentage(metrics.return_on_assets)} | "
        if metrics.return_on_assets and metrics.return_on_assets >= 0.15:
            output += "✓ Efficient"
        elif metrics.return_on_assets and metrics.return_on_assets >= 0.08:
            output += "✓ Moderate"
        elif metrics.return_on_assets:
            output += "⚠ Low"
        else:
            output += "Data unavailable"
        output += " |\n"

        output += f"| **Return on Equity (ROE)** | {format_percentage(metrics.return_on_equity)} | "
        if metrics.return_on_equity and metrics.return_on_equity >= 0.15:
            output += "✓ Excellent"
        elif metrics.return_on_equity and metrics.return_on_equity >= 0.08:
            output += "✓ Adequate"
        elif metrics.return_on_equity:
            output += "⚠ Low"
        else:
            output += "Data unavailable"
        output += " |\n"

    output += "\n**Formula Reference:**\n"
    output += "- Gross Margin = Gross Profit ÷ Revenue\n"
    output += "- Operating Margin = Operating Income ÷ Revenue\n"
    output += "- Net Margin = Net Income ÷ Revenue\n"
    output += "- ROA = Net Income ÷ Total Assets\n"
    output += "- ROE = Net Income ÷ Shareholders' Equity\n\n"

    output += "---\n\n"

    # Efficiency Ratios
    output += "## Efficiency Ratios\n"
    output += "*Asset and working capital management*\n\n"
    output += "| Ratio | Value | Interpretation |\n"
    output += "|-------|-------|----------------|\n"

    output += f"| **Asset Turnover** | {format_multiplier(metrics.asset_turnover)} | "
    output += f"{get_ratio_interpretation('asset_turnover', metrics.asset_turnover)} "
    if metrics.asset_turnover and metrics.asset_turnover >= 1.5:
        output += "Efficient revenue generation"
    elif metrics.asset_turnover and metrics.asset_turnover >= 0.5:
        output += "Typical for capital-intensive business"
    elif metrics.asset_turnover:
        output += "Low asset efficiency"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += f"| **Inventory Turnover** | {format_multiplier(metrics.inventory_turnover)} | "
    output += f"{get_ratio_interpretation('inventory_turnover', metrics.inventory_turnover)} "
    if metrics.inventory_turnover and metrics.inventory_turnover >= 10.0:
        output += "Excellent inventory management"
    elif metrics.inventory_turnover and metrics.inventory_turnover >= 5.0:
        output += "Healthy turnover"
    elif metrics.inventory_turnover:
        output += "Slow-moving inventory"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += f"| **Receivables Turnover** | {format_multiplier(metrics.receivables_turnover)} | "
    output += f"{get_ratio_interpretation('receivables_turnover', metrics.receivables_turnover)} "
    if metrics.receivables_turnover and metrics.receivables_turnover >= 8.0:
        output += "Fast collection"
    elif metrics.receivables_turnover and metrics.receivables_turnover >= 4.0:
        output += "Standard collection"
    elif metrics.receivables_turnover:
        output += "Slow collection"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += f"| **Days Sales Outstanding** | {format_ratio(metrics.days_sales_outstanding, 0)} days | "
    output += f"{get_ratio_interpretation('days_sales_outstanding', metrics.days_sales_outstanding)} "
    if metrics.days_sales_outstanding and metrics.days_sales_outstanding <= 45:
        output += "Fast collection cycle"
    elif metrics.days_sales_outstanding and metrics.days_sales_outstanding <= 60:
        output += "Standard collection period"
    elif metrics.days_sales_outstanding:
        output += "Extended collection period"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += "\n**Formula Reference:**\n"
    output += "- Asset Turnover = Revenue ÷ Average Total Assets\n"
    output += "- Inventory Turnover = Cost of Goods Sold ÷ Average Inventory\n"
    output += "- Receivables Turnover = Revenue ÷ Average Accounts Receivable\n"
    output += "- Days Sales Outstanding = (A/R ÷ Revenue) × Number of Days in Period\n\n"

    output += "---\n\n"

    # Calculation Notes
    if metrics.calculation_notes:
        output += "## Calculation Notes\n\n"
        for note in metrics.calculation_notes:
            output += f"- {note}\n"
        output += "\n---\n\n"

    # Data Source
    output += "## Data Source & Verification\n\n"
    output += f"**Filing Reference:** {metrics.filing_reference}  \n"
    output += f"**Period:** {metrics.period}  \n"
    output += f"**Filing Date:** {metrics.filing_date}  \n\n"
    output += "All ratios calculated from XBRL data extracted from official SEC EDGAR filings.  \n"
    output += "Ratios marked with '-' indicate insufficient data for calculation.  \n\n"

    output += "**Interpretation Guide:**\n"
    output += "- ✓ = Healthy/Strong (meets or exceeds industry standards)\n"
    output += "- ⚠ = Moderate/Adequate (acceptable but below optimal)\n"
    output += "- ✗ = Concerning/Weak (below industry standards or indicating potential issues)\n"
    output += "- - = Data unavailable or ratio not applicable\n"

    return output
