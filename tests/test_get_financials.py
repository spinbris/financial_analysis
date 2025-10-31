#!/usr/bin/env python3
import asyncio
import os
import json

os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

from agents.mcp import MCPServerStdio
from financial_research_agent.config import EdgarConfig

async def test():
    params = {
        "command": EdgarConfig.MCP_SERVER_COMMAND,
        "args": EdgarConfig.MCP_SERVER_ARGS,
        "env": EdgarConfig.get_mcp_env(),
    }

    edgar_server = MCPServerStdio(params=params, client_session_timeout_seconds=60.0)
    await edgar_server.connect()
    print("✓ Connected")

    result = await edgar_server.call_tool(
        "get_financials",
        arguments={
            "identifier": "0000320193",
            "statement_type": "all"
        }
    )

    text = result.content[0].text
    print(f"Response length: {len(text)} characters\n")
    
    # Try to parse as JSON
    try:
        data = json.loads(text)
        print("✓ Valid JSON response")
        print(f"Keys: {list(data.keys())}\n")
        
        # Print structure
        for key in data.keys():
            if isinstance(data[key], dict):
                print(f"{key}: {len(data[key])} items")
            elif isinstance(data[key], list):
                print(f"{key}: list with {len(data[key])} items")
            else:
                print(f"{key}: {type(data[key])}")
    except:
        print("Not JSON, showing first 3000 chars:")
        print(text[:3000])

    with open("get_financials_response.json", "w") as f:
        f.write(text)
    print("\n✓ Saved to get_financials_response.json")

    await edgar_server.cleanup()

asyncio.run(test())
