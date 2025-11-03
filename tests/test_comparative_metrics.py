"""
Test comparative financial metrics formatting.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from financial_research_agent.formatters import format_financial_metrics
from pydantic import BaseModel
from typing import Any


# Mock FinancialMetrics class
class FinancialMetrics(BaseModel):
    # Liquidity ratios (current period)
    current_ratio: float | None = 2.07
    quick_ratio: float | None = 1.85
    cash_ratio: float | None = 0.59

    # Solvency ratios
    debt_to_equity: float | None = 0.15
    debt_to_assets: float | None = 0.10
    equity_ratio: float | None = 0.60
    interest_coverage: float | None = None

    # Profitability ratios
    gross_profit_margin: float | None = 0.179
    operating_margin: float | None = 0.103
    net_profit_margin: float | None = 0.079
    return_on_assets: float | None = 0.064
    return_on_equity: float | None = 0.169

    # Efficiency ratios
    asset_turnover: float | None = None
    inventory_turnover: float | None = None
    receivables_turnover: float | None = None
    days_sales_outstanding: float | None = None

    # Metadata
    period: str = "Q3 2025"
    filing_date: str = "2025-10-23"
    filing_reference: str = "10-Q filed 2025-10-23"
    calculation_notes: list[str] = []
    executive_summary: str = "Tesla demonstrated solid financial performance in Q3 2025."

    # Financial statements with comparative data
    balance_sheet: dict[str, Any] = {
        'line_items': {
            'Assets Current_Current': 64530000000,
            'Assets Current_Prior': 59508000000,
            'Liabilities Current_Current': 31139000000,
            'Liabilities Current_Prior': 29467000000,
            'Cash and cash equivalents_Current': 18289000000,
            'Cash and cash equivalents_Prior': 16139000000,
            'Inventory_Current': 6838000000,
            'Inventory_Prior': 6500000000,
            'Total assets_Current': 133735000000,
            'Total assets_Prior': 122070000000,
            "Stockholders' equity_Current": 80373000000,
            "Stockholders' equity_Prior": 75387000000,
            'Long-term debt_Current': 11968000000,
            'Long-term debt_Prior': 11434000000,
        },
        'xbrl_concepts': {},
        'period_dates': {
            'current': '2025-09-30',
            'prior': '2024-12-31'
        }
    }

    income_statement: dict[str, Any] = {
        'line_items': {
            'Revenue_Current': 25182000000,
            'Revenue_Prior': 23350000000,
            'Gross profit_Current': 4509000000,
            'Gross profit_Prior': 4178000000,
            'Operating income_Current': 2724000000,
            'Operating income_Prior': 2067000000,
            'Net income_Current': 2167000000,
            'Net income_Prior': 1854000000,
        },
        'xbrl_concepts': {},
        'period_dates': {
            'current': '2025-09-30',
            'prior': '2024-12-31'
        }
    }

    cash_flow_statement: dict[str, Any] = {
        'line_items': {},
        'xbrl_concepts': {},
        'period_dates': {}
    }


def test_comparative_format():
    """Test that comparative metrics are formatted correctly."""

    print("="*80)
    print("TESTING: Comparative Financial Metrics Formatting")
    print("="*80)

    # Create mock metrics object
    metrics = FinancialMetrics()

    # Format the metrics
    result = format_financial_metrics(metrics, company_name="Tesla")

    # Check for comparative structure
    print("\n1. Checking for comparative period columns...")

    # Should have actual dates in headers
    has_current_date = '2025-09-30' in result
    has_prior_date = '2024-12-31' in result

    print(f"   Contains current date (2025-09-30): {'✅' if has_current_date else '❌'}")
    print(f"   Contains prior date (2024-12-31): {'✅' if has_prior_date else '❌'}")

    # Should have Change and % Change columns
    has_change_column = '| Change |' in result
    has_pct_change_column = '% Change' in result

    print(f"   Contains 'Change' column: {'✅' if has_change_column else '❌'}")
    print(f"   Contains '% Change' column: {'✅' if has_pct_change_column else '❌'}")

    # Should NOT have generic "Value" column
    has_value_column = '| Value |' in result and '| 2025-09-30 |' not in result

    print(f"   Does NOT use generic 'Value' column: {'✅' if not has_value_column else '❌'}")

    # Should have trend indicators
    has_trend_arrows = '↑' in result or '↓' in result or '→' in result

    print(f"   Contains trend indicators (↑/↓/→): {'✅' if has_trend_arrows else '❌'}")

    # Display sample output
    print("\n2. Sample of formatted output:")
    print("-"*80)
    lines = result.split('\n')

    # Find Liquidity Ratios section
    start_idx = next((i for i, line in enumerate(lines) if '## Liquidity Ratios' in line), 0)
    sample_lines = lines[start_idx:start_idx+15]
    print('\n'.join(sample_lines))
    print("-"*80)

    # Find Profitability Ratios section
    print("\n3. Sample of Profitability Ratios:")
    print("-"*80)
    start_idx = next((i for i, line in enumerate(lines) if '## Profitability Ratios' in line), 0)
    sample_lines = lines[start_idx:start_idx+15]
    print('\n'.join(sample_lines))
    print("-"*80)

    # Final verdict
    print("\n" + "="*80)
    all_checks = [has_current_date, has_prior_date, has_change_column,
                  has_pct_change_column, not has_value_column, has_trend_arrows]

    if all(all_checks):
        print("✅ SUCCESS: Financial metrics now show comparative analysis with actual dates!")
    else:
        print("❌ FAILURE: Some comparative features are missing")
        print(f"   Checks passed: {sum(all_checks)}/{len(all_checks)}")
    print("="*80)

    return all(all_checks)


if __name__ == "__main__":
    success = test_comparative_format()
    sys.exit(0 if success else 1)
