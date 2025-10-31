"""
Test script to verify deterministic EDGAR extraction works.
"""

import asyncio
from financial_research_agent.edgar_tools import extract_financial_data_deterministic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_extraction():
    """Test the deterministic extraction."""

    # Create MCP client to SEC EDGAR server
    server_params = StdioServerParameters(
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-secedgar@latest",
        ],
        env={
            "SEC_EDGAR_USER_AGENT": "FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"
        }
    )

    print("Starting SEC EDGAR MCP server...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            print("MCP session initialized\n")

            # Test extraction
            print("=" * 60)
            print("Testing deterministic extraction for Apple Inc")
            print("=" * 60)

            try:
                results = await extract_financial_data_deterministic(
                    session,
                    "Apple Inc"
                )

                print("\n" + "=" * 60)
                print("EXTRACTION RESULTS")
                print("=" * 60)

                # Show balance sheet sample
                print("\nBalance Sheet (first 5 items):")
                for i, (key, value) in enumerate(results['balance_sheet'].items()):
                    if i >= 5:
                        break
                    print(f"  {key}: {value}")

                # Show income statement sample
                print("\nIncome Statement (first 5 items):")
                for i, (key, value) in enumerate(results['income_statement'].items()):
                    if i >= 5:
                        break
                    print(f"  {key}: {value}")

                # Show cash flow statement sample
                print("\nCash Flow Statement (first 5 items):")
                for i, (key, value) in enumerate(results['cash_flow_statement'].items()):
                    if i >= 5:
                        break
                    print(f"  {key}: {value}")

                # Show totals
                print(f"\nTotal line items extracted:")
                print(f"  Balance Sheet: {len(results['balance_sheet'])} items")
                print(f"  Income Statement: {len(results['income_statement'])} items")
                print(f"  Cash Flow Statement: {len(results['cash_flow_statement'])} items")

            except Exception as e:
                print(f"\nERROR: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_extraction())
