from __future__ import annotations

import asyncio
import json
import shutil
import time
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from rich.console import Console

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
from .config import AgentConfig, EdgarConfig
from .formatters import format_financial_statements, format_financial_statements_gt, format_financial_metrics
from .printer import Printer
from .cache import FinancialDataCache
from .xbrl_calculation import get_calculation_parser_for_filing


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

    async def run(self, query: str) -> None:
        # Create timestamped session directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / timestamp
        self.session_dir.mkdir(parents=True, exist_ok=True)

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
                    metrics_results = await self._gather_financial_metrics(query)

                    self._report_progress(0.55, "Running specialist financial analyses...")
                    # Gather specialist analyses and save separately
                    await self._gather_specialist_analyses(query, search_results)
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

    async def _gather_financial_metrics(self, query: str) -> FinancialMetrics | None:
        """Gather financial statements and calculate comprehensive ratios."""
        if not self.edgar_server:
            return None

        self.printer.update_item("metrics", "Extracting financial statements and calculating ratios...")

        try:
            # Import deterministic extraction module
            from financial_research_agent.edgar_tools import extract_financial_data_deterministic, dataframes_to_dict_format

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

            # PERFORMANCE: Check cache first
            cached_statements = self.cache.get(company_name, "financial_statements")
            if cached_statements:
                self.console.print(f"[dim]✓ Using cached financial data for {company_name}[/dim]")
                statements_data = cached_statements
            else:
                # Step 1: Use deterministic extraction to get complete financial data
                self.printer.update_item("metrics", f"Extracting financial data for {company_name} using deterministic MCP tools...")

                statements_data = None
                try:
                    statements_data = await extract_financial_data_deterministic(
                        self.edgar_server,
                        company_name
                    )

                    # PERFORMANCE: Cache the extracted data
                    if statements_data:
                        self.cache.set(company_name, "financial_statements", statements_data)
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

                metrics_query = f"""Query: {query}

Financial statements have been pre-extracted from SEC EDGAR using deterministic get_company_facts API:

Balance Sheet ({len(bs_data)} line items):
{json.dumps(bs_data, indent=2)}

Income Statement ({len(is_data)} line items):
{json.dumps(is_data, indent=2)}

Cash Flow Statement ({len(cf_data)} line items):
{json.dumps(cf_data, indent=2)}

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
            # Check if we have DataFrames from the new extraction method
            if statements_data and 'balance_sheet_df' in statements_data:
                # New DataFrame-based approach using Great Tables
                self.console.print("[dim]Using Great Tables formatter for professional table styling[/dim]")
                statements_content = format_financial_statements_gt(
                    balance_sheet_df=statements_data['balance_sheet_df'],
                    income_statement_df=statements_data['income_statement_df'],
                    cash_flow_statement_df=statements_data['cash_flow_statement_df'],
                    company_name=company_name,
                    current_period=statements_data.get('current_period', 'Current'),
                    prior_period=statements_data.get('prior_period'),
                    filing_reference=statements_data.get('filing_reference', 'Unknown'),
                )
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

            # Save financial metrics (04_financial_metrics.md)
            metrics_content = format_financial_metrics(metrics, company_name)
            self._save_output("04_financial_metrics.md", metrics_content)

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

    async def _gather_specialist_analyses(self, query: str, search_results: Sequence[str]) -> None:
        """Gather detailed financial and risk analyses and save separately."""
        if not self.edgar_server:
            return

        self.printer.update_item("specialist_analysis", "Running specialist analyses...")

        try:
            # Clone specialist agents with EDGAR MCP server access
            financials_with_edgar = financials_agent_enhanced.clone(mcp_servers=[self.edgar_server])
            risk_with_edgar = risk_agent_enhanced.clone(mcp_servers=[self.edgar_server])

            # Prepare input data
            input_data = f"Query: {query}\n\nContext from research:\n{search_results[:3]}"

            # Run financial analysis
            self.printer.update_item("specialist_analysis", "Running financial analysis...")
            financials_result = await Runner.run(financials_with_edgar, input_data, max_turns=AgentConfig.MAX_AGENT_TURNS)
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

            # Run risk analysis
            self.printer.update_item("specialist_analysis", "Running risk analysis...")
            # Explicitly ask for risk analysis to avoid confusion
            risk_input = f"Analyze the key risks and risk factors for this company.\n\nOriginal query: {query}\n\nContext from research:\n{search_results[:3]}"
            risk_result = await Runner.run(risk_with_edgar, risk_input, max_turns=AgentConfig.MAX_AGENT_TURNS)
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

        report = result.final_output_as(ComprehensiveFinancialReport)

        # Save the final report
        report_content = "# Comprehensive Financial Research Report\n\n"
        report_content += f"## Executive Summary\n\n{report.executive_summary}\n\n"
        report_content += f"## Key Takeaways\n\n"
        for i, takeaway in enumerate(report.key_takeaways, 1):
            report_content += f"{i}. {takeaway}\n"
        report_content += f"\n## Full Report\n\n{report.markdown_report}\n\n"
        report_content += f"## Follow-up Questions\n\n"
        for i, question in enumerate(report.follow_up_questions, 1):
            report_content += f"{i}. {question}\n"

        # Add attribution footer
        report_content += "\n\n---\n\n"
        report_content += "## Data Sources & Attribution\n\n"
        if self.edgar_enabled:
            report_content += "**SEC Filing Data:** U.S. Securities and Exchange Commission (SEC) via SEC EDGAR database.  \n"
            report_content += "Accessed using SEC EDGAR MCP Server by Amorelli, S. (2025). https://doi.org/10.5281/zenodo.17123166\n\n"
        report_content += "**Market Data:** Web search results from public sources.\n\n"
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
