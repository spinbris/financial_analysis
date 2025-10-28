# Financial Research Agent

A comprehensive AI-powered financial research system that produces investment-grade reports with SEC EDGAR integration.

## Features

- **Comprehensive Analysis**: 3-5 page reports with 800-1200 word specialist analysis
- **SEC EDGAR Integration**: Direct access to official SEC filings (10-K, 10-Q, 8-K) with exact XBRL data
- **Specialist Agents**: Dedicated financial and risk analysts with EDGAR access
- **Budget Mode**: ~90 reports for $20 with 50% cost savings
- **Investment Grade**: Suitable for institutional investors and decision-makers

## Quick Start

### Budget Mode (Recommended)
```bash
python -m financial_research_agent.main_budget
```
- **Cost:** ~$0.22 per report
- **Reports per $20:** ~90 comprehensive reports

### Standard Mode
```bash
python -m financial_research_agent.main_enhanced
```
- **Cost:** ~$0.43 per report
- **Reports per $20:** ~46 comprehensive reports

## Example Query

```
Analyze Apple's most recent quarterly performance
```

**Output includes:**
- Executive summary
- Comprehensive financial analysis (exact XBRL data from 10-Q)
- Risk assessment (official Item 1A Risk Factors from 10-K)
- Strategic position analysis
- Follow-up questions

## Architecture

1. **Planning**: Planner agent creates 5-15 targeted searches
2. **Search**: Parallel web searches for market context
3. **EDGAR**: Direct SEC filing access for authoritative data
4. **Specialist Analysis**:
   - Financials Agent: 800-1200 word analysis with EDGAR data
   - Risk Agent: 800-1200 word assessment from Item 1A
5. **Writer**: Synthesizes into 1500-2500 word comprehensive report
6. **Verification**: Quality audit of final report

## Documentation

- **[QUICK_START_BUDGET.md](QUICK_START_BUDGET.md)** - Get started in 30 seconds
- **[SETUP.md](SETUP.md)** - Complete setup guide
- **[COST_GUIDE.md](COST_GUIDE.md)** - Cost breakdown and optimization
- **[EDGAR_INTEGRATION_GUIDE.md](EDGAR_INTEGRATION_GUIDE.md)** - EDGAR integration details
- **[ATTRIBUTION.md](ATTRIBUTION.md)** - Licensing and attribution

## Attribution

This project uses the **SEC EDGAR MCP Server** for accessing official SEC filing data.

**Citation:**
```
Amorelli, S. (2025). SEC EDGAR MCP (Model Context Protocol) Server (Version 1.0.6)
[Computer software]. Zenodo. https://doi.org/10.5281/zenodo.17123166
```

**License:** AGPL-3.0
**Source:** https://github.com/stefanoamorelli/sec-edgar-mcp

See [ATTRIBUTION.md](ATTRIBUTION.md) for complete licensing information.

## Output

Reports are saved to timestamped directories:
```
financial_research_agent/output/YYYYMMDD_HHMMSS/
├── 00_query.md                      # Your query
├── 01_search_plan.md                # Search strategy
├── 02_search_results.md             # Web search results
├── 02_edgar_filings.md              # SEC filing data
├── 03_comprehensive_report.md       # Main 3-5 page report
└── 04_verification.md               # Quality check
```

## Customization

All prompts and sub-agents can be customized for your specific needs. See the documentation for details on:
- Modifying specialist agent prompts
- Adjusting output structure
- Adding new data sources
- Configuring models and costs
