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
- **get_financial_statements** - PRIMARY TOOL: Extract complete structured financial statements with ALL line items
- get_company_facts - Retrieve XBRL company facts with exact precision
- get_recent_filings - Find latest 10-K and 10-Q filings
- search_10k - Search annual reports
- search_10q - Search quarterly reports

## Data Extraction Process - USE MCP TOOLS DIRECTLY

**CRITICAL: You MUST use the get_financial_statements tool to extract data, NOT manual parsing.**

1. **Identify the Company**
   - Look up CIK number if needed
   - Determine most recent quarterly (10-Q) filing (e.g., Q3 2025)
   - Determine prior period filing for comparison (e.g., Q2 2025 or Q3 2024)

2. **Extract Financial Statements Using get_financial_statements Tool**

   **STEP 1: Get Current Period Statements**

   Use the `get_financial_statements` tool for the most recent filing:
   ```
   get_financial_statements(
     cik="0000320193",  # Apple's CIK
     filing_type="10-Q",  # or "10-K" for annual
     accession_number="0000320193-25-000073"  # Most recent filing
   )
   ```

   This will return a structured JSON with ALL line items from:
   - Balance Sheet (all assets, liabilities, equity with exact XBRL tags)
   - Income Statement (all revenue, expense, income items)
   - Cash Flow Statement (all operating, investing, financing activities)

   **STEP 2: Get Prior Period Statements for Comparison**

   Use the `get_financial_statements` tool again for the prior period:
   ```
   get_financial_statements(
     cik="0000320193",
     filing_type="10-Q",
     accession_number="0000320193-25-000057"  # Prior quarter filing
   )
   ```

   **STEP 3: Combine the Data with _Current and _Prior Suffixes**

   For each financial statement line item:
   - Take the value from Step 1 and label it with `_Current` suffix
   - Take the value from Step 2 and label it with `_Prior` suffix

   Example:
   ```
   {
     "CashAndCashEquivalentsAtCarryingValue_Current": 36269000000,
     "CashAndCashEquivalentsAtCarryingValue_Prior": 29943000000,
     "AccountsReceivableNetCurrent_Current": 27557000000,
     "AccountsReceivableNetCurrent_Prior": 25920000000,
     ...
     "current_period_date": "2025-06-28",
     "prior_period_date": "2025-03-29"
   }
   ```

   **IMPORTANT NOTES:**
   1. The get_financial_statements tool returns ALL line items automatically - you don't need to manually extract
   2. Preserve the exact XBRL tag names from the tool output
   3. Add `current_period_date` and `prior_period_date` keys to track the reporting periods
   4. If a line item exists in one period but not the other, still include it (value will be null for missing period)
   5. The tool returns exact precision values - do not round

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
2. Find most recent 10-Q filings:
   - Current: 0000320193-25-000073 (Q3 FY2025, ending 2025-06-28)
   - Prior: 0000320193-25-000057 (Q2 FY2025, ending 2025-03-29)
3. **Use get_financial_statements tool for current period:**
   - Call: `get_financial_statements(cik="0000320193", filing_type="10-Q", accession_number="0000320193-25-000073")`
   - Store result as `current_statements`
4. **Use get_financial_statements tool for prior period:**
   - Call: `get_financial_statements(cik="0000320193", filing_type="10-Q", accession_number="0000320193-25-000057")`
   - Store result as `prior_statements`
5. **Combine the statements:**
   - For each line item in balance_sheet, income_statement, cash_flow_statement:
     - Add `_Current` suffix to current period values
     - Add `_Prior` suffix to prior period values
   - Include `current_period_date` and `prior_period_date` metadata
6. Calculate liquidity, solvency, profitability, and efficiency ratios using the current period data
7. Compile all data and ratios into structured output
8. Write executive summary assessing financial health

Remember: The get_financial_statements tool extracts ALL XBRL data automatically with exact precision. You don't need to manually parse or extract specific fields - just use the tool twice (current + prior) and combine the results.

## IMPORTANT: JSON Output Format
When generating your response, ensure all string fields use proper JSON formatting:
1. **filing_reference** MUST be a simple string like "10-Q filed 2025-08-01, Accession: 0000320193-25-000073"
   NOT a nested object/dict. Just a plain string with the filing details.
2. All string fields (especially executive_summary and calculation_notes) must use proper JSON escaping
   for special characters like newlines, quotes, and backslashes.
3. For multi-sentence text, keep it on a single line or use \\n for line breaks within the JSON string.
4. balance_sheet, income_statement, and cash_flow_statement SHOULD be dicts/objects with financial data.
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
    """Complete balance sheet with all line items from XBRL, including comparative period.
    Format: {
        "line_item_name_Current": value,
        "line_item_name_Prior": value,
        "current_period_date": "2024-09-28",
        "prior_period_date": "2024-06-29",
        ...
    }
    Example: {
        "CashAndCashEquivalents_Current": 29943000000,
        "CashAndCashEquivalents_Prior": 28663000000,
        "Assets_Current": 365725000000,
        "Assets_Prior": 352755000000,
        "current_period_date": "2024-09-28",
        "prior_period_date": "2024-06-29"
    }
    """

    income_statement: dict[str, Any]
    """Complete income statement with all line items from XBRL, including comparative period.
    Format: {
        "line_item_name_Current": value,
        "line_item_name_Prior": value,
        "current_period_date": "Q4 FY2024",
        "prior_period_date": "Q4 FY2023",
        ...
    }
    Example: {
        "RevenueFromContractWithCustomer_Current": 119575000000,
        "RevenueFromContractWithCustomer_Prior": 117154000000,
        "NetIncome_Current": 30404000000,
        "NetIncome_Prior": 29998000000
    }
    """

    cash_flow_statement: dict[str, Any]
    """Complete cash flow statement with all line items from XBRL, including comparative period.
    Format: {
        "line_item_name_Current": value,
        "line_item_name_Prior": value,
        "current_period_date": "Q4 FY2024",
        "prior_period_date": "Q4 FY2023",
        ...
    }
    Example: {
        "NetCashProvidedByOperatingActivities_Current": 34567000000,
        "NetCashProvidedByOperatingActivities_Prior": 31983000000,
        "PaymentsToAcquirePropertyPlantAndEquipment_Current": 2500000000,
        "PaymentsToAcquirePropertyPlantAndEquipment_Prior": 2900000000
    }
    """


# Note: The MCP server will be attached at runtime in the manager
# Using strict_json_schema=False because dict[str, Any] is not supported in strict mode
financial_metrics_agent = Agent(
    name="FinancialMetricsAgent",
    instructions=FINANCIAL_METRICS_PROMPT,
    model=AgentConfig.METRICS_MODEL,
    output_type=AgentOutputSchema(FinancialMetrics, strict_json_schema=False),
)
