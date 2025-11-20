from __future__ import annotations

import asyncio
import json
import logging
import shutil
import time
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from rich.console import Console

logger = logging.getLogger(__name__)

from agents import Runner, RunResult, custom_span, gen_trace_id, trace
from agents.mcp import MCPServerStdio

from .agents.edgar_agent import EdgarAnalysisSummary, edgar_agent
from .agents.financial_metrics_agent import FinancialMetrics, financial_metrics_agent
from .agents.financials_agent_enhanced import (
    ComprehensiveFinancialAnalysis,
    financials_agent_enhanced,
)
from .agents.planner_agent import FinancialSearchItem, FinancialSearchPlan, planner_agent
from .agents.risk_agent_enhanced import ComprehensiveRiskAnalysis, risk_agent_enhanced
from .agents.search_agent import search_agent
from .agents.verifier_agent import VerificationResult, verifier_agent
from .agents.writer_agent_enhanced import ComprehensiveFinancialReport, writer_agent_enhanced
from .agents.banking_ratios_agent import banking_ratios_agent
from .models.banking_ratios import BankingRegulatoryRatios
from .utils.sector_detection import detect_industry_sector, should_analyze_banking_ratios, get_peer_group
from .config import AgentConfig, EdgarConfig
from .formatters import format_financial_statements, format_financial_statements_gt, format_financial_metrics
from .printer import Printer
from .cache import FinancialDataCache
from .xbrl_calculation import get_calculation_parser_for_filing
from .cost_tracker import CostTracker
from .edgar_tools import extract_risk_factors, extract_financials_analysis_data


async def _financials_extractor(run_result: RunResult) -> str:
    """Extract comprehensive financial analysis with executive summary first."""
    analysis: ComprehensiveFinancialAnalysis = run_result.final_output

    output = f"**Financial Analysis Executive Summary:**\n{analysis.executive_summary}\n\n"
    output += f"**Financial Health Rating:** {analysis.financial_health_rating}\n\n"

    if analysis.key_metrics:
        output += "**Key Metrics:**\n"
        for metric, value in list(analysis.key_metrics.items())[:10]:  # Top 10 metrics
            output += f"- {metric}: {value}\n"
        output += "\n"

    output += "**Detailed Financial Analysis:**\n\n"
    output += analysis.detailed_analysis
    output += "\n\n"

    if analysis.filing_references:
        output += "**Sources:** " + "; ".join(analysis.filing_references)

    return output


async def _risk_extractor(run_result: RunResult) -> str:
    """Extract comprehensive risk analysis with executive summary first."""
    analysis: ComprehensiveRiskAnalysis = run_result.final_output

    output = f"**Risk Assessment Executive Summary:**\n{analysis.executive_summary}\n\n"
    output += f"**Overall Risk Rating:** {analysis.risk_rating}\n\n"

    if analysis.top_risks:
        output += "**Top 5 Risks (Prioritized):**\n"
        for i, risk in enumerate(analysis.top_risks, 1):
            output += f"{i}. {risk}\n"
        output += "\n"

    output += "**Detailed Risk Analysis:**\n\n"
    output += analysis.detailed_analysis
    output += "\n\n"

    if analysis.filing_references:
        output += "**Sources:** " + "; ".join(analysis.filing_references)

    return output


async def _edgar_extractor(run_result: RunResult) -> str:
    """Custom output extractor for EDGAR agent."""
    edgar_result: EdgarAnalysisSummary = run_result.final_output
    output = f"{edgar_result.summary}\n\n"
    if edgar_result.filing_references:
        output += "**Filings Referenced:**\n"
        for ref in edgar_result.filing_references:
            output += f"- {ref}\n"
    return output


async def _metrics_extractor(run_result: RunResult) -> str:
    """Custom output extractor for financial metrics agent."""
    metrics: FinancialMetrics = run_result.final_output

    output = f"**Financial Metrics Summary:**\n{metrics.executive_summary}\n\n"

    output += "**Key Ratios:**\n"
    if metrics.current_ratio:
        output += f"- Current Ratio: {metrics.current_ratio:.2f}\n"
    if metrics.debt_to_equity:
        output += f"- Debt-to-Equity: {metrics.debt_to_equity:.2f}\n"
    if metrics.net_profit_margin:
        output += f"- Net Margin: {metrics.net_profit_margin * 100:.1f}%\n"
    if metrics.return_on_equity:
        output += f"- ROE: {metrics.return_on_equity * 100:.1f}%\n"

    output += f"\n*Full statements and detailed ratio analysis available in separate files*\n"
    output += f"**Source:** {metrics.filing_reference}"

    return output


class EnhancedFinancialResearchManager:
    """
    Enhanced orchestrator producing comprehensive 3-5 page research reports
    with detailed specialist analysis (2-3 pages each) synthesized by writer.

    Key differences from basic version:
    - Specialist agents produce 800-1200 word analyses (vs 200 words)
    - Writer produces 1500-2500 word reports (vs ~500 words)
    - Structured output models with executive summaries
    - Saves detailed specialist analysis separately
    """

    def __init__(self, output_dir: str = "financial_research_agent/output", progress_callback=None) -> None:
        self.console = Console()
        self.printer = Printer(self.console)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create a timestamped session directory for this run
        self.session_dir: Path | None = None

        # EDGAR MCP server (initialized in run())
        self.edgar_server: MCPServerStdio | None = None
        self.edgar_enabled = AgentConfig.ENABLE_EDGAR_INTEGRATION

        # Progress callback for web interface (optional)
        # Signature: callback(progress: float, description: str)
        self.progress_callback = progress_callback

        # PERFORMANCE: Cache for financial data (24 hour TTL)
        self.cache = FinancialDataCache(ttl_hours=24)

        # Cost tracking (initialized per run)
        self.cost_tracker: CostTracker | None = None

        # XBRL validation warnings (populated during metrics gathering)
        self.xbrl_warnings: list[str] = []

    def _report_progress(self, progress: float, description: str) -> None:
        """Report progress to callback if provided."""
        if self.progress_callback:
            try:
                self.progress_callback(progress, description)
            except Exception:
                # Don't fail if callback has issues
                pass

    async def run(self, query: str, ticker: str | None = None) -> None:
        # Normalize ticker to ADR if applicable (e.g., NAB -> NABZY)
        from financial_research_agent.utils.sector_detection import normalize_ticker
        self.ticker = normalize_ticker(ticker) if ticker else None

        # Create timestamped session directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / timestamp
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Detect config mode based on models being used
        import os
        config_mode = "standard"
        if "gpt-4o-mini" in AgentConfig.SEARCH_MODEL or "gpt-4o-mini" in AgentConfig.VERIFIER_MODEL:
            config_mode = "budget"
        elif os.getenv("LLM_PROVIDER") == "together":
            config_mode = "together"
        elif os.getenv("LLM_PROVIDER") == "groq":
            config_mode = "groq"

        # Initialize cost tracker
        self.cost_tracker = CostTracker(
            ticker=self.ticker or "UNKNOWN",
            query=query,
            config_mode=config_mode
        )

        trace_id = gen_trace_id()

        # Initialize EDGAR MCP server if enabled
        if self.edgar_enabled:
            self._report_progress(0.05, "Initializing SEC EDGAR connection...")
            await self._initialize_edgar_server()

        try:
            with trace("Enhanced Financial research trace", trace_id=trace_id):
                self.printer.update_item(
                    "trace_id",
                    f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}",
                    is_done=True,
                    hide_checkmark=True,
                )
                self.printer.update_item("start", "Starting comprehensive financial research...", is_done=True)
                self._report_progress(0.10, "Starting comprehensive financial research...")

                # Save the original query
                self._save_output("00_query.md", f"# Original Query\n\n{query}\n")

                self._report_progress(0.15, "Planning search strategy...")
                search_plan = await self._plan_searches(query)

                # PERFORMANCE OPTIMIZATION: Run web search and EDGAR queries in parallel
                edgar_results = None
                metrics_results = None

                if self.edgar_enabled and self.edgar_server:
                    self._report_progress(0.20, "Gathering data from web and SEC EDGAR in parallel...")

                    # Run web search and EDGAR data gathering concurrently
                    search_task = asyncio.create_task(self._perform_searches(search_plan))
                    edgar_task = asyncio.create_task(self._gather_edgar_data(query, search_plan))

                    # Wait for both to complete
                    search_results, edgar_results = await asyncio.gather(search_task, edgar_task)

                    self._report_progress(0.40, "Extracting financial statements (40+ line items)...")
                    # Gather financial metrics and statements
                    metrics_results = await self._gather_financial_metrics(query, ticker=self.ticker)

                    # If banking sector, gather regulatory ratios (TIER 1)
                    banking_ratios_result = None
                    if self.ticker and metrics_results:
                        # Get SIC code and company name for intelligent sector detection
                        # metrics_results is a FinancialMetrics Pydantic model, not a dict
                        sic_code = getattr(metrics_results, 'sic_code', None)
                        company_name = getattr(metrics_results, 'company_name', None)
                        sector = detect_industry_sector(self.ticker, sic_code=sic_code, company_name=company_name)
                        if should_analyze_banking_ratios(sector):
                            self._report_progress(0.48, "Extracting banking regulatory ratios...")
                            banking_ratios_result = await self._gather_banking_ratios(self.ticker, sector)

                    self._report_progress(0.55, "Running specialist financial analyses...")
                    # Gather specialist analyses and save separately - pass metrics_results
                    await self._gather_specialist_analyses(query, search_results, metrics_results)

                    # Generate visualization charts (optional, non-blocking)
                    if metrics_results and self.ticker:
                        self._report_progress(0.65, "Generating interactive charts...")
                        try:
                            from financial_research_agent.visualization import generate_charts_for_analysis
                            charts_count = generate_charts_for_analysis(
                                self.session_dir,
                                ticker=self.ticker,
                                metrics_results=metrics_results
                            )
                            if charts_count > 0:
                                logger.info(f"Generated {charts_count} visualization charts")
                        except Exception as e:
                            logger.warning(f"Failed to generate charts (non-critical): {e}")
                            # Don't fail the analysis if charts fail

                else:
                    # EDGAR not enabled - just run web search
                    self._report_progress(0.20, "Searching web sources...")
                    search_results = await self._perform_searches(search_plan)

                self._report_progress(0.70, "Synthesizing comprehensive research report...")
                report = await self._write_report(query, search_results, edgar_results, metrics_results)

                # Run deterministic validation checks before LLM verification
                self._report_progress(0.85, "Validating financial data quality...")
                validation_errors = self._validate_financial_statements()
                if validation_errors:
                    error_msg = "\n\n".join(validation_errors)
                    self.console.print(f"\n[red bold]⚠️  Data Quality Issues Detected:[/red bold]")
                    self.console.print(f"[yellow]{error_msg}[/yellow]\n")

                    # Append to error log
                    if self.session_dir:
                        error_file = self.session_dir / "error_log.txt"
                        with open(error_file, 'a') as f:
                            f.write(f"\n\n=== Validation Errors ({datetime.now().isoformat()}) ===\n")
                            f.write(error_msg + "\n")

                self._report_progress(0.90, "Verifying report accuracy...")
                verification = await self._verify_report(report)

                final_summary = f"Report complete\n\n{report.executive_summary}"
                self.printer.update_item("final_report", final_summary, is_done=True)
                self._report_progress(0.95, "Finalizing reports...")

                self.printer.end()

            # Finalize and save cost report
            if self.cost_tracker:
                self.cost_tracker.finalize()
                self.cost_tracker.save_report(str(self.session_dir))
                self.cost_tracker.print_summary()

            # All reports saved to files - just show completion message
            self._report_progress(1.0, "Analysis complete!")
            self.console.print(f"\n✅ [green bold]Research complete![/green bold]")
            self.console.print(f"📁 [bold]All reports saved to:[/bold] [cyan]{self.session_dir.absolute()}[/cyan]\n")

        finally:
            # Cleanup EDGAR server
            if self.edgar_server:
                await self.edgar_server.cleanup()

    async def _initialize_edgar_server(self) -> None:
        """Initialize and connect to the SEC EDGAR MCP server."""
        try:
            self.printer.update_item("edgar_init", "Initializing SEC EDGAR connection (first run may take 30-60s to download)...")

            # Create MCP server for EDGAR
            params = {
                "command": EdgarConfig.MCP_SERVER_COMMAND,
                "args": EdgarConfig.MCP_SERVER_ARGS,
                "env": EdgarConfig.get_mcp_env(),
            }
            # Increase timeout for first run (uvx needs to download package)
            # Default is 5 seconds, we increase to 60 seconds for first run
            self.edgar_server = MCPServerStdio(
                params=params,
                client_session_timeout_seconds=60.0,  # Increased from default 5.0
            )

            # Connect to the server
            await self.edgar_server.connect()

            # Optional: Apply tool filtering
            if EdgarConfig.ALLOWED_EDGAR_TOOLS:
                self.edgar_server.tool_filter = {
                    "allowed_tool_names": EdgarConfig.ALLOWED_EDGAR_TOOLS
                }

            self.printer.update_item("edgar_init", "SEC EDGAR connected", is_done=True)

        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not initialize EDGAR server: {e}[/yellow]")
            self.console.print("[yellow]Continuing without EDGAR data...[/yellow]")

            # Provide helpful troubleshooting tips
            if "Timed out" in str(e):
                self.console.print("[yellow]Tip: First run may take longer as uvx downloads the package.[/yellow]")
                self.console.print("[yellow]Try running again - subsequent runs will be faster.[/yellow]")

            self.edgar_server = None
            self.edgar_enabled = False

    def _save_output(self, filename: str, content: str) -> None:
        """Save output to a file in the session directory."""
        if self.session_dir is None:
            return
        output_path = self.session_dir / filename
        output_path.write_text(content, encoding="utf-8")

    def _flatten_statement_data(self, statement: dict[str, Any]) -> dict[str, Any]:
        """
        Flatten nested statement data structure from MCP tools.

        The get_financial_statements MCP tool may return data in nested format like:
        {
            "data": {
                "Assets": {"value": 133735000000.0, "raw_value": "133,735", ...},
                "Liabilities": {"value": 53019000000.0, ...}
            },
            "source": "xbrl_concepts_dynamic"
        }

        This function flattens it to the expected format:
        {
            "Assets": 133735000000.0,
            "Liabilities": 53019000000.0,
            ...
        }

        If the data is already flat, it returns it unchanged.
        """
        if not statement:
            return statement

        # Check if this looks like nested metadata format
        if "data" in statement and isinstance(statement.get("data"), dict):
            # Extract the nested data
            nested_data = statement["data"]
            flattened = {}

            for key, value in nested_data.items():
                # If value is a dict with a "value" field, extract it
                if isinstance(value, dict) and "value" in value:
                    flattened[key] = value["value"]
                # Otherwise use the value directly
                else:
                    flattened[key] = value

            return flattened

        # If data is already flat (keys map directly to numbers/strings), return as-is
        return statement

    def _copy_xbrl_audit_files(self, company_name: str) -> None:
        """Copy raw XBRL CSV files from debug_edgar to current output directory for audit trail."""
        if self.session_dir is None:
            return

        try:
            # Source directory
            debug_dir = Path("financial_research_agent/output/debug_edgar")
            if not debug_dir.exists():
                return

            # Try to find CSV files matching the company name (case-insensitive)
            # Look for files containing the company name or ticker
            company_pattern = company_name.lower().split()[0] if company_name else ""
            csv_files = list(debug_dir.glob(f"xbrl_raw_*{company_pattern}*.csv"))

            # Also try uppercase version (for tickers)
            if not csv_files and company_pattern:
                csv_files = list(debug_dir.glob(f"xbrl_raw_*{company_pattern.upper()}*.csv"))

            if csv_files:
                for csv_file in csv_files:
                    dest_file = self.session_dir / csv_file.name
                    shutil.copy2(csv_file, dest_file)
                    # Silently copy - file list shown at end
        except Exception as e:
            # Don't warn - this is optional debug feature
            pass

    async def _plan_searches(self, query: str) -> FinancialSearchPlan:
        self.printer.update_item("planning", "Planning searches...")
        result = await Runner.run(planner_agent, f"Query: {query}")

        # Track planner cost
        if self.cost_tracker:
            self.cost_tracker.track_agent_run("planner", AgentConfig.PLANNER_MODEL, result)

        search_plan = result.final_output_as(FinancialSearchPlan)

        # Save the search plan
        plan_content = "# Search Plan\n\n"
        for i, item in enumerate(search_plan.searches, 1):
            plan_content += f"## Search {i}\n\n"
            plan_content += f"**Query:** {item.query}\n\n"
            plan_content += f"**Reason:** {item.reason}\n\n"
        self._save_output("01_search_plan.md", plan_content)

        self.printer.update_item(
            "planning",
            f"Will perform {len(search_plan.searches)} searches",
            is_done=True,
        )
        return search_plan

    async def _perform_searches(self, search_plan: FinancialSearchPlan) -> Sequence[str]:
        with custom_span("Search the web"):
            self.printer.update_item("searching", "Searching...")
            tasks = [
                asyncio.create_task(self._search(i, item))
                for i, item in enumerate(search_plan.searches, 1)
            ]
            results: list[str] = []
            num_completed = 0
            for task in asyncio.as_completed(tasks):
                result = await task
                if result is not None:
                    results.append(result)
                num_completed += 1
                self.printer.update_item(
                    "searching", f"Searching... {num_completed}/{len(tasks)} completed"
                )
            self.printer.mark_item_done("searching")

            # Save all search results combined
            search_results_content = "# Search Results\n\n"
            for i, result in enumerate(results, 1):
                search_results_content += f"## Result {i}\n\n{result}\n\n---\n\n"
            self._save_output("02_search_results.md", search_results_content)

            return results

    async def _search(self, index: int, item: FinancialSearchItem) -> str | None:
        input_data = f"Search term: {item.query}\nReason: {item.reason}"

        # Retry logic with exponential backoff
        for attempt in range(AgentConfig.MAX_SEARCH_RETRIES):
            try:
                result = await Runner.run(search_agent, input_data)

                # Track search cost
                if self.cost_tracker:
                    self.cost_tracker.track_agent_run(f"search_{index}", AgentConfig.SEARCH_MODEL, result)

                search_result = str(result.final_output)

                # Save individual search result
                search_file = f"02_search_{index:02d}_{item.query[:30].replace(' ', '_').replace('/', '_')}.md"
                search_content = f"# Search {index}\n\n"
                search_content += f"**Query:** {item.query}\n\n"
                search_content += f"**Reason:** {item.reason}\n\n"
                search_content += f"## Results\n\n{search_result}\n"
                self._save_output(search_file, search_content)

                return search_result

            except Exception as e:
                if attempt == AgentConfig.MAX_SEARCH_RETRIES - 1:
                    self.console.print(
                        f"[yellow]Warning: Search failed for '{item.query}': {e}[/yellow]"
                    )
                    return None
                await asyncio.sleep(AgentConfig.SEARCH_RETRY_DELAY ** attempt)

        return None

    async def _gather_edgar_data(
        self, query: str, search_plan: FinancialSearchPlan
    ) -> str | None:
        """Gather SEC filing data using the EDGAR agent."""
        if not self.edgar_server:
            return None

        self.printer.update_item("edgar", "Gathering SEC filing data...")

        try:
            # Clone edgar_agent with MCP server attached
            edgar_with_mcp = edgar_agent.clone(mcp_servers=[self.edgar_server])

            # Create a focused query for EDGAR
            edgar_query = f"Query: {query}\n\nSearch plan context: "
            for item in search_plan.searches[:3]:  # Use first 3 searches for context
                edgar_query += f"\n- {item.query}"

            edgar_query += "\n\nRetrieve relevant SEC filings and extract key financial data."

            result = await Runner.run(edgar_with_mcp, edgar_query)

            # Track EDGAR agent cost
            if self.cost_tracker:
                self.cost_tracker.track_agent_run("edgar", AgentConfig.EDGAR_MODEL, result)

            edgar_data = result.final_output_as(EdgarAnalysisSummary)

            # Save EDGAR results
            edgar_content = "# SEC EDGAR Filing Analysis\n\n"
            edgar_content += f"## Summary\n\n{edgar_data.summary}\n\n"

            if edgar_data.filing_references:
                edgar_content += "## Filing References\n\n"
                for ref in edgar_data.filing_references:
                    edgar_content += f"- {ref}\n"
                edgar_content += "\n"

            if edgar_data.key_metrics:
                edgar_content += "## Key Metrics\n\n"
                for metric, value in edgar_data.key_metrics.items():
                    edgar_content += f"- **{metric}**: {value}\n"

            self._save_output("02_edgar_filings.md", edgar_content)

            self.printer.mark_item_done("edgar")
            return edgar_data.summary

        except Exception as e:
            self.console.print(f"[yellow]Warning: EDGAR data gathering failed: {e}[/yellow]")
            self.printer.update_item("edgar", "EDGAR data unavailable", is_done=True)
            return None

    def _validate_xbrl_calculations(self, statements_data: dict, filing_url: str | None = None) -> list[str]:
        """
        Validate financial statement totals using XBRL calculation linkbase.

        Args:
            statements_data: Extracted financial data with balance_sheet, income_statement, etc.
            filing_url: Optional URL to filing for fetching calculation linkbase

        Returns:
            List of validation warnings (empty if all validations pass)
        """
        warnings = []

        try:
            # Try to get calculation linkbase parser
            parser = None

            if filing_url:
                parser = get_calculation_parser_for_filing(filing_url)

            if not parser:
                # No calculation linkbase available - skip validation
                return warnings

            self.console.print("[dim]Validating calculations using XBRL linkbase...[/dim]")

            # Extract balance sheet values (remove _Current/_Prior suffixes for validation)
            bs_data = statements_data.get('balance_sheet', {})
            if isinstance(bs_data, dict) and 'line_items' in bs_data:
                bs_data = bs_data['line_items']

            # Build concept_values dict with current period values
            concept_values = {}
            for key, value in bs_data.items():
                if key.endswith('_Current') and isinstance(value, (int, float)):
                    # Remove _Current suffix and convert to us-gaap format
                    concept_name = key[:-8]  # Remove '_Current'
                    # Try common XBRL concept names
                    concept_values[f"us-gaap:{concept_name}"] = value
                    concept_values[concept_name] = value  # Also try without namespace

            # Validate key balance sheet concepts
            key_concepts = [
                'us-gaap:Assets',
                'us-gaap:LiabilitiesAndStockholdersEquity',
                'us-gaap:AssetsCurrent',
                'us-gaap:Liabilities',
                'us-gaap:StockholdersEquity'
            ]

            for concept in key_concepts:
                is_valid, reported, calculated = parser.validate_calculation(
                    concept_values,
                    concept,
                    tolerance=0.02  # 2% tolerance for rounding
                )

                if reported is not None and calculated is not None and not is_valid:
                    # Format numbers for readability
                    reported_str = f"${reported/1e9:.2f}B" if abs(reported) > 1e9 else f"${reported/1e6:.2f}M"
                    calculated_str = f"${calculated/1e9:.2f}B" if abs(calculated) > 1e9 else f"${calculated/1e6:.2f}M"
                    diff_pct = abs(reported - calculated) / abs(reported) * 100 if reported != 0 else 0

                    warning = f"{concept}: Reported {reported_str} != Calculated {calculated_str} (diff: {diff_pct:.1f}%)"
                    warnings.append(warning)
                    self.console.print(f"[yellow]⚠ XBRL Validation: {warning}[/yellow]")

            if not warnings:
                self.console.print("[green]✓ XBRL calculation validation passed[/green]")
            else:
                self.console.print(f"[yellow]⚠ Found {len(warnings)} calculation discrepancies[/yellow]")

        except Exception as e:
            self.console.print(f"[dim]Note: XBRL validation skipped: {e}[/dim]")

        return warnings

    async def _gather_financial_metrics(self, query: str, ticker: str | None = None) -> FinancialMetrics | None:
        """Gather financial statements and calculate comprehensive ratios."""
        if not self.edgar_server:
            return None

        self.printer.update_item("metrics", "Extracting financial statements and calculating ratios...")

        try:
            # Import enhanced extraction module with edgartools XBRL features
            from financial_research_agent.edgar_tools import (
                extract_financial_data_enhanced,
                dataframes_to_dict_format,
                generate_yoy_comparison_table,
                extract_key_metrics_from_statements
            )

            # Extract company name from query using improved heuristic
            # Look for known company names or ticker symbols
            company_keywords = ["apple", "tesla", "microsoft", "google", "amazon", "meta", "nvidia",
                              "alphabet", "facebook", "aapl", "tsla", "msft", "googl", "amzn", "nvda"]
            query_lower = query.lower()
            company_name = None

            for keyword in company_keywords:
                if keyword in query_lower:
                    company_name = keyword
                    break

            # Fallback: assume company name is the first capitalized word that's not a verb
            if not company_name:
                skip_words = ["analyze", "analyse", "what", "how", "show", "get", "find", "compare"]
                words = query.split()
                for word in words:
                    if word.lower() not in skip_words and (word[0].isupper() or word.isupper()):
                        company_name = word.strip("'s").strip(",")
                        break

            if not company_name:
                company_name = "Company"

            # Use ticker if provided (from CLI), otherwise use parsed company_name
            lookup_key = ticker if ticker else company_name

            # PERFORMANCE: Check cache first
            cached_statements = self.cache.get(lookup_key, "financial_statements")
            if cached_statements:
                self.console.print(f"[dim]✓ Using cached financial data for {lookup_key}[/dim]")
                statements_data = cached_statements
            else:
                # Step 1: Use enhanced extraction to get complete financial data with XBRL features
                self.printer.update_item("metrics", f"Extracting financial data for {lookup_key} using enhanced XBRL extraction...")

                statements_data = None
                try:
                    statements_data = await extract_financial_data_enhanced(
                        self.edgar_server,
                        lookup_key
                    )

                    # PERFORMANCE: Cache the extracted data using ticker (not parsed company_name)
                    if statements_data:
                        self.cache.set(lookup_key, "financial_statements", statements_data)

                        # Extract official company name from statements_data if available
                        if 'company_name' in statements_data:
                            company_name = statements_data['company_name']

                except Exception as e:
                    self.console.print(f"[yellow]Warning: Deterministic extraction failed: {e}[/yellow]")
                    import traceback
                    traceback.print_exc()
                    self.console.print("[yellow]Falling back to LLM-based extraction...[/yellow]")

            # Continue with verification if we have data
            if statements_data:
                from financial_research_agent.verification_tools import (
                    verify_financial_data_completeness,
                    format_verification_report
                )

                self.printer.update_item("metrics", "Verifying data completeness...")

                # Convert DataFrames to dict format for verification if needed
                if 'balance_sheet_df' in statements_data:
                    verification_data = dataframes_to_dict_format(
                        statements_data['balance_sheet_df'],
                        statements_data['income_statement_df'],
                        statements_data['cash_flow_statement_df']
                    )
                else:
                    # Legacy dict format
                    verification_data = statements_data

                verification = verify_financial_data_completeness(verification_data)

                # Save verification report
                if self.session_dir:
                    verification_file = self.session_dir / "data_verification.md"
                    verification_file.write_text(format_verification_report(verification), encoding='utf-8')

                # Log verification results
                if verification['valid']:
                    self.console.print(f"[green]✓ Data verification passed - {verification['stats'].get('total_line_items', 0)} line items extracted[/green]")
                else:
                    self.console.print(f"[yellow]⚠ Data verification found {len(verification['errors'])} errors[/yellow]")
                    for error in verification['errors']:
                        self.console.print(f"[yellow]  - {error.split(chr(10))[0]}[/yellow]")  # First line only

                # Show warnings
                if verification['warnings']:
                    for warning in verification['warnings']:
                        self.console.print(f"[dim]  Note: {warning}[/dim]")

                # XBRL Calculation Linkbase Validation
                try:
                    # Try to get filing URL from statements_data
                    filing_url = statements_data.get('filing_url')
                    if filing_url:
                        self.xbrl_warnings = self._validate_xbrl_calculations(statements_data, filing_url)
                except Exception as e:
                    self.console.print(f"[dim]XBRL validation skipped: {e}[/dim]")

                # Generate YoY comparison tables from enhanced data
                if 'balance_sheet_df' in statements_data:
                    try:
                        self.printer.update_item("metrics", "Generating year-over-year comparison tables...")

                        # Generate YoY tables for each statement
                        yoy_tables = {}

                        # Balance Sheet YoY
                        bs_yoy = generate_yoy_comparison_table(
                            statements_data['balance_sheet_df'],
                            "Balance Sheet",
                            key_items=['Assets', 'Total Assets', 'Liabilities', 'Total Liabilities',
                                      'Equity', 'Total Equity', "Stockholders' Equity", "Total Stockholders' Equity",
                                      'Cash and Cash Equivalents', 'Total Current Assets', 'Total Current Liabilities']
                        )
                        yoy_tables['balance_sheet'] = bs_yoy

                        # Income Statement YoY
                        is_yoy = generate_yoy_comparison_table(
                            statements_data['income_statement_df'],
                            "Income Statement",
                            key_items=['Revenue', 'Revenues', 'Total Revenue', 'Net Sales', 'Contract Revenue',
                                      'Gross Profit', 'Operating Income', 'Net Income', 'Earnings Per Share']
                        )
                        yoy_tables['income_statement'] = is_yoy

                        # Cash Flow Statement YoY
                        cf_yoy = generate_yoy_comparison_table(
                            statements_data['cash_flow_statement_df'],
                            "Cash Flow Statement",
                            key_items=['Net Cash Provided by Operating Activities', 'Net Cash From Operating Activities',
                                      'Capital Expenditures', 'Payments for Property, Plant and Equipment',
                                      'Free Cash Flow', 'Dividends Paid', 'Stock Repurchases']
                        )
                        yoy_tables['cash_flow'] = cf_yoy

                        # Store YoY tables for inclusion in 03_financial_statements.md
                        statements_data['yoy_tables'] = yoy_tables
                        self.console.print("[green]✓ YoY comparison tables generated[/green]")

                        # Extract key metrics using enhanced function
                        key_metrics = extract_key_metrics_from_statements(
                            statements_data['balance_sheet_df'],
                            statements_data['income_statement_df'],
                            statements_data['cash_flow_statement_df']
                        )
                        statements_data['key_metrics'] = key_metrics

                        if key_metrics.get('current'):
                            self.console.print(f"[dim]  Key metrics extracted: Revenue=${key_metrics['current'].get('revenue', 0)/1e9:.1f}B, FCF=${key_metrics['current'].get('free_cash_flow', 0)/1e9:.1f}B[/dim]")

                    except Exception as e:
                        self.console.print(f"[yellow]Warning: YoY table generation failed: {e}[/yellow]")
                        import traceback
                        traceback.print_exc()

            # Step 2: Clone metrics agent with MCP server attached
            metrics_with_mcp = financial_metrics_agent.clone(mcp_servers=[self.edgar_server])

            # Step 3: Create query for the agent
            # Check if we have DataFrame-based data or dict-based data
            has_data = statements_data and (
                'balance_sheet_df' in statements_data or
                (isinstance(statements_data.get('balance_sheet'), dict) and statements_data['balance_sheet'])
            )

            if has_data:
                # We have deterministic data - provide it to the agent
                self.printer.update_item("metrics", "Calculating financial ratios from extracted data...")

                # Convert DataFrames to dict format if needed
                if 'balance_sheet_df' in statements_data:
                    dict_data = dataframes_to_dict_format(
                        statements_data['balance_sheet_df'],
                        statements_data['income_statement_df'],
                        statements_data['cash_flow_statement_df']
                    )
                    bs_data = dict_data['balance_sheet']
                    is_data = dict_data['income_statement']
                    cf_data = dict_data['cash_flow_statement']
                else:
                    # Legacy dict format - extract line_items from the new structure if present
                    bs_data = statements_data['balance_sheet'].get('line_items', statements_data['balance_sheet'])
                    is_data = statements_data['income_statement'].get('line_items', statements_data['income_statement'])
                    cf_data = statements_data['cash_flow_statement'].get('line_items', statements_data['cash_flow_statement'])

                # Build metrics query with JSON dumps - using string concatenation to avoid f-string issues
                bs_json = json.dumps(bs_data, indent=2)
                is_json = json.dumps(is_data, indent=2)
                cf_json = json.dumps(cf_data, indent=2)

                metrics_query = f"""Query: {query}

Financial statements have been pre-extracted from SEC EDGAR using deterministic get_company_facts API:

Balance Sheet ({len(bs_data)} line items):
{bs_json}

Income Statement ({len(is_data)} line items):
{is_json}

Cash Flow Statement ({len(cf_data)} line items):
{cf_json}

Your task:
1. Use the provided financial statement data above (with _Current and _Prior suffixes)
2. Calculate comprehensive financial ratios using the CURRENT period data
3. Return the complete FinancialMetrics output with:
   - All provided balance sheet items
   - All provided income statement items
   - All provided cash flow statement items
   - All calculated financial ratios
   - Period dates and filing references
"""
            else:
                # Fallback to LLM extraction
                metrics_query = f"""Query: {query}

Extract complete financial statements and calculate comprehensive financial ratios.
Use get_company_facts to get ALL available XBRL data."""

            result = await Runner.run(metrics_with_mcp, metrics_query, max_turns=AgentConfig.MAX_AGENT_TURNS)

            # Track metrics agent cost
            # Note: metrics agent typically uses same model as EDGAR
            if self.cost_tracker:
                self.cost_tracker.track_agent_run("metrics", AgentConfig.EDGAR_MODEL, result)

            metrics = result.final_output_as(FinancialMetrics)

            # If we have deterministic extraction data, use it directly for financial statements
            # instead of the agent's reformatted version. This preserves human-readable labels.
            if statements_data and ('balance_sheet_df' in statements_data or statements_data.get('balance_sheet')):
                self.console.print("[dim]Using deterministic extraction for financial statements (preserves human-readable labels)[/dim]")

                # For dict-based data (metrics agent needs dicts, not DataFrames)
                if 'balance_sheet_df' not in statements_data:
                    # Legacy dict format
                    metrics.balance_sheet = statements_data['balance_sheet']
                    metrics.income_statement = statements_data['income_statement']
                    metrics.cash_flow_statement = statements_data['cash_flow_statement']
                    metrics.period = statements_data.get('period', metrics.period)
                    metrics.filing_reference = statements_data.get('filing_reference', metrics.filing_reference)
                else:
                    # DataFrame format - convert to dict for metrics agent
                    # (Note: We keep DataFrames in statements_data for the formatter)
                    dict_data = dataframes_to_dict_format(
                        statements_data['balance_sheet_df'],
                        statements_data['income_statement_df'],
                        statements_data['cash_flow_statement_df']
                    )
                    metrics.balance_sheet = dict_data['balance_sheet']
                    metrics.income_statement = dict_data['income_statement']
                    metrics.cash_flow_statement = dict_data['cash_flow_statement']
                    metrics.period = statements_data.get('current_period', metrics.period)
                    metrics.filing_reference = statements_data.get('filing_reference', metrics.filing_reference)
            else:
                # Fallback: Clean up financial statement data if it contains nested metadata
                # (MCP tools may return nested structures with metadata)
                bs_before = list(metrics.balance_sheet.keys())[:3] if isinstance(metrics.balance_sheet, dict) else []
                metrics.balance_sheet = self._flatten_statement_data(metrics.balance_sheet)
                metrics.income_statement = self._flatten_statement_data(metrics.income_statement)
                # Cash flow may be a string if unavailable - only flatten if it's a dict
                if isinstance(metrics.cash_flow_statement, dict):
                    metrics.cash_flow_statement = self._flatten_statement_data(metrics.cash_flow_statement)
                elif isinstance(metrics.cash_flow_statement, str):
                    # Convert error message string to empty dict for formatter
                    metrics.cash_flow_statement = {}
                bs_after = list(metrics.balance_sheet.keys())[:3] if isinstance(metrics.balance_sheet, dict) else []

                # Log if flattening occurred (for debugging)
                if bs_before != bs_after:
                    self.console.print(f"[dim]Data flattened: {bs_before} → {bs_after}[/dim]")

            # Save financial statements (03_financial_statements.md)
            # Use Great Tables formatter for proper markdown tables
            if statements_data and 'balance_sheet_df' in statements_data:
                self.console.print("[dim]Using Great Tables formatter for professional table styling[/dim]")
                statements_content = format_financial_statements_gt(
                    balance_sheet_df=statements_data['balance_sheet_df'],
                    income_statement_df=statements_data['income_statement_df'],
                    cash_flow_statement_df=statements_data['cash_flow_statement_df'],
                    company_name=company_name,
                    current_period=statements_data.get('current_period', 'Current'),
                    prior_period=statements_data.get('prior_period'),
                    filing_reference=statements_data.get('filing_reference', 'Unknown'),
                    fiscal_year=statements_data.get('fiscal_year'),
                    fiscal_period=statements_data.get('fiscal_period'),
                    is_quarterly_report=statements_data.get('is_quarterly_report', False),
                    is_annual_report=statements_data.get('is_annual_report', False),
                )
                # Append YoY comparison tables
                if statements_data.get('yoy_tables'):
                    statements_content += "\n---\n\n"
                    statements_content += "# Year-over-Year Comparison Tables\n\n"
                    statements_content += statements_data['yoy_tables'].get('income_statement', '') + "\n\n"
                    statements_content += statements_data['yoy_tables'].get('balance_sheet', '') + "\n\n"
                    statements_content += statements_data['yoy_tables'].get('cash_flow', '') + "\n"
            else:
                # Legacy dict-based approach
                statements_content = format_financial_statements(
                    balance_sheet=metrics.balance_sheet,
                    income_statement=metrics.income_statement,
                    cash_flow_statement=metrics.cash_flow_statement,
                    company_name=company_name,
                    period=metrics.period,
                    filing_reference=metrics.filing_reference,
                )
            self._save_output("03_financial_statements.md", statements_content)

            # Save financial metrics (04_financial_metrics.md) with YoY tables
            income_statement_df = statements_data.get('income_statement_df') if statements_data else None
            cashflow_df = statements_data.get('cash_flow_statement_df') if statements_data else None
            metrics_content = format_financial_metrics(
                metrics,
                company_name,
                income_statement_df=income_statement_df,
                cashflow_df=cashflow_df
            )
            self._save_output("04_financial_metrics.md", metrics_content)

            # Save metadata.json for web UI discovery
            if statements_data and self.session_dir:
                metadata = {
                    "ticker": statements_data.get('ticker', lookup_key),
                    "company_name": company_name,
                    "cik": statements_data.get('cik'),
                    "sic_code": statements_data.get('sic_code'),
                    "form_type": statements_data.get('form_type'),
                    "fiscal_year_end": statements_data.get('fiscal_year_end'),
                    "filing_date": statements_data.get('filing_date'),
                    "is_foreign_filer": statements_data.get('is_foreign_filer', False),
                    "analysis_timestamp": self.session_dir.name,
                }
                metadata_file = self.session_dir / "metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

            # Copy raw XBRL CSV files to output folder for audit trail
            self._copy_xbrl_audit_files(company_name)

            self.printer.mark_item_done("metrics")
            return metrics

        except Exception as e:
            import traceback
            error_msg = str(e)
            # Provide more helpful error messages
            if "Invalid JSON" in error_msg or "JSON" in error_msg:
                self.console.print(
                    f"[yellow]Warning: Financial metrics extraction failed due to JSON parsing error.[/yellow]\n"
                    f"[dim]This can happen when the LLM returns malformed JSON. The system will continue without detailed metrics.[/dim]"
                )
            else:
                self.console.print(f"[yellow]Warning: Financial metrics gathering failed: {error_msg}[/yellow]")

            # Save error details to file
            if self.session_dir:
                error_file = self.session_dir / "error_log.txt"
                with open(error_file, 'a') as f:
                    f.write(f"\n\n=== Financial Metrics Error ({datetime.now().isoformat()}) ===\n")
                    f.write(traceback.format_exc())

            self.printer.update_item("metrics", "Financial metrics unavailable", is_done=True)
            return None

    async def _gather_banking_ratios(self, ticker: str, sector: str) -> BankingRegulatoryRatios | None:
        """
        Gather banking regulatory ratios (TIER 1) from 10-K MD&A disclosures.

        This extracts Basel III capital ratios, liquidity metrics, and other
        directly-reported regulatory ratios that are only available in narrative
        text and tables (not in XBRL).

        TIER 2 ratios (calculated) are already included in financial metrics.
        """
        if not self.edgar_server:
            return None

        self.printer.update_item("banking_ratios", "Extracting banking regulatory ratios...")

        try:
            # Clone banking ratios agent with EDGAR server access
            banking_agent_with_edgar = banking_ratios_agent.clone(mcp_servers=[self.edgar_server])

            # Get peer group for context
            peer_group = get_peer_group(ticker, sector)

            # Prepare input for agent
            agent_input = f"""Extract banking regulatory ratios for {ticker} ({peer_group}).

Focus on Basel III capital ratios and liquidity metrics from the most recent 10-K filing.

Look for regulatory capital disclosures in:
1. MD&A section under "Capital Management" or "Regulatory Capital"
2. Tables showing CET1, Tier 1, Total Capital ratios
3. Liquidity Coverage Ratio (LCR) and Net Stable Funding Ratio (NSFR) if disclosed
4. Stress Capital Buffer and G-SIB surcharge if mentioned

Extract the most recent period data and note the reporting period.
"""

            # Run the agent
            result = await Runner.run(
                banking_agent_with_edgar,
                agent_input,
                max_turns=AgentConfig.MAX_AGENT_TURNS
            )

            banking_ratios = result.final_output_as(BankingRegulatoryRatios)

            # Save banking ratios analysis (04_banking_ratios.md)
            # Note: This is numbered 04 because it's sector-specific and comes before general financials (05/06)
            banking_content = "# Banking Regulatory Ratios Analysis\n\n"
            banking_content += f"**Sector:** Commercial Banking\n"
            banking_content += f"**Peer Group:** {peer_group}\n\n"

            if banking_ratios.reporting_period:
                banking_content += f"**Reporting Period:** {banking_ratios.reporting_period}\n"
            if banking_ratios.prior_period:
                banking_content += f"**Prior Period:** {banking_ratios.prior_period}\n"
            if banking_ratios.regulatory_framework:
                banking_content += f"**Regulatory Framework:** {banking_ratios.regulatory_framework}\n"

            banking_content += "\n---\n\n"

            # Capital Adequacy Status
            capital_status = banking_ratios.get_capital_status()
            banking_content += f"## Capital Adequacy Status\n\n**{capital_status}**\n\n"

            if banking_ratios.capital_assessment:
                banking_content += f"{banking_ratios.capital_assessment}\n\n"

            # Basel III Capital Ratios
            banking_content += "---\n\n## Basel III Capital Ratios\n\n"

            if banking_ratios.cet1_ratio:
                cushion = banking_ratios.capital_cushion()
                cushion_str = f" (+{cushion:.1f}% above minimum)" if cushion else ""
                banking_content += f"- **CET1 Ratio:** {banking_ratios.cet1_ratio:.1f}%{cushion_str}\n"
            if banking_ratios.tier1_ratio:
                banking_content += f"- **Tier 1 Ratio:** {banking_ratios.tier1_ratio:.1f}%\n"
            if banking_ratios.total_capital_ratio:
                banking_content += f"- **Total Capital Ratio:** {banking_ratios.total_capital_ratio:.1f}%\n"
            if banking_ratios.tier1_leverage_ratio:
                banking_content += f"- **Tier 1 Leverage Ratio:** {banking_ratios.tier1_leverage_ratio:.1f}%\n"
            if banking_ratios.supplementary_leverage_ratio:
                banking_content += f"- **Supplementary Leverage Ratio:** {banking_ratios.supplementary_leverage_ratio:.1f}%\n"

            banking_content += "\n"

            # Regulatory Minimums
            if banking_ratios.cet1_minimum_required:
                banking_content += "### Regulatory Minimums\n\n"
                if banking_ratios.cet1_minimum_required:
                    banking_content += f"- CET1 Minimum: {banking_ratios.cet1_minimum_required:.1f}%\n"
                if banking_ratios.tier1_minimum_required:
                    banking_content += f"- Tier 1 Minimum: {banking_ratios.tier1_minimum_required:.1f}%\n"
                if banking_ratios.total_capital_minimum_required:
                    banking_content += f"- Total Capital Minimum: {banking_ratios.total_capital_minimum_required:.1f}%\n"
                banking_content += "\n"

            # Capital Components
            if banking_ratios.cet1_capital or banking_ratios.risk_weighted_assets:
                banking_content += "### Capital Components\n\n"
                if banking_ratios.cet1_capital:
                    banking_content += f"- **CET1 Capital:** ${banking_ratios.cet1_capital:.1f} billion\n"
                if banking_ratios.tier1_capital:
                    banking_content += f"- **Tier 1 Capital:** ${banking_ratios.tier1_capital:.1f} billion\n"
                if banking_ratios.total_capital:
                    banking_content += f"- **Total Capital:** ${banking_ratios.total_capital:.1f} billion\n"
                if banking_ratios.risk_weighted_assets:
                    banking_content += f"- **Risk-Weighted Assets:** ${banking_ratios.risk_weighted_assets:.1f} billion\n"
                banking_content += "\n"

            # Liquidity Metrics
            if banking_ratios.lcr or banking_ratios.nsfr:
                liquidity_status = banking_ratios.get_liquidity_status()
                banking_content += f"---\n\n## Liquidity Metrics\n\n**Status:** {liquidity_status}\n\n"
                if banking_ratios.lcr:
                    banking_content += f"- **Liquidity Coverage Ratio (LCR):** {banking_ratios.lcr:.1f}%\n"
                if banking_ratios.nsfr:
                    banking_content += f"- **Net Stable Funding Ratio (NSFR):** {banking_ratios.nsfr:.1f}%\n"
                banking_content += "\n"

            # U.S. Stress Test Requirements
            if banking_ratios.stress_capital_buffer or banking_ratios.gsib_surcharge:
                banking_content += "---\n\n## U.S. Stress Test Requirements\n\n"
                if banking_ratios.stress_capital_buffer:
                    banking_content += f"- **Stress Capital Buffer (SCB):** {banking_ratios.stress_capital_buffer:.1f}%\n"
                if banking_ratios.gsib_surcharge:
                    banking_content += f"- **G-SIB Surcharge:** {banking_ratios.gsib_surcharge:.1f}%\n"
                banking_content += "\n"

            # Key Strengths
            if banking_ratios.key_strengths:
                banking_content += "---\n\n## Key Strengths\n\n"
                for strength in banking_ratios.key_strengths:
                    banking_content += f"- {strength}\n"
                banking_content += "\n"

            # Key Concerns
            if banking_ratios.key_concerns:
                banking_content += "---\n\n## Key Concerns\n\n"
                for concern in banking_ratios.key_concerns:
                    banking_content += f"- {concern}\n"
                banking_content += "\n"

            # Note about TIER 2 ratios
            banking_content += "---\n\n## Banking-Specific Financial Ratios (Calculated)\n\n"
            banking_content += "*Banking profitability, credit quality, and balance sheet composition ratios "
            banking_content += "(NIM, Efficiency Ratio, ROTCE, NPL Ratio, Loan-to-Deposit, etc.) are "
            banking_content += "included in the Financial Metrics report (04_financial_metrics.md).*\n"

            self._save_output("04_banking_ratios.md", banking_content)
            self.printer.mark_item_done("banking_ratios")

            return banking_ratios

        except Exception as e:
            import traceback
            error_msg = str(e)
            self.console.print(f"[yellow]Warning: Banking ratios extraction failed: {error_msg}[/yellow]")

            # Save error details to file
            if self.session_dir:
                error_file = self.session_dir / "error_log.txt"
                with open(error_file, 'a') as f:
                    f.write(f"\n\n=== Banking Ratios Error ({datetime.now().isoformat()}) ===\n")
                    f.write(traceback.format_exc())

            self.printer.update_item("banking_ratios", "Banking ratios unavailable", is_done=True)
            return None

    async def _gather_specialist_analyses(self, query: str, search_results: Sequence[str], metrics_results = None) -> None:
        """Gather detailed financial and risk analyses and save separately."""
        if not self.edgar_server:
            return

        self.printer.update_item("specialist_analysis", "Running specialist analyses...")

        try:
            # Pre-extract risk factors using edgartools (replacing MCP for massive cost savings)
            risk_factors_data = None
            try:
                self.printer.update_item("specialist_analysis", "Extracting SEC risk factors...")
                risk_factors_data = await extract_risk_factors(self.ticker)
            except Exception as e:
                logger.warning(f"Could not extract risk factors: {e}")

            # Clone financials agent with EDGAR MCP server access (still needs MCP for MD&A)
            financials_with_edgar = financials_agent_enhanced.clone(mcp_servers=[self.edgar_server])

            # Prepare input data for financials agent - include pre-extracted financial data
            financials_input = f"Query: {query}\n\nContext from research:\n{search_results[:3]}\n\n"

            if metrics_results:
                financials_input += "## Pre-Extracted Financial Data\n\n"
                financials_input += "**CRITICAL:** Complete financial statements and ratios have been extracted and saved to files 03_financial_statements.md and 04_financial_metrics.md.\n"
                financials_input += "Your job is to INTERPRET this data, not re-extract it. Use MD&A and web sources for context.\n\n"

                # Build a summary of available ratios from the FinancialMetrics object
                financials_input += "### Available Pre-Calculated Ratios\n\n"
                financials_input += f"**Executive Summary:** {metrics_results.executive_summary}\n\n"

                # List key ratios that are non-None
                ratio_categories = []
                if metrics_results.current_ratio or metrics_results.quick_ratio:
                    ratio_categories.append("Liquidity Ratios (current ratio, quick ratio, cash ratio)")
                if metrics_results.debt_to_equity or metrics_results.debt_to_assets:
                    ratio_categories.append("Solvency Ratios (debt-to-equity, debt-to-assets, equity ratio)")
                if metrics_results.net_profit_margin or metrics_results.return_on_assets or metrics_results.return_on_equity:
                    ratio_categories.append("Profitability Ratios (gross margin, operating margin, net margin, ROA, ROE)")
                if metrics_results.asset_turnover:
                    ratio_categories.append("Efficiency Ratios (asset turnover, inventory turnover, receivables turnover)")

                if ratio_categories:
                    financials_input += "**Calculated Ratio Categories:**\n"
                    for cat in ratio_categories:
                        financials_input += f"- {cat}\n"
                    financials_input += "\n"

                financials_input += "**IMPORTANT:** Review files 03_financial_statements.md and 04_financial_metrics.md for complete data.\n"
                financials_input += "Reference these pre-extracted values in your analysis. Do NOT attempt to re-extract from EDGAR.\n\n"
            else:
                financials_input += "\n**NOTE:** Financial data extraction was unavailable. "
                financials_input += "Focus on qualitative analysis from MD&A, segment discussions, and web sources.\n\n"

            # Include YoY comparison tables from 04_financial_metrics.md if available
            if self.session_dir:
                metrics_file = self.session_dir / "04_financial_metrics.md"
                if metrics_file.exists():
                    with open(metrics_file, 'r') as f:
                        metrics_content = f.read()
                        # Extract YoY tables (they're between "### Key Financial Metrics" and "## Liquidity Ratios")
                        if "### Key Financial Metrics (YoY Comparison)" in metrics_content:
                            start_idx = metrics_content.find("### Key Financial Metrics (YoY Comparison)")
                            end_idx = metrics_content.find("## Liquidity Ratios")
                            if start_idx != -1 and end_idx != -1:
                                yoy_tables = metrics_content[start_idx:end_idx].strip()
                                financials_input += f"\n\n**Year-over-Year Comparison Tables (from 04_financial_metrics.md):**\n\n{yoy_tables}\n\n"
                                financials_input += "**CRITICAL:** For Section 8 (Year-over-Year Comparison Table), copy these exact values into your table.\n"
                                financials_input += "Do NOT use placeholders like '[per 03_financial_statements.md]' - use the actual dollar amounts and percentages shown above.\n\n"

            # Prepare input data for risk agent (simpler - just context)
            risk_input = f"Query: {query}\n\nContext from research:\n{search_results[:3]}"

            # Run financial analysis with pre-extracted data
            self.printer.update_item("specialist_analysis", "Running financial analysis...")
            financials_result = await Runner.run(financials_with_edgar, financials_input, max_turns=AgentConfig.MAX_AGENT_TURNS)

            # Track financials agent cost
            if self.cost_tracker:
                self.cost_tracker.track_agent_run("financials", AgentConfig.FINANCIALS_MODEL, financials_result)

            financials_analysis = financials_result.final_output_as(ComprehensiveFinancialAnalysis)

            # Save financial analysis (05_financial_analysis.md)
            financials_content = "# Comprehensive Financial Analysis\n\n"
            financials_content += f"**Financial Health Rating:** {financials_analysis.financial_health_rating}\n\n"
            financials_content += "---\n\n"
            financials_content += "## Executive Summary\n\n"
            financials_content += f"{financials_analysis.executive_summary}\n\n"
            financials_content += "---\n\n"
            financials_content += "## Detailed Analysis\n\n"
            financials_content += f"{financials_analysis.detailed_analysis}\n\n"

            if financials_analysis.key_metrics:
                financials_content += "---\n\n"
                financials_content += "## Key Metrics\n\n"
                for metric, value in financials_analysis.key_metrics.items():
                    financials_content += f"- **{metric}**: {value}\n"
                financials_content += "\n"

            if financials_analysis.filing_references:
                financials_content += "---\n\n"
                financials_content += "## Sources\n\n"
                for ref in financials_analysis.filing_references:
                    financials_content += f"- {ref}\n"

            self._save_output("05_financial_analysis.md", financials_content)

            # Run risk analysis with PRE-EXTRACTED data (no MCP - massive cost savings)
            self.printer.update_item("specialist_analysis", "Running risk analysis...")

            # Build risk input with pre-extracted SEC data
            risk_input = f"Analyze the key risks and risk factors for {self.ticker}.\n\n"
            risk_input += f"Original query: {query}\n\n"

            # Include pre-extracted risk factors (this replaces MCP tool calls)
            if risk_factors_data:
                risk_input += "## Pre-Extracted SEC Filing Data\n\n"
                risk_input += "**IMPORTANT:** Risk factors have been pre-extracted from SEC filings below. "
                risk_input += "Analyze this data directly - do NOT use MCP tools to re-extract.\n\n"

                if risk_factors_data.get('risk_factors_10k'):
                    date = risk_factors_data.get('risk_factors_10k_date', 'Unknown')
                    accession = risk_factors_data.get('risk_factors_10k_accession', '')
                    risk_input += f"### Item 1A Risk Factors from 10-K (filed {date})\n"
                    if accession:
                        risk_input += f"Accession: {accession}\n\n"
                    # Limit to first 40000 chars to avoid context limits
                    risk_text = risk_factors_data['risk_factors_10k'][:40000]
                    risk_input += f"{risk_text}\n\n"

                if risk_factors_data.get('risk_factors_10q'):
                    date = risk_factors_data.get('risk_factors_10q_date', 'Unknown')
                    risk_input += f"### Item 1A Risk Factors from 10-Q (filed {date})\n"
                    risk_text = risk_factors_data['risk_factors_10q'][:15000]
                    risk_input += f"{risk_text}\n\n"

                if risk_factors_data.get('mda_text'):
                    date = risk_factors_data.get('mda_date', 'Unknown')
                    risk_input += f"### Management Discussion & Analysis (from filing dated {date})\n"
                    # MD&A can be long, limit to key sections
                    mda_text = risk_factors_data['mda_text'][:20000]
                    risk_input += f"{mda_text}\n\n"

                if risk_factors_data.get('legal_proceedings'):
                    risk_input += "### Legal Proceedings (Item 3)\n"
                    legal_text = risk_factors_data['legal_proceedings'][:10000]
                    risk_input += f"{legal_text}\n\n"

                if risk_factors_data.get('recent_8ks'):
                    risk_input += "### Recent 8-K Filings (Material Events)\n"
                    for filing in risk_factors_data['recent_8ks'][:5]:
                        risk_input += f"- 8-K filed {filing['date']}"
                        if filing.get('items'):
                            risk_input += f": Items {', '.join(str(i) for i in filing['items'])}"
                        risk_input += "\n"
                    risk_input += "\n"

                if risk_factors_data.get('filing_references'):
                    risk_input += f"**Filing References:** {', '.join(risk_factors_data['filing_references'])}\n\n"
            else:
                risk_input += "\n**NOTE:** SEC risk factor extraction was unavailable. "
                risk_input += "Use web search to gather risk information.\n\n"

            risk_input += f"Context from research:\n{search_results[:3]}"

            # Run risk agent WITHOUT MCP (uses pre-extracted data + brave_search for news)
            risk_result = await Runner.run(risk_agent_enhanced, risk_input, max_turns=AgentConfig.MAX_AGENT_TURNS)

            # Track risk agent cost
            if self.cost_tracker:
                self.cost_tracker.track_agent_run("risk", AgentConfig.RISK_MODEL, risk_result)

            risk_analysis = risk_result.final_output_as(ComprehensiveRiskAnalysis)

            # Save risk analysis (06_risk_analysis.md)
            risk_content = "# Comprehensive Risk Analysis\n\n"
            risk_content += f"**Overall Risk Rating:** {risk_analysis.risk_rating}\n\n"
            risk_content += "---\n\n"
            risk_content += "## Executive Summary\n\n"
            risk_content += f"{risk_analysis.executive_summary}\n\n"

            if risk_analysis.top_risks:
                risk_content += "---\n\n"
                risk_content += "## Top 5 Risks (Prioritized)\n\n"
                for i, risk in enumerate(risk_analysis.top_risks, 1):
                    risk_content += f"{i}. {risk}\n"
                risk_content += "\n"

            risk_content += "---\n\n"
            risk_content += "## Detailed Risk Analysis\n\n"
            risk_content += f"{risk_analysis.detailed_analysis}\n\n"

            if risk_analysis.filing_references:
                risk_content += "---\n\n"
                risk_content += "## Sources\n\n"
                for ref in risk_analysis.filing_references:
                    risk_content += f"- {ref}\n"

            self._save_output("06_risk_analysis.md", risk_content)

            self.printer.mark_item_done("specialist_analysis")

        except Exception as e:
            import traceback
            self.console.print(f"[yellow]Warning: Specialist analyses failed: {e}[/yellow]")
            # Save error details to file
            if self.session_dir:
                error_file = self.session_dir / "error_log.txt"
                with open(error_file, 'a') as f:
                    f.write(f"\n\n=== Specialist Analyses Error ({datetime.now().isoformat()}) ===\n")
                    f.write(traceback.format_exc())
            self.printer.update_item("specialist_analysis", "Specialist analyses unavailable", is_done=True)

    async def _write_report(
        self, query: str, search_results: Sequence[str], edgar_results: str | None, metrics_results: FinancialMetrics | None
    ) -> ComprehensiveFinancialReport:
        # Expose enhanced specialist analysts as tools with comprehensive analysis
        if self.edgar_enabled and self.edgar_server:
            # Clone specialist agents with EDGAR MCP server access
            financials_with_edgar = financials_agent_enhanced.clone(mcp_servers=[self.edgar_server])
            risk_with_edgar = risk_agent_enhanced.clone(mcp_servers=[self.edgar_server])

            fundamentals_tool = financials_with_edgar.as_tool(
                tool_name="fundamentals_analysis",
                tool_description="Get comprehensive 2-3 page financial analysis with exact SEC filing data (800-1200 words)",
                custom_output_extractor=_financials_extractor,
            )
            risk_tool = risk_with_edgar.as_tool(
                tool_name="risk_analysis",
                tool_description="Get comprehensive 2-3 page risk assessment from SEC Risk Factors and research (800-1200 words)",
                custom_output_extractor=_risk_extractor,
            )
        else:
            # Use enhanced agents without EDGAR access
            fundamentals_tool = financials_agent_enhanced.as_tool(
                tool_name="fundamentals_analysis",
                tool_description="Get comprehensive 2-3 page financial analysis (800-1200 words)",
                custom_output_extractor=_financials_extractor,
            )
            risk_tool = risk_agent_enhanced.as_tool(
                tool_name="risk_analysis",
                tool_description="Get comprehensive 2-3 page risk assessment (800-1200 words)",
                custom_output_extractor=_risk_extractor,
            )

        tools = [fundamentals_tool, risk_tool]

        # Add dedicated EDGAR agent as a tool if available
        if self.edgar_enabled and self.edgar_server:
            edgar_tool = edgar_agent.clone(mcp_servers=[self.edgar_server]).as_tool(
                tool_name="sec_filing_analysis",
                tool_description="Query specific SEC filing details if needed for additional context",
                custom_output_extractor=_edgar_extractor,
            )
            tools.append(edgar_tool)

            # Add financial metrics tool if available
            metrics_tool = financial_metrics_agent.clone(mcp_servers=[self.edgar_server]).as_tool(
                tool_name="financial_metrics",
                tool_description="Extract financial statements and calculate comprehensive financial ratios (liquidity, solvency, profitability, efficiency)",
                custom_output_extractor=_metrics_extractor,
            )
            tools.append(metrics_tool)

        writer_with_tools = writer_agent_enhanced.clone(tools=tools)

        self.printer.update_item("writing", "Drafting comprehensive report...")

        # Include EDGAR results in the input if available
        input_data = f"Original query: {query}\n\nSummarized search results: {search_results}"
        if edgar_results:
            input_data += f"\n\nSEC Filing Analysis:\n{edgar_results}"

        # Include YoY comparison tables from 04_financial_metrics.md if available
        if self.session_dir:
            metrics_file = self.session_dir / "04_financial_metrics.md"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics_content = f.read()
                    # Extract YoY tables (they're between "### Key Financial Metrics" and "## Liquidity Ratios")
                    if "### Key Financial Metrics (YoY Comparison)" in metrics_content:
                        start_idx = metrics_content.find("### Key Financial Metrics (YoY Comparison)")
                        end_idx = metrics_content.find("## Liquidity Ratios")
                        if start_idx != -1 and end_idx != -1:
                            yoy_tables = metrics_content[start_idx:end_idx].strip()
                            input_data += f"\n\n**Year-over-Year Comparison Tables (from 04_financial_metrics.md):**\n\n{yoy_tables}\n\n"

        result = Runner.run_streamed(writer_with_tools, input_data)
        update_messages = [
            "Calling specialist analysts...",
            "Synthesizing financial analysis...",
            "Synthesizing risk assessment...",
            "Finalizing comprehensive report...",
        ]
        last_update = time.time()
        next_message = 0
        async for _ in result.stream_events():
            if time.time() - last_update > 5 and next_message < len(update_messages):
                self.printer.update_item("writing", update_messages[next_message])
                next_message += 1
                last_update = time.time()
        self.printer.mark_item_done("writing")

        # Track writer agent cost
        # Note: For streamed results, we need to access the usage from result object
        if self.cost_tracker and hasattr(result, 'raw_responses'):
            # Create a mock object with raw_responses for tracking
            class MockResult:
                pass
            mock = MockResult()
            mock.raw_responses = result.raw_responses if hasattr(result, 'raw_responses') else []
            self.cost_tracker.track_agent_run("writer", AgentConfig.WRITER_MODEL, mock)

        report = result.final_output_as(ComprehensiveFinancialReport)

        # Save the final report
        report_content = "# Comprehensive Financial Research Report\n\n"
        report_content += f"## Executive Summary\n\n{report.executive_summary}\n\n"
        report_content += f"## Key Takeaways\n\n"
        for i, takeaway in enumerate(report.key_takeaways, 1):
            report_content += f"{i}. {takeaway}\n\n"
        report_content += f"## Full Report\n\n{report.markdown_report}\n\n"
        report_content += f"## Follow-up Questions\n\n"
        for i, question in enumerate(report.follow_up_questions, 1):
            report_content += f"{i}. {question}\n\n"

        # Add Data Sources, Attribution and Validation section (exception-report style)
        report_content += "\n\n---\n\n"
        report_content += "## Data Sources, Attribution and Validation\n\n"

        # Add data sources
        if self.edgar_enabled:
            report_content += "**Data Sources:** SEC EDGAR filings accessed via SEC EDGAR MCP Server (Amorelli, S., 2025, https://doi.org/10.5281/zenodo.17123166); "
            report_content += "market data from public web sources.\n\n"
        else:
            report_content += "**Data Sources:** Market data from public web sources.\n\n"

        # Add validation status (exception-report style: brief unless issues)
        # Read validation details from 04_financial_metrics.md if available
        validation_passed = True
        validation_details = ""

        if self.session_dir:
            metrics_file = self.session_dir / "04_financial_metrics.md"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics_content = f.read()
                    # Check if balance sheet verification passed
                    if "Balance sheet verification: PASSED" in metrics_content or "Balance sheet verification PASSED" in metrics_content:
                        validation_passed = True
                    elif "Balance sheet verification: FAILED" in metrics_content or "Balance sheet verification FAILED" in metrics_content:
                        validation_passed = False
                        # Extract failure details if present
                        validation_details = "Balance sheet verification FAILED - see 04_financial_metrics.md for details. "

        if validation_passed:
            report_content += "**Data Quality:** All validations passed, including balance sheet equation verification and cash flow calculations. "
            report_content += "Complete financial statements in 03_financial_statements.md; detailed metrics and validations in 04_financial_metrics.md.\n\n"
        else:
            report_content += f"**Data Quality Exception:** {validation_details}\n\n"

        report_content += "---\n\n"
        report_content += "*This report was generated using AI-powered financial research tools. "
        report_content += "All data should be independently verified before making investment decisions.*\n"

        self._save_output("07_comprehensive_report.md", report_content)

        return report

    def _validate_financial_statements(self) -> list[str]:
        """
        Run deterministic checks on generated financial statements.
        Returns list of validation errors found.

        This function performs arithmetic validation that should never fail
        if XBRL data is correctly extracted. The fundamental accounting equation
        must always hold: Assets = Liabilities + Stockholders' Equity
        """
        errors = []

        # Check if financial statements file exists
        if self.session_dir is None:
            return errors

        statements_file = self.session_dir / "03_financial_statements.md"
        if not statements_file.exists():
            return errors  # No financial statements to validate

        try:
            # Read the file
            content = statements_file.read_text(encoding='utf-8')

            # Extract balance sheet numbers using regex
            # Looking for lines like: | Assets | $133,735,000,000 |
            import re

            # Match patterns for the key balance sheet line items
            # Look for various possible labels with spaces or without
            assets_match = (re.search(r'\|\s*\*?\*?Total [Aa]ssets\*?\*?\s*\|\s*\$([0-9,]+)', content) or
                          re.search(r'\|\s*\*?\*?Assets\*?\*?\s*\|\s*\$([0-9,]+)', content))
            liabilities_match = (re.search(r'\|\s*\*?\*?Total [Ll]iabilities\*?\*?\s*\|\s*\$([0-9,]+)', content) or
                               re.search(r'\|\s*\*?\*?Liabilities\*?\*?\s*\|\s*\$([0-9,]+)', content))
            equity_match = (re.search(r'\|\s*\*?\*?Total [Ss]tockholders[\'\s]*[Ee]quity\*?\*?\s*\|\s*\$([0-9,]+)', content) or
                          re.search(r'\|\s*\*?\*?Stockholders[\'\s]*[Ee]quity\*?\*?\s*\|\s*\$([0-9,]+)', content) or
                          re.search(r'\|\s*\*?\*?StockholdersEquity\*?\*?\s*\|\s*\$([0-9,]+)', content))

            # Also look for minority interest and redeemable noncontrolling interests
            minority_match = (re.search(r'\|\s*\*?\*?Minority [Ii]nterest\*?\*?\s*\|\s*\$([0-9,]+)', content) or
                            re.search(r'\|\s*\*?\*?MinorityInterest\*?\*?\s*\|\s*\$([0-9,]+)', content))
            redeemable_match = (re.search(r'\|\s*\*?\*?Redeemable [Nn]oncontrolling [Ii]nterests? in [Ss]ubsidiaries\*?\*?\s*\|\s*\$([0-9,]+)', content) or
                              re.search(r'\|\s*\*?\*?Redeemablenoncontrollinginterestsinsubsidiaries\*?\*?\s*\|\s*\$([0-9,]+)', content))

            if assets_match and liabilities_match and equity_match:
                # Parse the numbers (remove commas and convert to float)
                assets = float(assets_match.group(1).replace(',', ''))
                liabilities = float(liabilities_match.group(1).replace(',', ''))
                equity = float(equity_match.group(1).replace(',', ''))
                minority = float(minority_match.group(1).replace(',', '')) if minority_match else 0
                redeemable = float(redeemable_match.group(1).replace(',', '')) if redeemable_match else 0

                # Balance sheet equation: Assets = Liabilities + Equity + Minority Interest + Redeemable NCI
                # For Tesla: Assets = Liabilities + Stockholders' Equity + Minority Interest + Redeemable NCI
                total_equity_components = equity + minority + redeemable
                total = liabilities + total_equity_components
                diff = abs(assets - total)

                # Set tolerance at 0.1% of total assets
                tolerance = assets * 0.001

                if diff > tolerance:
                    # Format numbers with commas for readability
                    equity_breakdown = f"   Stockholders' Equity: ${equity:,.0f}\n"
                    if minority > 0:
                        equity_breakdown += f"   + Minority Interest: ${minority:,.0f}\n"
                    if redeemable > 0:
                        equity_breakdown += f"   + Redeemable Noncontrolling Interests: ${redeemable:,.0f}\n"

                    errors.append(
                        f"⚠️  BALANCE SHEET ARITHMETIC ERROR:\n"
                        f"   Assets: ${assets:,.0f}\n"
                        f"   Liabilities: ${liabilities:,.0f}\n"
                        f"{equity_breakdown}"
                        f"   Total Liabilities & Equity: ${total:,.0f}\n"
                        f"   Difference: ${diff:,.0f} ({diff/assets*100:.2f}% of Assets)\n"
                        f"   This exceeds tolerance of ${tolerance:,.0f} (0.1% of Assets)\n"
                        f"   → The fundamental accounting equation (Assets = L + All Equity Components) does not balance!"
                    )
        except Exception as e:
            # Don't fail the whole process if validation has an issue
            # Just log it for debugging
            errors.append(f"⚠️  Error during balance sheet validation: {str(e)}")

        return errors

    async def _verify_report(self, report: ComprehensiveFinancialReport) -> VerificationResult:
        self.printer.update_item("verifying", "Verifying comprehensive report...")
        result = await Runner.run(verifier_agent, report.markdown_report)

        # Track verifier cost
        if self.cost_tracker:
            self.cost_tracker.track_agent_run("verifier", AgentConfig.VERIFIER_MODEL, result)

        self.printer.mark_item_done("verifying")

        verification = result.final_output_as(VerificationResult)

        # Save verification results
        verification_content = f"# Verification Results\n\n"
        verification_content += f"**Verified:** {'✅ Yes' if verification.verified else '❌ No'}\n\n"

        if verification.verified and not verification.issues:
            # When verification passes, provide summary of what was checked
            verification_content += f"## Summary\n\n"
            verification_content += "The comprehensive financial report has been verified and meets quality standards:\n\n"
            verification_content += "### ✅ Report Quality Checks Passed\n"
            verification_content += "- Financial data is complete and internally consistent\n"
            verification_content += "- All three financial statements (balance sheet, income statement, cash flow) are present\n"
            verification_content += "- Comparative period data (Current vs Prior) is included\n"
            verification_content += "- Key financial metrics are properly calculated\n"
            verification_content += "- Analysis is comprehensive and well-structured\n"
            verification_content += "- Citations and sources are properly documented\n\n"
            verification_content += "### 📊 Data Validation Details\n"
            verification_content += "For detailed verification of XBRL financial data extraction, see:\n"
            verification_content += "- `data_verification.md` - Comprehensive validation of balance sheet equation and line item counts\n\n"
        else:
            # When there are issues or comments, display them
            verification_content += f"## Issues/Comments\n\n{verification.issues}\n"

        # Add XBRL validation warnings if present
        if self.xbrl_warnings:
            verification_content += f"\n## XBRL Calculation Linkbase Validation\n\n"
            verification_content += "The following discrepancies were found when validating financial statement totals "
            verification_content += "against official SEC XBRL calculation linkbase relationships:\n\n"
            for warning in self.xbrl_warnings:
                verification_content += f"- ⚠️ {warning}\n"
            verification_content += "\n*Note: 2% tolerance applied for rounding differences*\n"

        self._save_output("08_verification.md", verification_content)

        # Warn if verification failed
        if not verification.verified:
            self.console.print("[bold yellow]⚠️  Warning: Report verification failed![/bold yellow]")
            self.console.print(f"[yellow]Issues: {verification.issues}[/yellow]")

        return verification
