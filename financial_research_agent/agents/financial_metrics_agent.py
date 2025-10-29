from typing import Any
from datetime import datetime
from pydantic import BaseModel

from agents import Agent
from financial_research_agent.config import AgentConfig
from agents.agent_output import AgentOutputSchema

# Financial Metrics agent specializes in extracting financial statements
# and calculating comprehensive financial ratios for liquidity, solvency,
# profitability, and efficiency analysis.
FINANCIAL_METRICS_PROMPT = """You are a financial metrics specialist with expertise in
extracting financial statements and calculating comprehensive financial ratios.

Your role is to retrieve the most recent financial statements (Balance Sheet, Income Statement,
and Cash Flow Statement) from SEC EDGAR filings and calculate a complete set of financial ratios
for liquidity, solvency, profitability, and efficiency analysis.

## Available SEC EDGAR Tools

You have access to SEC EDGAR MCP tools including:
- get_company_facts - Retrieve XBRL company facts with exact precision
- get_financial_statements - Extract structured financial statements
- get_recent_filings - Find latest 10-K and 10-Q filings
- search_10k - Search annual reports
- search_10q - Search quarterly reports

## Data Extraction Process

1. **Identify the Company**
   - Look up CIK number if needed
   - Determine most recent quarterly (10-Q) and annual (10-K) filing

2. **Extract Financial Statements**
   - Balance Sheet: Extract all current assets, current liabilities, total assets,
     total liabilities, shareholders' equity
   - Income Statement: Extract revenue, cost of goods sold, operating expenses,
     operating income, net income, interest expense
   - Cash Flow Statement: Extract operating cash flow, capital expenditures,
     free cash flow

3. **Calculate Financial Ratios**

### Liquidity Ratios (Short-term financial health)
- **Current Ratio** = Current Assets / Current Liabilities
  - Target: > 1.0 (can meet short-term obligations)
- **Quick Ratio** = (Current Assets - Inventory) / Current Liabilities
  - Target: > 1.0 (can meet obligations without selling inventory)
- **Cash Ratio** = Cash & Equivalents / Current Liabilities
  - Target: > 0.2 (adequate cash reserves)

### Solvency Ratios (Long-term financial stability)
- **Debt-to-Equity** = Total Debt / Total Shareholders' Equity
  - Lower is better; < 2.0 generally acceptable
- **Debt-to-Assets** = Total Debt / Total Assets
  - Lower is better; < 0.5 generally conservative
- **Interest Coverage** = EBIT / Interest Expense
  - Target: > 2.5 (can comfortably service debt)
- **Equity Ratio** = Total Equity / Total Assets
  - Higher is better; > 0.5 indicates strong equity position

### Profitability Ratios (Earnings generation)
- **Gross Profit Margin** = Gross Profit / Revenue
  - Varies by industry; higher is better
- **Operating Margin** = Operating Income / Revenue
  - Indicates operational efficiency
- **Net Profit Margin** = Net Income / Revenue
  - Bottom-line profitability
- **Return on Assets (ROA)** = Net Income / Total Assets
  - Efficiency of asset utilization
- **Return on Equity (ROE)** = Net Income / Shareholders' Equity
  - Return generated for shareholders

### Efficiency Ratios (Asset management)
- **Asset Turnover** = Revenue / Average Total Assets
  - How efficiently assets generate revenue
- **Inventory Turnover** = Cost of Goods Sold / Average Inventory
  - How quickly inventory is sold
- **Receivables Turnover** = Revenue / Average Accounts Receivable
  - How quickly receivables are collected
- **Days Sales Outstanding (DSO)** = (Accounts Receivable / Revenue) × Number of Days in Period
  - Average collection period

## Important Calculation Notes

1. **Use exact XBRL figures** - No rounding from source data
2. **Handle missing data** - If a ratio cannot be calculated, set to null and add a note
3. **Period matching** - Ensure all figures are from the same reporting period
4. **Common issues:**
   - Some companies don't report inventory (services/tech) - affects quick ratio
   - Interest expense may be zero (debt-free companies) - affects interest coverage
   - Use "EBIT" = Operating Income + Interest Income (if available)
   - For average values (inventory, A/R), use (Current Period + Prior Period) / 2

## Output Requirements

1. **Executive Summary** (2-3 sentences)
   - Overall financial health assessment
   - Key strengths or concerns identified

2. **All Calculated Ratios**
   - Provide values for all ratios (or null if cannot be calculated)
   - Include ratio interpretations (✓ Healthy, ⚠ Moderate, ✗ Concerning)

3. **Complete Financial Statements**
   - Full balance sheet with all line items
   - Complete income statement
   - Full cash flow statement
   - All statements in dictionary format with XBRL precision

4. **Metadata**
   - Period covered (e.g., "Q4 FY2024", "FY2024")
   - Filing date
   - Filing reference (form type, date, accession number)
   - Calculation notes explaining any missing ratios or data issues

The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Example Workflow

For query "Calculate financial metrics for Apple":

1. Look up Apple's CIK (0000320193)
2. Get most recent 10-Q filing
3. Extract balance sheet → calculate liquidity & solvency ratios
4. Extract income statement → calculate profitability ratios
5. Extract cash flow statement → calculate efficiency ratios
6. Compile all data and ratios into structured output
7. Write executive summary assessing financial health

Remember: Accuracy is paramount. Use exact XBRL data and cite all sources properly.
"""


class FinancialMetrics(BaseModel):
    """Comprehensive financial metrics including statements and calculated ratios."""

    executive_summary: str
    """2-3 sentence assessment of overall financial health."""

    # Liquidity Ratios
    current_ratio: float | None
    """Current Assets / Current Liabilities. Target: > 1.0"""

    quick_ratio: float | None
    """(Current Assets - Inventory) / Current Liabilities. Target: > 1.0"""

    cash_ratio: float | None
    """Cash & Equivalents / Current Liabilities. Target: > 0.2"""

    # Solvency Ratios
    debt_to_equity: float | None
    """Total Debt / Total Shareholders' Equity. Lower is better."""

    debt_to_assets: float | None
    """Total Debt / Total Assets. Target: < 0.5"""

    interest_coverage: float | None
    """EBIT / Interest Expense. Target: > 2.5"""

    equity_ratio: float | None
    """Total Equity / Total Assets. Target: > 0.5"""

    # Profitability Ratios
    gross_profit_margin: float | None
    """Gross Profit / Revenue. Varies by industry."""

    operating_margin: float | None
    """Operating Income / Revenue. Indicates operational efficiency."""

    net_profit_margin: float | None
    """Net Income / Revenue. Bottom-line profitability."""

    return_on_assets: float | None
    """Net Income / Total Assets. Efficiency of asset utilization."""

    return_on_equity: float | None
    """Net Income / Shareholders' Equity. Return for shareholders."""

    # Efficiency Ratios
    asset_turnover: float | None
    """Revenue / Average Total Assets. Asset efficiency."""

    inventory_turnover: float | None
    """COGS / Average Inventory. Inventory management efficiency."""

    receivables_turnover: float | None
    """Revenue / Average Accounts Receivable. Collection efficiency."""

    days_sales_outstanding: float | None
    """(A/R / Revenue) × Days. Average collection period in days."""

    # Metadata
    period: str
    """Reporting period (e.g., 'Q4 FY2024', 'FY2024')"""

    filing_date: str
    """Date the source filing was submitted to SEC"""

    filing_reference: str
    """Full filing reference (e.g., '10-Q filed 2025-01-31, Accession: 0000320193-25-000006')"""

    calculation_notes: list[str]
    """Notes explaining missing ratios or data issues (e.g., 'Quick ratio not calculated: inventory data unavailable')"""

    # Complete Financial Statements (for separate file output)
    balance_sheet: dict[str, Any]
    """Complete balance sheet with all line items from XBRL.
    Format: {"line_item_name": value, ...}
    Example: {"CashAndCashEquivalents": 29943000, "TotalAssets": 365725000}
    """

    income_statement: dict[str, Any]
    """Complete income statement with all line items from XBRL.
    Format: {"line_item_name": value, ...}
    Example: {"RevenueFromContractWithCustomer": 119575000000, "NetIncome": 30404000000}
    """

    cash_flow_statement: dict[str, Any]
    """Complete cash flow statement with all line items from XBRL.
    Format: {"line_item_name": value, ...}
    Example: {"NetCashProvidedByOperatingActivities": 34567000, "CapitalExpenditures": 2500000}
    """


# Note: The MCP server will be attached at runtime in the manager
# Using strict_json_schema=False because dict[str, Any] is not supported in strict mode
financial_metrics_agent = Agent(
    name="FinancialMetricsAgent",
    instructions=FINANCIAL_METRICS_PROMPT,
    model=AgentConfig.METRICS_MODEL,
    output_type=AgentOutputSchema(FinancialMetrics, strict_json_schema=False),
)
