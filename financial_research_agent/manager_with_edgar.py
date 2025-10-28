from __future__ import annotations

import asyncio
import time
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from rich.console import Console

from agents import Runner, RunResult, custom_span, gen_trace_id, trace
from agents.mcp import MCPServerStdio

from .agents.edgar_agent import EdgarAnalysisSummary, edgar_agent
from .agents.financials_agent import financials_agent
from .agents.planner_agent import FinancialSearchItem, FinancialSearchPlan, planner_agent
from .agents.risk_agent import risk_agent
from .agents.search_agent import search_agent
from .agents.verifier_agent import VerificationResult, verifier_agent
from .agents.writer_agent import FinancialReportData, writer_agent
from .config import AgentConfig, EdgarConfig
from .printer import Printer


async def _summary_extractor(run_result: RunResult) -> str:
    """Custom output extractor for sub-agents that return an AnalysisSummary."""
    # The financial/risk analyst agents emit an AnalysisSummary with a `summary` field.
    # We want the tool call to return just that summary text so the writer can drop it inline.
    return str(run_result.final_output.summary)


async def _edgar_extractor(run_result: RunResult) -> str:
    """Custom output extractor for EDGAR agent."""
    edgar_result: EdgarAnalysisSummary = run_result.final_output
    output = f"{edgar_result.summary}\n\n"
    if edgar_result.filing_references:
        output += "**Filings Referenced:**\n"
        for ref in edgar_result.filing_references:
            output += f"- {ref}\n"
    return output


class FinancialResearchManagerWithEdgar:
    """
    Enhanced orchestrator with SEC EDGAR integration via MCP server.

    This version adds direct access to SEC filings for more authoritative
    financial data alongside web search results.
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
            with trace("Financial research trace", trace_id=trace_id):
                self.printer.update_item(
                    "trace_id",
                    f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}",
                    is_done=True,
                    hide_checkmark=True,
                )
                self.printer.update_item("start", "Starting financial research...", is_done=True)

                # Save the original query
                self._save_output("00_query.md", f"# Original Query\n\n{query}\n")

                search_plan = await self._plan_searches(query)
                search_results = await self._perform_searches(search_plan)

                # Optionally gather EDGAR data if enabled
                edgar_results = None
                if self.edgar_enabled and self.edgar_server:
                    edgar_results = await self._gather_edgar_data(query, search_plan)

                report = await self._write_report(query, search_results, edgar_results)
                verification = await self._verify_report(report)

                final_report = f"Report summary\n\n{report.short_summary}"
                self.printer.update_item("final_report", final_report, is_done=True)

                self.printer.end()

            # Print to stdout
            print("\n\n=====REPORT=====\n\n")
            print(f"Report:\n{report.markdown_report}")
            print("\n\n=====FOLLOW UP QUESTIONS=====\n\n")
            print("\n".join(report.follow_up_questions))
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

    async def _write_report(
        self, query: str, search_results: Sequence[str], edgar_results: str | None
    ) -> FinancialReportData:
        # Expose the specialist analysts as tools so the writer can invoke them inline
        # If EDGAR is available, give specialist agents access to EDGAR tools for better analysis
        if self.edgar_enabled and self.edgar_server:
            # Clone specialist agents with EDGAR MCP server access
            financials_with_edgar = financials_agent.clone(mcp_servers=[self.edgar_server])
            risk_with_edgar = risk_agent.clone(mcp_servers=[self.edgar_server])

            fundamentals_tool = financials_with_edgar.as_tool(
                tool_name="fundamentals_analysis",
                tool_description="Use to get a short write-up of key financial metrics from SEC filings and research",
                custom_output_extractor=_summary_extractor,
            )
            risk_tool = risk_with_edgar.as_tool(
                tool_name="risk_analysis",
                tool_description="Use to get a short write-up of potential red flags from SEC Risk Factors and research",
                custom_output_extractor=_summary_extractor,
            )
        else:
            # Use standard agents without EDGAR access
            fundamentals_tool = financials_agent.as_tool(
                tool_name="fundamentals_analysis",
                tool_description="Use to get a short write-up of key financial metrics",
                custom_output_extractor=_summary_extractor,
            )
            risk_tool = risk_agent.as_tool(
                tool_name="risk_analysis",
                tool_description="Use to get a short write-up of potential red flags",
                custom_output_extractor=_summary_extractor,
            )

        tools = [fundamentals_tool, risk_tool]

        # Add dedicated EDGAR agent as a tool if available (for writer to query filings directly)
        if self.edgar_enabled and self.edgar_server:
            edgar_tool = edgar_agent.clone(mcp_servers=[self.edgar_server]).as_tool(
                tool_name="sec_filing_analysis",
                tool_description="Use to retrieve and analyze official SEC filings with exact financial data",
                custom_output_extractor=_edgar_extractor,
            )
            tools.append(edgar_tool)

        writer_with_tools = writer_agent.clone(tools=tools)

        self.printer.update_item("writing", "Thinking about report...")

        # Include EDGAR results in the input if available
        input_data = f"Original query: {query}\n\nSummarized search results: {search_results}"
        if edgar_results:
            input_data += f"\n\nSEC Filing Analysis:\n{edgar_results}"

        result = Runner.run_streamed(writer_with_tools, input_data)
        update_messages = [
            "Planning report structure...",
            "Writing sections...",
            "Finalizing report...",
        ]
        last_update = time.time()
        next_message = 0
        async for _ in result.stream_events():
            if time.time() - last_update > 5 and next_message < len(update_messages):
                self.printer.update_item("writing", update_messages[next_message])
                next_message += 1
                last_update = time.time()
        self.printer.mark_item_done("writing")

        report = result.final_output_as(FinancialReportData)

        # Save the final report
        report_content = f"# Financial Research Report\n\n"
        report_content += f"## Executive Summary\n\n{report.short_summary}\n\n"
        report_content += f"## Full Report\n\n{report.markdown_report}\n\n"
        report_content += f"## Follow-up Questions\n\n"
        for i, question in enumerate(report.follow_up_questions, 1):
            report_content += f"{i}. {question}\n"
        self._save_output("03_final_report.md", report_content)

        return report

    async def _verify_report(self, report: FinancialReportData) -> VerificationResult:
        self.printer.update_item("verifying", "Verifying report...")
        result = await Runner.run(verifier_agent, report.markdown_report)
        self.printer.mark_item_done("verifying")

        verification = result.final_output_as(VerificationResult)

        # Save verification results
        verification_content = f"# Verification Results\n\n"
        verification_content += f"**Verified:** {'✅ Yes' if verification.verified else '❌ No'}\n\n"
        verification_content += f"## Issues/Comments\n\n{verification.issues}\n"
        self._save_output("04_verification.md", verification_content)

        # Warn if verification failed
        if not verification.verified:
            self.console.print("[bold yellow]⚠️  Warning: Report verification failed![/bold yellow]")
            self.console.print(f"[yellow]Issues: {verification.issues}[/yellow]")

        return verification
