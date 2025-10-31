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
        balance_sheet: Balance sheet line items (may include _Current and _Prior suffixed keys)
        income_statement: Income statement line items (may include _Current and _Prior suffixed keys)
        cash_flow_statement: Cash flow statement line items (may include _Current and _Prior suffixed keys)
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

    # Check if we have comparative period data (keys ending with _Current and _Prior)
    has_comparative = any(k.endswith("_Current") or k.endswith("_Prior") for k in balance_sheet.keys())

    # Extract period dates if available
    current_date = balance_sheet.get("current_period_date", "Current")
    prior_date = balance_sheet.get("prior_period_date", "Prior")

    # Balance Sheet
    output += "## Consolidated Balance Sheet\n"
    output += "*All figures in USD (from XBRL, exact values)*\n\n"

    if balance_sheet:
        if has_comparative:
            output += f"| Line Item | {current_date} | {prior_date} |\n"
            output += "|-----------|-----------|----------|\n"
        else:
            output += "| Line Item | Amount |\n"
            output += "|-----------|--------|\n"

        # Group balance sheet items by category
        current_assets = []
        noncurrent_assets = []
        current_liabilities = []
        noncurrent_liabilities = []
        equity = []
        totals = []

        # Collect unique base item names (without _Current/_Prior suffix)
        base_items = set()
        for item in balance_sheet.keys():
            if item not in ["current_period_date", "prior_period_date"]:
                base_name = item.replace("_Current", "").replace("_Prior", "")
                base_items.add(base_name)

        # Process each item
        for base_item in sorted(base_items):
            item_lower = base_item.lower()

            # Get current and prior values if available
            if has_comparative:
                current_val = balance_sheet.get(f"{base_item}_Current", balance_sheet.get(base_item))
                prior_val = balance_sheet.get(f"{base_item}_Prior")
                formatted_current = format_currency(current_val) if isinstance(current_val, (int, float)) else str(current_val) if current_val is not None else "—"
                formatted_prior = format_currency(prior_val) if isinstance(prior_val, (int, float)) else str(prior_val) if prior_val is not None else "—"
                row = (base_item, formatted_current, formatted_prior)
            else:
                value = balance_sheet.get(base_item)
                formatted_value = format_currency(value) if isinstance(value, (int, float)) else str(value) if value is not None else "—"
                row = (base_item, formatted_value)

            # Categorize items - improved logic based on standard XBRL naming
            if any(x in item_lower for x in ["assets_", "assetscurrent_", "liabilities_", "liabilitiescurrent_", "stockholdersequity", "liabilitiesandstockholders"]) and not any(x in item_lower for x in ["noncurrent", "net"]):
                totals.append(row)
            elif any(x in item_lower for x in ["cashandcash", "shortterminvestment", "marketablesecurities", "accountsreceivable", "inventory", "prepaidexpense"]) or item_lower == "assetscurrent":
                current_assets.append(row)
            elif any(x in item_lower for x in ["propertyplant", "goodwill", "intangibleassets", "longterminvestment", "otherassetsnoncurrent", "assetsnoncurrent"]):
                noncurrent_assets.append(row)
            elif any(x in item_lower for x in ["accountspayable", "accruedliabilities", "deferredrevenuecurrent", "commercialpaper", "longtermdebtcurrent"]) or item_lower == "liabilitiescurrent":
                current_liabilities.append(row)
            elif any(x in item_lower for x in ["longtermdebt", "deferredrevenuenoncurrent", "otherliabilitiesnoncurrent", "liabilitiesnoncurrent"]) and "current" not in item_lower:
                noncurrent_liabilities.append(row)
            elif any(x in item_lower for x in ["commonstock", "retainedearnings", "accumulated", "stockholdersequity"]):
                equity.append(row)
            else:
                # Check if it's an asset or liability based on context
                if "assets" in item_lower:
                    noncurrent_assets.append(row)
                elif "liabilities" in item_lower or "debt" in item_lower:
                    noncurrent_liabilities.append(row)

        # Assets section
        if current_assets:
            if has_comparative:
                output += "| **Current Assets** | | |\n"
                for item, curr, prior in current_assets:
                    output += f"| {item} | {curr} | {prior} |\n"
            else:
                output += "| **Current Assets** | |\n"
                for item, value in current_assets:
                    output += f"| {item} | {value} |\n"

        if noncurrent_assets:
            if has_comparative:
                output += "| **Non-Current Assets** | | |\n"
                for item, curr, prior in noncurrent_assets:
                    output += f"| {item} | {curr} | {prior} |\n"
            else:
                output += "| **Non-Current Assets** | |\n"
                for item, value in noncurrent_assets:
                    output += f"| {item} | {value} |\n"

        # Liabilities section
        if current_liabilities:
            if has_comparative:
                output += "| **Current Liabilities** | | |\n"
                for item, curr, prior in current_liabilities:
                    output += f"| {item} | {curr} | {prior} |\n"
            else:
                output += "| **Current Liabilities** | |\n"
                for item, value in current_liabilities:
                    output += f"| {item} | {value} |\n"

        if noncurrent_liabilities:
            if has_comparative:
                output += "| **Non-Current Liabilities** | | |\n"
                for item, curr, prior in noncurrent_liabilities:
                    output += f"| {item} | {curr} | {prior} |\n"
            else:
                output += "| **Non-Current Liabilities** | |\n"
                for item, value in noncurrent_liabilities:
                    output += f"| {item} | {value} |\n"

        # Equity section
        if equity:
            if has_comparative:
                output += "| **Shareholders' Equity** | | |\n"
                for item, curr, prior in equity:
                    output += f"| {item} | {curr} | {prior} |\n"
            else:
                output += "| **Shareholders' Equity** | |\n"
                for item, value in equity:
                    output += f"| {item} | {value} |\n"

        # Totals
        if totals:
            if has_comparative:
                output += "| | | |\n"
                for item, curr, prior in totals:
                    output += f"| **{item}** | **{curr}** | **{prior}** |\n"
            else:
                output += "| | |\n"
                for item, value in totals:
                    output += f"| **{item}** | **{value}** |\n"
    else:
        output += "*No balance sheet data available*\n"

    output += "\n---\n\n"

    # Income Statement
    output += "## Consolidated Statement of Operations\n"
    output += f"*Period: {period} (from XBRL, exact values)*\n\n"

    has_comparative_income = any(k.endswith("_Current") or k.endswith("_Prior") for k in income_statement.keys())
    current_date_income = income_statement.get("current_period_date", "Current")
    prior_date_income = income_statement.get("prior_period_date", "Prior")

    if income_statement:
        if has_comparative_income:
            output += f"| Line Item | {current_date_income} | {prior_date_income} |\n"
            output += "|-----------|-----------|----------|\n"
        else:
            output += "| Line Item | Amount |\n"
            output += "|-----------|--------|\n"

        # Collect unique base item names
        base_items_income = set()
        for item in income_statement.keys():
            if item not in ["current_period_date", "prior_period_date"]:
                base_name = item.replace("_Current", "").replace("_Prior", "")
                base_items_income.add(base_name)

        # Process each item in order
        for base_item in sorted(base_items_income):
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
    output += f"*Period: {period} (from XBRL, exact values)*\n\n"

    has_comparative_cf = any(k.endswith("_Current") or k.endswith("_Prior") for k in cash_flow_statement.keys())
    current_date_cf = cash_flow_statement.get("current_period_date", "Current")
    prior_date_cf = cash_flow_statement.get("prior_period_date", "Prior")

    if cash_flow_statement:
        if has_comparative_cf:
            output += f"| Line Item | {current_date_cf} | {prior_date_cf} |\n"
            output += "|-----------|-----------|----------|\n"
        else:
            output += "| Line Item | Amount |\n"
            output += "|-----------|--------|\n"

        # Group by activity type
        operating = []
        investing = []
        financing = []
        other = []

        # Collect unique base item names
        base_items_cf = set()
        for item in cash_flow_statement.keys():
            if item not in ["current_period_date", "prior_period_date"]:
                base_name = item.replace("_Current", "").replace("_Prior", "")
                base_items_cf.add(base_name)

        # Process each item and categorize
        for base_item in sorted(base_items_cf):
            item_lower = base_item.lower()

            if has_comparative_cf:
                current_val = cash_flow_statement.get(f"{base_item}_Current", cash_flow_statement.get(base_item))
                prior_val = cash_flow_statement.get(f"{base_item}_Prior")
                formatted_current = format_currency(current_val) if isinstance(current_val, (int, float)) else str(current_val) if current_val is not None else "—"
                formatted_prior = format_currency(prior_val) if isinstance(prior_val, (int, float)) else str(prior_val) if prior_val is not None else "—"
                row = (base_item, formatted_current, formatted_prior)
            else:
                value = cash_flow_statement.get(base_item)
                formatted_value = format_currency(value) if isinstance(value, (int, float)) else str(value) if value is not None else "—"
                row = (base_item, formatted_value)

            if "operating" in item_lower or "netincomeloss" in item_lower or "depreciation" in item_lower or "sharebasedcompensation" in item_lower or "increasedecrease" in item_lower:
                operating.append(row)
            elif "investing" in item_lower or "capitalexpenditure" in item_lower or "paymentstoaquire" in item_lower or "proceedsfromsale" in item_lower:
                investing.append(row)
            elif "financing" in item_lower or "dividend" in item_lower or "repurchase" in item_lower or "debtissuance" in item_lower or "debt" in item_lower:
                financing.append(row)
            else:
                other.append(row)

        if operating:
            if has_comparative_cf:
                output += "| **Operating Activities** | | |\n"
                for item, curr, prior in operating:
                    output += f"| {item} | {curr} | {prior} |\n"
            else:
                output += "| **Operating Activities** | |\n"
                for item, value in operating:
                    output += f"| {item} | {value} |\n"

        if investing:
            if has_comparative_cf:
                output += "| **Investing Activities** | | |\n"
                for item, curr, prior in investing:
                    output += f"| {item} | {curr} | {prior} |\n"
            else:
                output += "| **Investing Activities** | |\n"
                for item, value in investing:
                    output += f"| {item} | {value} |\n"

        if financing:
            if has_comparative_cf:
                output += "| **Financing Activities** | | |\n"
                for item, curr, prior in financing:
                    output += f"| {item} | {curr} | {prior} |\n"
            else:
                output += "| **Financing Activities** | |\n"
                for item, value in financing:
                    output += f"| {item} | {value} |\n"

        if other:
            if has_comparative_cf:
                output += "| **Other** | | |\n"
                for item, curr, prior in other:
                    output += f"| {item} | {curr} | {prior} |\n"
            else:
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
