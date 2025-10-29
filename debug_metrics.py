#!/usr/bin/env python3
"""
Debug script to test financial metrics extraction in isolation.
This will help identify the exact error without running the full enhanced manager.
"""
import asyncio
import sys
import os

# Ensure we can import the financial_research_agent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    from agents.mcp import MCPServerStdio
    from agents import Runner
    from financial_research_agent.agents.financial_metrics_agent import financial_metrics_agent, FinancialMetrics
    from financial_research_agent.config import EdgarConfig, AgentConfig

    print("=" * 70)
    print("FINANCIAL METRICS DEBUG TEST")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  MAX_AGENT_TURNS: {AgentConfig.MAX_AGENT_TURNS}")
    print(f"  METRICS_MODEL: {AgentConfig.METRICS_MODEL}")
    print(f"  EDGAR User-Agent: {EdgarConfig.USER_AGENT}")

    # Initialize EDGAR server
    print("\n[1/4] Initializing EDGAR server...")
    try:
        edgar_server = MCPServerStdio(
            params={
                "command": EdgarConfig.MCP_SERVER_COMMAND,
                "args": EdgarConfig.MCP_SERVER_ARGS,
                "env": EdgarConfig.get_mcp_env(),
            },
            client_session_timeout_seconds=60.0,
        )

        await edgar_server.connect()
        print("  ✓ EDGAR server connected successfully")
    except Exception as e:
        print(f"  ✗ EDGAR server connection failed: {e}")
        return

    # Clone metrics agent with MCP
    print("\n[2/4] Cloning metrics agent with EDGAR MCP server...")
    try:
        metrics_with_mcp = financial_metrics_agent.clone(mcp_servers=[edgar_server])
        print("  ✓ Agent cloned successfully")
    except Exception as e:
        print(f"  ✗ Agent cloning failed: {e}")
        await edgar_server.cleanup()
        return

    # Test query
    query = "Apple Inc latest quarterly performance"
    print(f"\n[3/4] Running financial metrics extraction...")
    print(f"  Query: {query}")
    print(f"  Max turns: {AgentConfig.MAX_AGENT_TURNS}")

    try:
        result = await Runner.run(
            metrics_with_mcp,
            f"Query: {query}\n\nExtract the most recent financial statements and calculate comprehensive financial ratios.",
            max_turns=AgentConfig.MAX_AGENT_TURNS
        )
        metrics = result.final_output_as(FinancialMetrics)

        print("\n  ✓ SUCCESS! Financial metrics extracted")
        print(f"\n[4/4] Results:")
        print(f"  Period: {metrics.period}")
        print(f"  Filing Date: {metrics.filing_date}")
        print(f"  Executive Summary: {metrics.executive_summary[:100]}...")
        print(f"  Current Ratio: {metrics.current_ratio}")
        print(f"  Quick Ratio: {metrics.quick_ratio}")
        print(f"  Debt-to-Equity: {metrics.debt_to_equity}")
        print(f"  ROE: {metrics.return_on_equity}")
        print(f"\n  Balance Sheet items: {len(metrics.balance_sheet)}")
        print(f"  Income Statement items: {len(metrics.income_statement)}")
        print(f"  Cash Flow items: {len(metrics.cash_flow_statement)}")

    except Exception as e:
        print(f"\n  ✗ FAILED: {e}")
        print(f"\n[4/4] Full Error Traceback:")
        import traceback
        traceback.print_exc()

    # Cleanup
    print("\nCleaning up...")
    await edgar_server.cleanup()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
