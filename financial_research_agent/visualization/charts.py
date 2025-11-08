"""
Core chart generation functions using Plotly.

This module provides functions to create interactive financial charts
from structured financial data.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional


def create_revenue_trend_chart(
    financial_data: Dict[str, Any],
    ticker: str = "",
    periods: Optional[List[str]] = None
) -> go.Figure:
    """
    Create a line chart showing revenue and profitability trends.

    Args:
        financial_data: Dictionary with keys 'revenue', 'gross_profit', 'operating_income'
                       Each value is a list of numbers for each period
        ticker: Stock ticker symbol for title
        periods: List of period labels (e.g., ['Q1 2024', 'Q2 2024', 'Q3 2024'])

    Returns:
        Plotly Figure object
    """
    if not periods and 'periods' in financial_data:
        periods = financial_data['periods']
    elif not periods:
        # Generate default period labels
        num_periods = len(financial_data.get('revenue', []))
        periods = [f"Period {i+1}" for i in range(num_periods)]

    # Create figure with secondary y-axis for margins
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": True}]],
        subplot_titles=[f"{ticker} Revenue & Profitability Trends" if ticker else "Revenue & Profitability Trends"]
    )

    # Add revenue line
    if 'revenue' in financial_data:
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=financial_data['revenue'],
                name="Revenue",
                mode='lines+markers',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ),
            secondary_y=False
        )

    # Add gross profit line
    if 'gross_profit' in financial_data:
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=financial_data['gross_profit'],
                name="Gross Profit",
                mode='lines+markers',
                line=dict(color='#2ca02c', width=3),
                marker=dict(size=8)
            ),
            secondary_y=False
        )

    # Add operating income line
    if 'operating_income' in financial_data:
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=financial_data['operating_income'],
                name="Operating Income",
                mode='lines+markers',
                line=dict(color='#ff7f0e', width=3),
                marker=dict(size=8)
            ),
            secondary_y=False
        )

    # Add margin percentages on secondary axis
    if 'gross_margin_pct' in financial_data:
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=financial_data['gross_margin_pct'],
                name="Gross Margin %",
                mode='lines+markers',
                line=dict(color='#2ca02c', width=2, dash='dot'),
                marker=dict(size=6),
                yaxis='y2'
            ),
            secondary_y=True
        )

    if 'operating_margin_pct' in financial_data:
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=financial_data['operating_margin_pct'],
                name="Operating Margin %",
                mode='lines+markers',
                line=dict(color='#ff7f0e', width=2, dash='dot'),
                marker=dict(size=6),
                yaxis='y2'
            ),
            secondary_y=True
        )

    # Update layout
    fig.update_xaxes(title_text="Period")
    fig.update_yaxes(title_text="Amount ($)", secondary_y=False)
    fig.update_yaxes(title_text="Margin (%)", secondary_y=True)

    fig.update_layout(
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500,
        template='plotly_white'
    )

    return fig


def create_margin_comparison_chart(
    financial_data: Dict[str, Any],
    ticker: str = "",
    comparison_label: str = "Comparison"
) -> go.Figure:
    """
    Create a grouped bar chart comparing margins across periods.

    Args:
        financial_data: Dictionary with keys 'current' and 'prior', each containing
                       {'gross_margin': float, 'operating_margin': float, 'net_margin': float}
        ticker: Stock ticker symbol for title
        comparison_label: Label for comparison (e.g., 'YoY', 'QoQ')

    Returns:
        Plotly Figure object
    """
    categories = ['Gross Margin', 'Operating Margin', 'Net Margin']

    current = financial_data.get('current', {})
    prior = financial_data.get('prior', {})

    current_values = [
        current.get('gross_margin', 0),
        current.get('operating_margin', 0),
        current.get('net_margin', 0)
    ]

    prior_values = [
        prior.get('gross_margin', 0),
        prior.get('operating_margin', 0),
        prior.get('net_margin', 0)
    ]

    current_label = financial_data.get('current_period', 'Current Period')
    prior_label = financial_data.get('prior_period', 'Prior Period')

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name=current_label,
        x=categories,
        y=current_values,
        marker_color='#1f77b4',
        text=[f"{v:.1f}%" for v in current_values],
        textposition='outside'
    ))

    fig.add_trace(go.Bar(
        name=prior_label,
        x=categories,
        y=prior_values,
        marker_color='#aec7e8',
        text=[f"{v:.1f}%" for v in prior_values],
        textposition='outside'
    ))

    title = f"{ticker} Profitability Margins - {comparison_label}" if ticker else f"Profitability Margins - {comparison_label}"

    fig.update_layout(
        title=title,
        xaxis_title="Margin Type",
        yaxis_title="Percentage (%)",
        barmode='group',
        height=450,
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_cash_flow_waterfall(
    financial_data: Dict[str, Any],
    ticker: str = ""
) -> go.Figure:
    """
    Create a waterfall chart showing cash flow components.

    Args:
        financial_data: Dictionary with keys:
                       - 'operating_cf': Operating cash flow
                       - 'investing_cf': Investing cash flow (usually negative)
                       - 'financing_cf': Financing cash flow
                       - 'net_change': Net change in cash
                       - 'period': Period label (optional)
        ticker: Stock ticker symbol for title

    Returns:
        Plotly Figure object
    """
    operating = financial_data.get('operating_cf', 0)
    investing = financial_data.get('investing_cf', 0)
    financing = financial_data.get('financing_cf', 0)
    net_change = financial_data.get('net_change', operating + investing + financing)
    period = financial_data.get('period', 'Period')

    fig = go.Figure(go.Waterfall(
        name="Cash Flow",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["Operating Activities", "Investing Activities", "Financing Activities", "Net Change in Cash"],
        textposition="outside",
        text=[
            f"${operating/1e9:.1f}B" if abs(operating) >= 1e9 else f"${operating/1e6:.1f}M",
            f"${investing/1e9:.1f}B" if abs(investing) >= 1e9 else f"${investing/1e6:.1f}M",
            f"${financing/1e9:.1f}B" if abs(financing) >= 1e9 else f"${financing/1e6:.1f}M",
            f"${net_change/1e9:.1f}B" if abs(net_change) >= 1e9 else f"${net_change/1e6:.1f}M"
        ],
        y=[operating, investing, financing, net_change],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#2ca02c"}},
        decreasing={"marker": {"color": "#d62728"}},
        totals={"marker": {"color": "#1f77b4"}}
    ))

    title = f"{ticker} Cash Flow Waterfall - {period}" if ticker else f"Cash Flow Waterfall - {period}"

    fig.update_layout(
        title=title,
        showlegend=False,
        height=500,
        template='plotly_white',
        yaxis_title="Amount ($)"
    )

    return fig


def create_key_metrics_dashboard(
    financial_data: Dict[str, Any],
    ticker: str = ""
) -> go.Figure:
    """
    Create a multi-chart dashboard showing key financial metrics.

    Args:
        financial_data: Dictionary with keys:
                       - 'roe': Return on Equity (%)
                       - 'roa': Return on Assets (%)
                       - 'current_ratio': Current Ratio
                       - 'debt_to_equity': Debt-to-Equity Ratio
                       - 'roe_prior': Prior period ROE (optional)
                       - 'roa_prior': Prior period ROA (optional)
                       - 'current_ratio_prior': Prior period Current Ratio (optional)
                       - 'debt_to_equity_prior': Prior period D/E (optional)
        ticker: Stock ticker symbol for title

    Returns:
        Plotly Figure object with 2x2 subplot grid
    """
    # Create subplots: 2 rows, 2 columns
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Return on Equity (%)", "Return on Assets (%)",
                       "Current Ratio", "Debt-to-Equity Ratio"),
        specs=[[{"type": "indicator"}, {"type": "indicator"}],
               [{"type": "indicator"}, {"type": "indicator"}]]
    )

    # ROE indicator
    roe = financial_data.get('roe', 0)
    roe_prior = financial_data.get('roe_prior')
    delta_roe = None if roe_prior is None else roe - roe_prior

    fig.add_trace(go.Indicator(
        mode="number+delta" if delta_roe is not None else "number",
        value=roe,
        delta={'reference': roe_prior, 'relative': False} if delta_roe is not None else None,
        number={'suffix': "%", 'font': {'size': 40}},
        domain={'x': [0, 1], 'y': [0, 1]}
    ), row=1, col=1)

    # ROA indicator
    roa = financial_data.get('roa', 0)
    roa_prior = financial_data.get('roa_prior')
    delta_roa = None if roa_prior is None else roa - roa_prior

    fig.add_trace(go.Indicator(
        mode="number+delta" if delta_roa is not None else "number",
        value=roa,
        delta={'reference': roa_prior, 'relative': False} if delta_roa is not None else None,
        number={'suffix': "%", 'font': {'size': 40}},
        domain={'x': [0, 1], 'y': [0, 1]}
    ), row=1, col=2)

    # Current Ratio indicator
    current_ratio = financial_data.get('current_ratio', 0)
    current_ratio_prior = financial_data.get('current_ratio_prior')
    delta_cr = None if current_ratio_prior is None else current_ratio - current_ratio_prior

    fig.add_trace(go.Indicator(
        mode="number+delta" if delta_cr is not None else "number",
        value=current_ratio,
        delta={'reference': current_ratio_prior, 'relative': False} if delta_cr is not None else None,
        number={'font': {'size': 40}},
        domain={'x': [0, 1], 'y': [0, 1]}
    ), row=2, col=1)

    # Debt-to-Equity indicator
    debt_to_equity = financial_data.get('debt_to_equity', 0)
    debt_to_equity_prior = financial_data.get('debt_to_equity_prior')
    delta_de = None if debt_to_equity_prior is None else debt_to_equity - debt_to_equity_prior

    fig.add_trace(go.Indicator(
        mode="number+delta" if delta_de is not None else "number",
        value=debt_to_equity,
        delta={'reference': debt_to_equity_prior, 'relative': False} if delta_de is not None else None,
        number={'font': {'size': 40}},
        domain={'x': [0, 1], 'y': [0, 1]}
    ), row=2, col=2)

    title = f"{ticker} Key Financial Metrics" if ticker else "Key Financial Metrics"

    fig.update_layout(
        title=title,
        height=600,
        template='plotly_white'
    )

    return fig


def create_revenue_segment_breakdown(
    financial_data: Dict[str, Any],
    ticker: str = ""
) -> go.Figure:
    """
    Create a donut chart showing revenue breakdown by segment.

    Args:
        financial_data: Dictionary with segment revenue data
                       Keys: 'US_Canada', 'EMEA', 'LatAm', 'APAC', etc.
                       Values: Revenue amounts
        ticker: Stock ticker symbol for title

    Returns:
        Plotly Figure object
    """
    # Extract segment data
    segments = financial_data.get('revenue_segments', {})

    if not segments:
        # Return empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No segment data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig

    # Prepare data for chart
    labels = []
    values = []

    label_mapping = {
        'US_Canada': 'United States & Canada',
        'EMEA': 'Europe, Middle East & Africa',
        'LatAm': 'Latin America',
        'APAC': 'Asia-Pacific',
        'Other': 'Other'
    }

    for key, value in segments.items():
        label = label_mapping.get(key, key)
        labels.append(label)
        values.append(value)

    # Calculate percentages
    total = sum(values)
    percentages = [(v / total * 100) for v in values]

    # Create donut chart
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,  # Makes it a donut chart
        textinfo='label+percent',
        textposition='auto',
        marker=dict(
            colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            line=dict(color='white', width=2)
        ),
        hovertemplate='<b>%{label}</b><br>' +
                     'Revenue: $%{value:,.0f}<br>' +
                     'Percentage: %{percent}<br>' +
                     '<extra></extra>'
    )])

    title = f"{ticker} Revenue by Segment" if ticker else "Revenue by Segment"
    period = financial_data.get('period', '')
    if period:
        title += f" - {period}"

    fig.update_layout(
        title=title,
        showlegend=True,
        height=500,
        template='plotly_white',
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )

    return fig


def create_risk_category_chart(
    risk_analysis_text: str,
    ticker: str = ""
) -> go.Figure:
    """
    Create a horizontal bar chart showing risk category breakdown.

    Uses keyword-based counting to analyze risk mentions without fabricating
    severity or likelihood data. Provides honest visualization of actual
    risk discussion in the analysis.

    Args:
        risk_analysis_text: Full text of risk analysis markdown
        ticker: Stock ticker symbol for title

    Returns:
        Plotly Figure object
    """
    import re

    # Define risk categories with their keyword patterns
    # Keywords are case-insensitive
    risk_categories = {
        'Competitive Risks': [
            'competit', 'rival', 'market share', 'piracy', 'streaming service',
            'generative ai', 'social media', 'ugc', 'linear tv'
        ],
        'Operational Risks': [
            'production', 'content creation', 'third-party', 'technology',
            'ui', 'product improvement', 'global operation', 'workforce',
            'collective bargaining', 'talent'
        ],
        'Financial Risks': [
            'margin', 'revenue', 'profitability', 'cash flow', 'liquidity',
            'fx', 'foreign exchange', 'currency', 'pricing', 'capital allocation',
            'share repurchase', 'debt'
        ],
        'Regulatory/Legal Risks': [
            'regulat', 'compliance', 'legal', 'litigation', 'tax dispute',
            'ip', 'intellectual property', 'copyright', 'trademark', 'quota',
            'ownership rights', 'content review'
        ],
        'Market/Economic Risks': [
            'macroeconomic', 'inflation', 'recession', 'economic', 'seasonality',
            'advertising', 'ad market', 'cyclical', 'household budget'
        ],
        'Content/Reputational Risks': [
            'content sensitivity', 'reputational', 'content removal',
            'controversy', 'culture', 'environmental', 'esg', 'member engagement',
            'churn', 'cancellation'
        ]
    }

    # Count mentions for each category
    category_counts = {}
    text_lower = risk_analysis_text.lower()

    for category, keywords in risk_categories.items():
        count = 0
        for keyword in keywords:
            # Use word boundaries for more accurate matching
            # Count all occurrences of the keyword
            pattern = re.compile(r'\b' + re.escape(keyword), re.IGNORECASE)
            matches = pattern.findall(text_lower)
            count += len(matches)
        category_counts[category] = count

    # Sort categories by count (descending)
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)

    # Prepare data for chart
    categories = [cat for cat, _ in sorted_categories]
    counts = [count for _, count in sorted_categories]

    # Create horizontal bar chart
    fig = go.Figure(data=[go.Bar(
        x=counts,
        y=categories,
        orientation='h',
        marker=dict(
            color=counts,
            colorscale='Reds',
            showscale=False,
            line=dict(color='white', width=1)
        ),
        text=counts,
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>' +
                     'Mentions: %{x}<br>' +
                     '<extra></extra>'
    )])

    title = f"{ticker} Risk Category Breakdown" if ticker else "Risk Category Breakdown"

    fig.update_layout(
        title=title,
        xaxis_title="Number of Mentions",
        yaxis_title="Risk Category",
        height=400,
        template='plotly_white',
        margin=dict(l=200),  # More space for category labels
        xaxis=dict(showgrid=True, gridcolor='lightgray')
    )

    # Add annotation explaining methodology
    fig.add_annotation(
        text="Based on keyword frequency in risk analysis text",
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        showarrow=False,
        font=dict(size=10, color='gray'),
        xanchor='center'
    )

    return fig


def save_chart_as_html(fig: go.Figure, output_path: str):
    """
    Save a Plotly figure as standalone HTML file.

    Args:
        fig: Plotly Figure object
        output_path: Path to save HTML file
    """
    fig.write_html(output_path, include_plotlyjs='cdn')


def save_chart_as_json(fig: go.Figure, output_path: str):
    """
    Save a Plotly figure as JSON file (for loading into gr.Plot).

    Args:
        fig: Plotly Figure object
        output_path: Path to save JSON file
    """
    import json
    with open(output_path, 'w') as f:
        json.dump(fig.to_dict(), f, indent=2)
