# SEC EDGAR Integration Guide

This guide explains how to integrate the SEC EDGAR MCP server into your financial research agent for direct access to official SEC filings.

## Overview

The SEC EDGAR integration provides:
- **Direct access** to company filings (10-K, 10-Q, 8-K, etc.)
- **Exact financial data** from XBRL with no rounding
- **Insider trading** information (Forms 3, 4, 5)
- **Verifiable sources** with direct SEC URLs
- **Deterministic responses** to prevent AI hallucination

## Architecture

The integration uses two complementary approaches:

1. **EDGAR Agent** - A specialized agent with MCP server access for complex analysis
2. **Writer Agent Tool** - The EDGAR agent is exposed as a tool for inline SEC filing queries

```
Query → Planner → Search Agent → Writer Agent
                                      ↓
                                  ┌───────────────┐
                                  │ Tools:        │
                                  │ - Fundamentals│
                                  │ - Risk        │
                                  │ - SEC Filings │◄── MCP Server
                                  └───────────────┘
```

## Setup Instructions

### Step 1: Install SEC EDGAR MCP Server

**Option A: Using uvx (Recommended)**
```bash
# uvx will automatically download and run the package
# No installation needed - just configure the environment variable
```

**Option B: Using pip**
```bash
pip install sec-edgar-mcp
```

**Option C: Using Docker**
```bash
docker pull stefanoamorelli/sec-edgar-mcp:latest
```

**Option D: Using Conda**
```bash
conda install -c conda-forge sec-edgar-mcp
```

### Step 2: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and configure:

   **Required Configuration:**
   ```bash
   # Enable EDGAR integration
   ENABLE_EDGAR_INTEGRATION=true

   # REQUIRED: Set your User-Agent (SEC requirement)
   # Format: "CompanyName/Version (your-email@example.com)"
   SEC_EDGAR_USER_AGENT=YourCompany/1.0 (contact@youremail.com)
   ```

   **Choose your MCP server method:**

   For **uvx** (recommended):
   ```bash
   EDGAR_MCP_COMMAND=uvx
   EDGAR_MCP_ARGS=sec-edgar-mcp
   ```

   For **Docker**:
   ```bash
   EDGAR_MCP_COMMAND=docker
   EDGAR_MCP_ARGS=run -i --rm stefanoamorelli/sec-edgar-mcp:latest
   ```

   For **Python**:
   ```bash
   EDGAR_MCP_COMMAND=python
   EDGAR_MCP_ARGS=-m sec_edgar_mcp
   ```

### Step 3: Optional - Filter Available Tools

By default, all EDGAR tools are available. To limit which tools the agent can use:

```bash
# Only enable specific tools (comma-separated)
EDGAR_ALLOWED_TOOLS=get_company_facts,get_recent_filings,get_financial_statements
```

Available tools:
- `get_company_facts` - Company information and CIK lookup
- `get_recent_filings` - Recent SEC filings
- `get_filing_content` - Full filing content
- `search_10k` - Search 10-K filings
- `search_10q` - Search 10-Q filings
- `get_financial_statements` - Extract financial statements with XBRL precision
- `get_insider_transactions` - Forms 3, 4, 5 insider trading data

### Step 4: Update Your Code

**Option A: Use the enhanced manager (recommended)**

```python
# In main.py
from .manager_with_edgar import FinancialResearchManagerWithEdgar

async def main() -> None:
    query = input("Enter a financial research query: ")
    mgr = FinancialResearchManagerWithEdgar()
    await mgr.run(query)
```

**Option B: Manual integration in existing code**

```python
from agents.mcp import MCPServerStdio
from .config import EdgarConfig
from .agents.edgar_agent import edgar_agent

# Initialize MCP server
edgar_server = MCPServerStdio(
    command=EdgarConfig.MCP_SERVER_COMMAND,
    args=EdgarConfig.MCP_SERVER_ARGS,
    env=EdgarConfig.get_mcp_env(),
)
await edgar_server.connect()

# Attach to agent
edgar_with_mcp = edgar_agent.clone(mcp_servers=[edgar_server])

# Use as a tool
edgar_tool = edgar_with_mcp.as_tool(
    tool_name="sec_filing_analysis",
    tool_description="Retrieve and analyze official SEC filings"
)

# Add to writer agent
writer_with_edgar = writer_agent.clone(tools=[..., edgar_tool])

# Cleanup when done
await edgar_server.cleanup()
```

## Usage Examples

### Example 1: Company Financial Analysis

```python
query = "Analyze Apple Inc.'s most recent quarterly performance"
```

The agent will:
1. Search the web for recent news and analysis
2. Query SEC EDGAR for Apple's latest 10-Q filing
3. Extract exact revenue, profit, and key metrics from XBRL
4. Synthesize both sources into a comprehensive report

### Example 2: Insider Trading Analysis

```python
query = "What insider trading activity has occurred at Tesla in the last 6 months?"
```

The agent will:
1. Use EDGAR to retrieve Forms 3, 4, and 5 for Tesla
2. Extract transaction details (shares, prices, dates)
3. Provide analysis of insider buying/selling patterns

### Example 3: Multi-Company Comparison

```python
query = "Compare the revenue growth and margins of Microsoft, Google, and Amazon"
```

The agent will:
1. Retrieve latest 10-K filings for all three companies
2. Extract exact financial metrics from XBRL
3. Create comparative analysis with verifiable numbers

## Output Structure

When EDGAR is enabled, additional output files are created:

```
output/
└── 20250128_143052/
    ├── 00_query.md
    ├── 01_search_plan.md
    ├── 02_search_results.md
    ├── 02_edgar_filings.md          ← New: EDGAR analysis
    ├── 03_final_report.md            ← Enhanced with SEC data
    └── 04_verification.md
```

### EDGAR Output Format

```markdown
# SEC EDGAR Filing Analysis

## Summary
Apple Inc. (CIK: 0000320193) filed their 10-Q for Q4 2024 on January 31, 2025.
Revenue: $119,575,000,000 (exact from XBRL)
Net Income: $33,916,000,000
...

## Filing References
- 10-Q filed 2025-01-31, Accession: 0000320193-25-000006
  https://www.sec.gov/cgi-bin/viewer?action=view&cik=320193&accession_number=0000320193-25-000006

## Key Metrics
- Revenue: 119575000000
- NetIncome: 33916000000
- GrossProfit: 52942000000
```

## Benefits of EDGAR Integration

### 1. **Authoritative Data**
- Direct from SEC filings, not third-party interpretations
- Exact numbers from XBRL (no rounding errors)
- Verifiable with clickable SEC URLs

### 2. **Reduced Hallucination**
- Deterministic responses based on actual filings
- No reliance on web search for financial figures
- Clear citations for every data point

### 3. **Comprehensive Analysis**
- Combines real-time news (web search) with official data (EDGAR)
- Historical trend analysis from past filings
- Insider trading patterns from Forms 3/4/5

### 4. **Compliance & Audit Trail**
- All data sourced from official SEC filings
- Filing references for compliance verification
- Exact numbers as reported to regulators

## Troubleshooting

### Error: "SEC_EDGAR_USER_AGENT not configured"

**Solution:** Set the required User-Agent header:
```bash
SEC_EDGAR_USER_AGENT=YourCompany/1.0 (your-email@example.com)
```

The SEC requires this header to identify who is accessing their data. Use a real email address.

### Error: "MCP server connection failed"

**Solutions:**
1. Check that uvx/docker/python is installed:
   ```bash
   uvx --version
   # or
   docker --version
   # or
   python --version
   ```

2. Test the MCP server manually:
   ```bash
   SEC_EDGAR_USER_AGENT="Test/1.0 (test@example.com)" uvx sec-edgar-mcp
   ```

3. Check your command/args configuration in `.env`

### Warning: "EDGAR data gathering failed"

**Possible causes:**
- Network connectivity issues
- SEC API rate limiting (wait and retry)
- Invalid company name/ticker in query
- Malformed query to EDGAR agent

**Solution:** The agent will continue without EDGAR data and use web search results only.

### Rate Limiting

The SEC EDGAR API has rate limits:
- 10 requests per second per IP
- Enforced User-Agent requirement

If you hit rate limits, the agent will log warnings but continue with available data.

## Advanced Configuration

### Custom Tool Filtering

Create dynamic tool filters based on query type:

```python
def edgar_tool_filter(context, tool):
    """Only enable filing tools for public companies."""
    query = context.context.get("query", "")
    if "private company" in query.lower():
        return False  # Disable EDGAR for private companies
    return True

edgar_server.tool_filter = edgar_tool_filter
```

### Multiple MCP Servers

Combine EDGAR with other MCP servers:

```python
edgar_server = MCPServerStdio(...)
financial_data_server = MCPServerStdio(...)

edgar_with_tools = edgar_agent.clone(
    mcp_servers=[edgar_server, financial_data_server]
)
```

### Custom EDGAR Prompts

Modify [edgar_agent.py](agents/edgar_agent.py) to customize instructions:

```python
EDGAR_PROMPT = """You are a SEC filing specialist focused on ESG metrics.

When analyzing filings:
1. Prioritize environmental and social impact data
2. Extract governance-related disclosures
3. Flag missing ESG information
..."""
```

## Performance Considerations

### Latency
- EDGAR MCP calls add 2-5 seconds per filing retrieval
- Use tool filtering to limit unnecessary calls
- Consider caching frequent queries (future enhancement)

### Cost
- EDGAR API access is free
- OpenAI API costs apply for agent reasoning
- More comprehensive data may increase token usage by 20-30%

### Parallelization
- EDGAR queries run in parallel with web searches when possible
- Writer agent can call EDGAR tool multiple times if needed
- Each filing retrieval is independent and async-safe

## Best Practices

1. **Use specific company names or tickers** in queries for better EDGAR results
2. **Combine with web search** for context and recent news
3. **Verify critical numbers** using the provided SEC URLs
4. **Set appropriate tool filters** to prevent unnecessary EDGAR calls
5. **Monitor token usage** as EDGAR adds detailed financial data to context
6. **Cache common queries** (implement in future versions)

## Migration from Current Implementation

To migrate from the current `manager.py` to EDGAR-enabled version:

1. **Copy configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Update imports**:
   ```python
   # Old
   from .manager import FinancialResearchManager

   # New
   from .manager_with_edgar import FinancialResearchManagerWithEdgar as FinancialResearchManager
   ```

3. **No code changes needed** - the enhanced manager is backward compatible

4. **Enable EDGAR** when ready:
   ```bash
   ENABLE_EDGAR_INTEGRATION=true
   ```

## Resources

- **SEC EDGAR MCP Server**: https://github.com/stefanoamorelli/sec-edgar-mcp
- **SEC EDGAR API Docs**: https://www.sec.gov/os/accessing-edgar-data
- **EdgarTools Library**: https://github.com/dgunning/edgartools
- **MCP Protocol**: https://modelcontextprotocol.io/
- **OpenAI Agents SDK**: https://github.com/openai/openai-agents

## Support

For issues with:
- **EDGAR integration**: File issue at https://github.com/stefanoamorelli/sec-edgar-mcp
- **Agent framework**: Consult OpenAI Agents SDK documentation
- **This implementation**: Check troubleshooting section above

## License

The SEC EDGAR MCP server is licensed under AGPL-3.0. Ensure compliance when using in commercial applications.
