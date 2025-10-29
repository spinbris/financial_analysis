"""Formatting utilities for financial statements and metrics output."""

from typing import Any


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
        balance_sheet: Balance sheet line items
        income_statement: Income statement line items
        cash_flow_statement: Cash flow statement line items
        company_name: Company name
        period: Reporting period
        filing_reference: Filing reference string

    Returns:
        Formatted markdown string with tables
    """
    output = f"# Financial Statements\n\n"
    output += f"**Company:** {company_name}  \n"
    output += f"**Period:** {period}  \n"
    output += f"**Filing:** {filing_reference}  \n\n"
    output += "---\n\n"

    # Balance Sheet
    output += "## Consolidated Balance Sheet\n"
    output += "*All figures in USD (from XBRL, values in thousands unless noted)*\n\n"

    if balance_sheet:
        output += "| Line Item | Amount |\n"
        output += "|-----------|--------|\n"

        # Group balance sheet items
        current_assets = []
        noncurrent_assets = []
        current_liabilities = []
        noncurrent_liabilities = []
        equity = []
        totals = []

        for item, value in balance_sheet.items():
            item_lower = item.lower()
            formatted_value = format_currency(value) if isinstance(value, (int, float)) else str(value)
            row = (item, formatted_value)

            if any(x in item_lower for x in ["totalassets", "totalliabilities", "totalequity", "totalshareholders"]):
                totals.append(row)
            elif any(x in item_lower for x in ["currentassets", "cash", "marketable", "receivable", "inventory", "prepaid"]) and "noncurrent" not in item_lower:
                current_assets.append(row)
            elif any(x in item_lower for x in ["currentliabilities", "accountspayable", "accruedliabilities", "deferredrevenue"]) and "noncurrent" not in item_lower and "long" not in item_lower:
                current_liabilities.append(row)
            elif any(x in item_lower for x in ["equity", "commonstock", "retainedearnings", "accumulated"]):
                equity.append(row)
            elif "liabilities" in item_lower or "debt" in item_lower:
                noncurrent_liabilities.append(row)
            elif "assets" in item_lower or "property" in item_lower or "goodwill" in item_lower or "intangible" in item_lower:
                noncurrent_assets.append(row)
            else:
                # Default to assets
                noncurrent_assets.append(row)

        # Assets section
        if current_assets:
            output += "| **Current Assets** | |\n"
            for item, value in current_assets:
                output += f"| {item} | {value} |\n"

        if noncurrent_assets:
            output += "| **Non-Current Assets** | |\n"
            for item, value in noncurrent_assets:
                output += f"| {item} | {value} |\n"

        # Liabilities section
        if current_liabilities:
            output += "| **Current Liabilities** | |\n"
            for item, value in current_liabilities:
                output += f"| {item} | {value} |\n"

        if noncurrent_liabilities:
            output += "| **Non-Current Liabilities** | |\n"
            for item, value in noncurrent_liabilities:
                output += f"| {item} | {value} |\n"

        # Equity section
        if equity:
            output += "| **Shareholders' Equity** | |\n"
            for item, value in equity:
                output += f"| {item} | {value} |\n"

        # Totals
        if totals:
            output += "| | |\n"
            for item, value in totals:
                output += f"| **{item}** | **{value}** |\n"
    else:
        output += "*No balance sheet data available*\n"

    output += "\n---\n\n"

    # Income Statement
    output += "## Consolidated Statement of Operations\n"
    output += f"*Period: {period} (from XBRL, values in thousands unless noted)*\n\n"

    if income_statement:
        output += "| Line Item | Amount |\n"
        output += "|-----------|--------|\n"

        for item, value in income_statement.items():
            formatted_value = format_currency(value) if isinstance(value, (int, float)) else str(value)
            # Bold the key totals
            if any(x in item.lower() for x in ["revenue", "grossprofit", "operatingincome", "netincome", "ebit"]):
                output += f"| **{item}** | **{formatted_value}** |\n"
            else:
                output += f"| {item} | {formatted_value} |\n"
    else:
        output += "*No income statement data available*\n"

    output += "\n---\n\n"

    # Cash Flow Statement
    output += "## Consolidated Statement of Cash Flows\n"
    output += f"*Period: {period} (from XBRL, values in thousands unless noted)*\n\n"

    if cash_flow_statement:
        output += "| Line Item | Amount |\n"
        output += "|-----------|--------|\n"

        # Group by activity type
        operating = []
        investing = []
        financing = []
        other = []

        for item, value in cash_flow_statement.items():
            item_lower = item.lower()
            formatted_value = format_currency(value) if isinstance(value, (int, float)) else str(value)
            row = (item, formatted_value)

            if "operating" in item_lower:
                operating.append(row)
            elif "investing" in item_lower or "capitalexpenditure" in item_lower:
                investing.append(row)
            elif "financing" in item_lower:
                financing.append(row)
            else:
                other.append(row)

        if operating:
            output += "| **Operating Activities** | |\n"
            for item, value in operating:
                output += f"| {item} | {value} |\n"

        if investing:
            output += "| **Investing Activities** | |\n"
            for item, value in investing:
                output += f"| {item} | {value} |\n"

        if financing:
            output += "| **Financing Activities** | |\n"
            for item, value in financing:
                output += f"| {item} | {value} |\n"

        if other:
            output += "| **Other** | |\n"
            for item, value in other:
                output += f"| {item} | {value} |\n"
    else:
        output += "*No cash flow statement data available*\n"

    output += "\n---\n\n"
    output += "## Data Source\n\n"
    output += f"All financial data extracted from official SEC EDGAR filings using XBRL precision.  \n"
    output += f"**Filing Reference:** {filing_reference}  \n\n"
    output += "*Note: Values are typically in thousands of USD unless otherwise specified in the line item name.*\n"

    return output


def format_financial_metrics(metrics: Any, company_name: str) -> str:
    """Format financial metrics and ratios as markdown with tables and analysis.

    Args:
        metrics: FinancialMetrics object
        company_name: Company name

    Returns:
        Formatted markdown string with ratio tables and interpretations
    """
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
    output += "| Ratio | Value | Interpretation |\n"
    output += "|-------|-------|----------------|\n"

    output += f"| **Current Ratio** | {format_ratio(metrics.current_ratio)} | "
    output += f"{get_ratio_interpretation('current_ratio', metrics.current_ratio)} "
    if metrics.current_ratio and metrics.current_ratio >= 1.0:
        output += "Healthy - can meet short-term obligations"
    elif metrics.current_ratio:
        output += "Below target - potential liquidity concerns"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += f"| **Quick Ratio** | {format_ratio(metrics.quick_ratio)} | "
    output += f"{get_ratio_interpretation('quick_ratio', metrics.quick_ratio)} "
    if metrics.quick_ratio and metrics.quick_ratio >= 1.0:
        output += "Strong - can meet obligations without selling inventory"
    elif metrics.quick_ratio and metrics.quick_ratio >= 0.7:
        output += "Adequate for most industries"
    elif metrics.quick_ratio:
        output += "Below target"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += f"| **Cash Ratio** | {format_ratio(metrics.cash_ratio)} | "
    output += f"{get_ratio_interpretation('cash_ratio', metrics.cash_ratio)} "
    if metrics.cash_ratio and metrics.cash_ratio >= 0.2:
        output += "Adequate cash reserves"
    elif metrics.cash_ratio:
        output += "Low cash position"
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
    output += "| Ratio | Value | Interpretation |\n"
    output += "|-------|-------|----------------|\n"

    output += f"| **Debt-to-Equity** | {format_ratio(metrics.debt_to_equity)} | "
    output += f"{get_ratio_interpretation('debt_to_equity', metrics.debt_to_equity)} "
    if metrics.debt_to_equity and metrics.debt_to_equity <= 1.0:
        output += "Conservative leverage"
    elif metrics.debt_to_equity and metrics.debt_to_equity <= 2.0:
        output += "Moderate leverage"
    elif metrics.debt_to_equity:
        output += "High leverage"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += f"| **Debt-to-Assets** | {format_ratio(metrics.debt_to_assets)} | "
    output += f"{get_ratio_interpretation('debt_to_assets', metrics.debt_to_assets)} "
    if metrics.debt_to_assets and metrics.debt_to_assets <= 0.3:
        output += "Very conservative"
    elif metrics.debt_to_assets and metrics.debt_to_assets <= 0.5:
        output += "Moderate debt usage"
    elif metrics.debt_to_assets:
        output += "High debt relative to assets"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += f"| **Interest Coverage** | {format_multiplier(metrics.interest_coverage)} | "
    output += f"{get_ratio_interpretation('interest_coverage', metrics.interest_coverage)} "
    if metrics.interest_coverage and metrics.interest_coverage >= 5.0:
        output += "Excellent debt servicing capacity"
    elif metrics.interest_coverage and metrics.interest_coverage >= 2.5:
        output += "Adequate coverage"
    elif metrics.interest_coverage:
        output += "Potential debt servicing concerns"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += f"| **Equity Ratio** | {format_ratio(metrics.equity_ratio)} | "
    output += f"{get_ratio_interpretation('equity_ratio', metrics.equity_ratio)} "
    if metrics.equity_ratio and metrics.equity_ratio >= 0.5:
        output += "Strong equity position"
    elif metrics.equity_ratio and metrics.equity_ratio >= 0.3:
        output += "Moderate equity position"
    elif metrics.equity_ratio:
        output += "Weak equity position"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += "\n**Formula Reference:**\n"
    output += "- Debt-to-Equity = Total Debt ÷ Total Shareholders' Equity\n"
    output += "- Debt-to-Assets = Total Debt ÷ Total Assets\n"
    output += "- Interest Coverage = EBIT ÷ Interest Expense\n"
    output += "- Equity Ratio = Total Equity ÷ Total Assets\n\n"

    output += "---\n\n"

    # Profitability Ratios
    output += "## Profitability Ratios\n"
    output += "*Earnings generation and margins*\n\n"
    output += "| Ratio | Value | Interpretation |\n"
    output += "|-------|-------|----------------|\n"

    output += f"| **Gross Margin** | {format_percentage(metrics.gross_profit_margin)} | "
    output += f"{get_ratio_interpretation('gross_profit_margin', metrics.gross_profit_margin)} "
    if metrics.gross_profit_margin and metrics.gross_profit_margin >= 0.40:
        output += "Excellent pricing power"
    elif metrics.gross_profit_margin and metrics.gross_profit_margin >= 0.20:
        output += "Healthy margins"
    elif metrics.gross_profit_margin:
        output += "Low margins"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += f"| **Operating Margin** | {format_percentage(metrics.operating_margin)} | "
    output += f"{get_ratio_interpretation('operating_margin', metrics.operating_margin)} "
    if metrics.operating_margin and metrics.operating_margin >= 0.20:
        output += "Strong operational efficiency"
    elif metrics.operating_margin and metrics.operating_margin >= 0.10:
        output += "Moderate efficiency"
    elif metrics.operating_margin:
        output += "Low efficiency"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += f"| **Net Margin** | {format_percentage(metrics.net_profit_margin)} | "
    output += f"{get_ratio_interpretation('net_profit_margin', metrics.net_profit_margin)} "
    if metrics.net_profit_margin and metrics.net_profit_margin >= 0.15:
        output += "Excellent bottom-line profitability"
    elif metrics.net_profit_margin and metrics.net_profit_margin >= 0.08:
        output += "Healthy profitability"
    elif metrics.net_profit_margin:
        output += "Low profitability"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += f"| **Return on Assets (ROA)** | {format_percentage(metrics.return_on_assets)} | "
    output += f"{get_ratio_interpretation('return_on_assets', metrics.return_on_assets)} "
    if metrics.return_on_assets and metrics.return_on_assets >= 0.15:
        output += "Efficient asset utilization"
    elif metrics.return_on_assets and metrics.return_on_assets >= 0.08:
        output += "Moderate asset efficiency"
    elif metrics.return_on_assets:
        output += "Low asset efficiency"
    else:
        output += "Data unavailable"
    output += " |\n"

    output += f"| **Return on Equity (ROE)** | {format_percentage(metrics.return_on_equity)} | "
    output += f"{get_ratio_interpretation('return_on_equity', metrics.return_on_equity)} "
    if metrics.return_on_equity and metrics.return_on_equity >= 0.15:
        output += "Excellent shareholder returns"
    elif metrics.return_on_equity and metrics.return_on_equity >= 0.08:
        output += "Adequate returns"
    elif metrics.return_on_equity:
        output += "Low returns"
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
    output += "**Period:** {metrics.period}  \n"
    output += "**Filing Date:** {metrics.filing_date}  \n\n"
    output += "All ratios calculated from XBRL data extracted from official SEC EDGAR filings.  \n"
    output += "Ratios marked with '-' indicate insufficient data for calculation.  \n\n"

    output += "**Interpretation Guide:**\n"
    output += "- ✓ = Healthy/Strong (meets or exceeds industry standards)\n"
    output += "- ⚠ = Moderate/Adequate (acceptable but below optimal)\n"
    output += "- ✗ = Concerning/Weak (below industry standards or indicating potential issues)\n"
    output += "- - = Data unavailable or ratio not applicable\n"

    return output
