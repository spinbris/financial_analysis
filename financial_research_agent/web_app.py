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
        self.analysis_map = {}  # Map labels to directory paths

    def get_existing_analyses(self):
        """Get list of existing analysis directories."""
        output_dir = Path("financial_research_agent/output")
        if not output_dir.exists():
            return []

        # Find all analysis directories (format: YYYYMMDD_HHMMSS)
        dirs = sorted(
            [d for d in output_dir.iterdir() if d.is_dir() and d.name[0].isdigit()],
            key=lambda x: x.name,
            reverse=True  # Most recent first
        )

        # Extract ticker from 00_query.md or directory metadata
        analyses = []
        for dir_path in dirs[:50]:  # Limit to 50 most recent
            query_file = dir_path / "00_query.md"
            comprehensive_file = dir_path / "07_comprehensive_report.md"

            # Check if analysis is complete
            if comprehensive_file.exists():
                # Try to extract company/ticker from query file
                ticker = "Unknown"
                if query_file.exists():
                    content = query_file.read_text()
                    # Extract ticker using regex pattern (1-5 uppercase letters, optionally with dots)
                    import re
                    # Look for stock ticker patterns: 1-5 uppercase letters, optionally with dots (e.g., BRK.B)
                    match = re.search(r'\b([A-Z]{1,5}(?:\.[A-Z])?)\b', content)
                    if match:
                        ticker = match.group(1)

                analyses.append({
                    'label': f"{ticker} - {dir_path.name}",
                    'value': str(dir_path),
                    'ticker': ticker,
                    'timestamp': dir_path.name
                })

        return analyses

    def load_existing_analysis(self, selected_label: str):
        """Load an existing analysis from disk."""
        if not selected_label or selected_label not in self.analysis_map:
            return ("", "", "", "", "")

        analysis_path = self.analysis_map[selected_label]
        dir_path = Path(analysis_path)
        if not dir_path.exists():
            return (
                "❌ Analysis directory not found",
                "", "", "", ""
            )

        # Load report files
        reports = {}
        file_map = {
            'comprehensive': '07_comprehensive_report.md',
            'statements': '03_financial_statements.md',
            'metrics': '04_financial_metrics.md',
            'verification': 'data_verification.md'
        }

        for key, filename in file_map.items():
            file_path = dir_path / filename
            if file_path.exists():
                reports[key] = file_path.read_text()
            else:
                reports[key] = f"*{filename} not found*"

        return (
            f"✅ Loaded analysis from {dir_path.name}",
            reports.get('comprehensive', ''),
            reports.get('statements', ''),
            reports.get('metrics', ''),
            reports.get('verification', '')
        )

    def query_knowledge_base(
        self,
        query: str,
        ticker_filter: str = "",
        analysis_type: str = "",
        num_results: int = 5
    ) -> str:
        """
        Query the ChromaDB knowledge base with semantic search and synthesis.

        Uses the RAG synthesis agent to provide coherent, well-cited answers
        instead of raw document chunks.

        Args:
            query: Natural language search query
            ticker_filter: Optional ticker to filter results
            analysis_type: Optional analysis type filter
            num_results: Number of results to return

        Returns:
            Formatted markdown with synthesized answer, sources, and confidence
        """
        from financial_research_agent.rag.chroma_manager import FinancialRAGManager

        if not query or query.strip() == "":
            return "❌ Please enter a search query"

        try:
            # Initialize ChromaDB
            rag = FinancialRAGManager(persist_directory="./chroma_db")

            # Prepare filters
            ticker = ticker_filter.strip().upper() if ticker_filter else None
            analysis_type_val = analysis_type if analysis_type else None

            # Query with synthesis - this returns a structured RAGResponse
            response = rag.query_with_synthesis(
                query=query,
                ticker=ticker,
                analysis_type=analysis_type_val,
                n_results=num_results
            )

            # Format synthesized response as markdown
            output = f"# 💡 Answer\n\n"

            # Add filter context
            if ticker or analysis_type_val:
                output += "*Filtered by: "
                filters = []
                if ticker:
                    filters.append(f"Ticker: {ticker}")
                if analysis_type_val:
                    filters.append(f"Type: {analysis_type_val}")
                output += ", ".join(filters) + "*\n\n"

            # Main synthesized answer
            output += response.answer + "\n\n"

            # Confidence indicator
            output += "---\n\n"
            confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}
            emoji = confidence_emoji.get(response.confidence.lower(), "⚪")
            output += f"**Confidence:** {emoji} {response.confidence.upper()}\n\n"

            # Sources cited
            if response.sources_cited:
                output += "### 📚 Sources\n\n"
                for i, source in enumerate(response.sources_cited, 1):
                    output += f"{i}. {source}\n"
                output += "\n"

            # Limitations/caveats
            if response.limitations:
                output += f"### ⚠️ Limitations\n\n{response.limitations}\n\n"

            # Suggested follow-up questions
            if response.suggested_followup:
                output += "### 💭 Suggested Follow-up Questions\n\n"
                for question in response.suggested_followup:
                    output += f"- {question}\n"
                output += "\n"

            output += "---\n\n*💡 Tip: Click a suggested question to explore further*"

            return output

        except FileNotFoundError:
            return "### 📂 ChromaDB Not Found\n\nThe knowledge base has not been initialized yet.\n\nTo populate it:\n1. Run analyses using the \"Run New Analysis\" mode\n2. Or run: `python scripts/upload_local_to_chroma.py --ticker AAPL --analysis-dir <path>`\n\n See `chroma_db/` directory."
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return f"### ❌ Error\n\nFailed to query knowledge base:\n\n```\n{str(e)}\n```\n\n<details>\n<summary>Full Error Details</summary>\n\n```\n{error_detail}\n```\n</details>"

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
                    gr.Markdown("## Run New Analysis or View Existing")

                    # Mode selection
                    with gr.Row():
                        mode = gr.Radio(
                            choices=["Run New Analysis", "View Existing Analysis", "Query Knowledge Base"],
                            value="Run New Analysis",
                            label="Mode"
                        )

                    # New analysis section
                    with gr.Group(visible=True) as new_analysis_section:
                        gr.Markdown("### Enter Your Financial Research Query")
                        query_input = gr.Textbox(
                            label="Research Query",
                            placeholder="E.g., 'Analyze Tesla's Q3 2025 financial performance'",
                            lines=3,
                            elem_classes=["query-box"]
                        )

                    # Existing analysis section
                    with gr.Group(visible=False) as existing_analysis_section:
                        gr.Markdown("### Select an Existing Analysis")
                        existing_dropdown = gr.Dropdown(
                            label="Previous Analyses",
                            choices=[],
                            interactive=True
                        )
                        load_btn = gr.Button("Load Selected Analysis", variant="primary")

                    # Knowledge base query section
                    with gr.Group(visible=False) as kb_query_section:
                        gr.Markdown("### 🔍 AI-Powered Knowledge Base Q&A")
                        gr.Markdown("*Ask questions about any indexed company and get synthesized, well-cited answers powered by RAG*")

                        with gr.Row():
                            with gr.Column(scale=3):
                                kb_query_input = gr.Textbox(
                                    label="Search Query",
                                    placeholder="E.g., 'What are Apple's main revenue sources?' or 'Compare cloud strategies'",
                                    lines=2
                                )
                            with gr.Column(scale=1):
                                kb_num_results = gr.Slider(
                                    minimum=1,
                                    maximum=10,
                                    value=5,
                                    step=1,
                                    label="Number of Results"
                                )

                        with gr.Row():
                            kb_ticker_filter = gr.Textbox(
                                label="Filter by Ticker (optional)",
                                placeholder="e.g., AAPL",
                                scale=1
                            )
                            kb_analysis_type = gr.Dropdown(
                                label="Filter by Analysis Type (optional)",
                                choices=["", "risk", "financial_metrics", "financial_statements", "comprehensive", "fundamental"],
                                value="",
                                scale=1
                            )

                        kb_search_btn = gr.Button("🔍 Search Knowledge Base", variant="primary", size="lg")

                        kb_results_output = gr.Markdown(
                            label="Search Results",
                            value="*Enter a query and click Search to find relevant information*"
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

            # Mode switcher - show/hide sections based on mode
            def toggle_mode(selected_mode):
                return {
                    new_analysis_section: gr.update(visible=(selected_mode == "Run New Analysis")),
                    existing_analysis_section: gr.update(visible=(selected_mode == "View Existing Analysis")),
                    kb_query_section: gr.update(visible=(selected_mode == "Query Knowledge Base"))
                }

            mode.change(
                fn=toggle_mode,
                inputs=[mode],
                outputs=[new_analysis_section, existing_analysis_section, kb_query_section]
            )

            # Load button for existing analyses
            load_btn.click(
                fn=self.load_existing_analysis,
                inputs=[existing_dropdown],
                outputs=[
                    status_output,
                    comprehensive_output,
                    statements_output,
                    metrics_output,
                    verification_output
                ]
            )

            # Knowledge base search button
            kb_search_btn.click(
                fn=self.query_knowledge_base,
                inputs=[kb_query_input, kb_ticker_filter, kb_analysis_type, kb_num_results],
                outputs=[kb_results_output]
            )

            # Populate dropdown on app load
            def load_dropdown_choices():
                analyses = self.get_existing_analyses()
                choices = [a['label'] for a in analyses]
                # Store mapping for later retrieval
                self.analysis_map = {a['label']: a['value'] for a in analyses}
                return gr.update(choices=choices, value=choices[0] if choices else None)

            app.load(
                fn=load_dropdown_choices,
                outputs=[existing_dropdown]
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
