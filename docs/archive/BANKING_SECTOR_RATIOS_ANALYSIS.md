# Banking Sector Regulatory Ratios - Implementation Plan

## Executive Summary

Based on your finance sector background and need for regulatory risk ratios, here's what's available and what we can implement for banking sector analysis.

**Good News:**
- ✅ Banks disclose regulatory capital ratios in 10-K filings (SEC requirement)
- ✅ EdgarTools can access these filings and extract HTML/text
- ✅ Ratios are typically presented in tables in the "Capital Management" or "Regulatory Capital" section
- ✅ We can extract and calculate these ratios programmatically

**Current State:**
- ⚠️ System currently calculates generic financial ratios (not banking-specific)
- ⚠️ No regulatory capital ratio extraction yet
- ⚠️ Standard ratio interpretations may not suit banks (as you noted)

---

## Banking Regulatory Ratios Available in SEC Filings

### 1. Basel III Capital Ratios (Primary)

Banks are required to disclose these under SEC regulations:

#### **Common Equity Tier 1 (CET1) Capital Ratio**
- **Formula:** CET1 Capital / Risk-Weighted Assets (RWA)
- **Regulatory Minimum:** 4.5%
- **2024 Requirements:** 4.5% + 2.5% buffer + G-SIB surcharge (if applicable)
- **Components:**
  - Common stock
  - Retained earnings
  - AOCI (Accumulated Other Comprehensive Income)
  - Less: Goodwill, intangibles, deferred tax assets

**Example from JPMorgan Chase 10-K:**
```
CET1 Capital Ratio: 15.3% (Dec 31, 2024)
CET1 Capital: $267.9 billion
Risk-Weighted Assets: $1,750 billion
```

#### **Tier 1 Capital Ratio**
- **Formula:** Tier 1 Capital / Risk-Weighted Assets
- **Regulatory Minimum:** 6.0%
- **Components:** CET1 + Additional Tier 1 (AT1) instruments
  - Preferred stock (qualifying)
  - Non-cumulative perpetual preferred stock

#### **Total Capital Ratio**
- **Formula:** Total Capital / Risk-Weighted Assets
- **Regulatory Minimum:** 8.0%
- **Components:** Tier 1 + Tier 2 Capital
  - Subordinated debt (qualifying)
  - Loan loss reserves (up to limit)

#### **Tier 1 Leverage Ratio**
- **Formula:** Tier 1 Capital / Average Total Assets (not risk-weighted)
- **Regulatory Minimum:** 4.0% (supplementary leverage ratio for G-SIBs: 3%)
- **Purpose:** Simple non-risk-based backstop

---

### 2. Liquidity Ratios (Basel III)

#### **Liquidity Coverage Ratio (LCR)**
- **Formula:** High-Quality Liquid Assets (HQLA) / Total Net Cash Outflows (30 days)
- **Regulatory Minimum:** 100%
- **Purpose:** Ensure banks can survive 30-day stress scenario
- **Disclosure:** Required quarterly for large banks

#### **Net Stable Funding Ratio (NSFR)**
- **Formula:** Available Stable Funding / Required Stable Funding
- **Regulatory Minimum:** 100%
- **Purpose:** Promote longer-term resilient funding structures

---

### 3. Stress Capital Buffer (SCB)

**U.S.-Specific Requirement (Fed)**
- Based on annual CCAR/DFAST stress test results
- Minimum: 2.5% of RWA
- Added to CET1 minimum requirement
- Varies by bank based on stress test performance

---

### 4. Additional Banking-Specific Ratios

#### **Loan-to-Deposit Ratio (LTD)**
- **Formula:** Total Loans / Total Deposits
- **Typical Range:** 80-90%
- **Interpretation:** >100% may indicate funding stress

#### **Net Interest Margin (NIM)**
- **Formula:** (Interest Income - Interest Expense) / Average Earning Assets
- **Typical Range:** 2.5-3.5%
- **Key Profitability Metric:** Higher is better (but consider risk)

#### **Efficiency Ratio**
- **Formula:** Non-Interest Expense / (Net Interest Income + Non-Interest Income)
- **Typical Range:** 55-65%
- **Interpretation:** Lower is better (more efficient)

#### **Non-Performing Loan (NPL) Ratio**
- **Formula:** Non-Performing Loans / Total Loans
- **Typical Range:** <1% (healthy), >3% (concerning)
- **Credit Quality Indicator**

#### **Provision Coverage Ratio**
- **Formula:** Loan Loss Reserves / Non-Performing Loans
- **Typical Range:** 70-100%+
- **Interpretation:** Higher = better coverage

#### **Return on Tangible Common Equity (ROTCE)**
- **Formula:** Net Income / (Common Equity - Intangibles)
- **Typical Range:** 15-20%
- **Bank-Specific Profitability:** Preferred over ROE for banks

---

## Data Sources & Extraction Methods

### Primary Source: SEC 10-K Filings

**Location in 10-K:**
1. **Item 1 - Business**
   - "Capital Management" section
   - "Regulatory Capital" subsection

2. **Item 7 - MD&A**
   - "Capital Management and Liquidity" section
   - Tables showing capital ratios (current vs. prior year)
   - Reconciliation of GAAP equity to regulatory capital

3. **Item 8 - Financial Statements**
   - Note on "Regulatory Capital" (typically Note 20-25)
   - Detailed breakdown of capital components

**What We Found (JPMorgan Example):**
```html
<table>
  <caption>Regulatory Capital Components</caption>
  <tr>
    <th>Capital Component</th>
    <th>2024</th>
    <th>2023</th>
  </tr>
  <tr>
    <td>CET1 Capital</td>
    <td>$267.9B</td>
    <td>$254.1B</td>
  </tr>
  <tr>
    <td>Risk-Weighted Assets</td>
    <td>$1,750B</td>
    <td>$1,727B</td>
  </tr>
  <tr>
    <td>CET1 Capital Ratio</td>
    <td>15.3%</td>
    <td>14.7%</td>
  </tr>
</table>
```

### EdgarTools Capabilities

**What EdgarTools CAN Do:**
- ✅ Fetch 10-K filings for any bank
- ✅ Extract HTML content with tables
- ✅ Access text of entire filing
- ✅ Get standard financial statements (balance sheet, income statement)

**What EdgarTools CANNOT Do Automatically:**
- ❌ Parse regulatory capital tables (not in standard XBRL taxonomy)
- ❌ Extract CET1/Tier 1 ratios directly
- ❌ Calculate risk-weighted assets

**Why Not in XBRL?**
Regulatory capital disclosures are often in:
- Narrative text sections (MD&A)
- Custom HTML tables
- PDF exhibits (Pillar 3 reports)
- Supplementary regulatory reports (not always in 10-K)

---

## Implementation Options

### Option 1: LLM-Based Extraction (Recommended)

**Approach:** Use existing agent system to extract regulatory ratios from 10-K text

**Steps:**
1. Create `RegulatoryCapitalAgent` specialized for banks
2. Agent searches 10-K for "Capital Management" or "Regulatory Capital" sections
3. LLM extracts ratios from narrative and tables
4. Returns structured `BankingRegulatoryRatios` Pydantic model

**Advantages:**
- ✅ Works with existing infrastructure
- ✅ Handles varied table formats
- ✅ Can extract from narrative text
- ✅ Flexible for different banks' disclosure styles

**Disadvantages:**
- ⚠️ Requires LLM call (cost: ~$0.01-0.02 per analysis)
- ⚠️ May hallucinate if data not clearly stated
- ⚠️ Needs verification

**Implementation Complexity:** Medium (2-3 hours)

---

### Option 2: Regex/HTML Parsing

**Approach:** Parse HTML tables directly to extract ratios

**Steps:**
1. Search filing HTML for tables containing "tier 1", "cet1", "capital ratio"
2. Parse table using BeautifulSoup or regex
3. Extract numeric values and calculate ratios

**Advantages:**
- ✅ No LLM cost
- ✅ Fast extraction
- ✅ Deterministic results

**Disadvantages:**
- ⚠️ Brittle (breaks with format changes)
- ⚠️ May miss ratios in narrative text
- ⚠️ Requires maintenance for different bank formats

**Implementation Complexity:** High (4-6 hours, ongoing maintenance)

---

### Option 3: Hybrid Approach (Best Balance)

**Approach:** Combine regex search + LLM verification

**Steps:**
1. Use regex to find "Capital Management" section in 10-K
2. Extract that section (reduces LLM context needed)
3. Pass section to specialized agent for extraction
4. Agent returns structured data with confidence scores

**Advantages:**
- ✅ Reduced LLM costs (smaller context)
- ✅ More reliable than pure regex
- ✅ Handles edge cases better

**Disadvantages:**
- ⚠️ More complex implementation

**Implementation Complexity:** Medium-High (3-4 hours)

---

## Recommended Implementation Plan

### Phase 1: Add Banking-Specific Ratio Extraction (Week 1)

**1. Create BankingRegulatoryRatios Pydantic Model**

```python
# financial_research_agent/models/banking_ratios.py

from pydantic import BaseModel, Field
from typing import Optional

class BankingRegulatoryRatios(BaseModel):
    """Regulatory capital ratios for banks (Basel III)."""

    # Capital Ratios
    cet1_ratio: Optional[float] = Field(None, description="Common Equity Tier 1 Capital Ratio (%)")
    tier1_ratio: Optional[float] = Field(None, description="Tier 1 Capital Ratio (%)")
    total_capital_ratio: Optional[float] = Field(None, description="Total Capital Ratio (%)")
    tier1_leverage_ratio: Optional[float] = Field(None, description="Tier 1 Leverage Ratio (%)")

    # Capital Components (in millions/billions)
    cet1_capital: Optional[float] = Field(None, description="CET1 Capital amount")
    tier1_capital: Optional[float] = Field(None, description="Tier 1 Capital amount")
    total_capital: Optional[float] = Field(None, description="Total Capital amount")
    risk_weighted_assets: Optional[float] = Field(None, description="Risk-Weighted Assets")

    # Liquidity Ratios
    lcr: Optional[float] = Field(None, description="Liquidity Coverage Ratio (%)")
    nsfr: Optional[float] = Field(None, description="Net Stable Funding Ratio (%)")

    # Stress Capital Buffer
    scb: Optional[float] = Field(None, description="Stress Capital Buffer (%)")
    gsib_surcharge: Optional[float] = Field(None, description="G-SIB Surcharge (%)")

    # Additional Banking Metrics
    loan_to_deposit_ratio: Optional[float] = Field(None, description="Loan-to-Deposit Ratio (%)")
    net_interest_margin: Optional[float] = Field(None, description="Net Interest Margin (%)")
    efficiency_ratio: Optional[float] = Field(None, description="Efficiency Ratio (%)")
    npl_ratio: Optional[float] = Field(None, description="Non-Performing Loan Ratio (%)")
    provision_coverage_ratio: Optional[float] = Field(None, description="Provision Coverage Ratio (%)")
    rotce: Optional[float] = Field(None, description="Return on Tangible Common Equity (%)")

    # Metadata
    reporting_period: Optional[str] = Field(None, description="Reporting period (e.g., 'Q4 2024')")
    regulatory_framework: Optional[str] = Field(None, description="e.g., 'Basel III Standardized Approach'")

    # Narrative Summary
    capital_summary: Optional[str] = Field(None, description="Brief summary of capital position")
    regulatory_context: Optional[str] = Field(None, description="Any regulatory changes or notable items")
```

**2. Create Banking Regulatory Capital Agent**

```python
# financial_research_agent/agents/banking_regulatory_agent.py

from agent_core import Agent
from .models import BankingRegulatoryRatios

BANKING_REGULATORY_PROMPT = """
You are a banking regulatory analyst specializing in Basel III capital requirements.

Your task is to extract regulatory capital ratios and banking-specific metrics from SEC 10-K filings.

## Data to Extract

### Primary Regulatory Capital Ratios (Basel III):
1. **Common Equity Tier 1 (CET1) Capital Ratio** - Most important
2. **Tier 1 Capital Ratio**
3. **Total Capital Ratio**
4. **Tier 1 Leverage Ratio**

### Capital Components:
- CET1 Capital amount
- Tier 1 Capital amount
- Total Capital amount
- Risk-Weighted Assets (RWA)

### Liquidity Ratios:
- Liquidity Coverage Ratio (LCR)
- Net Stable Funding Ratio (NSFR)

### Additional Banking Metrics:
- Loan-to-Deposit Ratio
- Net Interest Margin (NIM)
- Efficiency Ratio
- Non-Performing Loan (NPL) Ratio
- Provision Coverage Ratio
- Return on Tangible Common Equity (ROTCE)

## Where to Find This Data

Look in these sections of the 10-K:
1. **MD&A** → "Capital Management" or "Regulatory Capital" section
2. **Financial Statement Notes** → "Regulatory Capital" note (usually Note 20-25)
3. **Item 1 - Business** → "Regulation and Supervision" subsection

## Important Notes

- Banks typically present these ratios in tables comparing current vs. prior year
- Look for reconciliation of GAAP equity to regulatory capital
- CET1 ratio is THE most important metric for bank capital adequacy
- Ratios below regulatory minimums are red flags:
  - CET1 < 4.5% + buffer (usually 7%+)
  - Tier 1 < 6.0%
  - Total Capital < 8.0%

## Output Format

Return a structured JSON object with all extracted ratios and a brief narrative summary.

If a ratio is not found or not disclosed, return null for that field.
Include the reporting period and any regulatory context (e.g., Basel III framework, stress test results).
"""

banking_regulatory_agent = Agent(
    name="Banking Regulatory Analyst",
    instructions=BANKING_REGULATORY_PROMPT,
    output_type=BankingRegulatoryRatios,
)
```

**3. Integrate into Manager**

Add banking sector detection and specialized analysis:

```python
# In manager_enhanced.py

async def _detect_industry_sector(self, ticker: str) -> str:
    """Detect if company is in banking/finance sector."""
    # Use SIC code or simple ticker lookup
    BANK_TICKERS = ['JPM', 'BAC', 'C', 'WFC', 'GS', 'MS', 'USB', 'PNC', 'TFC', 'COF']

    if ticker in BANK_TICKERS:
        return 'banking'

    # Could also check SIC code from Edgar
    return 'general'

async def _gather_specialist_analyses(self, ...):
    """Enhanced to include banking-specific analysis."""

    sector = await self._detect_industry_sector(self.ticker)

    if sector == 'banking' and self.edgar_server:
        # Run banking regulatory analysis
        from .agents.banking_regulatory_agent import banking_regulatory_agent

        banking_agent_with_edgar = banking_regulatory_agent.clone(
            mcp_servers=[self.edgar_server]
        )

        banking_input = f"Extract regulatory capital ratios for {self.ticker}"
        banking_result = await Runner.run(banking_agent_with_edgar, banking_input)
        banking_ratios = banking_result.final_output_as(BankingRegulatoryRatios)

        # Save to file
        self._save_banking_regulatory_ratios(banking_ratios)

    # Continue with standard specialist analyses...
```

---

### Phase 2: Enhanced Banking Interpretation (Week 2)

**1. Update Financials Agent Prompt for Banks**

Add banking-specific interpretation guidance:

```python
BANKING_INTERPRETATION_ADDENDUM = """
## Banking-Specific Ratio Interpretation

When analyzing a bank, focus on these key metrics:

### Capital Adequacy (Most Critical)
- **CET1 Ratio > 10%**: Well-capitalized
- **CET1 Ratio 7-10%**: Adequately capitalized
- **CET1 Ratio < 7%**: Undercapitalized (regulatory concern)

Interpret in context of:
- Regulatory minimums + buffers
- Peer comparisons (other banks)
- Stress test requirements

### Profitability Metrics
- **ROTCE** (not ROE) is the gold standard for banks
- **Net Interest Margin** shows core lending profitability
- **Efficiency Ratio** < 60% is strong

### Credit Quality
- **NPL Ratio** < 1% is healthy
- **Provision Coverage** > 80% is adequate
- Watch for trends (increasing NPLs = deteriorating quality)

### Liquidity
- **LCR > 100%** = meets regulatory requirement
- **Loan-to-Deposit < 100%** = good funding position

### DO NOT Use Standard Ratios
- Debt-to-Equity: Meaningless for banks (high leverage is normal)
- Current Ratio: Doesn't apply to bank balance sheets
- Inventory Turnover: Banks don't have inventory

Instead, focus on regulatory capital, credit quality, and profitability.
"""
```

**2. Add Banking Ratio Visualization**

Create specialized charts for banking metrics:

```python
# financial_research_agent/visualization/banking_charts.py

def create_capital_ratio_chart(banking_ratios: BankingRegulatoryRatios) -> go.Figure:
    """
    Create waterfall chart showing capital ratio components.

    Shows:
    - CET1 ratio vs. regulatory minimum
    - Additional Tier 1
    - Tier 2 capital
    - Buffers and surcharges
    """

def create_nim_trend_chart(financials: Financials) -> go.Figure:
    """
    Create Net Interest Margin trend chart over time.

    Shows NIM with interest rate environment context.
    """

def create_credit_quality_dashboard(banking_ratios: BankingRegulatoryRatios) -> go.Figure:
    """
    Create credit quality metrics dashboard.

    Shows:
    - NPL ratio trend
    - Provision coverage
    - Charge-off rates
    """
```

---

### Phase 3: Industry Peer Comparisons (Week 3)

**Goal:** Compare bank's ratios against peer averages

**Implementation:**
1. Maintain database of banking ratios for major banks
2. Calculate percentiles for each ratio
3. Show peer comparison in analysis

**Example Output:**
```
JPMorgan Chase Regulatory Capital Position

CET1 Ratio: 15.3%
  - Regulatory Minimum: 7.0% (4.5% + 2.5% buffer)
  - Peer Median: 13.8%
  - Percentile: 85th (strong)

Tier 1 Leverage: 6.8%
  - Regulatory Minimum: 5.0% (G-SIB supplementary)
  - Peer Median: 6.2%
  - Percentile: 70th (above average)
```

---

## Testing Strategy

### Test Banks (Different Profiles)

1. **JPMorgan Chase (JPM)** - G-SIB, complex
2. **Bank of America (BAC)** - G-SIB
3. **U.S. Bancorp (USB)** - Regional, simpler
4. **PNC Financial (PNC)** - Regional
5. **First Republic Bank (FRC)** - Failed bank (historical test)

### Validation Criteria

1. **Accuracy:** Compare extracted ratios to published numbers
2. **Completeness:** All major ratios extracted
3. **Consistency:** Same bank analyzed twice produces same results
4. **Robustness:** Works across different bank sizes and formats

---

## Cost Estimate

### Implementation Time
- Phase 1 (Basic Extraction): 8-12 hours
- Phase 2 (Enhanced Interpretation): 6-8 hours
- Phase 3 (Peer Comparisons): 8-10 hours
- **Total:** 22-30 hours

### Ongoing Costs
- LLM extraction: ~$0.02 per bank analysis
- No additional data costs (using SEC EDGAR)

---

## Alternative: Manual Ratio Entry

If automatic extraction proves unreliable, we could add:

**Manual Ratio Input Mode:**
```python
# User manually enters key ratios from 10-K
banking_ratios = {
    'cet1_ratio': 15.3,
    'tier1_ratio': 16.5,
    'total_capital_ratio': 18.8,
    # ... etc
}

# System provides interpretation and peer comparison
analysis = analyze_banking_ratios(banking_ratios, peer_group='G-SIB')
```

This would be faster to implement (2-3 hours) but less automated.

---

## Recommendation

**Start with Phase 1: LLM-Based Extraction**

**Reasoning:**
1. Fastest path to value
2. Leverages existing infrastructure
3. Flexible enough to handle varied formats
4. Can always add regex/parsing later if needed

**Next Steps:**
1. Create `BankingRegulatoryRatios` Pydantic model
2. Create `banking_regulatory_agent.py`
3. Test with JPM and BAC
4. Integrate into manager with sector detection
5. Update financials agent prompt for banking interpretation

**Timeline:** Could have basic version working in 1-2 days.

---

## Questions for You

1. **Priority Ratios:** Which ratios are MOST critical for your analysis?
   - CET1, Tier 1, Total Capital (regulatory)
   - NIM, ROTCE, Efficiency (profitability)
   - NPL, Provision Coverage (credit quality)
   - LCR, NSFR (liquidity)

2. **Bank Types:** Are you focused on:
   - Large U.S. banks (G-SIBs)?
   - Regional banks?
   - International banks?
   - Credit unions or specialty lenders?

3. **Use Case:** Will you:
   - Analyze banks regularly?
   - Need peer comparisons?
   - Track ratios over time (trend analysis)?

4. **Automation Level:** Would you prefer:
   - Fully automated extraction (may have errors)?
   - Semi-automated with manual review?
   - Manual entry with automated interpretation?

Let me know your preferences and I can start implementing the most relevant features first!
