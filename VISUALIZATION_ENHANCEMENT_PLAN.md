# Visualization Enhancement Plan

## Overview

Add interactive financial visualizations to reports using edgartools' `Statement.to_dataframe()` capabilities with plotly for interactive charts.

## Current State

### What We Have
1. ✅ **EdgarTools Integration**: Already using `to_dataframe()` in wrapper (line 33-35)
2. ✅ **Plotly Infrastructure**: Already installed and used for stock price charts
3. ✅ **Chart Generation Script**: `scripts/generate_charts_from_analysis.py` exists but optional
4. ✅ **Gradio Display**: Three chart placeholders in web interface (margin, metrics, risk)

### What's Working
- Stock price charts with currency detection (just fixed)
- Chart JSON files are generated and loaded in Gradio
- Charts are optional (failures don't break analysis)

### Gap Analysis
The current chart generation script likely creates generic visualizations. We can enhance this to use financial statement DataFrames directly from edgartools for richer, more meaningful charts.

## Proposed Visualizations

### 1. Financial Statement Trends (Time Series)

**Chart: Revenue & Profitability Trends**
- Multi-line chart showing:
  - Total Revenue (bar chart)
  - Gross Profit (line)
  - Operating Income (line)
  - Net Income (line)
- X-axis: Fiscal periods (quarterly or annual)
- Y-axis: Currency value
- Colors: Progressive darkening (revenue lightest → net income darkest)

**Data Source:**
```python
income_df = financials.income_statement().to_dataframe()
# Columns are dates, rows are line items
```

**Implementation:**
```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_revenue_profitability_chart(income_df: pd.DataFrame):
    # Get date columns (exclude metadata columns)
    date_cols = [col for col in income_df.columns
                 if col not in ['concept', 'label', 'level', 'abstract']]

    # Extract key rows
    revenue = income_df[income_df['label'].str.contains('Revenue', case=False, na=False)][date_cols]
    gross_profit = income_df[income_df['label'].str.contains('Gross Profit', case=False, na=False)][date_cols]
    operating_income = income_df[income_df['label'].str.contains('Operating Income', case=False, na=False)][date_cols]
    net_income = income_df[income_df['label'].str.contains('Net Income', case=False, na=False)][date_cols]

    fig = go.Figure()

    # Add revenue bars
    fig.add_trace(go.Bar(
        x=date_cols,
        y=revenue.iloc[0].values,
        name='Revenue',
        marker_color='lightblue'
    ))

    # Add profitability lines
    fig.add_trace(go.Scatter(
        x=date_cols,
        y=gross_profit.iloc[0].values,
        name='Gross Profit',
        mode='lines+markers',
        line=dict(color='green', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=date_cols,
        y=operating_income.iloc[0].values,
        name='Operating Income',
        mode='lines+markers',
        line=dict(color='orange', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=date_cols,
        y=net_income.iloc[0].values,
        name='Net Income',
        mode='lines+markers',
        line=dict(color='darkblue', width=2)
    ))

    fig.update_layout(
        title='Revenue & Profitability Trends',
        xaxis_title='Period',
        yaxis_title='Amount (Currency)',
        hovermode='x unified',
        template='plotly_white',
        height=500
    )

    return fig
```

### 2. Balance Sheet Composition (Stacked Area/Waterfall)

**Chart: Assets, Liabilities, and Equity**
- Stacked bar chart showing:
  - Total Assets (left bar)
  - Total Liabilities (middle bar, stacked: current + non-current)
  - Total Equity (right bar)
- Demonstrates balance sheet equation visually
- Trend over time (multiple periods)

**Data Source:**
```python
bs_df = financials.balance_sheet().to_dataframe()
```

**Use Case:** Quickly see capital structure changes

### 3. Cash Flow Waterfall

**Chart: Operating, Investing, Financing Cash Flows**
- Waterfall chart showing:
  - Beginning cash
  - + Operating cash flow
  - - Investing cash flow
  - + Financing cash flow
  - = Ending cash

**Data Source:**
```python
cf_df = financials.cashflow_statement().to_dataframe()
```

**Use Case:** Understand sources and uses of cash

### 4. Margin Trends (Already Implemented?)

**Chart: Profitability Margins Over Time**
- Line chart with:
  - Gross Margin %
  - Operating Margin %
  - Net Margin %
- Shows margin expansion/compression

**Data Source:** Calculated from income statement ratios

### 5. Key Ratios Dashboard (Small Multiples)

**Chart: 4-panel dashboard**
- Panel 1: Liquidity (Current Ratio trend)
- Panel 2: Leverage (Debt-to-Equity trend)
- Panel 3: Profitability (ROE, ROA trend)
- Panel 4: Efficiency (Asset Turnover trend)

**Data Source:** Pre-calculated ratios from `FinancialMetrics`

## Implementation Strategy

### Phase 1: Enhanced Chart Generation Module (Recommended)

**File:** `financial_research_agent/visualization/chart_generator.py`

```python
"""
Financial statement visualization module using edgartools and plotly.
"""

from edgar import Company
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import json


class FinancialChartGenerator:
    """Generate interactive financial charts from edgartools data."""

    def __init__(self, ticker: str, identity: str):
        self.ticker = ticker
        self.company = Company(ticker)
        self.financials = self.company.get_financials()

    def create_revenue_profitability_chart(self) -> go.Figure:
        """Create revenue and profitability trends chart."""
        income_df = self.financials.income_statement().to_dataframe()
        # Implementation from above
        pass

    def create_balance_sheet_composition_chart(self) -> go.Figure:
        """Create balance sheet composition chart."""
        bs_df = self.financials.balance_sheet().to_dataframe()
        # Implementation
        pass

    def create_cash_flow_waterfall_chart(self) -> go.Figure:
        """Create cash flow waterfall chart."""
        cf_df = self.financials.cashflow_statement().to_dataframe()
        # Implementation
        pass

    def create_margin_trends_chart(self, metrics: 'FinancialMetrics') -> go.Figure:
        """Create margin trends from calculated ratios."""
        # Use pre-calculated ratios
        pass

    def create_ratios_dashboard(self, metrics: 'FinancialMetrics') -> go.Figure:
        """Create 4-panel ratios dashboard."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Liquidity Ratios',
                'Leverage Ratios',
                'Profitability Ratios',
                'Efficiency Ratios'
            )
        )
        # Implementation
        return fig

    def generate_all_charts(self, output_dir: Path, metrics: Optional['FinancialMetrics'] = None) -> Dict[str, Path]:
        """
        Generate all charts and save as JSON files for Gradio.

        Returns:
            Dict mapping chart names to file paths
        """
        charts = {}

        try:
            # Revenue & Profitability
            fig = self.create_revenue_profitability_chart()
            chart_path = output_dir / "chart_revenue_profitability.json"
            with open(chart_path, 'w') as f:
                json.dump(fig.to_dict(), f)
            charts['revenue_profitability'] = chart_path
        except Exception as e:
            print(f"Warning: Failed to generate revenue chart: {e}")

        try:
            # Balance Sheet Composition
            fig = self.create_balance_sheet_composition_chart()
            chart_path = output_dir / "chart_balance_sheet.json"
            with open(chart_path, 'w') as f:
                json.dump(fig.to_dict(), f)
            charts['balance_sheet'] = chart_path
        except Exception as e:
            print(f"Warning: Failed to generate balance sheet chart: {e}")

        if metrics:
            try:
                # Margin Trends
                fig = self.create_margin_trends_chart(metrics)
                chart_path = output_dir / "chart_margins.json"
                with open(chart_path, 'w') as f:
                    json.dump(fig.to_dict(), f)
                charts['margins'] = chart_path
            except Exception as e:
                print(f"Warning: Failed to generate margin chart: {e}")

            try:
                # Ratios Dashboard
                fig = self.create_ratios_dashboard(metrics)
                chart_path = output_dir / "chart_ratios_dashboard.json"
                with open(chart_path, 'w') as f:
                    json.dump(fig.to_dict(), f)
                charts['ratios'] = chart_path
            except Exception as e:
                print(f"Warning: Failed to generate ratios dashboard: {e}")

        return charts


def generate_charts_for_analysis(session_dir: Path, ticker: str, metrics = None) -> int:
    """
    Generate charts for an analysis session.

    Args:
        session_dir: Output directory for the analysis
        ticker: Stock ticker
        metrics: FinancialMetrics object (optional)

    Returns:
        Number of charts successfully generated
    """
    import os
    identity = os.getenv("EDGAR_IDENTITY", "User user@example.com")

    try:
        generator = FinancialChartGenerator(ticker, identity)
        charts = generator.generate_all_charts(session_dir, metrics)
        return len(charts)
    except Exception as e:
        print(f"Error generating charts: {e}")
        return 0
```

### Phase 2: Integration Points

**1. Manager Integration** (financial_research_agent/manager_enhanced.py)

After financial metrics extraction, generate charts:

```python
# Around line 220 (after metrics agent runs)
if metrics_results:
    # Generate visualizations
    from financial_research_agent.visualization.chart_generator import generate_charts_for_analysis

    try:
        charts_count = generate_charts_for_analysis(
            self.session_dir,
            ticker=detected_ticker,
            metrics=metrics_results
        )
        logger.info(f"Generated {charts_count} visualization charts")
    except Exception as e:
        logger.warning(f"Failed to generate charts: {e}")
        # Don't fail the analysis
```

**2. Gradio Display** (financial_research_agent/web_app.py)

Already has chart loading logic (lines 591-607), just need to add more chart types:

```python
# Add after existing chart loading
revenue_chart_path = self.current_session_dir / "chart_revenue_profitability.json"
if revenue_chart_path.exists():
    with open(revenue_chart_path, 'r') as f:
        revenue_chart_data = json.load(f)
    revenue_chart_fig = go.Figure(revenue_chart_data)

balance_sheet_chart_path = self.current_session_dir / "chart_balance_sheet.json"
if balance_sheet_chart_path.exists():
    with open(balance_sheet_chart_path, 'r') as f:
        balance_sheet_chart_data = json.load(f)
    balance_sheet_chart_fig = go.Figure(balance_sheet_chart_data)
```

**3. New Gradio Tab** (financial_research_agent/web_app.py)

Add a dedicated "📊 Visualizations" tab after Verification:

```python
with gr.Tab("📊 Visualizations", id=7):
    gr.Markdown("""
        ## Interactive Financial Charts
        *Auto-generated visualizations from SEC EDGAR data*
    """)

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Revenue & Profitability Trends")
            revenue_chart = gr.Plot(label="Revenue Analysis")

        with gr.Column():
            gr.Markdown("### Balance Sheet Composition")
            balance_sheet_chart = gr.Plot(label="Balance Sheet")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Margin Trends")
            margin_trends_chart = gr.Plot(label="Margins")

        with gr.Column():
            gr.Markdown("### Key Ratios Dashboard")
            ratios_dashboard_chart = gr.Plot(label="Ratios")
```

## Benefits

### For Users
1. **Visual Understanding**: Quickly grasp trends without reading tables
2. **Interactive Exploration**: Hover for exact values, zoom, pan
3. **Professional Presentation**: Charts suitable for presentations
4. **Time Efficiency**: Spot trends faster than reading text

### For Analysis Quality
1. **Validation**: Visual anomalies are easier to spot
2. **Context**: Trends reveal patterns not obvious in static numbers
3. **Comparison**: Multi-period trends show trajectory
4. **Storytelling**: Charts support narrative in reports

## Challenges & Solutions

### Challenge 1: Different Statement Structures
**Problem:** Companies use different XBRL tags and presentation

**Solution:** Fuzzy matching on label text, fallback gracefully
```python
def find_line_item(df, search_terms: list[str]):
    for term in search_terms:
        matches = df[df['label'].str.contains(term, case=False, na=False)]
        if not matches.empty:
            return matches.iloc[0]
    return None

# Usage
revenue = find_line_item(income_df, ['Revenue', 'Sales', 'Net Sales'])
```

### Challenge 2: Missing Data Periods
**Problem:** Not all companies report all periods

**Solution:** Handle gaps gracefully, show what's available
```python
date_cols = [col for col in df.columns if isinstance(col, str) and col not in METADATA_COLS]
if len(date_cols) < 2:
    logger.warning(f"Insufficient periods for trend chart (need 2+, have {len(date_cols)})")
    return None  # Skip chart
```

### Challenge 3: Foreign Filers (20-F)
**Problem:** Limited or different XBRL structure

**Solution:** Degrade gracefully, show what's available
```python
try:
    # Try full chart
    fig = create_full_chart(df)
except KeyError:
    # Fallback to simplified chart
    fig = create_basic_chart(df)
except Exception as e:
    logger.warning(f"Chart generation failed: {e}")
    return None
```

### Challenge 4: Performance
**Problem:** Chart generation adds latency

**Solution:**
- Generate charts in parallel with other agents (already async)
- Charts are optional (failures don't block analysis)
- Cache chart objects where possible

## Testing Plan

### Test 1: U.S. Company (Full Data)
```bash
# Test: Apple (rich XBRL)
python -m financial_research_agent.main_enhanced
# Input: "Analyze Apple"
# Expected: All 4 charts generated successfully
```

### Test 2: Foreign Filer (Limited Data)
```bash
# Test: Westpac (20-F)
python -m financial_research_agent.main_enhanced
# Input: "Analyze Westpac Banking Corporation"
# Expected: Some charts generated, graceful degradation
```

### Test 3: Missing Data
```bash
# Test: Company with minimal filings
# Expected: Charts skip gracefully, analysis continues
```

## Implementation Priorities

### Must Have (Phase 1)
1. ✅ Revenue & Profitability Trends - Most valuable, always available
2. ✅ Margin Trends - Already partially implemented, enhance with time series
3. ✅ Integration into manager - Auto-generate during analysis

### Nice to Have (Phase 2)
4. ⭐ Balance Sheet Composition - Good for capital structure analysis
5. ⭐ Cash Flow Waterfall - Excellent storytelling tool
6. ⭐ Ratios Dashboard - Comprehensive view

### Future Enhancements (Phase 3)
7. 🔮 Segment Revenue Breakdown (pie/treemap)
8. 🔮 Peer Comparison Charts (requires multi-company data)
9. 🔮 Historical P/E, P/B Charts (requires market data)
10. 🔮 Analyst Estimates vs Actuals (requires third-party data)

## Recommendation

**Start with Phase 1:**
1. Create `financial_research_agent/visualization/chart_generator.py`
2. Implement Revenue & Profitability chart (highest value)
3. Enhance existing margin trends chart with time series
4. Integrate into manager to auto-generate
5. Test with U.S. and foreign companies

**Estimated Effort:** 2-3 hours for Phase 1

**ROI:** High - visual trends significantly improve report quality and user understanding

---

**Would you like me to implement Phase 1 now?**
