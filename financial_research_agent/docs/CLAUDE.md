# Claude Context File - Financial Research Agent

This file provides context for AI assistants (like Claude) working on this project.

## Project Overview

A multi-agent financial research system built with OpenAI Agents SDK that:
- Generates comprehensive 3-5 page financial analysis reports
- Integrates with SEC EDGAR via Model Context Protocol (MCP)
- Uses specialized agents for planning, searching, risk analysis, financials, and writing
- Optimized for budget-conscious usage (~$0.22 per report in budget mode)

## Architecture

### Agent Workflow
```
User Query → Planner → Search Agent → [EDGAR Agent, Risk Agent, Financials Agent] → Writer → Output
```

### Key Components

1. **Planner Agent** (`agents/planner_agent*.py`)
   - Generates 5-15 search queries (5-8 in budget mode)
   - Output: `FinancialSearchPlan` with list of queries

2. **Search Agent** (built-in web search)
   - Executes search queries in parallel
   - Returns web results for analysis

3. **EDGAR Agent** (`agents/edgar_agent.py`)
   - Accesses SEC EDGAR database via MCP server
   - Retrieves 10-K, 10-Q, 8-K filings
   - Extracts exact XBRL financial data
   - Output: `EdgarAnalysisSummary` (2-3 paragraphs + key_metrics)

4. **Risk Agent** (`agents/risk_agent_enhanced.py`)
   - Analyzes risk factors (Item 1A from 10-K)
   - Has access to EDGAR MCP tools when available
   - Output: `ComprehensiveRiskAnalysis` (800-1200 words)

5. **Financials Agent** (`agents/financials_agent_enhanced.py`)
   - Analyzes financial statements with XBRL precision
   - Has access to EDGAR MCP tools when available
   - Output: `ComprehensiveFinancialAnalysis` (800-1200 words)

6. **Writer Agent** (`agents/writer_agent_enhanced.py`)
   - Synthesizes all analysis into final report
   - Output: `ComprehensiveFinancialReport` (1500-2500 words, 3-5 pages)

7. **Verifier Agent** (`agents/verifier_agent.py`)
   - Quality control and fact-checking
   - Output: `VerificationResult`

### Manager (`manager_enhanced.py`)
- Orchestrates the entire workflow
- Initializes EDGAR MCP server
- Clones specialist agents with EDGAR access
- Saves all outputs to timestamped directories
- Adds attribution footer for EDGAR MCP server

## Critical Technical Patterns

### 1. Strict JSON Schema Issue

**Problem:** OpenAI's strict JSON schema doesn't support `dict[str, Any]` in Pydantic models.

**Solution:** Use `AgentOutputSchema` with `strict_json_schema=False`:

```python
from agents.agent_output import AgentOutputSchema

edgar_agent = Agent(
    name="EdgarFilingAgent",
    output_type=AgentOutputSchema(EdgarAnalysisSummary, strict_json_schema=False),
)
```

**Applies to:**
- `agents/edgar_agent.py` (key_metrics field)
- `agents/financials_agent_enhanced.py` (key_metrics field)

**Why:** These agents need flexible dict fields to store variable financial data (strings, numbers, None).

### 2. MCP Server Initialization

**Correct pattern:**
```python
params = {
    "command": "uvx",
    "args": ["sec-edgar-mcp"],
    "env": {"SEC_EDGAR_USER_AGENT": "..."},
}
self.edgar_server = MCPServerStdio(
    params=params,
    client_session_timeout_seconds=60.0,  # 60s for first run download
)
```

**Common mistake:** Passing command/args/env as separate kwargs (causes error).

### 3. Agent Cloning with MCP

Specialist agents need EDGAR access:

```python
risk_agent_with_edgar = risk_agent_enhanced.clone(
    mcp_servers=[self.edgar_server]
)
```

This gives them access to EDGAR tools at runtime.

### 4. Output Persistence

All agent outputs saved to timestamped directories:
```
output/YYYYMMDD_HHMMSS/
  01_search_plan.md
  02_edgar_filings.md
  03_risk_analysis.md
  04_financial_analysis.md
  05_final_report.md
  06_verification.md
```

## Environment Configuration

### Two Modes

1. **Budget Mode** (`.env.budget`) - ~$0.22/report
   - Planner: o3-mini
   - Search/EDGAR/Verification: gpt-4o-mini (17x cheaper)
   - Writer: gpt-4.1 (quality maintained)
   - Fewer searches: 5-8 vs 5-15

2. **Standard Mode** (`.env`) - ~$0.43/report
   - All agents use gpt-4.1

### Required Environment Variables

```bash
OPENAI_API_KEY=sk-proj-...
ENABLE_EDGAR_INTEGRATION=true
SEC_EDGAR_USER_AGENT=YourCompany/1.0 (your@email.com)
```

### Optional Model Overrides

```bash
PLANNER_MODEL=o3-mini
SEARCH_MODEL=gpt-4o-mini
EDGAR_MODEL=gpt-4o-mini
WRITER_MODEL=gpt-4.1
VERIFIER_MODEL=gpt-4o-mini
RISK_MODEL=gpt-4.1
FINANCIALS_MODEL=gpt-4.1
```

## Dependencies

Key packages:
- `openai-agents` - Multi-agent orchestration
- `python-dotenv` - Environment management
- `rich` - Terminal output formatting

MCP server (runtime):
- `sec-edgar-mcp` - Downloaded via uvx on first run

## Common Issues & Solutions

### 1. JSON Schema Validation Error
**Error:** "Strict JSON schema is enabled, but the output type is not valid"
**Fix:** Use `AgentOutputSchema(..., strict_json_schema=False)` (already applied)

### 2. MCP Connection Timeout (First Run)
**Error:** "Timed out waiting 5.0 seconds"
**Fix:** Run again - package now cached. Timeout increased to 60s.

### 3. ModuleNotFoundError
**Error:** "No module named 'agents.output'"
**Fix:** Correct import is `from agents.agent_output import AgentOutputSchema`

### 4. No EDGAR Data
**Check:**
- User-Agent configured in .env?
- uvx installed? (`uvx --version`)
- US company with SEC filings?
- Check logs for "SEC EDGAR connected"

## File Organization

```
financial_research_agent/
├── agents/                    # Agent definitions
│   ├── edgar_agent.py        # SEC filing specialist
│   ├── risk_agent_enhanced.py
│   ├── financials_agent_enhanced.py
│   ├── writer_agent_enhanced.py
│   ├── planner_agent*.py
│   └── verifier_agent.py
├── manager_enhanced.py        # Main orchestrator
├── main_enhanced.py          # Standard entry point
├── main_budget.py            # Budget entry point
├── config.py                 # Configuration management
├── output/                   # Generated reports
├── .env                      # Standard config
├── .env.budget              # Budget config
└── docs/                     # Documentation
    ├── SETUP.md
    ├── QUICK_START_BUDGET.md
    ├── COST_GUIDE.md
    ├── TROUBLESHOOTING.md
    ├── JSON_SCHEMA_FIX.md
    └── ATTRIBUTION.md
```

## Design Decisions

### Why MCP for EDGAR?
- Standard protocol for LLM data access
- Subprocess isolation (security)
- Community-maintained server
- Exact XBRL data extraction

### Why Multi-Agent?
- Separation of concerns
- Parallel execution where possible
- Specialized prompts per domain
- Better quality than single agent

### Why Budget Mode?
- gpt-4o-mini is 17x cheaper than gpt-4.1
- Quality preserved where it matters (final writing)
- Search/data gathering doesn't need top-tier model
- $20 → ~90 reports vs ~46 reports

### Why Non-Strict JSON Schema?
- SEC filing data is highly variable
- dict[str, Any] needed for flexibility
- Pydantic still validates structure
- OpenAI strict mode too restrictive

## Attribution Requirements

**AGPL-3.0 License:** Must cite sec-edgar-mcp usage.

**Automatic attribution** added to all reports:
```markdown
---
Data Sources: SEC EDGAR filings accessed via sec-edgar-mcp
Citation: Amorelli, S. (2025). SEC EDGAR MCP...
```

See `ATTRIBUTION.md` for full citation details.

## Testing

### Quick Test
```bash
cd financial_research_agent
python main_budget.py "AAPL Q4 2024 analysis"
```

### Expected Output
- 01_search_plan.md (5-8 queries)
- 02_edgar_filings.md (SEC data summary)
- 03_risk_analysis.md (800-1200 words)
- 04_financial_analysis.md (800-1200 words)
- 05_final_report.md (1500-2500 words)
- 06_verification.md (quality checks)

### Success Indicators
✅ "SEC EDGAR connected"
✅ "Gathering SEC filing data..."
✅ All 6 output files generated
✅ Final report 3-5 pages
✅ Attribution footer present

## Cost Estimates (Budget Mode)

| Component | Model | Est. Cost |
|-----------|-------|-----------|
| Planning | o3-mini | $0.01 |
| Searching (6 queries) | gpt-4o-mini | $0.03 |
| EDGAR gathering | gpt-4o-mini | $0.02 |
| Risk analysis | gpt-4.1 | $0.06 |
| Financials analysis | gpt-4.1 | $0.06 |
| Final report | gpt-4.1 | $0.03 |
| Verification | gpt-4o-mini | $0.01 |
| **Total** | | **~$0.22** |

With $20 budget: ~90 reports

## Future Considerations

### Potential Enhancements
- Stream output for real-time feedback
- Cache EDGAR data to reduce API calls
- Add peer comparison analysis
- Support international filings (non-US)
- Interactive Q&A mode after report
- Export to PDF/Excel formats

### Known Limitations
- EDGAR only covers US public companies
- First run may timeout (package download)
- No support for private companies
- Relies on web search for recent news
- Cost scales with number of searches

## When Making Changes

### Adding a New Agent
1. Create agent file in `agents/`
2. Define Pydantic output model
3. Use `AgentOutputSchema(..., strict_json_schema=False)` if using dict[str, Any]
4. Update `manager_enhanced.py` workflow
5. Add output saving logic
6. Update cost estimates

### Modifying EDGAR Integration
1. Check `config.py` for environment vars
2. Test with `uvx sec-edgar-mcp` manually first
3. Verify timeout is sufficient (60s minimum)
4. Update attribution if changing server

### Changing Models
1. Update `.env` or `.env.budget`
2. Recalculate costs in `COST_GUIDE.md`
3. Test quality vs. cost trade-off
4. Document in this file

## Resources

- OpenAI Agents SDK: https://github.com/openai/openai-agents-python
- SEC EDGAR MCP: https://github.com/stefanoamorelli/sec-edgar-mcp
- SEC EDGAR API: https://www.sec.gov/os/accessing-edgar-data
- Model Context Protocol: https://modelcontextprotocol.io/

## Quick Reference Commands

```bash
# Budget mode (recommended)
python main_budget.py "ticker analysis request"

# Standard mode
python main_enhanced.py "ticker analysis request"

# Test EDGAR connection
SEC_EDGAR_USER_AGENT="Test/1.0 (test@email.com)" uvx sec-edgar-mcp

# Check costs
cat COST_GUIDE.md

# Troubleshoot
cat TROUBLESHOOTING.md
```

---

**Last Updated:** 2025-10-28
**Project Version:** 1.0 (Budget-optimized with EDGAR integration)
