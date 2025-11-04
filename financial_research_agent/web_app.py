"""
Gradio web interface for Financial Research Agent.

Provides a professional, Morningstar-inspired UI for generating investment-grade
financial analysis reports.
"""

import gradio as gr
import asyncio
from pathlib import Path
from datetime import datetime

from financial_research_agent.manager_enhanced import EnhancedFinancialResearchManager


# Morningstar-inspired theme
def create_theme():
    """Create a professional Morningstar-style theme."""
    return gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
    ).set(
        body_background_fill="#f5f7fa",
        body_text_color="#1a1d1f",
        block_background_fill="white",
        block_border_color="#e0e4e8",
        block_border_width="1px",
        block_label_background_fill="white",
        block_label_text_color="#1a1d1f",
        block_title_text_color="#1a1d1f",
        button_primary_background_fill="#0066cc",
        button_primary_background_fill_hover="#0052a3",
        button_primary_text_color="white",
        button_secondary_background_fill="#f0f2f5",
        button_secondary_text_color="#1a1d1f",
        input_background_fill="white",
        input_border_color="#d0d5dd",
    )


# Query templates
QUERY_TEMPLATES = {
    "Tesla Q3 2025 Performance": "Analyze Tesla's Q3 2025 financial performance",
    "Apple Quarterly Analysis": "Analyze Apple's most recent quarterly performance",
    "Microsoft Financial Health": "Evaluate Microsoft's financial health and stability",
    "Amazon Risk Assessment": "What are the key financial risks facing Amazon?",
    "NVIDIA Profitability Analysis": "Analyze NVIDIA's profitability trends",
    "Google vs Microsoft Comparison": "Compare Google and Microsoft's financial performance",
    "Meta Investment Potential": "Is Meta a good investment based on recent financials?",
}


class WebApp:
    """Gradio web application for Financial Research Agent."""

    def __init__(self):
        self.manager = None
        self.current_session_dir = None
        self.current_reports = {}

    async def generate_analysis(
        self,
        query: str,
        progress=gr.Progress()
    ):
        """
        Generate financial analysis from query with streaming updates.

        Yields:
            Tuple of (status_message, comprehensive_report, financial_statements,
                     financial_metrics, data_verification)
        """
        if not query or query.strip() == "":
            yield (
                "❌ Please enter a query or select a template",
                "", "", "", ""
            )
            return

        try:
            # Initialize empty reports
            reports = {
                'comprehensive': '*⏳ Waiting for comprehensive report...*',
                'statements': '*⏳ Waiting for financial statements...*',
                'metrics': '*⏳ Waiting for financial metrics...*',
                'verification': '*⏳ Waiting for verification...*'
            }

            # Track which reports we've already loaded
            loaded_reports = set()

            # Define progress callback with streaming updates
            def progress_callback(prog: float, desc: str):
                progress(prog, desc=desc)

            # Initialize manager with progress callback
            progress(0.0, desc="Initializing analysis engine...")
            self.manager = EnhancedFinancialResearchManager(progress_callback=progress_callback)

            # Start the analysis in background
            import asyncio
            analysis_task = asyncio.create_task(self.manager.run(query))

            # Poll for completed reports while analysis runs
            last_check = 0
            while not analysis_task.done():
                # Check every 2 seconds for new reports
                await asyncio.sleep(2)

                if self.manager.session_dir and self.manager.session_dir.exists():
                    self.current_session_dir = self.manager.session_dir

                    # Check for new reports
                    new_reports = self._load_reports()
                    has_updates = False

                    for key, content in new_reports.items():
                        if (not content.startswith('*Report not generated:') and
                            key not in loaded_reports):
                            reports[key] = content
                            loaded_reports.add(key)
                            has_updates = True

                    # Yield update if we found new reports
                    if has_updates:
                        timestamp = self.current_session_dir.name if self.current_session_dir else "unknown"
                        status_msg = f"🔄 Analysis in progress...\n\n**Session:** {timestamp}\n**Query:** {query}\n\n**Completed:** {', '.join(sorted(loaded_reports))}"

                        yield (
                            status_msg,
                            reports.get('comprehensive', ''),
                            reports.get('statements', ''),
                            reports.get('metrics', ''),
                            reports.get('verification', '')
                        )

            # Wait for analysis to complete
            await analysis_task

            # Get the session directory that was created
            self.current_session_dir = self.manager.session_dir

            progress(0.98, desc="Loading final reports...")

            # Load all final reports
            reports = self._load_reports()

            progress(1.0, desc="Complete!")

            timestamp = self.current_session_dir.name if self.current_session_dir else "unknown"
            status_msg = f"✅ Analysis completed successfully!\n\n**Session:** {timestamp}\n**Query:** {query}"

            yield (
                status_msg,
                reports.get('comprehensive', ''),
                reports.get('statements', ''),
                reports.get('metrics', ''),
                reports.get('verification', '')
            )

        except Exception as e:
            error_msg = f"❌ Error during analysis:\n\n{str(e)}"
            yield (error_msg, "", "", "", "")

    def _load_reports(self) -> dict[str, str]:
        """Load generated markdown reports from session directory."""
        reports = {}

        if not self.current_session_dir or not self.current_session_dir.exists():
            return reports

        # Map report files to keys (using actual filenames from manager_enhanced.py)
        report_files = {
            'comprehensive': '07_comprehensive_report.md',
            'statements': '03_financial_statements.md',
            'metrics': '04_financial_metrics.md',
            'verification': '08_verification.md',
        }

        for key, filename in report_files.items():
            file_path = self.current_session_dir / filename
            if file_path.exists():
                reports[key] = file_path.read_text(encoding='utf-8')
            else:
                reports[key] = f"*Report not generated: {filename}*"

        return reports

    def use_template(self, template_name: str) -> str:
        """Return the query for a selected template."""
        return QUERY_TEMPLATES.get(template_name, "")

    def create_interface(self):
        """Create the Gradio interface."""

        with gr.Blocks(
            theme=create_theme(),
            title="Financial Research Agent",
            css="""
                .query-box textarea { font-size: 16px; }
                .status-box { padding: 20px; border-radius: 8px; }
                .report-content { font-family: 'Georgia', serif; line-height: 1.6; }
                .template-button { margin: 4px; }

                /* Right-align numbers in markdown tables */
                .report-content table td:nth-child(2),
                .report-content table td:nth-child(3),
                .report-content table td:nth-child(4),
                .report-content table td:nth-child(5) {
                    text-align: right;
                }

                /* Keep first column (labels) left-aligned */
                .report-content table td:first-child {
                    text-align: left;
                }

                /* Better table formatting */
                .report-content table {
                    border-collapse: collapse;
                    width: 100%;
                    margin: 16px 0;
                }

                .report-content table th {
                    background-color: #f5f7fa;
                    font-weight: 600;
                    padding: 12px;
                    border-bottom: 2px solid #0066cc;
                }

                .report-content table td {
                    padding: 10px 12px;
                    border-bottom: 1px solid #e0e4e8;
                }

                .report-content table tr:hover {
                    background-color: #f9fafb;
                }

                /* Monospace for numbers */
                .report-content table td:nth-child(n+2) {
                    font-family: 'IBM Plex Mono', 'Consolas', monospace;
                    font-size: 0.95em;
                }
            """
        ) as app:

            # Header
            gr.Markdown(
                """
                # 📊 Financial Research Agent
                ### *Investment-Grade Financial Analysis powered by SEC EDGAR*

                Generate comprehensive 3-5 page research reports with:
                • Complete financial statement extraction from official SEC filings
                • Comparative period analysis with human-readable formatting
                • Financial metrics & ratios with YoY trends
                • Risk assessment and forward-looking indicators
                • Data quality verification and validation
                """
            )

            with gr.Tabs() as tabs:

                # ==================== TAB 1: Query & Analysis Setup ====================
                with gr.Tab("🔍 Query", id=0):
                    gr.Markdown("## Enter Your Financial Research Query")

                    query_input = gr.Textbox(
                        label="Research Query",
                        placeholder="E.g., 'Analyze Tesla's Q3 2025 financial performance'",
                        lines=3,
                        elem_classes=["query-box"]
                    )

                    gr.Markdown("### 📋 Quick Query Templates")
                    gr.Markdown("*Click a template to auto-fill your query*")

                    with gr.Row():
                        with gr.Column(scale=1):
                            for i, template_name in enumerate(list(QUERY_TEMPLATES.keys())[:4]):
                                btn = gr.Button(
                                    template_name,
                                    size="sm",
                                    elem_classes=["template-button"]
                                )
                                btn.click(
                                    fn=lambda name=template_name: QUERY_TEMPLATES[name],
                                    outputs=query_input
                                )

                        with gr.Column(scale=1):
                            for template_name in list(QUERY_TEMPLATES.keys())[4:]:
                                btn = gr.Button(
                                    template_name,
                                    size="sm",
                                    elem_classes=["template-button"]
                                )
                                btn.click(
                                    fn=lambda name=template_name: QUERY_TEMPLATES[name],
                                    outputs=query_input
                                )

                    gr.Markdown("---")

                    generate_btn = gr.Button(
                        "🔍 Generate Analysis",
                        variant="primary",
                        size="lg"
                    )

                    status_output = gr.Markdown(
                        label="Status",
                        elem_classes=["status-box"]
                    )

                # ==================== TAB 2: Comprehensive Report ====================
                with gr.Tab("📄 Comprehensive Report", id=1):
                    gr.Markdown(
                        """
                        ## Full Investment-Grade Research Report
                        *3-5 page comprehensive analysis including executive summary,
                        financial performance, risk assessment, and forward-looking indicators*
                        """
                    )

                    comprehensive_output = gr.Markdown(
                        label="Research Report",
                        elem_classes=["report-content"]
                    )

                    with gr.Row():
                        download_comp_md = gr.DownloadButton(
                            label="📥 Download as Markdown",
                            visible=False
                        )
                        # download_comp_pdf = gr.Button(
                        #     "📥 Download as PDF",
                        #     size="sm"
                        # )

                # ==================== TAB 3: Financial Statements ====================
                with gr.Tab("💰 Financial Statements", id=2):
                    gr.Markdown(
                        """
                        ## Complete Financial Statements from SEC EDGAR
                        *Balance Sheet, Income Statement, and Cash Flow Statement
                        with comparative periods and human-readable labels*
                        """
                    )

                    with gr.Tabs():
                        with gr.Tab("All Statements"):
                            statements_output = gr.Markdown(
                                elem_classes=["report-content"]
                            )

                        # Future: Individual statement tabs with interactive tables
                        # with gr.Tab("Balance Sheet"):
                        #     balance_sheet_table = gr.DataFrame()
                        # with gr.Tab("Income Statement"):
                        #     income_statement_table = gr.DataFrame()
                        # with gr.Tab("Cash Flow"):
                        #     cash_flow_table = gr.DataFrame()

                    with gr.Row():
                        download_stmt_md = gr.DownloadButton(
                            label="📥 Download Statements",
                            visible=False
                        )

                # ==================== TAB 4: Financial Metrics ====================
                with gr.Tab("📈 Financial Metrics & Ratios", id=3):
                    gr.Markdown(
                        """
                        ## Financial Metrics Analysis with YoY Comparison
                        *Liquidity, Solvency, Profitability, and Efficiency ratios
                        with comparative period analysis and trend indicators*
                        """
                    )

                    metrics_output = gr.Markdown(
                        elem_classes=["report-content"]
                    )

                    with gr.Row():
                        download_metrics_md = gr.DownloadButton(
                            label="📥 Download Metrics",
                            visible=False
                        )

                # ==================== TAB 5: Data Verification ====================
                with gr.Tab("✅ Data Verification", id=4):
                    gr.Markdown(
                        """
                        ## Data Quality & Validation Report
                        *Verification of data completeness, balance sheet equations,
                        comparative periods, and critical line items*
                        """
                    )

                    verification_output = gr.Markdown(
                        elem_classes=["report-content"]
                    )

                    gr.Markdown(
                        """
                        ---

                        **Data Source:** All financial data is extracted directly from official
                        SEC EDGAR filings using XBRL precision. Values are exact to the penny
                        as reported in SEC filings.

                        **Methodology:** Deterministic extraction using edgartools library,
                        validated against balance sheet equations and completeness checks.
                        """
                    )

            # Footer
            gr.Markdown(
                """
                ---

                **About:** This tool generates investment-grade financial analysis reports using
                official SEC EDGAR filings. All data is extracted with XBRL precision and validated
                for accuracy and completeness.

                **Disclaimer:** This tool is for informational and educational purposes only.
                Not financial advice. Always consult with qualified financial professionals
                before making investment decisions.
                """
            )

            # Connect the generate button to the analysis function
            generate_btn.click(
                fn=self.generate_analysis,
                inputs=[query_input],
                outputs=[
                    status_output,
                    comprehensive_output,
                    statements_output,
                    metrics_output,
                    verification_output
                ]
            )

        return app

    def launch(self, **kwargs):
        """Launch the Gradio app."""
        app = self.create_interface()

        # Default launch settings
        launch_settings = {
            'server_name': '0.0.0.0',
            'server_port': 7860,
            'share': False,
            'show_error': True,
            'inbrowser': True,  # Auto-open browser
            'favicon_path': None,
        }
        launch_settings.update(kwargs)

        app.launch(**launch_settings)


def main():
    """Main entry point for web app."""
    web_app = WebApp()
    web_app.launch()


if __name__ == "__main__":
    main()
