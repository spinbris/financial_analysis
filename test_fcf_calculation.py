"""
Test script to verify FCF calculation fields are populated correctly.

This tests:
1. FinancialMetrics model accepts FCF fields
2. FCF calculation section formats correctly
"""

from financial_research_agent.agents.financial_metrics_agent import FinancialMetrics
from financial_research_agent.formatters import format_financial_metrics

print("=== Testing FCF Calculation Pipeline ===\n")

# Create mock FinancialMetrics with FCF data
print("Creating FinancialMetrics object with FCF fields...")

# Apple Q3 FY2025 data from 03_financial_statements.md
# OCF: $81,754,000,000
# CapEx: $9,473,000,000
# FCF: $72,281,000,000

mock_metrics = FinancialMetrics(
    executive_summary="Apple Q3 FY2025 shows strong cash generation.",
    current_ratio=0.87,
    quick_ratio=0.83,
    cash_ratio=0.47,
    debt_to_equity=2.76,
    debt_to_assets=0.28,
    interest_coverage=None,
    equity_ratio=0.20,
    gross_profit_margin=0.468,
    operating_margin=0.321,
    net_profit_margin=0.269,
    return_on_assets=0.255,
    return_on_equity=1.284,
    asset_turnover=0.9,
    inventory_turnover=28.2,
    receivables_turnover=10.9,
    days_sales_outstanding=34,
    period="Q3 FY2025",
    filing_date="2025-08-01",
    filing_reference="10-Q filed 2025-08-01, Accession: 0000320193-25-000073",
    company_name="Apple Inc.",
    sic_code=3571,
    calculation_notes=[],
    # Balance Sheet Verification
    balance_sheet_verified=True,
    balance_sheet_verification_error=0.0000,
    balance_sheet_total_assets=331495000000,
    balance_sheet_total_liabilities=265665000000,
    balance_sheet_total_equity=65830000000,
    # FCF Calculation (NEW FIELDS)
    fcf_operating_cash_flow=81754000000,
    fcf_capital_expenditures=9473000000,
    fcf_free_cash_flow=72281000000,
    # Financial statements (minimal mock data)
    balance_sheet={'Assets_Current': 331495000000},
    income_statement={'Revenue_Current': 313695000000},
    cash_flow_statement={'NetCashProvidedByOperatingActivities_Current': 81754000000}
)

print("✓ FinancialMetrics object created with FCF fields\n")

# Format the metrics and check for FCF section
print("Formatting metrics to markdown...")
formatted = format_financial_metrics(mock_metrics, "Apple Inc.")

# Check that FCF section exists
if "## Free Cash Flow Calculation" in formatted:
    print("✓ Free Cash Flow Calculation section found in formatted output\n")

    # Extract just the FCF section
    start_idx = formatted.find("## Free Cash Flow Calculation")
    end_idx = formatted.find("## Data Source")
    fcf_section = formatted[start_idx:end_idx]

    print("Free Cash Flow Calculation Section:")
    print("=" * 70)
    print(fcf_section)
    print("=" * 70)

    # Verify the calculation is correct
    if "$81,754,000,000" in fcf_section and "$9,473,000,000" in fcf_section and "$72,281,000,000" in fcf_section:
        print("\n✓ FCF calculation values are correct")
        print("  OCF: $81.754B")
        print("  CapEx: $9.473B")
        print("  FCF: $72.281B")
    else:
        print("\n✗ FCF calculation values not found or incorrect")
else:
    print("✗ Free Cash Flow Calculation section NOT found in formatted output")

print("\n✅ Test complete!")
print("\nNext step: Run full analysis to verify LLM populates these fields correctly")
