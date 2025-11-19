"""
Test script to verify balance sheet verification flows through the entire pipeline.

This tests:
1. EdgarToolsWrapper extracts verification data correctly
2. FinancialMetrics model can hold verification data
3. format_financial_metrics displays verification section
"""

from financial_research_agent.tools.edgartools_wrapper import EdgarToolsWrapper
from financial_research_agent.agents.financial_metrics_agent import FinancialMetrics
from financial_research_agent.formatters import format_financial_metrics

print("=== Testing Balance Sheet Verification Pipeline ===\n")

# Step 1: Extract verification data using wrapper
print("Step 1: Extracting verification data for Apple...")
wrapper = EdgarToolsWrapper(identity='stephen.parton@sjpconsulting.com')
verification = wrapper.verify_balance_sheet_equation('AAPL')

print(f"✓ Verification passed: {verification['passed']}")
print(f"  Assets: ${verification['assets']:,.0f}")
print(f"  Liabilities: ${verification['liabilities']:,.0f}")
print(f"  Equity: ${verification['equity']:,.0f}")
print(f"  Difference: {verification['difference_pct']:.4f}%\n")

# Step 2: Create a mock FinancialMetrics object with verification data
print("Step 2: Creating FinancialMetrics object with verification fields...")

mock_metrics = FinancialMetrics(
    executive_summary="Test company showing strong financial health.",
    current_ratio=1.5,
    quick_ratio=1.2,
    cash_ratio=0.5,
    debt_to_equity=0.8,
    debt_to_assets=0.3,
    interest_coverage=5.0,
    equity_ratio=0.7,
    gross_profit_margin=0.43,
    operating_margin=0.30,
    net_profit_margin=0.25,
    return_on_assets=0.15,
    return_on_equity=0.18,
    asset_turnover=0.8,
    inventory_turnover=None,
    receivables_turnover=None,
    days_sales_outstanding=None,
    period="Q1 FY2025",
    filing_date="2025-01-30",
    filing_reference="10-Q filed 2025-01-30, Accession: 0000320193-25-000006",
    company_name="Apple Inc.",
    sic_code=3571,
    calculation_notes=[],
    # NEW FIELDS - Balance Sheet Verification
    balance_sheet_verified=verification['passed'],
    balance_sheet_verification_error=verification['difference_pct'],
    balance_sheet_total_assets=verification['assets'],
    balance_sheet_total_liabilities=verification['liabilities'],
    balance_sheet_total_equity=verification['equity'],
    # Financial statements (minimal mock data)
    balance_sheet={'Assets_Current': 100000000},
    income_statement={'Revenue_Current': 500000000},
    cash_flow_statement={'NetCashProvidedByOperatingActivities_Current': 120000000}
)

print("✓ FinancialMetrics object created with verification fields\n")

# Step 3: Format the metrics and check for verification section
print("Step 3: Formatting metrics to markdown...")
formatted = format_financial_metrics(mock_metrics, "Apple Inc.")

# Check that verification section exists
if "## Balance Sheet Verification" in formatted:
    print("✓ Balance Sheet Verification section found in formatted output\n")

    # Extract just the verification section
    start_idx = formatted.find("## Balance Sheet Verification")
    end_idx = formatted.find("## Data Source")
    verification_section = formatted[start_idx:end_idx]

    print("Balance Sheet Verification Section:")
    print("=" * 70)
    print(verification_section)
    print("=" * 70)
else:
    print("✗ Balance Sheet Verification section NOT found in formatted output")
    print("\nSearching for 'verification' in output...")
    if 'verification' in formatted.lower():
        print("Found 'verification' keyword - may be formatted differently")
    else:
        print("No 'verification' keyword found at all")

print("\n✅ Test complete!")
print("\nNext step: Run full analysis to verify LLM populates these fields correctly")
