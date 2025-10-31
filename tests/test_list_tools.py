#!/usr/bin/env python3
import asyncio
import os

os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

from agents.mcp import MCPServerStdio
from financial_research_agent.config import EdgarConfig

async def test_list():
    params = {
        "command": EdgarConfig.MCP_SERVER_COMMAND,
        "args": EdgarConfig.MCP_SERVER_ARGS,
        "env": EdgarConfig.get_mcp_env(),
    }

    edgar_server = MCPServerStdio(params=params, client_session_timeout_seconds=60.0)
    await edgar_server.connect()
   
    tools = await edgar_server.list_tools()
    print(f"Found {len(tools)} tools:\n")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
        if hasattr(tool, 'inputSchema') and tool.inputSchema:
            schema = tool.inputSchema
            if 'properties' in schema:
                print(f"  Parameters: {list(schema['properties'].keys())}")
        print()

    await edgar_server.cleanup()

asyncio.run(test_list())
