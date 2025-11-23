"""
Financial Chart Generator using edgartools and plotly.

Generates interactive visualizations from SEC EDGAR financial statements.
"""

from edgar import Company, set_identity
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List
import json
import logging

logger = logging.getLogger(__name__)


class FinancialChartGenerator:
    """Generate interactive financial charts from edgartools data."""

    def __init__(self, ticker: str, identity: str):
        """
        Initialize chart generator.

        Args:
            ticker: Stock ticker symbol
            identity: SEC EDGAR identity string
        """
        self.ticker = ticker
        set_identity(identity)
        try:
            self.company = Company(ticker)
            self.financials = self.company.get_financials()
        except Exception as e:
            logger.error(f"Failed to initialize financials for {ticker}: {e}")
            self.financials = None

    def _find_line_item(self, df: pd.DataFrame, search_terms: List[str]) -> Optional[pd.Series]:
        """
        Find a line item in DataFrame by searching for terms in label column.

        Args:
            df: Financial statement DataFrame
            search_terms: List of search terms to try

        Returns:
            Series containing the row data, or None if not found
        """
        for term in search_terms:
            try:
                matches = df[df['label'].str.contains(term, case=False, na=False, regex=False)]
                if not matches.empty:
                    return matches.iloc[0]
            except Exception:
                continue
        return None

    def _get_date_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Extract date columns from DataFrame (exclude metadata columns).

        Args:
            df: Financial statement DataFrame

        Returns:
            List of date column names
        """
        metadata_cols = ['concept', 'label', 'level', 'abstract', 'dimension', 
                        'balance', 'weight', 'preferred_sign', 'unit']
        date_cols = [col for col in df.columns if col not in metadata_cols]
        return date_cols

    def create_revenue_profitability_chart(self) -> Optional[go.Figure]:
        """
        Create revenue and profitability trends chart.

        Shows revenue (bars) with gross profit, operating income, and net income (lines).

        Returns:
            Plotly Figure or None if data unavailable
        """
        if not self.financials:
            return None

        try:
            income_df = self.financials.income_statement().to_dataframe()
            date_cols = self._get_date_columns(income_df)

            if len(date_cols) < 2:
                logger.warning(f"Insufficient periods for trend chart (need 2+, have {len(date_cols)})")
                return None

            # Find key line items
            revenue = self._find_line_item(income_df, [
                'Revenues', 'Revenue', 'Net Sales', 'Total Revenues', 'Sales'
            ])
            gross_profit = self._find_line_item(income_df, [
                'Gross Profit', 'Gross Income'
            ])
            operating_income = self._find_line_item(income_df, [
                'Operating Income', 'Income from Operations', 'Operating Profit'
            ])
            net_income = self._find_line_item(income_df, [
                'Net Income', 'Net Earnings', 'Profit'
            ])

            if revenue is None:
                logger.warning("Could not find revenue line item")
                return None

            # Create figure
            fig = go.Figure()

            # Add revenue bars
            fig.add_trace(go.Bar(
                x=date_cols,
                y=[revenue[col] for col in date_cols],
                name='Revenue',
                marker_color='lightblue',
                yaxis='y'
            ))

            # Add profitability lines
            if gross_profit is not None:
                fig.add_trace(go.Scatter(
                    x=date_cols,
                    y=[gross_profit[col] for col in date_cols],
                    name='Gross Profit',
                    mode='lines+markers',
                    line=dict(color='green', width=2),
                    yaxis='y'
                ))

            if operating_income is not None:
                fig.add_trace(go.Scatter(
                    x=date_cols,
                    y=[operating_income[col] for col in date_cols],
                    name='Operating Income',
                    mode='lines+markers',
                    line=dict(color='orange', width=2),
                    yaxis='y'
                ))

            if net_income is not None:
                fig.add_trace(go.Scatter(
                    x=date_cols,
                    y=[net_income[col] for col in date_cols],
                    name='Net Income',
                    mode='lines+markers',
                    line=dict(color='darkblue', width=2),
                    yaxis='y'
                ))

            fig.update_layout(
                title=f'{self.ticker} - Revenue & Profitability Trends',
                xaxis_title='Period',
                yaxis_title='Amount',
                hovermode='x unified',
                template='plotly_white',
                height=500,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating revenue profitability chart: {e}")
            return None

    def create_margin_trends_chart(self, metrics_results=None) -> Optional[go.Figure]:
        """
        Create margin trends chart using calculated ratios.

        Args:
            metrics_results: FinancialMetrics object with pre-calculated ratios

        Returns:
            Plotly Figure or None if data unavailable
        """
        if not metrics_results:
            return None

        try:
            # For now, create a simple display of current margins
            # TODO: Enhance with historical trend when available
            margins = []
            margin_names = []
            
            if hasattr(metrics_results, 'gross_profit_margin') and metrics_results.gross_profit_margin:
                margins.append(metrics_results.gross_profit_margin * 100)
                margin_names.append('Gross Margin')
            
            if hasattr(metrics_results, 'operating_margin') and metrics_results.operating_margin:
                margins.append(metrics_results.operating_margin * 100)
                margin_names.append('Operating Margin')
            
            if hasattr(metrics_results, 'net_profit_margin') and metrics_results.net_profit_margin:
                margins.append(metrics_results.net_profit_margin * 100)
                margin_names.append('Net Margin')

            if not margins:
                logger.warning("No margin data available")
                return None

            # Create bar chart
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=margin_names,
                y=margins,
                marker_color=['lightgreen', 'green', 'darkgreen'][:len(margins)],
                text=[f'{m:.1f}%' for m in margins],
                textposition='outside'
            ))

            fig.update_layout(
                title=f'{self.ticker} - Profitability Margins',
                xaxis_title='Margin Type',
                yaxis_title='Percentage (%)',
                template='plotly_white',
                height=400,
                showlegend=False
            )

            fig.update_yaxes(range=[0, max(margins) * 1.2])

            return fig

        except Exception as e:
            logger.error(f"Error creating margin trends chart: {e}")
            return None

    def create_balance_sheet_composition_chart(self) -> Optional[go.Figure]:
        """
        Create balance sheet composition chart showing assets, liabilities, and equity.

        Returns:
            Plotly Figure or None if data unavailable
        """
        if not self.financials:
            return None

        try:
            bs_df = self.financials.balance_sheet().to_dataframe()
            date_cols = self._get_date_columns(bs_df)

            if len(date_cols) < 1:
                logger.warning("No date columns found in balance sheet")
                return None

            # Use most recent period
            latest_date = date_cols[0] if date_cols else None
            if not latest_date:
                return None

            # Find key items
            total_assets = self._find_line_item(bs_df, [
                'Total Assets', 'Assets'
            ])
            current_liabilities = self._find_line_item(bs_df, [
                'Current Liabilities', 'Liabilities Current'
            ])
            noncurrent_liabilities = self._find_line_item(bs_df, [
                'Liabilities Noncurrent', 'Long-term Liabilities', 'Noncurrent Liabilities'
            ])
            total_liabilities = self._find_line_item(bs_df, [
                'Total Liabilities', 'Liabilities'
            ])
            total_equity = self._find_line_item(bs_df, [
                'Total Equity', 'Stockholders\' Equity', 'Shareholders\' Equity', 'Equity'
            ])

            if not total_assets or not total_equity:
                logger.warning("Missing required balance sheet items")
                return None

            # Prepare data
            assets_value = total_assets[latest_date]
            equity_value = total_equity[latest_date]

            # Calculate liabilities
            if total_liabilities is not None:
                liabilities_value = total_liabilities[latest_date]
            elif current_liabilities is not None and noncurrent_liabilities is not None:
                liabilities_value = current_liabilities[latest_date] + noncurrent_liabilities[latest_date]
            else:
                liabilities_value = assets_value - equity_value

            # Create waterfall-style chart
            fig = go.Figure()

            fig.add_trace(go.Bar(
                name='Total Assets',
                x=['Assets'],
                y=[assets_value],
                marker_color='lightblue'
            ))

            fig.add_trace(go.Bar(
                name='Total Liabilities',
                x=['Liabilities'],
                y=[liabilities_value],
                marker_color='orange'
            ))

            fig.add_trace(go.Bar(
                name='Total Equity',
                x=['Equity'],
                y=[equity_value],
                marker_color='green'
            ))

            fig.update_layout(
                title=f'{self.ticker} - Balance Sheet Composition ({latest_date})',
                xaxis_title='Category',
                yaxis_title='Amount',
                barmode='group',
                template='plotly_white',
                height=400
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating balance sheet composition chart: {e}")
            return None

    def generate_all_charts(self, output_dir: Path, metrics_results=None) -> Dict[str, Path]:
        """
        Generate all charts and save as JSON files for Gradio AND PNG for markdown embedding.

        Args:
            output_dir: Directory to save chart JSON files
            metrics_results: Optional FinancialMetrics object

        Returns:
            Dict mapping chart names to file paths
        """
        charts = {}

        # Revenue & Profitability
        try:
            fig = self.create_revenue_profitability_chart()
            if fig:
                # Save as JSON for Gradio
                chart_path = output_dir / "chart_revenue_profitability.json"
                with open(chart_path, 'w') as f:
                    json.dump(fig.to_dict(), f)

                # Save as PNG for markdown embedding
                try:
                    png_path = output_dir / "chart_revenue_profitability.png"
                    fig.write_image(str(png_path), width=1000, height=600, engine='kaleido')
                    logger.info(f"Generated revenue profitability chart: {chart_path} + PNG")
                except Exception as e:
                    # Kaleido failed (needs Chrome) - skip PNG export
                    logger.info(f"PNG export skipped (kaleido requires Chrome): {chart_path} (JSON only)")
                    # Charts will still display in Gradio via JSON files

                charts['revenue_profitability'] = chart_path
        except Exception as e:
            logger.warning(f"Failed to generate revenue chart: {e}")

        # Margin Trends
        if metrics_results:
            try:
                fig = self.create_margin_trends_chart(metrics_results)
                if fig:
                    # Save as JSON for Gradio
                    chart_path = output_dir / "chart_margins.json"
                    with open(chart_path, 'w') as f:
                        json.dump(fig.to_dict(), f)

                    # Save as PNG for markdown embedding
                    try:
                        png_path = output_dir / "chart_margins.png"
                        fig.write_image(str(png_path), width=1000, height=600, engine='kaleido')
                        logger.info(f"Generated margin chart: {chart_path} + PNG")
                    except Exception as e:
                        logger.info(f"PNG export skipped (kaleido requires Chrome): {chart_path} (JSON only)")

                    charts['margins'] = chart_path
            except Exception as e:
                logger.warning(f"Failed to generate margin chart: {e}")

        # Balance Sheet Composition
        try:
            fig = self.create_balance_sheet_composition_chart()
            if fig:
                # Save as JSON for Gradio
                chart_path = output_dir / "chart_balance_sheet.json"
                with open(chart_path, 'w') as f:
                    json.dump(fig.to_dict(), f)

                # Save as PNG for markdown embedding
                try:
                    png_path = output_dir / "chart_balance_sheet.png"
                    fig.write_image(str(png_path), width=1000, height=600, engine='kaleido')
                    logger.info(f"Generated balance sheet chart: {chart_path} + PNG")
                except Exception as e:
                    logger.info(f"PNG export skipped (kaleido requires Chrome): {chart_path} (JSON only)")

                charts['balance_sheet'] = chart_path
        except Exception as e:
            logger.warning(f"Failed to generate balance sheet chart: {e}")

        return charts


def generate_charts_for_analysis(session_dir: Path, ticker: str, metrics_results=None) -> int:
    """
    Generate charts for an analysis session.

    Args:
        session_dir: Output directory for the analysis
        ticker: Stock ticker symbol
        metrics_results: Optional FinancialMetrics object

    Returns:
        Number of charts successfully generated
    """
    import os

    identity = os.getenv("EDGAR_IDENTITY", "User user@example.com")

    try:
        generator = FinancialChartGenerator(ticker, identity)
        charts = generator.generate_all_charts(session_dir, metrics_results)
        return len(charts)
    except Exception as e:
        logger.error(f"Error generating charts: {e}")
        return 0
