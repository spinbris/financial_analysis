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
        self.session_id = None  # For API key management
        from financial_research_agent.config import AgentConfig
        self.llm_provider = AgentConfig.DEFAULT_PROVIDER  # Use config default

        # Set SEC EDGAR user agent for edgartools (required for company lookups)
        import os
        from edgar import set_identity
        user_agent = os.getenv(
            "SEC_EDGAR_USER_AGENT",
            "FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"
        )
        set_identity(user_agent)

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
                    # Use the sophisticated ticker extraction from utils.py
                    from financial_research_agent.rag.utils import extract_tickers_from_query
                    detected_tickers = extract_tickers_from_query(content)
                    if detected_tickers:
                        ticker = detected_tickers[0]  # Use first detected ticker
                    else:
                        # Fallback to regex pattern for explicit tickers (e.g., "AAPL", "BRK.B")
                        import re
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
        from financial_research_agent.rag.utils import format_analysis_age
        import json
        import plotly.graph_objects as go

        if not selected_label or selected_label not in self.analysis_map:
            return ("", "", "", "", "", "", "", None, None)

        analysis_path = self.analysis_map[selected_label]
        dir_path = Path(analysis_path)
        if not dir_path.exists():
            return (
                "❌ Analysis directory not found",
                "", "", "", "", "", "", None, None
            )

        # Load report files
        reports = {}
        file_map = {
            'comprehensive': '07_comprehensive_report.md',
            'statements': '03_financial_statements.md',
            'metrics': '04_financial_metrics.md',
            'financial_analysis': '05_financial_analysis.md',
            'risk_analysis': '06_risk_analysis.md',
            'verification': 'data_verification.md'
        }

        for key, filename in file_map.items():
            file_path = dir_path / filename
            if file_path.exists():
                reports[key] = file_path.read_text()
            else:
                reports[key] = f"*{filename} not found*"

        # Load chart data (if available) and convert to Plotly Figure objects
        margin_chart_fig = None
        metrics_chart_fig = None
        risk_chart_fig = None

        margin_chart_path = dir_path / "chart_margins.json"
        if margin_chart_path.exists():
            try:
                with open(margin_chart_path, 'r') as f:
                    margin_chart_data = json.load(f)
                # Convert JSON dict to Plotly Figure
                margin_chart_fig = go.Figure(margin_chart_data)
            except Exception as e:
                print(f"Warning: Failed to load margin chart: {e}")

        metrics_chart_path = dir_path / "chart_metrics.json"
        if metrics_chart_path.exists():
            try:
                with open(metrics_chart_path, 'r') as f:
                    metrics_chart_data = json.load(f)
                # Convert JSON dict to Plotly Figure
                metrics_chart_fig = go.Figure(metrics_chart_data)
            except Exception as e:
                print(f"Warning: Failed to load metrics chart: {e}")

        risk_chart_path = dir_path / "chart_risk_categories.json"
        if risk_chart_path.exists():
            try:
                with open(risk_chart_path, 'r') as f:
                    risk_chart_data = json.load(f)
                # Convert JSON dict to Plotly Figure
                risk_chart_fig = go.Figure(risk_chart_data)
            except Exception as e:
                print(f"Warning: Failed to load risk chart: {e}")

        # Format timestamp with human-readable date
        age_info = format_analysis_age(dir_path.name)

        status_msg = f"""✅ Loaded analysis successfully!

**Analysis Date:** {age_info['formatted']} {age_info['status_emoji']}
**Session ID:** {dir_path.name}
"""

        return (
            status_msg,
            reports.get('comprehensive', ''),
            reports.get('statements', ''),
            reports.get('metrics', ''),
            reports.get('financial_analysis', ''),
            reports.get('risk_analysis', ''),
            reports.get('verification', ''),
            margin_chart_fig,
            metrics_chart_fig,
            risk_chart_fig
        )

    def query_knowledge_base(
        self,
        query: str,
        ticker_filter: str = "",
        analysis_type: str = "",
        num_results: int = 5
    ):
        """
        Query the ChromaDB knowledge base with semantic search and synthesis.

        Uses the RAG synthesis agent to provide coherent, well-cited answers
        instead of raw document chunks.

        Args:
            query: Natural language search query
            ticker_filter: Optional ticker to filter results
            analysis_type: Optional analysis type filter
            num_results: Number of results to return

        Yields:
            Formatted markdown with synthesized answer, sources, and confidence
        """
        from financial_research_agent.rag.chroma_manager import FinancialRAGManager
        from financial_research_agent.rag.utils import extract_tickers_from_query

        if not query or query.strip() == "":
            yield "❌ Please enter a search query"
            return

        # Show initial progress
        yield "🔍 Analyzing query..."

        try:
            # Initialize ChromaDB
            rag = FinancialRAGManager(persist_directory="./chroma_db")

            # Extract tickers from query if not explicitly filtered
            if not ticker_filter:
                detected_tickers = extract_tickers_from_query(query)
            else:
                detected_tickers = [ticker_filter.strip().upper()]

            # Use smart routing to decide how to handle the query
            from financial_research_agent.rag.intelligence import (
                decide_query_routing,
                format_query_decision_prompt
            )

            decision = decide_query_routing(
                detected_tickers=detected_tickers,
                chroma_manager=rag,
                require_fresh=False  # Allow aging data for queries
            )

            # If we should suggest analysis instead of querying, show the prompt
            if decision.action == "suggest_analysis":
                yield "📊 Checking knowledge base status..."
                kb_companies = rag.get_companies_with_status()
                prompt = format_query_decision_prompt(decision, query, kb_companies)
                if prompt:
                    yield prompt
                    return

            # If we have mixed quality data, show a warning but allow proceeding
            if decision.action == "mixed_quality":
                yield "⚠️ Checking data quality..."
                kb_companies = rag.get_companies_with_status()
                prompt = format_query_decision_prompt(decision, query, kb_companies)
                if prompt:
                    yield prompt
                    return

            # Show searching progress
            yield "🔍 Searching knowledge base..."

            # Prepare filters
            ticker = ticker_filter.strip().upper() if ticker_filter else None
            analysis_type_val = analysis_type if analysis_type else None

            # Query with synthesis - this returns a structured RAGResponse
            yield "🤖 Synthesizing answer from sources..."
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

            # Data age warning (if present)
            if response.data_age_warning:
                output += f"### ⏰ Data Age Notice\n\n{response.data_age_warning}\n\n"
                output += "*Consider running a fresh analysis if you need the most current data.*\n\n"

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

            yield output

        except FileNotFoundError:
            yield "### 📂 ChromaDB Not Found\n\nThe knowledge base has not been initialized yet.\n\nTo populate it:\n1. Run analyses using the \"Run New Analysis\" mode\n2. Or run: `python scripts/upload_local_to_chroma.py --ticker AAPL --analysis-dir <path>`\n\n See `chroma_db/` directory."
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            yield f"### ❌ Error\n\nFailed to query knowledge base:\n\n```\n{str(e)}\n```\n\n<details>\n<summary>Full Error Details</summary>\n\n```\n{error_detail}\n```\n</details>"

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
                "", "", "", "", "", "", None, None, None
            )
            return

        try:
            # Initialize empty reports
            reports = {
                'comprehensive': '*⏳ Waiting for comprehensive report...*',
                'statements': '*⏳ Waiting for financial statements...*',
                'metrics': '*⏳ Waiting for financial metrics...*',
                'financial_analysis': '*⏳ Waiting for financial analysis...*',
                'risk_analysis': '*⏳ Waiting for risk analysis...*',
                'verification': '*⏳ Waiting for verification...*'
            }

            # Track which reports we've already loaded
            loaded_reports = set()

            # Define progress callback with streaming updates
            def progress_callback(prog: float, desc: str):
                progress(prog, desc=desc)

            # Configure LLM provider before initializing manager
            progress(0.0, desc="Configuring LLM provider...")
            import os
            from financial_research_agent.llm_provider import get_session_manager

            # Get API keys from session if available
            manager = get_session_manager()
            groq_key = None
            openai_key = None

            if self.session_id:
                groq_key = manager.get_api_key(self.session_id, "groq")
                openai_key = manager.get_api_key(self.session_id, "openai")

            # Configure environment based on provider
            if self.llm_provider == "groq":
                # Use Groq with OpenAI-compatible endpoint
                if groq_key:
                    os.environ["OPENAI_API_KEY"] = groq_key
                elif "GROQ_API_KEY" in os.environ:
                    os.environ["OPENAI_API_KEY"] = os.environ["GROQ_API_KEY"]

                # Set Groq base URL for OpenAI client
                os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"

                # Override model selections to use Groq models
                from financial_research_agent.llm_provider import get_groq_model
                os.environ["PLANNER_MODEL"] = get_groq_model("planner")
                os.environ["SEARCH_MODEL"] = get_groq_model("search")
                os.environ["WRITER_MODEL"] = get_groq_model("writer")
                os.environ["VERIFIER_MODEL"] = get_groq_model("verifier")
                os.environ["EDGAR_MODEL"] = get_groq_model("edgar")
                os.environ["FINANCIALS_MODEL"] = get_groq_model("financials")
                os.environ["RISK_MODEL"] = get_groq_model("risk")
                os.environ["METRICS_MODEL"] = get_groq_model("metrics")

                # Disable reasoning effort for Groq (doesn't support ModelSettings)
                # Set to empty string so get_model_settings() returns None
                os.environ["PLANNER_REASONING_EFFORT"] = ""
                os.environ["SEARCH_REASONING_EFFORT"] = ""
                os.environ["WRITER_REASONING_EFFORT"] = ""
                os.environ["VERIFIER_REASONING_EFFORT"] = ""
                os.environ["EDGAR_REASONING_EFFORT"] = ""
                os.environ["FINANCIALS_REASONING_EFFORT"] = ""
                os.environ["RISK_REASONING_EFFORT"] = ""
                os.environ["METRICS_REASONING_EFFORT"] = ""
            else:
                # Use OpenAI
                if openai_key:
                    os.environ["OPENAI_API_KEY"] = openai_key

                # Clear Groq base URL if previously set
                if "OPENAI_BASE_URL" in os.environ:
                    del os.environ["OPENAI_BASE_URL"]

            # Initialize manager with progress callback
            progress(0.05, desc="Initializing analysis engine...")
            self.manager = EnhancedFinancialResearchManager(progress_callback=progress_callback)

            # Start the analysis in background
            import asyncio
            analysis_task = asyncio.create_task(self.manager.run(query))

            # Poll for completed reports while analysis runs
            last_check = 0
            poll_count = 0
            while not analysis_task.done():
                # Check every 2 seconds for new reports
                await asyncio.sleep(2)
                poll_count += 1

                # Keep progress bar alive even if no updates
                # This prevents the timer from appearing frozen
                if poll_count % 5 == 0:  # Every 10 seconds
                    progress(None, desc="Analysis in progress...")

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
                        from financial_research_agent.rag.utils import format_analysis_age
                        age_info = format_analysis_age(self.current_session_dir.name)
                        status_msg = f"""🔄 Analysis in progress...

**Analysis Started:** {age_info['formatted']}
**Session ID:** {self.current_session_dir.name}
**Query:** {query}

**Completed Reports:** {', '.join(sorted(loaded_reports))}
"""

                        yield (
                            status_msg,
                            reports.get('comprehensive', ''),
                            reports.get('statements', ''),
                            reports.get('metrics', ''),
                            reports.get('financial_analysis', ''),
                            reports.get('risk_analysis', ''),
                            reports.get('verification', ''),
                            None,  # Charts not available yet
                            None,
                            None
                        )

            # Wait for analysis to complete
            await analysis_task

            # Get the session directory that was created
            self.current_session_dir = self.manager.session_dir

            progress(0.95, desc="Loading final reports...")

            # Load all final reports
            reports = self._load_reports()

            # Auto-index to ChromaDB for instant Q&A
            progress(0.96, desc="Indexing to knowledge base...")
            try:
                from financial_research_agent.rag.chroma_manager import FinancialRAGManager
                from financial_research_agent.rag.utils import extract_tickers_from_query

                # Extract ticker from query
                detected_tickers = extract_tickers_from_query(query)
                ticker = detected_tickers[0] if detected_tickers else "UNKNOWN"

                # Index the analysis
                rag = FinancialRAGManager(persist_directory="./chroma_db")
                rag.index_analysis_from_directory(self.current_session_dir, ticker=ticker)
            except Exception as index_error:
                # Don't fail the whole analysis if indexing fails
                print(f"Warning: Failed to auto-index analysis: {index_error}")

            # Auto-generate charts
            progress(0.98, desc="Generating interactive charts...")
            margin_chart_fig = None
            metrics_chart_fig = None
            risk_chart_fig = None

            try:
                from scripts.generate_charts_from_analysis import generate_charts_for_analysis

                # Generate charts automatically
                charts_count = generate_charts_for_analysis(self.current_session_dir, ticker=ticker)

                if charts_count and charts_count > 0:
                    # Load the generated charts
                    import json
                    import plotly.graph_objects as go

                    margin_chart_path = self.current_session_dir / "chart_margins.json"
                    if margin_chart_path.exists():
                        with open(margin_chart_path, 'r') as f:
                            margin_chart_data = json.load(f)
                        margin_chart_fig = go.Figure(margin_chart_data)

                    metrics_chart_path = self.current_session_dir / "chart_metrics.json"
                    if metrics_chart_path.exists():
                        with open(metrics_chart_path, 'r') as f:
                            metrics_chart_data = json.load(f)
                        metrics_chart_fig = go.Figure(metrics_chart_data)

                    risk_chart_path = self.current_session_dir / "chart_risk_categories.json"
                    if risk_chart_path.exists():
                        with open(risk_chart_path, 'r') as f:
                            risk_chart_data = json.load(f)
                        risk_chart_fig = go.Figure(risk_chart_data)
            except Exception as chart_error:
                # Don't fail the whole analysis if chart generation fails
                print(f"Warning: Failed to auto-generate charts: {chart_error}")

            progress(1.0, desc="Complete!")

            from financial_research_agent.rag.utils import format_analysis_age
            age_info = format_analysis_age(self.current_session_dir.name)
            status_msg = f"""✅ Analysis completed successfully!

**Analysis Date:** {age_info['formatted']} {age_info['status_emoji']}
**Session ID:** {self.current_session_dir.name}
**Query:** {query}

📊 All reports are now available in the tabs below. The analysis has been automatically indexed to the knowledge base for instant Q&A!
"""

            yield (
                status_msg,
                reports.get('comprehensive', ''),
                reports.get('statements', ''),
                reports.get('metrics', ''),
                reports.get('financial_analysis', ''),
                reports.get('risk_analysis', ''),
                reports.get('verification', ''),
                margin_chart_fig,
                metrics_chart_fig,
                risk_chart_fig
            )

        except Exception as e:
            error_msg = f"❌ Error during analysis:\n\n{str(e)}"
            yield (error_msg, "", "", "", "", "", "", None, None, None)

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
            'financial_analysis': '05_financial_analysis.md',
            'risk_analysis': '06_risk_analysis.md',
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

    def _format_missing_companies_prompt(self, missing_tickers: list[str], query: str) -> str:
        """
        Format a helpful prompt when companies are not in knowledge base.

        Args:
            missing_tickers: List of tickers not in KB
            query: Original user query

        Returns:
            Formatted markdown guidance
        """
        if len(missing_tickers) == 1:
            ticker = missing_tickers[0]
            return f"""## ⚠️ Company Not in Knowledge Base

**{ticker}** has not been analyzed yet and is not in the knowledge base.

### To answer questions about {ticker}:

1. **Run a comprehensive analysis first** (Recommended)
   - Switch to the **"Run New Analysis"** mode
   - Enter query: `Analyze {ticker}'s most recent quarterly performance`
   - Time: ~3-5 minutes
   - Cost: ~$0.08
   - Includes: Complete SEC filings, 118+ line items, risk analysis

2. **Try a different company**
   - Query companies already in the knowledge base (see below)

---

### 📊 Companies Currently in Knowledge Base:

{self._format_kb_companies_list()}

---

*Once {ticker} is analyzed, you can ask unlimited questions about it instantly!*
"""
        else:
            ticker_list = ", ".join(missing_tickers)
            return f"""## ⚠️ Multiple Companies Not in Knowledge Base

The following companies are not yet in the knowledge base:
**{ticker_list}**

### To compare these companies:

1. **Analyze each company** (Recommended for accurate comparisons)
   - Switch to **"Run New Analysis"** mode
   - Analyze each ticker separately (or in sequence)
   - Total time: ~{len(missing_tickers) * 3}-{len(missing_tickers) * 5} minutes
   - Total cost: ~${len(missing_tickers) * 0.08:.2f}

2. **Partial comparison** (if some companies are in KB)
   - Refine your query to only include companies already analyzed

---

### 📊 Companies Currently in Knowledge Base:

{self._format_kb_companies_list()}

---

*Tip: Build up your knowledge base over time by analyzing companies as needed!*
"""

    def _format_kb_companies_list(self) -> str:
        """
        Get formatted list of companies in knowledge base.

        Returns:
            Markdown formatted list
        """
        from financial_research_agent.rag.chroma_manager import FinancialRAGManager
        from financial_research_agent.rag.utils import format_company_status

        try:
            rag = FinancialRAGManager(persist_directory="./chroma_db")
            companies = rag.get_companies_with_status()

            if not companies:
                return "*Knowledge base is empty. Run your first analysis!*"

            # Format as bullet list
            lines = []
            for company in companies[:20]:  # Limit to top 20
                lines.append(f"- {format_company_status(company)}")

            if len(companies) > 20:
                lines.append(f"\n*...and {len(companies) - 20} more companies*")

            return "\n".join(lines)

        except Exception:
            return "*Unable to load knowledge base status*"

    def save_session_keys(self, provider: str, groq_key: str, openai_key: str) -> str:
        """Save API keys for the current session."""
        from financial_research_agent.llm_provider import get_session_manager

        # Create session if needed
        if not self.session_id:
            manager = get_session_manager()
            self.session_id = manager.create_session()

        manager = get_session_manager()

        # Store provided keys
        if groq_key:
            manager.set_api_key(self.session_id, "groq", groq_key)

        if openai_key:
            manager.set_api_key(self.session_id, "openai", openai_key)

        # Update provider preference
        self.llm_provider = provider

        # Build status message
        status_parts = []
        if groq_key:
            status_parts.append("✅ Groq key saved")
        if openai_key:
            status_parts.append("✅ OpenAI key saved")

        if status_parts:
            status = " | ".join(status_parts)
            return f"**{status}** (Active provider: {provider.upper()})\n\n*Keys stored in-memory only. Remember to delete from provider after use!*"
        else:
            return f"*Using environment/default keys (Active provider: {provider.upper()})*"

    def clear_session_keys(self) -> str:
        """Clear all session keys."""
        from financial_research_agent.llm_provider import get_session_manager

        if self.session_id:
            manager = get_session_manager()
            manager.clear_session(self.session_id)
            self.session_id = None
            return "✅ **Session keys cleared**\n\n*Remember to delete keys from your provider (Groq/OpenAI)!*"
        else:
            return "*No session keys to clear*"

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
                """
            )

            # Company-Centric Dashboard Section
            gr.Markdown("## 🏢 Company Dashboard")

            with gr.Row():
                with gr.Column(scale=2):
                    company_selector = gr.Dropdown(
                        label="Select Company or Enter Ticker/Name",
                        choices=[],
                        allow_custom_value=True,
                        interactive=True
                    )
                with gr.Column(scale=1):
                    add_new_ticker = gr.Textbox(
                        label="Or Enter Company Name/Ticker",
                        placeholder="e.g., Apple, AAPL, Microsoft",
                        max_lines=1
                    )
                with gr.Column(scale=1):
                    add_company_btn = gr.Button("+ Add Company", variant="primary")

            # Company Status Card
            company_status_card = gr.Markdown(elem_classes=["status-box"])

            # Action Buttons Row
            with gr.Row():
                ask_question_btn = gr.Button("💭 Ask Questions", variant="primary", size="lg")
                refresh_analysis_btn = gr.Button("🔄 Refresh Analysis", variant="secondary", size="lg")
                view_reports_btn = gr.Button("📊 View Reports", variant="secondary", size="lg")

            gr.Markdown("---")

            # Functions for company dashboard
            def load_company_list():
                """Load list of companies from knowledge base."""
                from financial_research_agent.rag.chroma_manager import FinancialRAGManager

                try:
                    rag = FinancialRAGManager(persist_directory="./chroma_db")
                    companies = rag.get_companies_with_status()

                    if not companies:
                        return gr.update(choices=[], value=None)

                    # Format: "AAPL - Apple Inc. (updated 2 days ago)"
                    choices = []
                    for company in companies:
                        status_emoji = {"fresh": "✅", "aging": "⚠️", "stale": "🔴", "missing": "❌"}
                        emoji = status_emoji.get(company["status"], "❓")
                        label = f"{emoji} {company['ticker']} - {company['company']} ({company['days_old']}d ago)"
                        choices.append((label, company["ticker"]))

                    return gr.update(choices=choices)
                except Exception as e:
                    return gr.update(choices=[], value=None)

            def show_company_status(selected_input):
                """Show status card for selected company (ticker or name)."""
                if not selected_input:
                    return """
                    ### 👋 Welcome to Financial Research Agent

                    **Get Started:**
                    1. Select a company from the dropdown above (if available in your knowledge base)
                    2. Or enter a company name or ticker symbol (e.g., "Apple", "AAPL", "Microsoft", "MSFT")

                    **What You Can Do:**
                    - 🔬 **Run Deep Analysis**: Generate comprehensive SEC filing analysis (~3-5 min)
                    - 💬 **Ask Questions**: Query knowledge base for instant answers (~5 sec)
                    - 📊 **View Reports**: Access detailed financial reports and charts

                    **Examples:** Try "Apple", "Tesla", "AAPL", "TSLA", "Amazon", or any US public company!
                    """

                from financial_research_agent.rag.chroma_manager import FinancialRAGManager
                from financial_research_agent.utils.sec_filing_checker import SECFilingChecker
                from edgar import Company, find_company

                # First, try to resolve company name to ticker if needed
                selected_ticker = selected_input.strip()

                try:
                    # Try direct ticker lookup first
                    try:
                        company = Company(selected_ticker.upper())
                        selected_ticker = company.tickers[0] if company.tickers else selected_ticker.upper()
                    except:
                        # If direct lookup fails, try company name search
                        try:
                            results = find_company(selected_ticker)
                            if results:
                                if isinstance(results, list) and len(results) > 0:
                                    selected_ticker = results[0].tickers[0] if hasattr(results[0], 'tickers') and results[0].tickers else selected_ticker.upper()
                                else:
                                    selected_ticker = results.tickers[0] if hasattr(results, 'tickers') and results.tickers else selected_ticker.upper()
                        except:
                            # Use input as-is if lookup fails
                            selected_ticker = selected_ticker.upper()
                except:
                    # Use input as-is if any error
                    selected_ticker = selected_ticker.upper()

                # Now show status for the resolved ticker
                try:
                    rag = FinancialRAGManager(persist_directory="./chroma_db")
                    status = rag.check_company_status(selected_ticker)

                    if not status["in_kb"]:
                        return f"""
                        ### ❌ {selected_ticker} Not in Knowledge Base

                        **To analyze this company:**
                        1. Click "🔄 Refresh Analysis" to run a comprehensive analysis (~3-5 min, ~$0.08)
                        2. This will extract complete financials from SEC filings and index them for instant Q&A

                        **Or try web search fallback** (less reliable, no SEC data):
                        - Type your question below and we'll attempt to answer using web sources
                        """

                    # Company is in KB - show detailed status
                    metadata = status["metadata"]
                    status_emoji = {"fresh": "✅", "aging": "⚠️", "stale": "🔴"}
                    emoji = status_emoji.get(status["status"], "❓")

                    output = f"""
                    ### {emoji} {metadata['company']} ({metadata['ticker']})

                    **Status:** {status["status"].upper()} | **Last Updated:** {metadata['last_updated']} ({metadata['days_old']} days ago)

                    **Latest Data:**
                    - **Period:** {metadata['period']}
                    - **Filing:** {metadata['filing']}
                    """

                    # Check for newer filings
                    try:
                        checker = SECFilingChecker()
                        comparison = checker.compare_to_indexed_date(
                            selected_ticker,
                            metadata['last_updated']
                        )

                        if comparison["newer_filing_available"]:
                            output += f"""

                            ### 🆕 Newer Filing Available!

                            **Latest SEC Filing:** {comparison['latest_filing_type']} filed {comparison['latest_filing_date']} ({comparison['days_behind']} days newer)

                            **Recommendation:** Click "🔄 Refresh Analysis" to get the latest data
                            """
                        else:
                            output += f"""

                            ✅ **Up to date** - No newer filings available
                            """
                    except Exception as e:
                        output += f"\n\n*Could not check for newer filings: {str(e)}*"

                    # Add quick actions
                    output += f"""

                    ---

                    **Quick Actions:**
                    - 💭 **Ask Questions**: Query this company's data instantly
                    - 🔄 **Refresh Analysis**: Update with latest SEC filings
                    - 📊 **View Reports**: See detailed analysis and charts
                    """

                    return output

                except Exception as e:
                    return f"### ❌ Error\n\nFailed to load company status:\n```\n{str(e)}\n```"

            # Load companies on app start
            app.load(fn=load_company_list, outputs=[company_selector])

            # Update status card when company selected
            company_selector.change(
                fn=show_company_status,
                inputs=[company_selector],
                outputs=[company_status_card]
            )

            # Handle adding new company
            def handle_add_company(company_input):
                """Handle adding a new company to analyze using flexible lookup."""
                if not company_input:
                    return {
                        company_status_card: "⚠️ Please enter a company name or ticker symbol",
                        company_selector: gr.update(),
                        add_new_ticker: gr.update()
                    }

                search_term = company_input.strip()

                # Use edgartools to lookup company
                # Note: SEC user agent is set in __init__ for all edgartools calls
                try:
                    from edgar import Company, find_company

                    # Try direct ticker lookup first (fast)
                    try:
                        company = Company(search_term.upper())
                        ticker = company.tickers[0] if company.tickers else search_term.upper()
                        company_name = company.name if hasattr(company, 'name') else ticker

                        # Success - show status for this ticker
                        status_text = show_company_status(ticker)

                        return {
                            company_status_card: status_text,
                            company_selector: gr.update(value=ticker),
                            add_new_ticker: gr.update(value="")
                        }
                    except:
                        # Direct lookup failed, try search
                        pass

                    # If direct lookup fails, try company name search
                    results = find_company(search_term)

                    if not results:
                        return {
                            company_status_card: f"""
                            ### ❌ Company Not Found

                            Could not find "{search_term}" in SEC EDGAR database.

                            **Suggestions:**
                            - Check spelling (e.g., "Apple", "Microsoft", "Tesla")
                            - Try the stock ticker instead (e.g., "AAPL", "MSFT", "TSLA")
                            - Make sure the company is publicly traded in the US

                            **Examples that work:**
                            - Company names: Apple, Microsoft, Tesla, Amazon
                            - Ticker symbols: AAPL, MSFT, TSLA, AMZN
                            """,
                            company_selector: gr.update(),
                            add_new_ticker: gr.update(value="")
                        }

                    # If we get multiple results, use the first match
                    if isinstance(results, list) and len(results) > 0:
                        # Use first result
                        first_result = results[0]
                        ticker = first_result.tickers[0] if hasattr(first_result, 'tickers') and first_result.tickers else search_term.upper()
                        company_name = first_result.name if hasattr(first_result, 'name') else ticker
                    else:
                        # Single result
                        ticker = results.tickers[0] if hasattr(results, 'tickers') and results.tickers else search_term.upper()
                        company_name = results.name if hasattr(results, 'name') else ticker

                    # Show status for the found company
                    status_text = show_company_status(ticker)

                    # Add note about the lookup if company name was used
                    if search_term.upper() != ticker:
                        status_text = f"""
                        ### ✅ Found: {company_name}

                        *Matched "{search_term}" → Ticker: **{ticker}***

                        ---

                        {status_text}
                        """

                    return {
                        company_status_card: status_text,
                        company_selector: gr.update(value=ticker),
                        add_new_ticker: gr.update(value="")
                    }

                except Exception as e:
                    import traceback
                    error_detail = traceback.format_exc()
                    return {
                        company_status_card: f"""
                        ### ❌ Error Looking Up Company

                        Failed to find "{search_term}" in SEC EDGAR database.

                        **Error:** {str(e)}

                        **Suggestions:**
                        - Try entering the stock ticker directly (e.g., AAPL, MSFT)
                        - Check spelling of company name
                        - Ensure company is publicly traded in the US

                        <details>
                        <summary>Technical Details</summary>

                        ```
                        {error_detail}
                        ```
                        </details>
                        """,
                        company_selector: gr.update(),
                        add_new_ticker: gr.update(value="")
                    }

            add_company_btn.click(
                fn=handle_add_company,
                inputs=[add_new_ticker],
                outputs=[company_status_card, company_selector, add_new_ticker]
            )

            with gr.Tabs() as tabs:

                # ==================== TAB 1: Ask Questions ====================
                with gr.Tab("💭 Ask Questions", id=0):
                    gr.Markdown("## 💬 Ask Questions About Your Company")
                    gr.Markdown("*Get instant, AI-powered answers from the knowledge base with full citations*")

                    query_input = gr.Textbox(
                        label="Your Question",
                        placeholder="E.g., 'What were Apple's Q3 revenues?' or 'What are the main risk factors?'",
                        lines=3,
                        elem_classes=["query-box"]
                    )

                    with gr.Row():
                        ask_btn = gr.Button("🔍 Ask Question", variant="primary", size="lg", scale=3)
                        clear_btn = gr.Button("Clear", variant="secondary", scale=1)

                    kb_results_output = gr.Markdown(
                        value="*Select a company above and enter your question*",
                        elem_classes=["report-content"]
                    )

                    gr.Markdown("*Common questions: 'What were Q3 revenues?' • 'What are the main risks?' • 'How has profitability changed?'*")

                # ==================== TAB 2: Run/Refresh Analysis ====================
                with gr.Tab("🔄 Run Analysis", id=1):
                    gr.Markdown("## 🔬 Generate Comprehensive SEC Filing Analysis")
                    gr.Markdown("""
                    **This will:**
                    - Extract complete financials from latest SEC filings (10-K/10-Q)
                    - Analyze 118+ line items with comparative periods
                    - Calculate financial ratios and metrics
                    - Assess risk factors
                    - Generate comprehensive 3-5 page report
                    - Index everything for instant Q&A

                    **Time:** ~3-5 minutes | **Cost:** ~$0.08 per analysis
                    """)

                    analysis_query_input = gr.Textbox(
                        label="Analysis Query (optional - will auto-detect from selected company)",
                        placeholder="E.g., 'Analyze Apple's latest quarterly performance'",
                        lines=2,
                        elem_classes=["query-box"]
                    )

                    generate_btn = gr.Button(
                        "🚀 Run Comprehensive Analysis",
                        variant="primary",
                        size="lg"
                    )

                    status_output = gr.Markdown(
                        label="Analysis Status",
                        elem_classes=["status-box"],
                        value="*Select a company and click 'Run Comprehensive Analysis' to begin*"
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

                # ==================== TAB 5: Financial Analysis ====================
                with gr.Tab("💡 Financial Analysis", id=4):
                    gr.Markdown(
                        """
                        ## Specialist Financial Analysis (800-1200 words)
                        *In-depth analysis of financial performance, trends, and key metrics
                        by the Financial Analyst agent with direct access to SEC EDGAR data*
                        """
                    )

                    financial_analysis_output = gr.Markdown(
                        elem_classes=["report-content"]
                    )

                    # Interactive Charts Section
                    gr.Markdown("### 📊 Interactive Charts")

                    with gr.Row():
                        margin_chart = gr.Plot(
                            label="Profitability Margins",
                            visible=True
                        )
                        metrics_chart = gr.Plot(
                            label="Key Financial Metrics",
                            visible=True
                        )

                    with gr.Row():
                        segment_chart = gr.Plot(
                            label="Revenue by Segment",
                            visible=True
                        )

                    with gr.Row():
                        download_fin_analysis_md = gr.DownloadButton(
                            label="📥 Download Financial Analysis",
                            visible=False
                        )

                # ==================== TAB 6: Risk Analysis ====================
                with gr.Tab("⚠️ Risk Analysis", id=5):
                    gr.Markdown(
                        """
                        ## Specialist Risk Assessment (800-1200 words)
                        *Comprehensive risk analysis prioritizing 10-K Item 1A Risk Factors
                        by the Risk Analyst agent with access to annual and quarterly SEC filings*
                        """
                    )

                    risk_analysis_output = gr.Markdown(
                        elem_classes=["report-content"]
                    )

                    with gr.Row():
                        risk_chart = gr.Plot(
                            label="Risk Category Breakdown (Keyword-based Analysis)",
                            visible=True
                        )

                    with gr.Row():
                        download_risk_analysis_md = gr.DownloadButton(
                            label="📥 Download Risk Analysis",
                            visible=False
                        )

                # ==================== TAB 7: Data Verification ====================
                with gr.Tab("✅ Data Verification", id=6):
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

            # ==================== EVENT HANDLERS ====================

            # Connect dashboard action buttons
            def handle_ask_questions_click(selected_ticker):
                """Switch to Ask Questions tab."""
                if not selected_ticker:
                    return {tabs: gr.update(selected=0)}
                return {tabs: gr.update(selected=0)}

            def handle_refresh_analysis_click(selected_ticker):
                """Switch to Run Analysis tab and populate query."""
                if not selected_ticker:
                    return {
                        tabs: gr.update(selected=1),
                        analysis_query_input: ""
                    }
                # Auto-populate query with ticker
                query = f"Analyze {selected_ticker}'s latest quarterly financial performance"
                return {
                    tabs: gr.update(selected=1),
                    analysis_query_input: query
                }

            def handle_view_reports_click(selected_ticker):
                """Switch to Comprehensive Report tab."""
                return {tabs: gr.update(selected=2)}

            ask_question_btn.click(
                fn=handle_ask_questions_click,
                inputs=[company_selector],
                outputs=[tabs]
            )

            refresh_analysis_btn.click(
                fn=handle_refresh_analysis_click,
                inputs=[company_selector],
                outputs=[tabs, analysis_query_input]
            )

            view_reports_btn.click(
                fn=handle_view_reports_click,
                inputs=[company_selector],
                outputs=[tabs]
            )

            # Connect Ask Question button
            def handle_ask_question(question, selected_ticker):
                """Handle asking a question."""
                if not question or not question.strip():
                    return "⚠️ Please enter a question"

                # Use selected ticker as filter
                ticker_filter = selected_ticker if selected_ticker else ""

                # Call the existing query_knowledge_base function
                result = ""
                for chunk in self.query_knowledge_base(question, ticker_filter, "", 5):
                    result = chunk  # Get final result

                return result

            ask_btn.click(
                fn=handle_ask_question,
                inputs=[query_input, company_selector],
                outputs=[kb_results_output]
            )

            clear_btn.click(
                fn=lambda: ("", "*Select a company above and enter your question*"),
                outputs=[query_input, kb_results_output]
            )

            # Connect generate button to analysis function
            async def handle_generate_analysis(query, selected_ticker):
                """Handle running comprehensive analysis."""
                # Auto-detect from selected company if query is empty
                if not query or not query.strip():
                    if selected_ticker:
                        query = f"Analyze {selected_ticker}'s latest quarterly financial performance"
                    else:
                        yield (
                            "⚠️ Please select a company or enter an analysis query",
                            "", "", "", "", "", "", None, None, None
                        )
                        return

                # Call the existing generate_analysis function
                async for result in self.generate_analysis(query):
                    yield result

            generate_btn.click(
                fn=handle_generate_analysis,
                inputs=[analysis_query_input, company_selector],
                outputs=[
                    status_output,
                    comprehensive_output,
                    statements_output,
                    metrics_output,
                    financial_analysis_output,
                    risk_analysis_output,
                    verification_output,
                    margin_chart,
                    metrics_chart,
                    risk_chart
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
