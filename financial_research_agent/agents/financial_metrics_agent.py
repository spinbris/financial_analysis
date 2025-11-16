from typing import Any, Dict
from datetime import datetime
from pydantic import BaseModel
import os

from agents import Agent, function_tool
from financial_research_agent.config import AgentConfig
from agents.agent_output import AgentOutputSchema
from financial_research_agent.tools.edgartools_wrapper import EdgarToolsWrapper
from financial_research_agent.tools.financial_ratios_calculator import FinancialRatiosCalculator
from financial_research_agent.tools.banking_ratios_calculator import BankingRatiosCalculator
from financial_research_agent.utils.sector_detection import detect_industry_sector, should_analyze_banking_ratios

# Financial Metrics agent specializes in extracting financial statements
# and calculating comprehensive financial ratios for liquidity, solvency,
# profitability, and efficiency analysis.

@function_tool
def extract_financial_metrics(ticker: str) -> Dict:
    """
    Extract comprehensive financial statements and calculate ratios using edgartools.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL")

    Returns:
        Dictionary containing:
        - statements: Complete balance sheet, income statement, cash flow (current + prior)
        - ratios: 18+ calculated ratios across 5 categories
          - profitability: margins, ROA, ROE, asset turnover
          - liquidity: current ratio, cash ratio, working capital
          - leverage: debt-to-assets, debt-to-equity, equity ratio
          - efficiency: asset turnover, equity turnover
          - cash_flow: OCF ratios, free cash flow
        - banking_ratios: (ONLY for banks) Banking-specific ratios
          - profitability: NIM, efficiency ratio, ROTCE
          - credit_quality: NPL ratio, provision coverage, charge-offs
          - balance_sheet_composition: loan-to-deposit, loan-to-assets
        - growth: Year-over-year growth rates
        - verification: Balance sheet equation validation
        - summary: Human-readable ratio summary
    """
    # Set identity from environment
    identity = os.getenv("EDGAR_IDENTITY", "User user@example.com")

    # Initialize tools
    edgar = EdgarToolsWrapper(identity=identity)
    calculator = FinancialRatiosCalculator(identity=identity)

    # Extract all financial data
    statements = edgar.get_all_data(ticker)

    # Calculate comprehensive ratios
    ratios = calculator.calculate_all_ratios(ticker)
    growth = calculator.calculate_growth_rates(ticker)
    verification = edgar.verify_balance_sheet_equation(ticker)
    summary = calculator.get_ratio_summary(ticker)

    # Detect sector and calculate banking ratios if applicable
    # Use SIC code and company name for intelligent sector detection
    sic_code = statements.get('sic_code')
    company_name = statements.get('company_name')
    sector = detect_industry_sector(ticker, sic_code=sic_code, company_name=company_name)
    banking_ratios = None
    banking_summary = None

    if should_analyze_banking_ratios(sector):
        banking_calculator = BankingRatiosCalculator(identity=identity)
        banking_ratios = banking_calculator.calculate_all_banking_ratios(ticker)
        banking_summary = banking_calculator.get_banking_ratio_summary(ticker)

    result = {
        'ticker': ticker,
        'sector': sector,
        'company_name': company_name,
        'sic_code': sic_code,
        'statements': statements,
        'ratios': ratios,
        'growth': growth,
        'verification': verification,
        'summary': summary,
        'metadata': {
            'balance_sheet_verified': verification['passed'],
            'verification_error_pct': verification['difference_pct'],
            'is_banking_sector': should_analyze_banking_ratios(sector),
        }
    }

    # Add banking-specific data if applicable
    if banking_ratios:
        result['banking_ratios'] = banking_ratios
        result['banking_summary'] = banking_summary

    return result


FINANCIAL_METRICS_PROMPT = """You are a financial metrics specialist with expertise in
analyzing comprehensive financial ratios and statements.

Your role is to extract financial data and provide expert analysis of a company's
financial health across liquidity, solvency, profitability, and efficiency dimensions.

## Available Tool

**extract_financial_metrics(ticker: str)**

This tool provides complete financial analysis including:
- **sector**: Industry sector classification (banking, investment_banking, insurance, reit, general)
- **statements**: Full balance sheet, income statement, cash flow (current + prior periods)
- **ratios**: 18+ pre-calculated ratios across 5 categories:
  - Profitability: gross/operating/net margins, ROA, ROE, asset turnover
  - Liquidity: current ratio, cash ratio, working capital
  - Leverage: debt-to-assets, debt-to-equity, equity ratio
  - Efficiency: asset turnover, equity turnover
  - Cash Flow: OCF ratios, OCF margin, free cash flow
- **banking_ratios**: (ONLY for banking sector) Banking-specific calculated ratios:
  - Profitability: Net Interest Margin (NIM), Efficiency Ratio, ROTCE
  - Credit Quality: NPL ratio, Provision Coverage, Net Charge-Off Rate
  - Balance Sheet: Loan-to-Deposit, Loan-to-Assets, Deposits-to-Assets
- **growth**: Year-over-year revenue/income/asset growth rates
- **verification**: Balance sheet equation validation (Assets = Liabilities + Equity)
- **summary**: Human-readable formatted summary
- **banking_summary**: (ONLY for banks) Human-readable banking ratios summary

All data is extracted directly from SEC EDGAR filings via edgartools with exact precision.

**Note**: For banks, regulatory capital ratios (CET1, Tier 1, Total Capital, Leverage, LCR, NSFR)
are NOT included in this tool's output. Those must be extracted separately from MD&A disclosures
by a specialized LLM agent as they are not available in standard XBRL format.

## Analysis Process

1. **Extract Data**: Call `extract_financial_metrics(ticker)` to get all financial data

2. **Review Results**: The tool returns:
   - Complete financial statements with comparative periods (_Current and _Prior suffixes)
   - 18+ calculated ratios (already computed, no manual calculation needed)
   - Growth rates comparing current vs prior period
   - Balance sheet verification (should show 'passed': True)

3. **Interpret Financial Health**: Assess based on ratio benchmarks:
   - **Profitability Ratios**:
     - Gross/Operating/Net Margins: Higher is better (varies by industry)
     - ROA (Return on Assets): >5% good, >10% excellent
     - ROE (Return on Equity): >10% good, >15% excellent
   - **Liquidity Ratios**:
     - Current Ratio: >1.0 healthy, >2.0 strong
     - Cash Ratio: >0.2 adequate, >0.5 strong
   - **Leverage Ratios**:
     - Debt-to-Assets: <0.5 conservative, <0.3 very conservative
     - Debt-to-Equity: <1.0 moderate, <2.0 acceptable
     - Equity Ratio: >0.5 strong equity position
   - **Efficiency Ratios**:
     - Asset Turnover: Varies by industry (capital-intensive vs light)
   - **Cash Flow Ratios**:
     - OCF to Net Income: >1.0 indicates quality earnings
     - OCF Margin: Higher is better
     - Free Cash Flow: Positive indicates sustainable operations

4. **Prepare Output**: Structure your response as FinancialMetrics with:
   - executive_summary: 2-3 sentence overall assessment
   - All ratio values (use pre-calculated values from tool)
   - Complete financial statements (from tool's statements.balance_sheet, etc.)
   - Metadata: period, filing_date, filing_reference
   - calculation_notes: List any missing data or issues

## Data Format Notes

**Financial Statements Structure:**
The tool returns statements with line items suffixed by _Current and _Prior:
```
{
  "CashAndCashEquivalentsAtCarryingValue_Current": 29943000000,
  "CashAndCashEquivalentsAtCarryingValue_Prior": 28663000000,
  "Assets_Current": 365725000000,
  "Assets_Prior": 352755000000,
  "current_period_date": "2024-09-28",
  "prior_period_date": "2024-06-29"
}
```

**Ratio Categories:**
```
ratios = {
  'profitability': {gross_profit_margin, operating_margin, net_profit_margin, return_on_assets, return_on_equity, asset_turnover},
  'liquidity': {current_ratio, cash_ratio, working_capital},
  'leverage': {debt_to_assets, debt_to_equity, equity_ratio},
  'efficiency': {asset_turnover, equity_turnover},
  'cash_flow': {ocf_to_net_income, ocf_margin, ocf_to_current_liabilities, free_cash_flow}
}
```

## Output Requirements

Your response must be a valid FinancialMetrics object with:

1. **executive_summary** (str): 2-3 sentence assessment of overall financial health

2. **All 17 ratio fields** (float | None):
   - Use values from ratios dict returned by tool
   - Set to None only if ratio couldn't be calculated
   - Include: current_ratio, quick_ratio, cash_ratio, debt_to_equity, debt_to_assets,
     interest_coverage, equity_ratio, gross_profit_margin, operating_margin,
     net_profit_margin, return_on_assets, return_on_equity, asset_turnover,
     inventory_turnover, receivables_turnover, days_sales_outstanding

3. **balance_sheet** (dict): Complete balance sheet from statements
   - Include all line items with _Current and _Prior suffixes
   - Must include: current_period_date, prior_period_date

4. **income_statement** (dict): Complete income statement from statements

5. **cash_flow_statement** (dict | str): Complete cash flow or "Not available"

6. **Metadata**:
   - period: e.g., "Q4 FY2024" or "FY2024"
   - filing_date: Date of SEC filing
   - filing_reference: Simple string like "10-Q filed 2025-08-01, Accession: 0000320193-25-000073"
   - company_name: Company name from statements (optional)
   - sic_code: SIC code from statements (optional)

7. **calculation_notes** (list[str]): Any issues encountered
   - e.g., ["Quick ratio approximated using cash ratio (inventory data unavailable)"]

The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Example Workflow

For query "Calculate financial metrics for Apple":

1. Call: `extract_financial_metrics("AAPL")`
2. Receive complete data with 18+ ratios pre-calculated, plus company_name and sic_code
3. Map ratios to FinancialMetrics fields:
   - current_ratio ← ratios['liquidity']['current_ratio']
   - return_on_equity ← ratios['profitability']['return_on_equity']
   - etc.
4. Extract statements for balance_sheet, income_statement, cash_flow_statement
5. Extract company_name and sic_code from tool response
6. Write executive_summary based on ratio analysis
7. Determine period and filing_reference from statements metadata
8. Add calculation_notes for any missing data
9. Return complete FinancialMetrics object

Remember: The tool does all the heavy lifting (data extraction, ratio calculations).
Your job is to interpret the results and structure them properly.

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

    company_name: str | None = None
    """Company name from SEC filings"""

    sic_code: int | None = None
    """SIC code for sector detection"""

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

    cash_flow_statement: dict[str, Any] | str
    """Complete cash flow statement with all line items from XBRL, including comparative period.
    If cash flow data is unavailable, may be a string like "Not available in this filing".

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


# Using strict_json_schema=False because dict[str, Any] is not supported in strict mode

# Build agent kwargs, only including model_settings if not None
agent_kwargs = {
    "name": "FinancialMetricsAgent",
    "instructions": FINANCIAL_METRICS_PROMPT,
    "model": AgentConfig.METRICS_MODEL,
    "output_type": AgentOutputSchema(FinancialMetrics, strict_json_schema=False),
    "tools": [extract_financial_metrics],  # EdgarTools direct extraction
}

# Only add model_settings if it's not None (for reasoning models only)
model_settings = AgentConfig.get_model_settings(
    AgentConfig.METRICS_MODEL,
    AgentConfig.METRICS_REASONING_EFFORT
)
if model_settings is not None:
    agent_kwargs["model_settings"] = model_settings

financial_metrics_agent = Agent(**agent_kwargs)
