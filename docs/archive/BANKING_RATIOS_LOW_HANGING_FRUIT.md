# Banking Ratios - Low-Hanging Fruit Implementation

## Quick Win: Focus on Directly Reported Ratios

Based on your requirements (all ratios, US + international banks, peer comparisons), here's what we can extract **easily** from 10-Ks without complex calculations.

---

## ✅ TIER 1: Directly Reported (Just Extract - No Calculation)

These are **explicitly disclosed** in 10-K regulatory capital tables. Just need LLM extraction.

### Basel III Regulatory Capital Ratios

| Ratio | Where Found | Implementation Effort |
|-------|-------------|----------------------|
| **CET1 Ratio** | MD&A "Capital Management" table | ⭐ Easy (1 hour) |
| **Tier 1 Capital Ratio** | Same table | ⭐ Easy (included with CET1) |
| **Total Capital Ratio** | Same table | ⭐ Easy (included with CET1) |
| **Tier 1 Leverage Ratio** | Same table | ⭐ Easy (included with CET1) |
| **Supplementary Leverage Ratio** | Same table (if G-SIB) | ⭐ Easy (included with CET1) |

**Sample Data Found (JPMorgan):**
```
CET1 capital ratio: 15.7% (Dec 2024)
CET1 capital ratio: 15.0% (Dec 2023)
Regulatory minimum: 7.0%
```

**Implementation:** Single LLM extraction agent
- Input: 10-K text (Capital Management section)
- Output: All 5 ratios + regulatory minimums
- **Time:** 1-2 hours
- **Cost per analysis:** ~$0.01

---

### Liquidity Ratios (Large Banks)

| Ratio | Where Found | Implementation Effort |
|-------|-------------|----------------------|
| **Liquidity Coverage Ratio (LCR)** | MD&A "Liquidity" section | ⭐ Easy (30 min) |
| **Net Stable Funding Ratio (NSFR)** | Same section | ⭐ Easy (included with LCR) |

**Note:** Only disclosed by large banks (>$250B assets). Regional banks may not report.

**Implementation:** Add to same extraction agent
- **Time:** +30 minutes
- **Cost:** Same LLM call (no additional cost)

---

### Stress Test Results (U.S. G-SIBs only)

| Ratio | Where Found | Implementation Effort |
|-------|-------------|----------------------|
| **Stress Capital Buffer (SCB)** | MD&A or CCAR disclosure | ⭐ Easy (15 min) |
| **G-SIB Surcharge** | Regulatory capital table | ⭐ Easy (included) |

**U.S. G-SIBs:** JPM, BAC, C, WFC, GS, MS, BNY, STLD

---

## ⭐ TIER 2: Simple Calculations (One Formula)

These require **one simple calculation** from reported numbers. Very reliable.

### Profitability Ratios

| Ratio | Calculation | Data Source | Effort |
|-------|-------------|-------------|--------|
| **Net Interest Margin (NIM)** | (Interest Income - Interest Expense) / Avg Earning Assets | Income statement | ⭐⭐ Easy (30 min) |
| **Efficiency Ratio** | Non-Interest Expense / (Net Interest Income + Non-Interest Income) | Income statement | ⭐⭐ Easy (30 min) |
| **Return on Tangible Equity (ROTCE)** | Net Income / (Total Equity - Intangibles) | Income stmt + Balance sheet | ⭐⭐ Easy (30 min) |

**Why Easy:**
- All inputs are standard XBRL line items (already extracted)
- Single formula
- No special adjustments needed

**Example (NIM for JPM):**
```python
nim = (interest_income - interest_expense) / avg_earning_assets * 100
# Data: Interest income = $100B, Interest expense = $50B, Earning assets = $2.5T
# NIM = ($100B - $50B) / $2.5T = 2.0%
```

**Implementation:** Add to financial metrics agent
- **Time:** 1 hour total for all 3
- **Cost:** No additional (uses existing financial statements)

---

### Credit Quality Ratios

| Ratio | Calculation | Data Source | Effort |
|-------|-------------|-------------|--------|
| **Non-Performing Loan (NPL) Ratio** | Non-Performing Loans / Total Loans | Loan disclosure note | ⭐⭐ Easy (30 min) |
| **Provision Coverage Ratio** | Allowance for Loan Losses / NPLs | Same note | ⭐⭐ Easy (15 min) |
| **Net Charge-Off Rate** | Net Charge-Offs / Average Loans | Same note | ⭐⭐ Easy (15 min) |

**Where Found:** 10-K Note on "Allowance for Credit Losses" or "Loan Portfolio"

**Why Easy:**
- Disclosed in standard loan disclosure table
- Already required by CECL accounting standard
- Simple division

**Implementation:** Add to existing credit analysis
- **Time:** 1 hour
- **Cost:** No additional

---

### Balance Sheet Ratios

| Ratio | Calculation | Data Source | Effort |
|-------|-------------|-------------|--------|
| **Loan-to-Deposit Ratio** | Total Loans / Total Deposits | Balance sheet | ⭐ Trivial (5 min) |
| **Loan-to-Assets Ratio** | Total Loans / Total Assets | Balance sheet | ⭐ Trivial (5 min) |
| **Deposits-to-Assets Ratio** | Total Deposits / Total Assets | Balance sheet | ⭐ Trivial (5 min) |

**Why Easy:**
- Standard balance sheet line items (already have)
- No adjustments needed
- Single division

**Implementation:** Add to financial metrics calculator
- **Time:** 15 minutes
- **Cost:** No additional

---

## 🚀 RECOMMENDED QUICK WIN IMPLEMENTATION

### MVP: 2-3 Hours of Work

**Step 1: Add Banking Ratios Pydantic Model (30 min)**

```python
# financial_research_agent/models/banking_ratios.py

from pydantic import BaseModel
from typing import Optional

class BankingRegulatoryRatios(BaseModel):
    """Banking-specific ratios (directly reported + simple calcs)."""

    # TIER 1: Directly Reported (LLM extraction)
    cet1_ratio: Optional[float] = None  # %
    tier1_ratio: Optional[float] = None  # %
    total_capital_ratio: Optional[float] = None  # %
    tier1_leverage_ratio: Optional[float] = None  # %
    supplementary_leverage_ratio: Optional[float] = None  # % (G-SIBs only)

    lcr: Optional[float] = None  # % (Liquidity Coverage Ratio)
    nsfr: Optional[float] = None  # % (Net Stable Funding Ratio)

    stress_capital_buffer: Optional[float] = None  # % (U.S. banks)
    gsib_surcharge: Optional[float] = None  # % (G-SIBs only)

    # Regulatory minimums (for context)
    cet1_minimum: Optional[float] = None  # Usually 7.0% (4.5% + 2.5% buffer)
    tier1_minimum: Optional[float] = None  # Usually 8.5%

    # TIER 2: Simple Calculations (from existing financial statements)
    net_interest_margin: Optional[float] = None  # %
    efficiency_ratio: Optional[float] = None  # %
    return_on_tangible_equity: Optional[float] = None  # %

    npl_ratio: Optional[float] = None  # %
    provision_coverage_ratio: Optional[float] = None  # %
    net_charge_off_rate: Optional[float] = None  # %

    loan_to_deposit_ratio: Optional[float] = None  # %
    loan_to_assets_ratio: Optional[float] = None  # %

    # Metadata
    reporting_period: Optional[str] = None
    peer_group: Optional[str] = None  # "G-SIB", "Large Regional", etc.
```

**Step 2: Create Simple Extraction Agent (1 hour)**

```python
# financial_research_agent/agents/banking_ratios_agent.py

from agents import Agent
from ..models.banking_ratios import BankingRegulatoryRatios

BANKING_RATIOS_PROMPT = """
You are a banking analyst extracting regulatory capital ratios from SEC 10-K filings.

## Your Task

Extract these ratios from the 10-K. They are typically in the MD&A section under "Capital Management" or "Regulatory Capital".

### Primary Ratios (look for table with these):

1. **CET1 Ratio** (Common Equity Tier 1 Capital Ratio)
2. **Tier 1 Capital Ratio**
3. **Total Capital Ratio**
4. **Tier 1 Leverage Ratio**
5. **Supplementary Leverage Ratio** (if mentioned - G-SIBs only)

These are usually presented in a table like:

| Ratio | December 31, 2024 | Minimum Required |
|-------|-------------------|------------------|
| CET1  | 15.7%             | 7.0%            |
| Tier 1| 16.9%             | 8.5%            |
| ...   | ...               | ...             |

### Liquidity Ratios (if mentioned):

- **Liquidity Coverage Ratio (LCR)** - usually >100%
- **Net Stable Funding Ratio (NSFR)** - usually >100%

### Stress Test Info (U.S. banks):

- **Stress Capital Buffer (SCB)** - usually 2.5% to 4.5%
- **G-SIB Surcharge** - 0% to 3.5% (only for largest banks)

## Important Notes

- Look for the MOST RECENT period (usually December 31, 2024 or most recent quarter)
- If ratio is not found, return null (don't guess)
- Ratios are expressed as percentages (e.g., 15.7, not 0.157)
- Note the reporting period in the output

## Where to Look

1. **MD&A** → "Capital Management" or "Capital Resources and Liquidity"
2. **MD&A** → "Regulatory Capital" subsection
3. Sometimes in **Financial Statement Notes** → "Regulatory Matters" or "Capital"

## Output

Return structured JSON with all extracted ratios.
"""

banking_ratios_agent = Agent(
    name="Banking Ratios Extractor",
    instructions=BANKING_RATIOS_PROMPT,
    output_type=BankingRegulatoryRatios,
)
```

**Step 3: Add Simple Calculations to Financial Metrics (1 hour)**

```python
# In financial_metrics_agent.py, add banking-specific calculations

def calculate_banking_ratios(financial_statements: dict) -> dict:
    """Calculate simple banking ratios from standard financial statements."""

    ratios = {}

    # Net Interest Margin (NIM)
    interest_income = financial_statements.get('interest_income')
    interest_expense = financial_statements.get('interest_expense')
    avg_earning_assets = financial_statements.get('average_earning_assets') or \
                        financial_statements.get('total_assets')  # fallback

    if interest_income and interest_expense and avg_earning_assets:
        net_interest_income = interest_income - interest_expense
        ratios['net_interest_margin'] = (net_interest_income / avg_earning_assets) * 100

    # Efficiency Ratio
    non_interest_expense = financial_statements.get('non_interest_expense') or \
                          financial_statements.get('operating_expenses')
    non_interest_income = financial_statements.get('non_interest_income')

    if non_interest_expense and net_interest_income and non_interest_income:
        total_revenue = net_interest_income + non_interest_income
        ratios['efficiency_ratio'] = (non_interest_expense / total_revenue) * 100

    # ROTCE (Return on Tangible Common Equity)
    net_income = financial_statements.get('net_income')
    total_equity = financial_statements.get('stockholders_equity')
    intangible_assets = financial_statements.get('intangible_assets') or \
                       financial_statements.get('goodwill', 0)

    if net_income and total_equity:
        tangible_equity = total_equity - intangible_assets
        if tangible_equity > 0:
            ratios['return_on_tangible_equity'] = (net_income / tangible_equity) * 100

    # Loan-to-Deposit Ratio (LTD)
    total_loans = financial_statements.get('loans') or \
                 financial_statements.get('loans_receivable')
    total_deposits = financial_statements.get('deposits')

    if total_loans and total_deposits:
        ratios['loan_to_deposit_ratio'] = (total_loans / total_deposits) * 100

    # Loan-to-Assets
    total_assets = financial_statements.get('total_assets')
    if total_loans and total_assets:
        ratios['loan_to_assets_ratio'] = (total_loans / total_assets) * 100

    return ratios
```

**Step 4: Integrate into Manager (30 min)**

```python
# In manager_enhanced.py

# Add to _gather_specialist_analyses or create new method
async def _extract_banking_ratios(self, ticker: str) -> BankingRegulatoryRatios:
    """Extract banking-specific ratios if company is a bank."""

    # Simple bank detection
    BANK_TICKERS = {
        # U.S. G-SIBs
        'JPM', 'BAC', 'C', 'WFC', 'GS', 'MS', 'BNY', 'STT',
        # Large U.S. Regional
        'USB', 'PNC', 'TFC', 'COF', 'MTB', 'KEY', 'FITB', 'HBAN', 'RF', 'CFG',
        # International
        'HSBC', 'DB', 'CS', 'UBS', 'BCS', 'BBVA', 'SAN', 'RY', 'TD', 'BNS',
    }

    if ticker not in BANK_TICKERS:
        return None

    # Run banking ratios agent
    from .agents.banking_ratios_agent import banking_ratios_agent

    agent_with_edgar = banking_ratios_agent.clone(mcp_servers=[self.edgar_server])

    banking_input = f"""
    Extract regulatory capital ratios for {ticker}.

    Look in the most recent 10-K filing in:
    - MD&A → Capital Management section
    - Notes → Regulatory Capital note

    Extract CET1, Tier 1, Total Capital, and Leverage ratios.
    """

    result = await Runner.run(agent_with_edgar, banking_input)
    ratios = result.final_output_as(BankingRegulatoryRatios)

    # Add calculated ratios from financial statements
    if self.financial_statements:
        calculated = calculate_banking_ratios(self.financial_statements)
        # Merge calculated ratios into extracted ratios
        for key, value in calculated.items():
            if not getattr(ratios, key):  # Only fill if not already extracted
                setattr(ratios, key, value)

    return ratios
```

---

## 📊 Sample Output

```markdown
# JPMorgan Chase Banking Ratios Analysis

## Regulatory Capital (Basel III)

**Common Equity Tier 1 (CET1) Ratio:** 15.7%
  - Regulatory Minimum: 7.0% (4.5% + 2.5% buffer)
  - Excess Capital: 8.7 percentage points
  - Status: ✅ Well-Capitalized

**Tier 1 Capital Ratio:** 16.9%
  - Regulatory Minimum: 8.5%
  - Excess Capital: 8.4 percentage points

**Total Capital Ratio:** 18.8%
  - Regulatory Minimum: 10.5%
  - Excess Capital: 8.3 percentage points

**Tier 1 Leverage Ratio:** 6.8%
  - Regulatory Minimum: 4.0%

**Supplementary Leverage Ratio:** 6.1%
  - Regulatory Minimum: 5.0% (G-SIB enhanced)

## Liquidity Position

**Liquidity Coverage Ratio (LCR):** 114%
  - Regulatory Minimum: 100%
  - Status: ✅ Adequate

**Net Stable Funding Ratio (NSFR):** 119%
  - Regulatory Minimum: 100%
  - Status: ✅ Adequate

## Profitability Metrics

**Net Interest Margin (NIM):** 2.48%
  - Peer Median: 2.35%
  - Industry Range: 2.0% - 3.0%

**Return on Tangible Common Equity (ROTCE):** 17.2%
  - Peer Median: 15.1%
  - Status: ✅ Above Average

**Efficiency Ratio:** 57%
  - Peer Median: 62%
  - Interpretation: More efficient (lower is better)

## Credit Quality

**Non-Performing Loan (NPL) Ratio:** 0.8%
  - Peer Median: 1.1%
  - Status: ✅ Strong (below 1%)

**Provision Coverage Ratio:** 185%
  - Interpretation: Reserves cover NPLs 1.85x

**Net Charge-Off Rate:** 0.42%
  - Peer Median: 0.38%
  - Status: Adequate

## Balance Sheet Composition

**Loan-to-Deposit Ratio:** 67%
  - Interpretation: Well-funded (excess deposits)

**Loan-to-Assets Ratio:** 32%
  - Interpretation: Diversified balance sheet (many non-loan assets)
```

---

## 🎯 Peer Comparison (Phase 2 - Optional)

Once we have extraction working, add peer comparison:

### U.S. Peer Groups

**G-SIBs (Systemically Important):**
- JPM, BAC, C, WFC, GS, MS, BNY, STT

**Large Regional Banks:**
- USB, PNC, TFC, COF, MTB, KEY, FITB

**Mid-Regional Banks:**
- HBAN, RF, CFG, FHN, CMA, ZION

### International Peer Groups

**European G-SIBs:**
- HSBC, DB, BCS, SAN, BBVA, UBS

**Canadian Big 5:**
- RY, TD, BNS, BMO, CM

### Comparison Output

```markdown
## Peer Comparison (U.S. G-SIBs)

| Metric | JPM | Peer Median | Percentile |
|--------|-----|-------------|------------|
| CET1 Ratio | 15.7% | 13.8% | 85th ⭐ |
| ROTCE | 17.2% | 15.1% | 80th ⭐ |
| NIM | 2.48% | 2.35% | 65th |
| Efficiency | 57% | 62% | 75th ⭐ |
| NPL Ratio | 0.8% | 1.1% | 70th ⭐ |

**Interpretation:** JPM ranks in top quartile for capital strength, profitability, and credit quality.
```

---

## ⏱️ Total Implementation Time

**MVP (Core Functionality):**
- Pydantic model: 30 min
- LLM extraction agent: 1 hour
- Simple calculations: 1 hour
- Integration: 30 min
- **Total: 3 hours**

**Optional Enhancements:**
- Peer comparison database: +2 hours
- Banking-specific visualizations: +2 hours
- Trend analysis (multi-period): +1 hour

---

## 🧪 Testing Banks

### U.S. Banks (Easy - Good Disclosure)
1. **JPMorgan (JPM)** - Most comprehensive disclosure
2. **Bank of America (BAC)** - G-SIB
3. **U.S. Bancorp (USB)** - Large regional (simpler)
4. **PNC (PNC)** - Regional

### International Banks (Moderate - May Need Adjustments)
1. **HSBC (HSBC)** - UK, good English disclosure
2. **Royal Bank of Canada (RY)** - Canadian
3. **Toronto-Dominion (TD)** - Canadian
4. **Barclays (BCS)** - UK

**International Challenges:**
- Different regulatory frameworks (EU CRD, Canadian OSFI)
- May use different terminology
- Some file 20-F instead of 10-K
- May need currency conversion

**Solution:** LLM is flexible enough to handle varied formats

---

## 💰 Cost Estimate

**Per-Bank Analysis:**
- LLM extraction: ~$0.01 (small section of 10-K)
- Calculations: $0 (simple math)
- **Total: ~$0.01 per bank**

**For 50 banks (full peer database):**
- One-time cost: ~$0.50
- Monthly updates: ~$0.50

---

## 🚀 Next Steps

**Want me to implement the MVP (3 hours)?**

I can:
1. Create the Pydantic model
2. Write the extraction agent
3. Add simple calculations
4. Integrate into manager
5. Test with JPM, BAC, USB

Then you'll have:
- ✅ All regulatory capital ratios (CET1, Tier 1, Total, Leverage)
- ✅ Liquidity ratios (LCR, NSFR)
- ✅ Profitability ratios (NIM, ROTCE, Efficiency)
- ✅ Credit quality ratios (NPL, Coverage, Charge-offs)
- ✅ Balance sheet ratios (LTD, LTA)

**Would you like me to start implementing?**

Or would you prefer to:
- Review the plan first?
- Prioritize specific ratios?
- Test manual extraction with one bank first?

Let me know and I'll get started!
