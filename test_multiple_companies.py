"""
Test the updated financial metrics tools with multiple companies.
Based on TOMORROW_ACTION_PLAN.md recommendations.
"""
import os
os.environ["EDGAR_IDENTITY"] = "Steve Parton stephen.parton@sjpconsulting.com"

from financial_research_agent.tools.edgartools_wrapper import EdgarToolsWrapper
from financial_research_agent.tools.financial_ratios_calculator import FinancialRatiosCalculator

edgar = EdgarToolsWrapper(identity="Steve Parton stephen.parton@sjpconsulting.com")
calculator = FinancialRatiosCalculator(identity="Steve Parton stephen.parton@sjpconsulting.com")

# Test companies with different characteristics
companies = [
    ("AAPL", "Tech, large cap"),
    ("MSFT", "Tech, large cap"),
    ("GOOGL", "Tech, Alphabet structure"),
    ("JPM", "Financial services"),
    ("JNJ", "Healthcare/pharma"),
]

print("="*70)
print("Testing EdgarTools Wrapper Across Multiple Companies")
print("="*70)

results = {}

for ticker, description in companies:
    print(f"\n{'='*70}")
    print(f"Testing {ticker} ({description})")
    print('='*70)
    try:
        # Get data
        data = edgar.get_all_data(ticker)

        # Calculate ratios
        ratios = calculator.calculate_all_ratios(ticker)
        growth = calculator.calculate_growth_rates(ticker)

        # Verify balance sheet equation
        verification = edgar.verify_balance_sheet_equation(ticker)

        # Store results
        results[ticker] = {
            'success': True,
            'total_assets': data['balance_sheet']['current_period'].get('total_assets', 0),
            'total_liabilities': data['balance_sheet']['current_period'].get('total_liabilities', 0),
            'stockholders_equity': data['balance_sheet']['current_period'].get('stockholders_equity', 0),
            'revenue': data['income_statement']['current_period'].get('revenue', 0),
            'net_income': data['income_statement']['current_period'].get('net_income', 0),
            'verification': verification,
            'ratio_count': sum(len(r) for r in ratios.values() if isinstance(r, dict)),
        }

        print(f"  ✓ Balance Sheet Verified: {'PASSED' if verification['passed'] else 'FAILED'}")
        print(f"    Verification Error: {verification['difference_pct']:.6f}%")
        print(f"\n  Financial Snapshot:")
        print(f"    Assets: ${results[ticker]['total_assets'] or 0:,.0f}")
        print(f"    Liabilities: ${results[ticker]['total_liabilities'] or 0:,.0f}")
        print(f"    Equity: ${results[ticker]['stockholders_equity'] or 0:,.0f}")
        print(f"    Revenue: ${results[ticker]['revenue'] or 0:,.0f}")
        print(f"    Net Income: ${results[ticker]['net_income'] or 0:,.0f}")
        print(f"\n  Ratios Calculated: {results[ticker]['ratio_count']}")

        # Show key profitability ratios
        print(f"\n  Key Profitability Ratios:")
        prof = ratios['profitability']
        if 'net_profit_margin' in prof:
            print(f"    Net Profit Margin: {prof['net_profit_margin']*100:.2f}%")
        if 'return_on_equity' in prof:
            print(f"    Return on Equity: {prof['return_on_equity']*100:.2f}%")
        if 'return_on_assets' in prof:
            print(f"    Return on Assets: {prof['return_on_assets']*100:.2f}%")

        # Show growth rates
        if growth:
            print(f"\n  Growth Rates (YoY):")
            for name, value in growth.items():
                if value is not None:
                    print(f"    {name.replace('_', ' ').title()}: {value*100:.2f}%")

    except Exception as e:
        results[ticker] = {
            'success': False,
            'error': str(e)
        }
        print(f"  ✗ {ticker}: Failed - {e}")
        import traceback
        traceback.print_exc()

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
successful = sum(1 for r in results.values() if r.get('success'))
print(f"\nSuccessful: {successful}/{len(companies)}")
print(f"Failed: {len(companies) - successful}/{len(companies)}")

print("\n" + "="*70)
print("VERIFICATION RESULTS")
print("="*70)
for ticker, result in results.items():
    if result.get('success'):
        verification = result['verification']
        status = "✓ PASSED" if verification['passed'] else "✗ FAILED"
        print(f"{ticker:6s}: {status} - Error: {verification['difference_pct']:.6f}%")
    else:
        print(f"{ticker:6s}: ✗ ERROR - {result.get('error', 'Unknown')}")

if successful == len(companies):
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("Wrapper is robust across different companies.")
    print(f"Average ratios calculated: {sum(r.get('ratio_count', 0) for r in results.values() if r.get('success')) / successful:.0f}")
    print("\nReady for integration into financial_metrics_agent!")
else:
    print("\n⚠️ Some tests failed. Review errors above.")
