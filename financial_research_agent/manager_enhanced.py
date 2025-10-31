from __future__ import annotations

import asyncio
import json
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
from .formatters import format_financial_statements, format_financial_metrics
from .printer import Printer


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

    def __init__(self, output_dir: str = "financial_research_agent/output") -> None:
        self.console = Console()
        self.printer = Printer(self.console)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create a timestamped session directory for this run
        self.session_dir: Path | None = None

        # EDGAR MCP server (initialized in run())
        self.edgar_server: MCPServerStdio | None = None
        self.edgar_enabled = AgentConfig.ENABLE_EDGAR_INTEGRATION

    async def run(self, query: str) -> None:
        # Create timestamped session directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / timestamp
        self.session_dir.mkdir(parents=True, exist_ok=True)

        trace_id = gen_trace_id()

        # Initialize EDGAR MCP server if enabled
        if self.edgar_enabled:
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

                # Save the original query
                self._save_output("00_query.md", f"# Original Query\n\n{query}\n")

                search_plan = await self._plan_searches(query)
                search_results = await self._perform_searches(search_plan)

                # Optionally gather EDGAR data if enabled
                edgar_results = None
                metrics_results = None
                if self.edgar_enabled and self.edgar_server:
                    edgar_results = await self._gather_edgar_data(query, search_plan)
                    # Gather financial metrics and statements
                    metrics_results = await self._gather_financial_metrics(query)
                    # Gather specialist analyses and save separately
                    await self._gather_specialist_analyses(query, search_results)

                report = await self._write_report(query, search_results, edgar_results, metrics_results)
                verification = await self._verify_report(report)

                final_summary = f"Report complete\n\n{report.executive_summary}"
                self.printer.update_item("final_report", final_summary, is_done=True)

                self.printer.end()

            # Print to stdout
            print("\n\n=====COMPREHENSIVE RESEARCH REPORT=====\n\n")
            print(f"Executive Summary:\n{report.executive_summary}\n")
            print(f"\n{report.markdown_report}")
            print("\n\n=====KEY TAKEAWAYS=====\n\n")
            for i, takeaway in enumerate(report.key_takeaways, 1):
                print(f"{i}. {takeaway}")
            print("\n\n=====FOLLOW UP QUESTIONS=====\n\n")
            for i, question in enumerate(report.follow_up_questions, 1):
                print(f"{i}. {question}")
            print("\n\n=====VERIFICATION=====\n\n")
            print(verification)
            print(f"\n\nOutputs saved to: {self.session_dir.absolute()}")

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

    async def _gather_financial_metrics(self, query: str) -> FinancialMetrics | None:
        """Gather financial statements and calculate comprehensive ratios."""
        if not self.edgar_server:
            return None

        self.printer.update_item("metrics", "Extracting financial statements and calculating ratios...")

        try:
            # Import deterministic extraction module
            from financial_research_agent.edgar_tools import extract_financial_data_deterministic

            # Extract company name from query (simple heuristic)
            company_name = query.split()[0] if query else "Company"

            # Step 1: Use deterministic extraction to get complete financial data
            self.printer.update_item("metrics", f"Extracting financial data for {company_name} using deterministic MCP tools...")

            statements_data = None
            try:
                statements_data = await extract_financial_data_deterministic(
                    self.edgar_server,
                    company_name
                )
                self.console.print(f"[green]Successfully extracted {len(statements_data['balance_sheet'])} balance sheet items[/green]")
                self.console.print(f"[green]Successfully extracted {len(statements_data['income_statement'])} income statement items[/green]")
                self.console.print(f"[green]Successfully extracted {len(statements_data['cash_flow_statement'])} cash flow items[/green]")
            except Exception as e:
                self.console.print(f"[yellow]Warning: Deterministic extraction failed: {e}[/yellow]")
                import traceback
                traceback.print_exc()
                self.console.print("[yellow]Falling back to LLM-based extraction...[/yellow]")

            # Step 2: Clone metrics agent with MCP server attached
            metrics_with_mcp = financial_metrics_agent.clone(mcp_servers=[self.edgar_server])

            # Step 3: Create query for the agent
            if statements_data and statements_data['balance_sheet']:
                # We have deterministic data - provide it to the agent
                self.printer.update_item("metrics", "Calculating financial ratios from extracted data...")
                metrics_query = f"""Query: {query}

Financial statements have been pre-extracted from SEC EDGAR using deterministic get_company_facts API:

Balance Sheet ({len(statements_data['balance_sheet'])} line items):
{json.dumps(statements_data['balance_sheet'], indent=2)}

Income Statement ({len(statements_data['income_statement'])} line items):
{json.dumps(statements_data['income_statement'], indent=2)}

Cash Flow Statement ({len(statements_data['cash_flow_statement'])} line items):
{json.dumps(statements_data['cash_flow_statement'], indent=2)}

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

            # Save financial statements (03_financial_statements.md)
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

            # Debug: Print full traceback
            self.console.print(f"[dim]Full error details:[/dim]")
            self.console.print(f"[dim]{traceback.format_exc()}[/dim]")

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
            risk_result = await Runner.run(risk_with_edgar, input_data, max_turns=AgentConfig.MAX_AGENT_TURNS)
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
            # Debug: Print full traceback
            self.console.print(f"[dim]Full error details:[/dim]")
            self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
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

    async def _verify_report(self, report: ComprehensiveFinancialReport) -> VerificationResult:
        self.printer.update_item("verifying", "Verifying comprehensive report...")
        result = await Runner.run(verifier_agent, report.markdown_report)
        self.printer.mark_item_done("verifying")

        verification = result.final_output_as(VerificationResult)

        # Save verification results
        verification_content = f"# Verification Results\n\n"
        verification_content += f"**Verified:** {'✅ Yes' if verification.verified else '❌ No'}\n\n"
        verification_content += f"## Issues/Comments\n\n{verification.issues}\n"
        self._save_output("08_verification.md", verification_content)

        # Warn if verification failed
        if not verification.verified:
            self.console.print("[bold yellow]⚠️  Warning: Report verification failed![/bold yellow]")
            self.console.print(f"[yellow]Issues: {verification.issues}[/yellow]")

        return verification
