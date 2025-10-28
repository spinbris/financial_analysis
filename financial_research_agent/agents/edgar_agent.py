from typing import Any
from datetime import datetime
from pydantic import BaseModel

from agents import Agent
from agents.agent_output import AgentOutputSchema

# EDGAR agent specializes in retrieving and analyzing SEC filings.
# It will have access to the SEC EDGAR MCP server tools.
EDGAR_PROMPT = """You are a SEC filing specialist. You have access to the SEC EDGAR database through specialized tools.

Your capabilities include:
- Looking up company CIK numbers
- Retrieving recent filings (10-K, 10-Q, 8-K, etc.)
- Extracting specific sections from filings
- Analyzing financial statements with exact XBRL precision
- Tracking insider trading (Forms 3, 4, 5)

When analyzing filings:
1. Always cite the specific filing (form type, filing date, accession number)
2. Use exact numbers from XBRL when available (no rounding)
3. Include direct SEC URLs for verification
4. Focus on material facts and figures


The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Keep your analysis focused and concise, highlighting the most relevant information
for financial research purposes."""


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
# This agent will be created with mcp_servers parameter
# Using strict_json_schema=False because dict[str, Any] is not supported in strict mode
edgar_agent = Agent(
    name="EdgarFilingAgent",
    instructions=EDGAR_PROMPT,
    model="gpt-4.1",
    output_type=AgentOutputSchema(EdgarAnalysisSummary, strict_json_schema=False),
)
