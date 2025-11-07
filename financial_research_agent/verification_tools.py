"""
Deterministic verification tools for financial data extraction.

These tools run immediately after extraction to ensure data quality and completeness,
catching issues early before they reach the final verification stage.
"""

from typing import Any


def verify_financial_data_completeness(statements_data: dict[str, Any]) -> dict[str, Any]:
    """
    Verify that extracted financial data is complete and valid.

    Checks:
    1. All three statements are present (balance sheet, income statement, cash flow)
    2. Both Current and Prior period data exists
    3. Balance sheet equation holds: Assets = Liabilities + All Equity Components
    4. Minimum expected line items are present
    5. No missing critical values

    Args:
        statements_data: Dictionary containing balance_sheet, income_statement, cash_flow_statement

    Returns:
        Dictionary with:
        - 'valid': bool - Whether data passed all checks
        - 'errors': list[str] - Critical errors that must be fixed
        - 'warnings': list[str] - Issues that should be addressed
        - 'stats': dict - Statistics about the extracted data
    """
    errors = []
    warnings = []
    stats = {}

    # Check 1: All three statements present
    required_statements = ['balance_sheet', 'income_statement', 'cash_flow_statement']
    for stmt in required_statements:
        if stmt not in statements_data or not statements_data[stmt]:
            errors.append(f"Missing {stmt.replace('_', ' ')}")

    if errors:
        return {
            'valid': False,
            'errors': errors,
            'warnings': warnings,
            'stats': stats
        }

    # Extract line items from new structure or use directly
    bs = statements_data['balance_sheet'].get('line_items', statements_data['balance_sheet']) if isinstance(statements_data['balance_sheet'], dict) else statements_data['balance_sheet']
    inc = statements_data['income_statement'].get('line_items', statements_data['income_statement']) if isinstance(statements_data['income_statement'], dict) else statements_data['income_statement']
    cf = statements_data['cash_flow_statement'].get('line_items', statements_data['cash_flow_statement']) if isinstance(statements_data['cash_flow_statement'], dict) else statements_data['cash_flow_statement']

    # Check 2: Comparative period data exists
    bs_has_current = any(k.endswith('_Current') for k in bs.keys())
    bs_has_prior = any(k.endswith('_Prior') for k in bs.keys())
    inc_has_current = any(k.endswith('_Current') for k in inc.keys())
    inc_has_prior = any(k.endswith('_Prior') for k in inc.keys())
    cf_has_current = any(k.endswith('_Current') for k in cf.keys())
    cf_has_prior = any(k.endswith('_Prior') for k in cf.keys())

    if not bs_has_current:
        errors.append("Balance sheet missing Current period data")
    if not bs_has_prior:
        warnings.append("Balance sheet missing Prior period data for comparative analysis")
    if not inc_has_current:
        errors.append("Income statement missing Current period data")
    if not inc_has_prior:
        warnings.append("Income statement missing Prior period data for comparative analysis")
    if not cf_has_current:
        errors.append("Cash flow statement missing Current period data")
    if not cf_has_prior:
        warnings.append("Cash flow statement missing Prior period data for comparative analysis")

    # Check 3: Balance sheet equation
    # Extract key line items
    assets_key = None
    liabilities_key = None
    equity_key = None
    minority_key = None
    redeemable_key = None

    # For cases where Total Liabilities is missing, track individual liability components
    current_liabilities_key = None
    liability_component_keys = []

    for key in bs.keys():
        key_lower = key.lower()
        # Check if this is a Current period key (case-insensitive)
        if not key.endswith('_Current'):
            continue

        if 'total' in key_lower and 'asset' in key_lower:
            # Exclude "Total Liabilities and Stockholders' Equity" when looking for assets
            if 'liabilit' not in key_lower:
                assets_key = key
        elif 'total' in key_lower and 'liabilit' in key_lower:
            # CRITICAL: Exclude "Total Liabilities and Stockholders' Equity"
            # We want ONLY "Total Liabilities" (without equity)
            if 'equity' not in key_lower and 'stockholder' not in key_lower and 'shareholder' not in key_lower:
                # Check if this is "Total Current Liabilities" (we'll need this for Amazon-style balance sheets)
                if 'current' in key_lower:
                    current_liabilities_key = key
                else:
                    liabilities_key = key
        elif ('stockholder' in key_lower or 'shareholder' in key_lower) and 'equity' in key_lower:
            # Exclude "Total Liabilities and Stockholders' Equity" when looking for equity
            if 'liabilit' not in key_lower:
                equity_key = key
        elif 'minority' in key_lower and 'interest' in key_lower:
            minority_key = key
        elif 'redeemable' in key_lower and 'noncontrolling' in key_lower:
            redeemable_key = key
        # Collect non-current liability components (for companies like Amazon that don't have "Total Liabilities")
        elif any(term in key_lower for term in ['lease liabilit', 'long term debt', 'long-term debt', 'other non current liabilit', 'other liabilit']) and 'current' not in key_lower:
            # Only add if it's a liability line and not already counted as current liabilities
            liability_component_keys.append(key)

    # If no "Total Liabilities" found but we have "Total Current Liabilities" and other components,
    # calculate total liabilities by summing components
    if not liabilities_key and current_liabilities_key and liability_component_keys and equity_key:
        total_liabilities = bs[current_liabilities_key]
        for component_key in liability_component_keys:
            total_liabilities += bs[component_key]
        # Create synthetic check
        if assets_key:
            assets = bs[assets_key]
            equity = bs[equity_key]
            minority = bs.get(minority_key, 0) if minority_key else 0
            redeemable = bs.get(redeemable_key, 0) if redeemable_key else 0

            # Check if it balances
            total_check1 = total_liabilities + equity
            diff1 = abs(assets - total_check1)
            tolerance = assets * 0.001  # 0.1%

            if diff1 <= tolerance:
                stats['balance_sheet_verified'] = True
            else:
                # Try adding minority and redeemable
                total_equity = equity + minority + redeemable
                total = total_liabilities + total_equity
                diff = abs(assets - total)

                if diff > tolerance:
                    # Build component breakdown for error message
                    component_details = f"  Total Current Liabilities: ${bs[current_liabilities_key]:,.0f}\n"
                    for comp_key in liability_component_keys:
                        comp_name = comp_key.replace('_Current', '')
                        component_details += f"  {comp_name}: ${bs[comp_key]:,.0f}\n"

                    errors.append(
                        f"Balance sheet equation does not balance:\n"
                        f"  Assets: ${assets:,.0f}\n"
                        f"{component_details}"
                        f"  Calculated Total Liabilities: ${total_liabilities:,.0f}\n"
                        f"  Stockholders' Equity: ${equity:,.0f}\n"
                        f"  Minority Interest: ${minority:,.0f}\n"
                        f"  Redeemable NCI: ${redeemable:,.0f}\n"
                        f"  Total L+E: ${total:,.0f}\n"
                        f"  Difference: ${diff:,.0f} ({diff/assets*100:.3f}% of Assets)\n"
                        f"  Exceeds tolerance of ${tolerance:,.0f} (0.1%)"
                    )
                else:
                    stats['balance_sheet_verified'] = True
    elif assets_key and liabilities_key and equity_key:
        assets = bs[assets_key]
        liabilities = bs[liabilities_key]
        equity = bs[equity_key]
        minority = bs.get(minority_key, 0) if minority_key else 0
        redeemable = bs.get(redeemable_key, 0) if redeemable_key else 0

        # Total Liabilities already includes all liabilities
        # The equation is: Assets = Total Liabilities + Total Equity
        # Where Total Equity = Stockholders' Equity + Minority Interest + Redeemable NCI
        # BUT: If equity_key is "Total Stockholders' Equity" it may already include minority/redeemable
        # Check if liabilities + equity alone balances first (most common case)
        total_check1 = liabilities + equity
        diff1 = abs(assets - total_check1)
        tolerance = assets * 0.001  # 0.1%

        # If that balances, equity already includes all equity components
        if diff1 <= tolerance:
            stats['balance_sheet_verified'] = True
        else:
            # Try adding minority and redeemable separately
            total_equity = equity + minority + redeemable
            total = liabilities + total_equity
            diff = abs(assets - total)

            if diff > tolerance:
                errors.append(
                    f"Balance sheet equation does not balance:\n"
                    f"  Assets: ${assets:,.0f}\n"
                    f"  Liabilities: ${liabilities:,.0f}\n"
                    f"  Stockholders' Equity: ${equity:,.0f}\n"
                    f"  Minority Interest: ${minority:,.0f}\n"
                    f"  Redeemable NCI: ${redeemable:,.0f}\n"
                    f"  Total L+E: ${total:,.0f}\n"
                    f"  Difference: ${diff:,.0f} ({diff/assets*100:.3f}% of Assets)\n"
                    f"  Exceeds tolerance of ${tolerance:,.0f} (0.1%)"
                )
            else:
                stats['balance_sheet_verified'] = True
    else:
        warnings.append(f"Could not verify balance sheet equation - missing key line items (Assets: {assets_key}, Liabilities: {liabilities_key}, Equity: {equity_key})")

    # Check 4: Minimum line item counts
    # Count unique base items (without _Current/_Prior suffix)
    bs_items = set(k.replace('_Current', '').replace('_Prior', '') for k in bs.keys())
    inc_items = set(k.replace('_Current', '').replace('_Prior', '') for k in inc.keys())
    cf_items = set(k.replace('_Current', '').replace('_Prior', '') for k in cf.keys())

    stats['balance_sheet_line_items'] = len(bs_items)
    stats['income_statement_line_items'] = len(inc_items)
    stats['cash_flow_line_items'] = len(cf_items)
    stats['total_line_items'] = len(bs_items) + len(inc_items) + len(cf_items)

    # Expected minimums (based on typical 10-Q/10-K)
    if len(bs_items) < 15:
        warnings.append(f"Balance sheet has only {len(bs_items)} line items (expected 15+). Data may be incomplete.")
    if len(inc_items) < 10:
        warnings.append(f"Income statement has only {len(inc_items)} line items (expected 10+). Data may be incomplete.")
    if len(cf_items) < 15:
        warnings.append(f"Cash flow statement has only {len(cf_items)} line items (expected 15+). Data may be incomplete.")

    # Check 5: Critical line items present
    critical_bs_items = ['total assets', 'total liabilities', 'equity']
    critical_inc_items = ['revenue', 'net income']
    critical_cf_items = ['operating activities', 'investing activities', 'financing activities']

    for critical in critical_bs_items:
        if not any(critical in k.lower() for k in bs_items):
            errors.append(f"Balance sheet missing critical item: {critical}")

    for critical in critical_inc_items:
        if not any(critical in k.lower() for k in inc_items):
            errors.append(f"Income statement missing critical item: {critical}")

    for critical in critical_cf_items:
        if not any(critical in k.lower() for k in cf_items):
            errors.append(f"Cash flow statement missing critical item: {critical}")

    # Final validity check
    valid = len(errors) == 0

    return {
        'valid': valid,
        'errors': errors,
        'warnings': warnings,
        'stats': stats
    }


def format_verification_report(verification: dict[str, Any]) -> str:
    """Format verification results as a readable report."""
    output = "# Financial Data Verification Report\n\n"

    if verification['valid']:
        output += "**Status:** ✅ PASSED - Data is complete and valid\n\n"
    else:
        output += "**Status:** ❌ FAILED - Critical errors found\n\n"

    # Statistics
    if verification['stats']:
        output += "## Data Statistics\n\n"
        stats = verification['stats']
        if 'balance_sheet_line_items' in stats:
            output += f"- Balance Sheet: {stats['balance_sheet_line_items']} line items\n"
        if 'income_statement_line_items' in stats:
            output += f"- Income Statement: {stats['income_statement_line_items']} line items\n"
        if 'cash_flow_line_items' in stats:
            output += f"- Cash Flow Statement: {stats['cash_flow_line_items']} line items\n"
        if 'total_line_items' in stats:
            output += f"- **Total: {stats['total_line_items']} line items**\n"
        if stats.get('balance_sheet_verified'):
            output += "- ✅ Balance sheet equation verified\n"
        output += "\n"

    # Errors
    if verification['errors']:
        output += "## Critical Errors\n\n"
        for i, error in enumerate(verification['errors'], 1):
            output += f"{i}. {error}\n\n"

    # Warnings
    if verification['warnings']:
        output += "## Warnings\n\n"
        for i, warning in enumerate(verification['warnings'], 1):
            output += f"{i}. {warning}\n\n"

    if verification['valid'] and not verification['warnings']:
        output += "## Summary\n\n"
        output += "All validation checks passed. The extracted financial data is:\n"
        output += "- ✅ Complete with all three financial statements\n"
        output += "- ✅ Includes both Current and Prior period data\n"
        output += "- ✅ Balance sheet equation holds\n"
        output += "- ✅ Contains all critical line items\n"
        output += "- ✅ Meets minimum line item count expectations\n"

    return output
