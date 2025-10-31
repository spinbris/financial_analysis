#!/usr/bin/env python3
import asyncio
import os

os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

from agents.mcp import MCPServerStdio
from financial_research_agent.config import EdgarConfig
from financial_research_agent.edgar_tools import extract_financial_data_deterministic

async def test():
    params = {
        "command": EdgarConfig.MCP_SERVER_COMMAND,
        "args": EdgarConfig.MCP_SERVER_ARGS,
        "env": EdgarConfig.get_mcp_env(),
    }

    edgar_server = MCPServerStdio(params=params, client_session_timeout_seconds=60.0)
    await edgar_server.connect()
    print("✓ Connected to EDGAR server\n")

    try:
        result = await extract_financial_data_deterministic(edgar_server, "Apple")
        
        print(f"✓ Extraction successful!\n")
        print(f"Balance Sheet items: {len(result['balance_sheet'])}")
        print(f"  Sample: {list(result['balance_sheet'].keys())[:5]}\n")
        
        print(f"Income Statement items: {len(result['income_statement'])}")
        print(f"  Sample: {list(result['income_statement'].keys())[:5]}\n")
        
        print(f"Cash Flow items: {len(result['cash_flow_statement'])}")
        print(f"  Sample: {list(result['cash_flow_statement'].keys())[:5]}\n")
        
        print(f"Period: {result['period']}")
        print(f"Filing: {result['filing_reference']}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await edgar_server.cleanup()

asyncio.run(test())
