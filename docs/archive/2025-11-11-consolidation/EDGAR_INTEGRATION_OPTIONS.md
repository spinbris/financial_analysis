# SEC EDGAR Integration - Implementation Options

This document compares different approaches to integrating SEC EDGAR data into your financial research agent.

## Option Comparison Table

| Feature | **Option 1: MCP Server (Recommended)** | **Option 2: Custom Tools** | **Option 3: EdgarTools Direct** |
|---------|----------------------------------------|----------------------------|----------------------------------|
| **Implementation Effort** | ⭐⭐⭐⭐⭐ Minimal (ready-to-use) | ⭐⭐⭐ Moderate | ⭐⭐ Complex |
| **Data Quality** | ⭐⭐⭐⭐⭐ Official SEC, XBRL precision | ⭐⭐⭐⭐⭐ Official SEC, XBRL precision | ⭐⭐⭐⭐⭐ Official SEC, XBRL precision |
| **Flexibility** | ⭐⭐⭐⭐ High (tool filtering, config) | ⭐⭐⭐⭐⭐ Maximum | ⭐⭐⭐ Medium |
| **Maintenance** | ⭐⭐⭐⭐⭐ Low (upstream maintained) | ⭐⭐ High (you maintain) | ⭐⭐⭐ Medium |
| **Agent Integration** | ⭐⭐⭐⭐⭐ Native MCP support | ⭐⭐⭐⭐ Via @function_tool | ⭐⭐⭐ Via @function_tool |
| **Setup Time** | 5 minutes | 1-2 hours | 30-60 minutes |
| **Dependencies** | sec-edgar-mcp (auto-installed) | edgartools, custom code | edgartools |
| **Tool Discovery** | Automatic via MCP | Manual registration | Manual registration |
| **Error Handling** | Built-in | Must implement | Must implement |
| **Rate Limiting** | Built-in | Must implement | Must implement |
| **Caching** | Not included | Must implement | Must implement |

## Detailed Comparison

### Option 1: MCP Server Integration (Implemented Above)

**What it is:** Use the pre-built `sec-edgar-mcp` MCP server with native agent SDK support.

**Pros:**
✅ Ready-to-use, battle-tested implementation
✅ Automatic tool discovery and registration
✅ Built-in error handling and retries
✅ Maintained by community (bug fixes, updates)
✅ Multiple tools available out-of-box
✅ Easy configuration via environment variables
✅ Works with any MCP-compatible LLM/framework

**Cons:**
❌ External dependency (sec-edgar-mcp package)
❌ Less control over internal implementation
❌ AGPL-3.0 license (copyleft requirements)
❌ Requires stdio/docker/http transport

**Best for:**
- Production deployments
- Teams wanting low maintenance
- Projects needing standard SEC data access
- Quick prototyping

**Setup:**
```bash
# Install
pip install sec-edgar-mcp  # or use uvx

# Configure
ENABLE_EDGAR_INTEGRATION=true
SEC_EDGAR_USER_AGENT=YourCompany/1.0 (you@email.com)

# Use
from .manager_with_edgar import FinancialResearchManagerWithEdgar
mgr = FinancialResearchManagerWithEdgar()
```

---

### Option 2: Custom Function Tools

**What it is:** Write your own tools using `@function_tool` decorator and EdgarTools library directly.

**Pros:**
✅ Maximum flexibility and control
✅ Custom business logic per tool
✅ Can choose any license for your code
✅ No MCP server overhead
✅ Easier debugging (all code is yours)
✅ Can combine multiple data sources easily

**Cons:**
❌ Must implement error handling yourself
❌ Must handle rate limiting yourself
❌ More code to maintain
❌ Need to understand EdgarTools API
❌ Manual tool registration

**Best for:**
- Specialized use cases
- Custom data transformations
- Projects with unique requirements
- Teams with Python expertise

**Example Implementation:**
```python
from agents import function_tool
from edgartools import Company, Filing

@function_tool
async def get_company_revenue(ticker: str, filing_type: str = "10-K") -> str:
    """Get exact revenue from most recent SEC filing.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL)
        filing_type: Type of filing (10-K or 10-Q)

    Returns:
        Revenue information with filing reference
    """
    try:
        company = Company(ticker)
        filings = company.get_filings(form=filing_type)
        latest = filings[0]

        # Extract revenue from XBRL
        facts = latest.obj()
        revenue = facts.financials.get_fact("Revenues")

        return f"Revenue: ${revenue.value:,.0f} (from {filing_type} filed {latest.filing_date})"
    except Exception as e:
        return f"Error retrieving revenue: {str(e)}"

@function_tool
async def get_insider_trades(ticker: str, months: int = 6) -> str:
    """Get recent insider trading activity.

    Args:
        ticker: Stock ticker symbol
        months: Number of months to look back

    Returns:
        Summary of insider trades
    """
    # Implementation...
    pass

# Register with agent
agent = Agent(
    name="FinancialAgent",
    tools=[get_company_revenue, get_insider_trades]
)
```

**Maintenance Required:**
- Error handling for API failures
- Rate limiting compliance (10 req/sec)
- User-Agent header management
- Retry logic with exponential backoff
- XBRL parsing for different fact formats
- Filing type variations (10-K vs 10-K/A)

---

### Option 3: EdgarTools Direct Integration

**What it is:** Use EdgarTools library directly without wrapping in tools, call it from agent code.

**Pros:**
✅ Straightforward Python code
✅ No tool registration overhead
✅ Good for simple, one-off queries
✅ Easy to understand control flow
✅ MIT license (permissive)

**Cons:**
❌ LLM cannot decide when to use it
❌ Less flexible (hardcoded logic)
❌ Harder to extend with new capabilities
❌ No tool-based orchestration

**Best for:**
- Simple, predefined workflows
- Non-LLM-driven analysis
- Batch processing scripts
- Data extraction pipelines

**Example Implementation:**
```python
from edgartools import Company
from .agents.writer_agent import writer_agent

async def run_with_edgar(query: str):
    # Extract ticker from query (hardcoded logic)
    ticker = extract_ticker(query)  # Custom function

    # Get SEC data directly
    company = Company(ticker)
    filings = company.get_filings(form="10-K")
    latest = filings[0]

    # Extract data
    revenue_data = latest.obj().financials.get_fact("Revenues")

    # Format for LLM
    sec_data = f"SEC Data for {ticker}:\n"
    sec_data += f"Revenue: ${revenue_data.value:,.0f}\n"
    sec_data += f"Filing: {latest.filing_date}\n"

    # Run writer agent with pre-fetched data
    input_data = f"{query}\n\nSEC Filing Data:\n{sec_data}"
    result = await Runner.run(writer_agent, input_data)

    return result.final_output
```

---

## Recommendation Matrix

### Use MCP Server (Option 1) if:
- ✅ You want minimal setup and maintenance
- ✅ You need multiple SEC data tools
- ✅ You want automatic tool discovery
- ✅ You're building a production system
- ✅ You want community support and updates
- ✅ AGPL-3.0 license is acceptable

### Use Custom Tools (Option 2) if:
- ✅ You need highly specialized data transformations
- ✅ You want maximum control over implementation
- ✅ You're combining SEC data with proprietary sources
- ✅ You need a non-AGPL license
- ✅ You have Python/EdgarTools expertise
- ✅ You need custom caching/rate limiting strategies

### Use Direct Integration (Option 3) if:
- ✅ You have simple, predefined workflows
- ✅ You don't need LLM to decide when to fetch data
- ✅ You're building batch processing pipelines
- ✅ You want minimal dependencies
- ✅ You're doing exploratory analysis

## Hybrid Approach

You can combine options for maximum benefit:

```python
# Use MCP for standard queries
edgar_mcp = MCPServerStdio(command="uvx", args=["sec-edgar-mcp"])

# Add custom tools for specialized needs
@function_tool
async def custom_esg_analysis(ticker: str) -> str:
    """Custom ESG metric extraction from SEC filings."""
    # Your proprietary logic here
    pass

# Combine both
agent = Agent(
    name="FinancialAgent",
    mcp_servers=[edgar_mcp],  # Standard SEC tools
    tools=[custom_esg_analysis]  # Custom additions
)
```

## Decision Tree

```
Do you need SEC filing data?
├─ No → Use web search only (current implementation)
└─ Yes
   │
   ├─ Is this a production system?
   │  ├─ Yes → Use MCP Server (Option 1) ✅ RECOMMENDED
   │  └─ No → Continue...
   │
   ├─ Do you need custom data transformations?
   │  ├─ Yes → Use Custom Tools (Option 2)
   │  └─ No → Continue...
   │
   ├─ Do you want LLM to decide when to fetch data?
   │  ├─ Yes → Use MCP Server (Option 1) ✅ RECOMMENDED
   │  └─ No → Use Direct Integration (Option 3)
   │
   └─ Is maintenance burden a concern?
      ├─ Yes → Use MCP Server (Option 1) ✅ RECOMMENDED
      └─ No → Use Custom Tools (Option 2)
```

## Cost Comparison

### Development Costs

| Phase | Option 1: MCP | Option 2: Custom | Option 3: Direct |
|-------|---------------|------------------|------------------|
| **Setup** | 5 minutes | 2-4 hours | 30-60 minutes |
| **Testing** | Minimal (pre-tested) | 4-8 hours | 2-4 hours |
| **Documentation** | Use existing | Write your own | Write your own |
| **Total Initial** | ~1 hour | ~12-16 hours | ~4-6 hours |

### Ongoing Costs

| Activity | Option 1: MCP | Option 2: Custom | Option 3: Direct |
|----------|---------------|------------------|------------------|
| **Bug Fixes** | Upstream handles | You handle | You handle |
| **Updates** | Automatic via package | Manual | Manual |
| **New Features** | Community adds | You implement | You implement |
| **Support** | Community forums | Internal only | Internal only |

### Runtime Costs

All options have similar runtime costs:
- **SEC API**: Free (no costs)
- **OpenAI Tokens**: Similar (same data retrieved)
- **Latency**: Similar (2-5 seconds per filing)

## Migration Paths

### From Current Implementation → MCP Server

**Effort:** Low (5-10 minutes)

```python
# Before
from .manager import FinancialResearchManager

# After
from .manager_with_edgar import FinancialResearchManagerWithEdgar
```

### From MCP Server → Custom Tools

**Effort:** Medium (2-4 hours)

1. Study MCP server tool definitions
2. Implement equivalent @function_tool versions
3. Replace MCP server with custom tools
4. Test thoroughly

### From Direct → Tool-Based (MCP or Custom)

**Effort:** Medium (1-2 hours)

1. Extract data fetching logic
2. Wrap in tools or use MCP
3. Update orchestration to use tools
4. Test agent decision-making

## License Considerations

### MCP Server (sec-edgar-mcp)
- **License:** AGPL-3.0 (copyleft)
- **Implication:** If you distribute your system, you must open-source it under AGPL
- **Note:** Using it as a service (API) doesn't trigger AGPL (network loophole)

### Custom Tools (EdgarTools)
- **License:** MIT (permissive)
- **Implication:** Free to use in commercial/proprietary software
- **Note:** You can keep your tools proprietary

### Recommendation:
- **SaaS/API product**: Either option works (AGPL network loophole applies)
- **Distributed software**: Use Custom Tools (Option 2) to avoid AGPL
- **Internal use**: Either option works

## Conclusion

**For most use cases, we recommend Option 1 (MCP Server Integration)** because:

1. ✅ Lowest total cost of ownership
2. ✅ Production-ready out of the box
3. ✅ Community maintained and improved
4. ✅ Easy to setup and configure
5. ✅ Flexible tool filtering

**Consider Option 2 (Custom Tools) only if:**
- You need proprietary closed-source distribution
- You have very specialized requirements
- You need custom data transformations

**Consider Option 3 (Direct Integration) only if:**
- You have simple, predefined workflows
- You don't need LLM orchestration

---

## Already Implemented

The files created above implement **Option 1 (MCP Server)** with:
- Full configuration system
- Error handling and fallbacks
- Output persistence
- Comprehensive documentation

You can start using it immediately by following [EDGAR_QUICK_START.md](EDGAR_QUICK_START.md).

If you later decide you need custom tools (Option 2), you can implement them alongside the MCP integration for a hybrid approach.
