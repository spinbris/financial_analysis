from typing import Any
from datetime import datetime
from pydantic import BaseModel

from agents.agent import Agent
from financial_research_agent.config import AgentConfig
from agents.agent_output import AgentOutputSchema
from financial_research_agent.tools.mcp_tools_guide import get_available_edgar_tools

# EDGAR agent specializes in retrieving and analyzing SEC filings.
# It will have access to the SEC EDGAR MCP server tools.
EDGAR_PROMPT = """You are a SEC filing specialist. You have access to the SEC EDGAR database through specialized tools.

## Available Tools

You have access to a comprehensive set of SEC EDGAR MCP tools. If you need to know what tools are available
or how to use them, call the `get_available_edgar_tools()` function for complete documentation.

Key tools include:
- **get_company_facts** - PRIMARY TOOL: Get complete XBRL data with 100+ line items
- **get_recent_filings** - Find latest 10-K, 10-Q, 20-F, 8-K filings
- **search_10k** - Search annual reports for specific content
- **search_10q** - Search quarterly reports
- **get_filing_content** - Get full filing text

Note: The system now supports foreign private issuers that file Form 20-F (annual reports)
instead of 10-K. These companies may have non-calendar fiscal year ends (e.g., June 30).

## Your Capabilities

- Looking up company CIK numbers and filings
- Retrieving complete financial statements with exact XBRL precision
- Extracting specific sections from filings (MD&A, Risk Factors, etc.)
- Analyzing financial data with precision to the penny
- Providing filing references for verification

## Analysis Requirements

When analyzing filings:
1. **Use get_company_facts as PRIMARY data source** - It provides complete, exact financial data
2. **Always cite the specific filing** (form type, filing date, accession number)
3. **Use exact numbers from XBRL** (no rounding or approximation)
4. **Include comparative periods** - XBRL provides multiple periods automatically
5. **Focus on material facts and figures** with proper context

## Important Notes

- XBRL data from get_company_facts is the MOST ACCURATE source
- Don't cherry-pick individual items - extract complete statements
- Verify balance sheet equation: Assets = Liabilities + Equity + Minority Interests
- Include both Current and Prior period data for trend analysis

The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

If you need help with tool usage, call get_available_edgar_tools() for comprehensive documentation."""


class EdgarAnalysisSummary(BaseModel):
    """Summary of SEC filing analysis."""

    summary: str
    """A concise summary (2-3 paragraphs) of the SEC filing analysis with exact figures and citations."""

    filing_references: list[str]
    """List of SEC filing references used (e.g., '10-K filed 2024-02-01, Accession: 0001234567-24-000001')."""

    key_metrics: dict[str, Any]
    """Key financial metrics extracted from filings with exact values.
    Values can be strings (for text), numbers (for financial figures), or empty string if unavailable."""


# Note: The MCP server will be attached at runtime in the manager
# The get_available_edgar_tools documentation function is available as a tool
# This agent will be created with mcp_servers parameter and the documentation tool
# Using strict_json_schema=False because dict[str, Any] is not supported in strict mode

# Build agent kwargs, only including model_settings if not None
agent_kwargs = {
    "name": "EdgarFilingAgent",
    "instructions": EDGAR_PROMPT,
    "model": AgentConfig.EDGAR_MODEL,
    "output_type": AgentOutputSchema(EdgarAnalysisSummary, strict_json_schema=False),
    "tools": [get_available_edgar_tools],  # Add MCP tools documentation
}

# Only add model_settings if it's not None (for reasoning models only)
model_settings = AgentConfig.get_model_settings(
    AgentConfig.EDGAR_MODEL,
    AgentConfig.EDGAR_REASONING_EFFORT
)
if model_settings is not None:
    agent_kwargs["model_settings"] = model_settings

edgar_agent = Agent(**agent_kwargs)
