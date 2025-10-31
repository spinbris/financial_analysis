#!/usr/bin/env python3
import asyncio
import os

os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

from agents.mcp import MCPServerStdio
from financial_research_agent.config import EdgarConfig

async def test_get_metrics():
    print("Testing get_company_metrics...")

    params = {
        "command": EdgarConfig.MCP_SERVER_COMMAND,
        "args": EdgarConfig.MCP_SERVER_ARGS,
        "env": EdgarConfig.get_mcp_env(),
    }

    edgar_server = MCPServerStdio(params=params, client_session_timeout_seconds=60.0)
    await edgar_server.connect()
    print("✓ Connected")

    # Test get_company_metrics
    result = await edgar_server.call_tool(
        "get_company_metrics",
        arguments={"identifier": "0000320193"}
    )

    text = result.content[0].text
    print(f"Response length: {len(text)} characters")
    print(f"First 2000 chars:\n{text[:2000]}")

    with open("get_company_metrics_response.json", "w") as f:
        f.write(text)
    print("\n✓ Saved to get_company_metrics_response.json")

    await edgar_server.cleanup()

asyncio.run(test_get_metrics())
