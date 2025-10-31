#!/usr/bin/env python3
"""Direct test of EDGAR extraction without running full agent."""

import asyncio
import os

# Set required env var
os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

from agents.mcp import MCPServerStdio
from financial_research_agent.config import EdgarConfig


async def test_extraction():
    """Test direct EDGAR MCP tool call."""
    print("Starting direct extraction test...")

    # Initialize EDGAR server
    print("Initializing EDGAR server...")
    params = {
        "command": EdgarConfig.MCP_SERVER_COMMAND,
        "args": EdgarConfig.MCP_SERVER_ARGS,
        "env": EdgarConfig.get_mcp_env(),
    }

    edgar_server = MCPServerStdio(
        params=params,
        client_session_timeout_seconds=60.0,
    )

    print("Connecting to EDGAR server...")
    await edgar_server.connect()
    print("✓ Connected to EDGAR server")

    # Test call_tool method
    print("\nTesting get_company_facts for Apple (CIK 0000320193)...")
    try:
        result = await edgar_server.call_tool(
            "get_company_facts",
            arguments={"identifier": "0000320193"}  # Correct parameter name
        )

        print(f"✓ call_tool succeeded!")
        print(f"Result type: {type(result)}")
        print(f"Result has 'content' attr: {hasattr(result, 'content')}")

        if hasattr(result, 'content'):
            print(f"Content length: {len(result.content)}")
            if len(result.content) > 0:
                first_item = result.content[0]
                print(f"First content item type: {type(first_item)}")
                print(f"Has 'text' attr: {hasattr(first_item, 'text')}")

                if hasattr(first_item, 'text'):
                    text = first_item.text
                    print(f"Text length: {len(text)} characters")
                    print(f"First 1000 chars:\n{text[:1000]}")

                    # Save to file for inspection
                    with open("get_company_facts_response.json", "w") as f:
                        f.write(text)
                    print(f"\n✓ Full response saved to get_company_facts_response.json")

        print("\n✓ Test completed successfully!")

    except Exception as e:
        print(f"✗ Error calling tool: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await edgar_server.cleanup()


if __name__ == "__main__":
    asyncio.run(test_extraction())
