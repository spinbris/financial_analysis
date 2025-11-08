"""
Script to generate charts from existing financial analysis markdown files.

This script parses financial statements and metrics from markdown files
and generates interactive Plotly charts.
"""

import json
import re
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from financial_research_agent.visualization.charts import (
    create_revenue_trend_chart,
    create_margin_comparison_chart,
    create_cash_flow_waterfall,
    create_key_metrics_dashboard,
    create_revenue_segment_breakdown,
    create_risk_category_chart,
    save_chart_as_html,
    save_chart_as_json
)


def parse_financial_statements(md_path: Path) -> dict:
    """Parse financial statements markdown to extract structured data."""
    if not md_path.exists():
        return {}

    content = md_path.read_text()
    data = {}

    # Extract company and period from header
    company_match = re.search(r'\*\*Company:\*\* (.+)', content)
    period_match = re.search(r'\*\*Period:\*\* (.+)', content)

    if company_match:
        data['company'] = company_match.group(1).strip()
    if period_match:
        data['period'] = period_match.group(1).strip()

    # Parse Income Statement section
    income_section = re.search(
        r'## Consolidated Statement of Operations.*?\n(.*?)(?=\n##|\Z)',
        content,
        re.DOTALL
    )

    if income_section:
        income_table = income_section.group(1)

        # Extract revenue by segment (current period - column 2)
        segments = {
            'US_Canada': r'Streaming - United States and Canada.*?\|\s*\$?([\d,]+)',
            'EMEA': r'Streaming - Europe, Middle East, and Africa.*?\|\s*\$?([\d,]+)',
            'LatAm': r'Streaming - Latin America.*?\|\s*\$?([\d,]+)',
            'APAC': r'Streaming - Asia-Pacific.*?\|\s*\$?([\d,]+)',
        }

        revenue_data = {}
        for segment, pattern in segments.items():
            match = re.search(pattern, income_table)
            if match:
                # Extract current period (first value after segment name)
                value_str = match.group(1).replace(',', '')
                revenue_data[segment] = float(value_str)

        # Extract total revenue (sum of segments)
        total_revenue_match = re.search(r'Reportable Segment.*?\|\s*\$?([\d,]+),', income_table)
        if total_revenue_match:
            data['total_revenue_current'] = float(total_revenue_match.group(1).replace(',', ''))

        # Extract cost of revenue
        cost_match = re.search(r'\*\*Total Cost of Revenue\*\*.*?\|\s*\$?([\d,]+),', income_table)
        if cost_match:
            data['cost_of_revenue_current'] = float(cost_match.group(1).replace(',', ''))

        # Extract operating income
        op_income_match = re.search(r'\*\*Operating Income\*\*.*?\|\s*\$?([\d,]+),', income_table)
        if op_income_match:
            data['operating_income_current'] = float(op_income_match.group(1).replace(',', ''))

        # Extract net income
        net_income_match = re.search(r'\*\*Net Income\*\*.*?\|\s*\$?([\d,]+),', income_table)
        if net_income_match:
            data['net_income_current'] = float(net_income_match.group(1).replace(',', ''))

        data['revenue_segments'] = revenue_data

    # Parse Cash Flow Statement section
    cash_flow_section = re.search(
        r'## Consolidated Statement of Cash Flows.*?\n(.*?)(?=\n##|\Z)',
        content,
        re.DOTALL
    )

    if cash_flow_section:
        cf_table = cash_flow_section.group(1)

        # Extract cash flow components
        operating_cf_match = re.search(r'Cash from Operating Activities.*?\|\s*\$?([\d,]+),', cf_table)
        investing_cf_match = re.search(r'Cash from Investing Activities.*?\|\s*\$?(-?[\d,]+),', cf_table)
        financing_cf_match = re.search(r'Cash from Financing Activities.*?\|\s*\$?(-?[\d,]+),', cf_table)
        net_change_match = re.search(r'Net Change in Cash.*?\|\s*\$?(-?[\d,]+),', cf_table)

        if operating_cf_match:
            data['operating_cf'] = float(operating_cf_match.group(1).replace(',', ''))
        if investing_cf_match:
            data['investing_cf'] = float(investing_cf_match.group(1).replace(',', ''))
        if financing_cf_match:
            data['financing_cf'] = float(financing_cf_match.group(1).replace(',', ''))
        if net_change_match:
            data['net_change_cash'] = float(net_change_match.group(1).replace(',', ''))

    return data


def parse_financial_metrics(md_path: Path) -> dict:
    """Parse financial metrics markdown to extract ratios."""
    if not md_path.exists():
        return {}

    content = md_path.read_text()
    data = {}

    # Extract profitability ratios from table
    profitability_section = re.search(
        r'## Profitability Ratios.*?\n(.*?)(?=\n##|\Z)',
        content,
        re.DOTALL
    )

    if profitability_section:
        prof_table = profitability_section.group(1)

        # Extract margin percentages (current period)
        gross_margin_match = re.search(r'\*\*Gross Margin\*\*.*?\|\s*([\d.]+)%', prof_table)
        op_margin_match = re.search(r'\*\*Operating Margin\*\*.*?\|\s*([\d.]+)%', prof_table)
        net_margin_match = re.search(r'\*\*Net Margin\*\*.*?\|\s*([\d.]+)%', prof_table)
        roe_match = re.search(r'\*\*Return on Equity \(ROE\)\*\*.*?\|\s*([\d.]+)%', prof_table)
        roa_match = re.search(r'\*\*Return on Assets \(ROA\)\*\*.*?\|\s*([\d.]+)%', prof_table)

        if gross_margin_match:
            data['gross_margin'] = float(gross_margin_match.group(1))
        if op_margin_match:
            data['operating_margin'] = float(op_margin_match.group(1))
        if net_margin_match:
            data['net_margin'] = float(net_margin_match.group(1))
        if roe_match:
            data['roe'] = float(roe_match.group(1))
        if roa_match:
            data['roa'] = float(roa_match.group(1))

    # Extract solvency ratios
    solvency_section = re.search(
        r'## Solvency Ratios.*?\n(.*?)(?=\n##|\Z)',
        content,
        re.DOTALL
    )

    if solvency_section:
        solv_table = solvency_section.group(1)

        debt_equity_match = re.search(r'\*\*Debt-to-Equity\*\*.*?\|\s*([\d.]+)', solv_table)
        current_ratio_match = re.search(r'\*\*Current Ratio\*\*.*?\|\s*([\d.]+)', content)  # Search in full content

        if debt_equity_match:
            data['debt_to_equity'] = float(debt_equity_match.group(1))
        if current_ratio_match:
            data['current_ratio'] = float(current_ratio_match.group(1))

    return data


def generate_charts_for_analysis(analysis_dir: Path, ticker: str = ""):
    """Generate all charts for a given analysis directory."""
    print(f"\nGenerating charts for: {analysis_dir.name}")

    # Parse data from markdown files
    statements_path = analysis_dir / "03_financial_statements.md"
    metrics_path = analysis_dir / "04_financial_metrics.md"

    statements_data = parse_financial_statements(statements_path)
    metrics_data = parse_financial_metrics(metrics_path)

    if not statements_data and not metrics_data:
        print("  ❌ No financial data found in markdown files")
        return

    # Merge data
    financial_data = {**statements_data, **metrics_data}

    # Determine ticker from company name if not provided
    if not ticker and 'company' in financial_data:
        company = financial_data['company']
        if 'Netflix' in company:
            ticker = 'NFLX'
        elif 'Apple' in company:
            ticker = 'AAPL'
        # Add more mappings as needed

    period = financial_data.get('period', 'Current Period')

    charts_created = 0

    # 1. Margin Comparison Chart
    if all(k in financial_data for k in ['gross_margin', 'operating_margin', 'net_margin']):
        print("  📊 Creating margin comparison chart...")
        margin_data = {
            'current': {
                'gross_margin': financial_data['gross_margin'],
                'operating_margin': financial_data['operating_margin'],
                'net_margin': financial_data['net_margin']
            },
            'prior': {},  # Would need to parse prior period data
            'current_period': period
        }

        fig = create_margin_comparison_chart(margin_data, ticker=ticker)
        save_chart_as_html(fig, str(analysis_dir / "chart_margins.html"))
        save_chart_as_json(fig, str(analysis_dir / "chart_margins.json"))
        charts_created += 1

    # 2. Cash Flow Waterfall
    if 'operating_cf' in financial_data:
        print("  📊 Creating cash flow waterfall chart...")
        cf_data = {
            'operating_cf': financial_data.get('operating_cf', 0),
            'investing_cf': financial_data.get('investing_cf', 0),
            'financing_cf': financial_data.get('financing_cf', 0),
            'net_change': financial_data.get('net_change_cash', 0),
            'period': period
        }

        fig = create_cash_flow_waterfall(cf_data, ticker=ticker)
        save_chart_as_html(fig, str(analysis_dir / "chart_cashflow.html"))
        save_chart_as_json(fig, str(analysis_dir / "chart_cashflow.json"))
        charts_created += 1

    # 3. Key Metrics Dashboard
    if any(k in financial_data for k in ['roe', 'roa', 'current_ratio', 'debt_to_equity']):
        print("  📊 Creating key metrics dashboard...")
        metrics_chart_data = {
            'roe': financial_data.get('roe', 0),
            'roa': financial_data.get('roa', 0),
            'current_ratio': financial_data.get('current_ratio', 0),
            'debt_to_equity': financial_data.get('debt_to_equity', 0)
        }

        fig = create_key_metrics_dashboard(metrics_chart_data, ticker=ticker)
        save_chart_as_html(fig, str(analysis_dir / "chart_metrics.html"))
        save_chart_as_json(fig, str(analysis_dir / "chart_metrics.json"))
        charts_created += 1

    # 4. Revenue Segment Breakdown
    if 'revenue_segments' in financial_data and financial_data['revenue_segments']:
        print("  📊 Creating revenue segment breakdown chart...")
        segment_data = {
            'revenue_segments': financial_data['revenue_segments'],
            'period': period
        }

        fig = create_revenue_segment_breakdown(segment_data, ticker=ticker)
        save_chart_as_html(fig, str(analysis_dir / "chart_segments.html"))
        save_chart_as_json(fig, str(analysis_dir / "chart_segments.json"))
        charts_created += 1

    # 5. Risk Category Breakdown
    risk_analysis_path = analysis_dir / "06_risk_analysis.md"
    if risk_analysis_path.exists():
        print("  📊 Creating risk category breakdown chart...")
        risk_text = risk_analysis_path.read_text()

        fig = create_risk_category_chart(risk_text, ticker=ticker)
        save_chart_as_html(fig, str(analysis_dir / "chart_risk_categories.html"))
        save_chart_as_json(fig, str(analysis_dir / "chart_risk_categories.json"))
        charts_created += 1

    print(f"  ✅ Created {charts_created} charts")
    return charts_created


def main():
    """Generate charts for all analyses or a specific analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate charts from financial analysis")
    parser.add_argument('--analysis-dir', type=str, help='Specific analysis directory (e.g., 20251108_094548)')
    parser.add_argument('--ticker', type=str, help='Stock ticker symbol')

    args = parser.parse_args()

    output_dir = Path("financial_research_agent/output")

    if args.analysis_dir:
        # Generate for specific analysis
        analysis_path = output_dir / args.analysis_dir
        if not analysis_path.exists():
            print(f"❌ Analysis directory not found: {analysis_path}")
            return

        generate_charts_for_analysis(analysis_path, ticker=args.ticker or "")
    else:
        # Generate for all analyses
        print("Generating charts for all analyses...")
        total_charts = 0

        for analysis_dir in sorted(output_dir.iterdir()):
            if analysis_dir.is_dir() and re.match(r'\d{8}_\d{6}', analysis_dir.name):
                charts_count = generate_charts_for_analysis(analysis_dir)
                total_charts += charts_count if charts_count else 0

        print(f"\n✅ Total charts created: {total_charts}")


if __name__ == "__main__":
    main()
