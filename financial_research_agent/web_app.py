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


# KB Query examples
KB_QUERY_EXAMPLES = [
    "What are Apple's main revenue sources?",
    "Compare Microsoft and Google's cloud strategies",
    "What are Tesla's key financial risks?",
    "How has Amazon's profitability changed over time?",
    "What is NVIDIA's debt-to-equity ratio?",
    "Compare profit margins across tech companies",
]


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

    def get_existing_analyses(self):
        """Get list of existing analysis directories with company names."""
        output_dir = Path("financial_research_agent/output")
        if not output_dir.exists():
            return []

        # Find all analysis directories (format: YYYYMMDD_HHMMSS)
        dirs = sorted(
            [d for d in output_dir.iterdir() if d.is_dir() and d.name[0].isdigit()],
            key=lambda x: x.name,
            reverse=True  # Most recent first
        )

        # Extract company name and ticker from 00_query.md
        analyses = []
        for dir_path in dirs[:50]:  # Limit to 50 most recent
            query_file = dir_path / "00_query.md"
            comprehensive_file = dir_path / "07_comprehensive_report.md"

            # Check if analysis is complete
            if comprehensive_file.exists():
                # Try to extract company name and ticker from metadata.json (preferred)
                ticker = "Unknown"
                company_name = None

                # First, try to read from metadata.json
                metadata_file = dir_path / "metadata.json"
                if metadata_file.exists():
                    try:
                        import json
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            ticker = metadata.get('ticker', 'Unknown')
                            company_name = metadata.get('company_name')
                    except Exception:
                        pass  # Fall through to query file parsing

                # Fallback to query file extraction if metadata not available
                if ticker == "Unknown" and query_file.exists():
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

                # Create a nice label with company name and ticker
                if company_name:
                    # Format: "Apple Inc. (AAPL)" or "WESTPAC BANKING CORP (WBKCY)"
                    label = f"{company_name} ({ticker})"
                else:
                    # Fallback to just ticker if no company name available
                    label = ticker

                analyses.append({
                    'label': label,
                    'value': str(dir_path),
                    'ticker': ticker,
                    'company_name': company_name,
                    'timestamp': dir_path.name
                })

        # Deduplicate by ticker - keep most recent for each ticker
        seen_tickers = {}
        for analysis in analyses:
            ticker_key = analysis['ticker']
            if ticker_key not in seen_tickers or analysis['timestamp'] > seen_tickers[ticker_key]['timestamp']:
                seen_tickers[ticker_key] = analysis

        # Convert back to list and sort alphabetically by ticker
        unique_analyses = list(seen_tickers.values())
        unique_analyses.sort(key=lambda x: x['ticker'])
        return unique_analyses

    def load_existing_analysis(self, selected_label: str):
        """Load an existing analysis from disk."""
        from financial_research_agent.rag.utils import format_analysis_age
        import json
        import plotly.graph_objects as go

        if not selected_label or selected_label not in self.analysis_map:
            return ("", "", "", "", "", "", "", "", "", None, None, None)

        analysis_path = self.analysis_map[selected_label]
        dir_path = Path(analysis_path)
        if not dir_path.exists():
            return (
                "❌ Analysis directory not found",
                "", "", "", "", "", "", "", "", None, None, None
            )

        # Load report files
        reports = {}
        file_map = {
            'comprehensive': '07_comprehensive_report.md',
            'statements': '03_financial_statements.md',
            'metrics': '04_financial_metrics.md',
            'financial_analysis': '05_financial_analysis.md',
            'risk_analysis': '06_risk_analysis.md',
            'verification': '08_verification.md',
            'search_results': '02_search_results.md',
            'edgar_filings': '02_edgar_filings.md'
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
            reports.get('search_results', '*Search results not available for this analysis*'),
            reports.get('edgar_filings', '*EDGAR filings data not available for this analysis*'),
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
                /* ==================== PROFESSIONAL FINANCIAL PLATFORM STYLING ==================== */

                /* Global Container */
                .gradio-container {
                    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif !important;
                    max-width: 1600px;
                    margin: 0 auto;
                    background: #fafbfc;
                }

                /* Clean Card-Based Layout */
                .gr-box, .gr-form, .gr-panel {
                    border-radius: 12px !important;
                    border: 1px solid #e1e4e8 !important;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
                    background: white !important;
                    padding: 20px !important;
                }

                /* Header Typography */
                h1 {
                    font-size: 2.25rem !important;
                    font-weight: 700 !important;
                    color: #0d1117 !important;
                    letter-spacing: -0.02em !important;
                    margin-bottom: 0.5rem !important;
                }

                h2 {
                    font-size: 1.75rem !important;
                    font-weight: 600 !important;
                    color: #1f2937 !important;
                    margin-top: 1.5rem !important;
                    margin-bottom: 1rem !important;
                }

                h3 {
                    font-size: 1.25rem !important;
                    font-weight: 600 !important;
                    color: #374151 !important;
                    margin-top: 1.25rem !important;
                    margin-bottom: 0.75rem !important;
                }

                /* Primary Action Buttons */
                .gr-button-primary {
                    background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%) !important;
                    border: none !important;
                    border-radius: 8px !important;
                    font-weight: 600 !important;
                    font-size: 15px !important;
                    padding: 12px 24px !important;
                    box-shadow: 0 4px 12px rgba(0, 102, 204, 0.2) !important;
                    transition: all 0.2s ease !important;
                    letter-spacing: 0.01em !important;
                }

                .gr-button-primary:hover {
                    background: linear-gradient(135deg, #0052a3 0%, #003d7a 100%) !important;
                    box-shadow: 0 6px 16px rgba(0, 102, 204, 0.3) !important;
                    transform: translateY(-1px) !important;
                }

                /* Secondary Buttons */
                .gr-button-secondary {
                    background: white !important;
                    border: 1.5px solid #d1d5db !important;
                    border-radius: 8px !important;
                    color: #374151 !important;
                    font-weight: 500 !important;
                    transition: all 0.2s ease !important;
                }

                .gr-button-secondary:hover {
                    border-color: #0066cc !important;
                    background: #f8fafc !important;
                    color: #0066cc !important;
                }

                /* Template Buttons */
                .template-button {
                    margin: 6px 4px !important;
                    border-radius: 6px !important;
                    font-size: 14px !important;
                    padding: 8px 16px !important;
                    background: #f3f4f6 !important;
                    border: 1px solid #e5e7eb !important;
                    color: #1f2937 !important;
                    font-weight: 500 !important;
                    transition: all 0.15s ease !important;
                }

                .template-button:hover {
                    background: white !important;
                    border-color: #0066cc !important;
                    color: #0066cc !important;
                    box-shadow: 0 2px 6px rgba(0, 102, 204, 0.1) !important;
                }

                /* Input Fields */
                .query-box textarea,
                input[type="text"],
                .gr-textbox {
                    font-size: 15px !important;
                    border: 1.5px solid #d1d5db !important;
                    border-radius: 8px !important;
                    padding: 12px 16px !important;
                    background: white !important;
                    transition: all 0.2s ease !important;
                }

                .query-box textarea:focus,
                input[type="text"]:focus,
                .gr-textbox:focus {
                    border-color: #0066cc !important;
                    box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1) !important;
                    outline: none !important;
                }

                /* Status Box */
                .status-box {
                    padding: 24px !important;
                    border-radius: 12px !important;
                    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%) !important;
                    border: 1px solid #bae6fd !important;
                    box-shadow: 0 2px 8px rgba(14, 165, 233, 0.08) !important;
                }

                /* Report Content - Professional Reading Experience */
                .report-content {
                    font-family: 'Charter', 'Georgia', 'Times New Roman', serif !important;
                    font-size: 16px !important;
                    line-height: 1.7 !important;
                    color: #1f2937 !important;
                    padding: 24px !important;
                }

                .report-content p {
                    margin-bottom: 1.25em !important;
                }

                .report-content strong {
                    color: #0d1117 !important;
                    font-weight: 600 !important;
                }

                /* Financial Tables - Bloomberg/Morningstar Style */
                .report-content table {
                    border-collapse: collapse !important;
                    width: 100% !important;
                    margin: 24px 0 !important;
                    background: white !important;
                    border-radius: 8px !important;
                    overflow: hidden !important;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
                }

                .report-content table thead {
                    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
                    border-bottom: 2px solid #0066cc !important;
                }

                .report-content table th {
                    font-weight: 600 !important;
                    font-size: 13px !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.05em !important;
                    padding: 14px 16px !important;
                    color: #374151 !important;
                    text-align: left !important;
                }

                .report-content table td {
                    padding: 12px 16px !important;
                    border-bottom: 1px solid #f1f5f9 !important;
                    font-size: 15px !important;
                }

                /* Alternate row colors for better readability */
                .report-content table tbody tr:nth-child(even) {
                    background-color: #fafbfc !important;
                }

                .report-content table tbody tr:hover {
                    background-color: #f0f9ff !important;
                    transition: background-color 0.15s ease !important;
                }

                /* Right-align numeric columns */
                .report-content table td:nth-child(2),
                .report-content table td:nth-child(3),
                .report-content table td:nth-child(4),
                .report-content table td:nth-child(5),
                .report-content table th:nth-child(2),
                .report-content table th:nth-child(3),
                .report-content table th:nth-child(4),
                .report-content table th:nth-child(5) {
                    text-align: right !important;
                }

                /* First column (labels) left-aligned */
                .report-content table td:first-child,
                .report-content table th:first-child {
                    text-align: left !important;
                    font-weight: 500 !important;
                }

                /* Monospace font for numbers - professional financial styling */
                .report-content table td:nth-child(n+2) {
                    font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', 'Courier New', monospace !important;
                    font-size: 14px !important;
                    font-variant-numeric: tabular-nums !important;
                }

                /* Source Attribution Badges */
                .report-content code {
                    background: #f3f4f6 !important;
                    border: 1px solid #e5e7eb !important;
                    border-radius: 4px !important;
                    padding: 2px 8px !important;
                    font-size: 13px !important;
                    font-family: 'SF Mono', Monaco, monospace !important;
                    color: #374151 !important;
                }

                /* Enhanced Code Blocks */
                .report-content pre {
                    background: #f8fafc !important;
                    border: 1px solid #e5e7eb !important;
                    border-radius: 8px !important;
                    padding: 16px !important;
                    overflow-x: auto !important;
                    font-size: 14px !important;
                }

                /* Tabs */
                .tab-nav button {
                    font-weight: 500 !important;
                    font-size: 15px !important;
                    padding: 12px 24px !important;
                    border-radius: 8px 8px 0 0 !important;
                    color: #6b7280 !important;
                    transition: all 0.2s ease !important;
                }

                .tab-nav button.selected {
                    color: #0066cc !important;
                    background: white !important;
                    border-bottom: 2px solid #0066cc !important;
                    font-weight: 600 !important;
                }

                /* Markdown Lists */
                .report-content ul,
                .report-content ol {
                    margin-left: 24px !important;
                    margin-bottom: 1.25em !important;
                }

                .report-content li {
                    margin-bottom: 0.5em !important;
                    line-height: 1.6 !important;
                }

                /* Blockquotes */
                .report-content blockquote {
                    border-left: 4px solid #0066cc !important;
                    padding-left: 20px !important;
                    margin: 20px 0 !important;
                    color: #4b5563 !important;
                    font-style: italic !important;
                    background: #f8fafc !important;
                    padding: 16px 20px !important;
                    border-radius: 0 8px 8px 0 !important;
                }

                /* Horizontal Rules */
                .report-content hr {
                    border: none !important;
                    border-top: 2px solid #e5e7eb !important;
                    margin: 32px 0 !important;
                }

                /* Download Buttons */
                .gr-download-button {
                    background: #10b981 !important;
                    color: white !important;
                    border: none !important;
                    border-radius: 6px !important;
                    font-weight: 500 !important;
                    padding: 8px 16px !important;
                    transition: all 0.2s ease !important;
                }

                .gr-download-button:hover {
                    background: #059669 !important;
                    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
                }

                /* Radio Buttons & Dropdowns */
                .gr-radio,
                .gr-dropdown {
                    border-radius: 8px !important;
                }

                /* Progress Bar */
                .progress-bar {
                    background: linear-gradient(90deg, #0066cc, #0ea5e9) !important;
                    border-radius: 8px !important;
                }

                /* Error Messages */
                .error {
                    background: #fef2f2 !important;
                    border: 1px solid #fecaca !important;
                    color: #991b1b !important;
                    padding: 16px !important;
                    border-radius: 8px !important;
                }

                /* Success Messages */
                .success {
                    background: #f0fdf4 !important;
                    border: 1px solid #bbf7d0 !important;
                    color: #166534 !important;
                    padding: 16px !important;
                    border-radius: 8px !important;
                }

                /* Plotly Charts */
                .js-plotly-plot {
                    border-radius: 12px !important;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
                }

                /* Footer */
                footer {
                    text-align: center !important;
                    color: #6b7280 !important;
                    font-size: 14px !important;
                    padding: 32px 0 !important;
                }

                /* Mobile Responsiveness */
                @media (max-width: 768px) {
                    .gradio-container {
                        padding: 12px !important;
                    }

                    h1 {
                        font-size: 1.75rem !important;
                    }

                    h2 {
                        font-size: 1.5rem !important;
                    }

                    .report-content {
                        font-size: 15px !important;
                        padding: 16px !important;
                    }

                    .report-content table {
                        font-size: 13px !important;
                    }
                }

                /* ==================== NUMBERED SECTION BADGES ==================== */
                .section-header {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 16px !important;
                }

                .section-badge {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    font-weight: 600;
                    font-size: 18px;
                    flex-shrink: 0;
                    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                }

                .section-title {
                    font-size: 1.5rem !important;
                    font-weight: 600 !important;
                    margin: 0 !important;
                    color: #0d1117;
                }

                /* Section containers */
                .home-section {
                    background: white !important;
                    border-radius: 12px !important;
                    padding: 24px !important;
                    margin-bottom: 24px !important;
                    border: 1px solid #e1e4e8 !important;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
                }
            """
        ) as app:

            # Header - Simplified to match Figma design
            gr.Markdown(
                """
                # 📊 AI Financial Analysis Knowledge Base
                Select companies, add new analysis, and query the knowledge base
                """
            )

            # Knowledge Base Status Banner (Summary only)
            kb_status_banner = gr.Markdown(elem_classes=["status-box"])

            # View Details button and expandable details section
            with gr.Row():
                view_details_btn = gr.Button("📋 View Details", size="sm", variant="secondary")

            kb_details_section = gr.Markdown(visible=False, elem_classes=["status-box"])

            # Initialize KB status on load
            def load_kb_status():
                from financial_research_agent.rag.intelligence import get_kb_summary_banner
                from financial_research_agent.rag.chroma_manager import FinancialRAGManager

                try:
                    rag = FinancialRAGManager(persist_directory="./chroma_db")
                    return get_kb_summary_banner(rag)
                except Exception as e:
                    return f"### 💾 Knowledge Base Status\n\n*Unable to load: {str(e)}*"

            def toggle_kb_details(current_visibility, current_content):
                from financial_research_agent.rag.intelligence import get_kb_detailed_status
                from financial_research_agent.rag.chroma_manager import FinancialRAGManager

                # If currently visible, hide it
                if current_visibility:
                    return gr.update(visible=False), "📋 View Details"

                # If currently hidden, show it (load content if not loaded yet)
                try:
                    if not current_content or current_content == "":
                        rag = FinancialRAGManager(persist_directory="./chroma_db")
                        content = get_kb_detailed_status(rag)
                    else:
                        content = current_content  # Use cached content

                    return gr.update(value=content, visible=True), "🔼 Hide Details"
                except Exception as e:
                    return gr.update(value=f"*Unable to load details: {str(e)}*", visible=True), "🔼 Hide Details"

            # Load KB status when app starts
            app.load(fn=load_kb_status, outputs=[kb_status_banner])

            # Toggle details when button clicked
            view_details_btn.click(
                fn=toggle_kb_details,
                inputs=[kb_details_section.visible, kb_details_section.value],
                outputs=[kb_details_section, view_details_btn]
            )

            with gr.Tabs() as main_tabs:

                # ==================== TAB 1: HOME ====================
                with gr.Tab("🏠 Home", id=0) as home_tab:

                    # ==================== SECTION 1: View Existing Analysis ====================
                    with gr.Group(elem_classes=["home-section"]):
                        gr.HTML("""
                            <div class="section-header">
                                <div class="section-badge">1</div>
                                <h2 class="section-title">View Existing Analysis</h2>
                            </div>
                        """)
                        gr.Markdown("*Load a previously generated financial analysis report from your history*")

                        existing_dropdown = gr.Dropdown(
                            label="Select Previous Analysis",
                            choices=[],
                            interactive=True,
                            scale=3
                        )

                        load_btn = gr.Button("📂 Load Analysis", variant="primary", size="lg")

                    # ==================== SECTION 2: Run New Analysis ====================
                    with gr.Group(elem_classes=["home-section"]):
                        gr.HTML("""
                            <div class="section-header">
                                <div class="section-badge">2</div>
                                <h2 class="section-title">Run New Analysis</h2>
                            </div>
                        """)
                        gr.Markdown("*Generate a comprehensive financial research report for any public company*")

                        query_input = gr.Textbox(
                            label="Company Ticker or Name",
                            placeholder="E.g., 'AAPL' or 'Apple' or 'Analyze Tesla's Q3 2025 performance'",
                            lines=2,
                            elem_classes=["query-box"]
                        )

                        generate_btn = gr.Button(
                            "🔍 Generate Analysis",
                            variant="primary",
                            size="lg"
                        )

                        status_output = gr.Markdown(
                            label="Status",
                            elem_classes=["status-box"]
                        )

                    # ==================== SECTION 3: Query Knowledge Base ====================
                    with gr.Group(elem_classes=["home-section"]):
                        gr.HTML("""
                            <div class="section-header">
                                <div class="section-badge">3</div>
                                <h2 class="section-title">Query Knowledge Base</h2>
                            </div>
                        """)
                        gr.Markdown("*Ask questions about any company already analyzed and get AI-powered answers with citations*")

                        kb_query_input = gr.Textbox(
                            label="Search Query",
                            placeholder="E.g., 'What are Apple's main revenue sources?'",
                            lines=2
                        )

                        gr.Markdown("#### Example Questions")
                        gr.Markdown("*Click an example to auto-fill the search*")

                        with gr.Row():
                            with gr.Column(scale=1):
                                for example in KB_QUERY_EXAMPLES[:3]:
                                    btn = gr.Button(
                                        example,
                                        size="sm",
                                        elem_classes=["template-button"]
                                    )
                                    btn.click(
                                        fn=lambda ex=example: ex,
                                        outputs=kb_query_input
                                    )

                            with gr.Column(scale=1):
                                for example in KB_QUERY_EXAMPLES[3:]:
                                    btn = gr.Button(
                                        example,
                                        size="sm",
                                        elem_classes=["template-button"]
                                    )
                                    btn.click(
                                        fn=lambda ex=example: ex,
                                        outputs=kb_query_input
                                    )

                        kb_search_btn = gr.Button("🔍 Search Knowledge Base", variant="primary", size="lg")

                        kb_results_output = gr.Markdown(
                            label="Search Results",
                            value="*Enter a query and click Search to find relevant information*"
                        )

                # ==================== REPORTS TAB (PARENT) ====================
                with gr.Tab("📊 Reports"):
                    with gr.Tabs():

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
                                # download_comp_md = gr.Button(
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

                        # ==================== TAB 8: Search Results (Dev) ====================
                        with gr.Tab("🔍 Search Results", id=7):
                            gr.Markdown(
                                """
                                ## Multi-Source Search Results
                                *Combined search results from web and various data sources
                                used in generating the analysis*

                                **Note:** This tab is primarily for development and debugging purposes.
                                """
                            )

                            search_results_output = gr.Markdown(
                                elem_classes=["report-content"]
                            )

                        # ==================== TAB 9: EDGAR Filings (Dev) ====================
                        with gr.Tab("📄 EDGAR Filings", id=8):
                            gr.Markdown(
                                """
                                ## SEC EDGAR Filings Data
                                *Raw EDGAR filings information and metadata extracted
                                from SEC database*

                                **Note:** This tab is primarily for development and debugging purposes.
                                """
                            )

                            edgar_filings_output = gr.Markdown(
                                elem_classes=["report-content"]
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
                    financial_analysis_output,
                    risk_analysis_output,
                    verification_output,
                    search_results_output,
                    edgar_filings_output,
                    margin_chart,
                    metrics_chart,
                    risk_chart
                ]
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
                    financial_analysis_output,
                    risk_analysis_output,
                    verification_output,
                    search_results_output,
                    edgar_filings_output,
                    margin_chart,
                    metrics_chart,
                    risk_chart
                ]
            )

            # Knowledge base search button - using defaults for removed filters
            # Note: query_knowledge_base is a generator, so we need to consume it
            def kb_search_handler(query):
                """Wrapper to consume the generator and return final result."""
                result_parts = []
                for chunk in self.query_knowledge_base(query, "", "", 10):
                    result_parts.append(chunk)
                # Return the last (final) result which contains the complete output
                return result_parts[-1] if result_parts else "No results"

            kb_search_btn.click(
                fn=kb_search_handler,
                inputs=[kb_query_input],
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
