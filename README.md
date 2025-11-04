# Financial Research Agent

A comprehensive AI-powered financial research system that produces investment-grade reports with SEC EDGAR integration. 

At this stage though it is very much still in development stage and is still incomplete, and in any case is being used to investigate the technologies used rather than to develop an operational tool! So please do not use for anything serious!

**Based on:** [OpenAI Agents SDK Financial Research Example](https://github.com/openai/openai-agents-python/tree/main/examples/financial_research_agent)

## Features

- **Comprehensive Analysis**: 3-5 page reports with 800-1200 word specialist analysis
- **Complete Financial Statements**: 118+ line items with comparative periods via deterministic [edgartools](https://github.com/dgunning/edgartools) extraction
  - Balance Sheet: 36+ line items (current & prior period)
  - Income Statement: 46+ line items with product/geographic breakdowns
  - Cash Flow: 36+ line items with all activities
  - **8.6x more data** than MCP tool approach
- **SEC EDGAR Integration**: Direct access to official SEC filings (10-K, 10-Q, 8-K) with exact XBRL precision
- **Specialist Agents**: Dedicated financial and risk analysts with EDGAR access
- **Budget Mode**: Cost-optimized configuration still available
- **Investment Grade**: Suitable for institutional investors and decision-makers

## Quick Start

### Optimized Mode (Recommended) - GPT-5
```bash
python launch_web_app.py
# Or: python -m financial_research_agent.main_enhanced
```
- **Time:** 3-5 minutes (first run), 2-3 minutes (cached)
- **Cost:** ~$0.08 per report
- **Reports per $20:** ~250 comprehensive reports
- Uses GPT-5-nano for planning/search, GPT-5 for analysis
- **70% faster and 47% cheaper than original!**

### Budget Mode
```bash
python -m financial_research_agent.main_budget
```
- **Time:** 8-10 minutes
- **Cost:** ~$0.10 per report (lower quality)
- **Reports per $20:** ~200 reports
- Uses gpt-4o-mini for all tasks (quality trade-off)

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

## Attribution & License

### This Project
**License:** MIT License
**Copyright:** 2025 Stephen Parton
See [LICENSE](LICENSE) for full license text.

As stated more fully in the license file: THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED

### Dependencies

**Based on OpenAI Agents SDK Example**
- Source: https://github.com/openai/openai-agents-python/tree/main/examples/financial_research_agent
- License: MIT (Copyright OpenAI)

**Financial Data Extraction: edgartools**
- Author: Dwight Gunning
- Source: https://github.com/dgunning/edgartools
- License: MIT

**SEC EDGAR MCP Server** (for EDGAR agent)
- Author: Stefano Amorelli
- Source: https://github.com/stefanoamorelli/sec-edgar-mcp
- License: AGPL-3.0
- Citation: Amorelli, S. (2025). SEC EDGAR MCP Server. https://doi.org/10.5281/zenodo.17123166

See [ATTRIBUTION.md](financial_research_agent/docs/ATTRIBUTION.md) for complete licensing information.

## Output

Reports are saved to timestamped directories with minimal terminal output:

```
✅ Research complete!
📁 All reports saved to: financial_research_agent/output/YYYYMMDD_HHMMSS/
```

**Output Structure:**
```
financial_research_agent/output/YYYYMMDD_HHMMSS/
├── 00_query.md                               # Your query
├── 01_search_plan.md                         # Search strategy
├── 02_search_results.md                      # Web search results
├── 02_edgar_filings.md                       # SEC filing data
├── 03_financial_statements.md                # Balance Sheet, Income, Cash Flow (XBRL order)
├── 04_financial_metrics.md                   # Calculated financial ratios
├── 05_financial_analysis.md                  # 800-1200 word specialist analysis
├── 06_risk_analysis.md                       # 800-1200 word risk assessment
├── 07_comprehensive_report.md                # Main 3-5 page synthesized report
├── 08_verification.md                        # Quality check
├── xbrl_raw_balance_sheet_TICKER_DATE.csv    # Raw XBRL audit trail
├── xbrl_raw_income_statement_TICKER_DATE.csv # Raw XBRL audit trail
├── xbrl_raw_cashflow_TICKER_DATE.csv         # Raw XBRL audit trail
└── error_log.txt                             # Error details (if any)
```

**Key Features:**
- **SEC XBRL Presentation Order**: Financial statements match official 10-Q/10-K structure
- **Audit Trail**: Raw XBRL CSV files with all metadata (concept, label, level, abstract, weight)
- **Comparative Periods**: Current vs. Prior period for all line items
- **Correct Totals**: Subtotals appear in proper hierarchical positions and add up correctly

## Customization

All prompts and sub-agents can be customized for your specific needs. See the documentation for details on:
- Modifying specialist agent prompts
- Adjusting output structure
- Adding new data sources
- Configuring models and costs

## Technology Stack

**LLM Provider:** OpenAI (GPT-4.1, o3-mini)
- Required for OpenAI Agents SDK compatibility
- Advanced function calling for EDGAR MCP tools
- Investment-grade analysis quality

**Note on Open-Source Models:**
While open-source models from [Hugging Face](https://huggingface.co/open-llm-leaderboard) (e.g., Llama 3.3 70B, Qwen 2.5 72B) are improving rapidly, this project currently requires OpenAI models due to:
- OpenAI Agents SDK framework dependency
- Reliable tool/function calling for MCP integration
- Quality requirements for financial analysis

Future versions could support open-source models with agent framework migration (LangChain, AutoGen, etc.).
