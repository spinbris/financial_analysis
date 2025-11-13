# Banking Sector Detection & Filtering

## Recommended Approach: Auto-Detect with Filtering

Only run banking-specific analysis when the company is actually a bank or financial institution.

---

## Implementation

### 1. Sector Detection Function

```python
# financial_research_agent/utils/sector_detection.py

from typing import Literal

IndustrySector = Literal['banking', 'investment_banking', 'insurance', 'reit', 'general']

# Curated lists of financial institutions
COMMERCIAL_BANKS = {
    # U.S. G-SIBs
    'JPM', 'BAC', 'C', 'WFC', 'BNY', 'STT',
    # Large Regional
    'USB', 'PNC', 'TFC', 'COF', 'MTB', 'KEY', 'FITB', 'HBAN', 'RF', 'CFG',
    'FHN', 'CMA', 'ZION', 'WAL', 'WTFC', 'ONB', 'UBSI', 'CBSH',
    # International
    'HSBC', 'RY', 'TD', 'BNS', 'BMO', 'CM',  # Canadian
    'BCS', 'DB', 'UBS', 'CS', 'SAN', 'BBVA',  # European
    'MUFG', 'SMFG', 'MFG',  # Japanese
}

INVESTMENT_BANKS = {
    'GS', 'MS',  # Bulge bracket
    'SCHW', 'IBKR', 'ETFC', 'AMTD',  # Brokerages
    'LAZ', 'EVR', 'PJT', 'MC', 'PIPR',  # Boutique investment banks
}

INSURANCE_COMPANIES = {
    'BRK.A', 'BRK.B', 'PGR', 'TRV', 'CB', 'AIG', 'MET', 'PRU', 'AFL', 'ALL',
    'AXP', 'HIG', 'CNA', 'WRB', 'RNR', 'L', 'LNC', 'UNM', 'TMK',
}

REITS = {
    'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'DLR', 'O', 'WELL', 'AVB', 'EQR',
    'SPG', 'VTR', 'ARE', 'ESS', 'MAA', 'UDR', 'CPT', 'FRT', 'KIM', 'REG',
}

ASSET_MANAGERS = {
    'BLK', 'BX', 'KKR', 'APO', 'ARES', 'CG', 'BAM',  # Private equity / alternatives
    'TROW', 'BEN', 'IVZ', 'STT', 'BK',  # Traditional asset managers
}

# SIC Code mappings
BANKING_SIC_CODES = {
    6020: 'Commercial Banks',
    6021: 'National Commercial Banks',
    6022: 'State Commercial Banks',
    6029: 'Commercial Banks, NEC',
    6035: 'Savings Institution, Federally Chartered',
    6036: 'Savings Institutions, Not Federally Chartered',
}

INVESTMENT_SIC_CODES = {
    6211: 'Security Brokers, Dealers & Flotation Companies',
    6282: 'Investment Advice',
}

INSURANCE_SIC_CODES = {
    6311: 'Life Insurance',
    6321: 'Accident & Health Insurance',
    6331: 'Fire, Marine & Casualty Insurance',
    6351: 'Surety Insurance',
    6361: 'Title Insurance',
    6371: 'Pension, Health & Welfare Funds',
    6411: 'Insurance Agents, Brokers & Service',
}

REIT_SIC_CODES = {
    6798: 'Real Estate Investment Trusts',
}


def detect_industry_sector(ticker: str, sic_code: int = None) -> IndustrySector:
    """
    Detect the industry sector for a given company.

    Args:
        ticker: Stock ticker symbol
        sic_code: Optional SIC code from SEC filings

    Returns:
        Industry sector classification
    """
    ticker = ticker.upper()

    # Method 1: Ticker-based lookup (fastest, most reliable)
    if ticker in COMMERCIAL_BANKS:
        return 'banking'

    if ticker in INVESTMENT_BANKS or ticker in ASSET_MANAGERS:
        return 'investment_banking'

    if ticker in INSURANCE_COMPANIES:
        return 'insurance'

    if ticker in REITS:
        return 'reit'

    # Method 2: SIC code lookup (if provided)
    if sic_code:
        if sic_code in BANKING_SIC_CODES:
            return 'banking'

        if sic_code in INVESTMENT_SIC_CODES:
            return 'investment_banking'

        if sic_code in INSURANCE_SIC_CODES:
            return 'insurance'

        if sic_code in REIT_SIC_CODES:
            return 'reit'

    # Default: general company
    return 'general'


def should_analyze_banking_ratios(sector: IndustrySector) -> bool:
    """Check if banking ratios analysis should be run."""
    return sector == 'banking'


def should_analyze_investment_metrics(sector: IndustrySector) -> bool:
    """Check if investment banking metrics should be run."""
    return sector == 'investment_banking'


def get_peer_group(ticker: str, sector: IndustrySector) -> str:
    """
    Get peer group classification for benchmarking.

    Returns peer group name for comparison purposes.
    """
    if sector == 'banking':
        # U.S. G-SIBs
        if ticker in {'JPM', 'BAC', 'C', 'WFC', 'GS', 'MS', 'BNY', 'STT'}:
            return 'U.S. G-SIB'

        # Large Regional
        if ticker in {'USB', 'PNC', 'TFC', 'COF', 'MTB', 'KEY', 'FITB'}:
            return 'Large Regional Bank'

        # Canadian Big 5
        if ticker in {'RY', 'TD', 'BNS', 'BMO', 'CM'}:
            return 'Canadian Big 5'

        # European
        if ticker in {'HSBC', 'BCS', 'DB', 'UBS', 'SAN', 'BBVA'}:
            return 'European G-SIB'

        return 'Regional Bank'

    if sector == 'investment_banking':
        if ticker in {'GS', 'MS'}:
            return 'Bulge Bracket Investment Bank'

        if ticker in {'BLK', 'BX', 'KKR', 'APO'}:
            return 'Alternative Asset Manager'

        return 'Investment Management'

    return 'General'
```

---

### 2. Integration into Manager

```python
# In manager_enhanced.py

from .utils.sector_detection import detect_industry_sector, should_analyze_banking_ratios

async def run_analysis(self, query: str):
    """Main analysis workflow with sector detection."""

    # Extract ticker from query
    ticker = self._extract_ticker(query)  # You already have this

    # Detect sector early
    sector = detect_industry_sector(ticker)
    self.sector = sector  # Store for later use

    logger.info(f"Detected sector: {sector} for {ticker}")

    # ... normal analysis flow ...

    # After financial statements/metrics extraction:
    if should_analyze_banking_ratios(sector):
        logger.info("Company is a bank - running banking-specific analysis")
        self._report_progress(0.65, "Extracting banking regulatory ratios...")

        banking_ratios = await self._extract_banking_ratios(ticker)

        if banking_ratios:
            self._save_output("09_banking_regulatory_ratios.md",
                            self._format_banking_ratios(banking_ratios))
    else:
        logger.info(f"Company is not a bank (sector: {sector}) - skipping banking analysis")

    # Continue with rest of analysis...
```

---

### 3. Conditional UI Display in Gradio

```python
# In web_app.py

def load_analysis(self, dir_path: Path):
    """Load analysis with conditional banking tab."""

    # ... load standard reports ...

    # Check if banking ratios file exists
    banking_ratios_path = dir_path / "09_banking_regulatory_ratios.md"
    show_banking_tab = banking_ratios_path.exists()

    # Load banking ratios if available
    banking_ratios_content = ""
    if show_banking_tab:
        banking_ratios_content = banking_ratios_path.read_text()

    return {
        'financial_analysis': financial_analysis_md,
        'risk_analysis': risk_analysis_md,
        'banking_ratios': banking_ratios_content,
        'show_banking_tab': show_banking_tab,  # Control visibility
        # ... other outputs ...
    }


# In Gradio interface definition
with gr.Tab("🏦 Banking Ratios", id=6, visible=False) as banking_tab:
    gr.Markdown(
        """
        ## Banking Regulatory Ratios
        *Basel III capital ratios, liquidity metrics, and banking-specific analysis*
        """
    )

    banking_ratios_output = gr.Markdown(elem_classes=["report-content"])

    # ... banking charts ...

# Update visibility based on loaded analysis
# This updates when analysis is loaded or completed
banking_tab.visible = show_banking_tab
```

---

### 4. Example Outputs

**For Apple (AAPL) - General Company:**
```
Analysis Results:
✅ 00_query.md
✅ 03_financial_statements.md
✅ 04_financial_metrics.md
✅ 05_financial_analysis.md
✅ 06_risk_analysis.md
✅ 07_comprehensive_report.md
✅ 08_verification.md
(No banking ratios - not a bank)

UI Tabs:
- 📊 Overview
- 🔍 Search Results
- 📋 Filings
- 💰 Statements
- 📈 Metrics
- 💡 Analysis
- ⚠️ Risks
- 📄 Report
(Banking Ratios tab hidden)
```

**For JPMorgan (JPM) - Bank:**
```
Analysis Results:
✅ 00_query.md
✅ 03_financial_statements.md
✅ 04_financial_metrics.md
✅ 05_financial_analysis.md
✅ 06_risk_analysis.md
✅ 07_comprehensive_report.md
✅ 08_verification.md
✅ 09_banking_regulatory_ratios.md ← NEW
✅ chart_capital_adequacy.json ← NEW (banking-specific chart)

UI Tabs:
- 📊 Overview
- 🔍 Search Results
- 📋 Filings
- 💰 Statements
- 📈 Metrics
- 💡 Analysis
- ⚠️ Risks
- 🏦 Banking Ratios ← NEW (visible only for banks)
- 📄 Report
```

---

### 5. Logging & Transparency

Make it clear to the user what's happening:

```python
# In manager progress reporting
if sector == 'banking':
    self.console.print("[cyan]ℹ️ Detected banking sector - running specialized analysis[/cyan]")
else:
    self.console.print(f"[dim]ℹ️ Sector: {sector} - using standard financial analysis[/dim]")
```

---

## Benefits of This Approach

### 1. Clean User Experience
- ✅ Apple analysis: No confusing NA banking ratios
- ✅ JPM analysis: Full banking analysis with specialized metrics
- ✅ UI adapts automatically

### 2. Cost Efficiency
- ✅ No wasted LLM calls on non-banks
- ✅ Faster analysis for general companies
- ✅ ~$0.01 saved per non-bank analysis

### 3. Accurate Analysis
- ✅ Banks get banking-specific interpretation
- ✅ Tech companies get tech-appropriate ratios
- ✅ No misleading "debt-to-equity" for banks

### 4. Future Extensibility
```python
if sector == 'insurance':
    run_insurance_analysis()  # Loss ratios, combined ratio, etc.

elif sector == 'reit':
    run_reit_analysis()  # FFO, NAV, occupancy rates, etc.

elif sector == 'banking':
    run_banking_analysis()  # Regulatory capital, NIM, etc.
```

---

## Edge Cases Handled

### Case 1: Misclassification
**Problem:** Ticker not in our list, but is actually a bank

**Solution:**
1. SIC code fallback (from Edgar)
2. User can manually trigger banking analysis
3. Update ticker list as needed

### Case 2: Hybrid Companies
**Example:** American Express (AXP) - credit card company with bank charter

**Solution:**
```python
HYBRID_FINANCIALS = {
    'AXP': 'banking',  # Has bank charter, reports capital ratios
    'DFS': 'banking',  # Discover Financial - credit card + bank
    'SYF': 'banking',  # Synchrony - store credit + bank
}
```

### Case 3: International Banks
**Example:** Deutsche Bank (DB) files 20-F, different format

**Solution:**
- LLM extraction is flexible enough to handle
- May need to adjust prompts for non-U.S. banks
- Test with major international banks (HSBC, RY, TD)

---

## Fallback: Manual Override (Optional)

If detection fails, allow manual selection:

```python
# In web_app.py advanced options
with gr.Accordion("⚙️ Advanced Options", open=False):
    force_banking_analysis = gr.Checkbox(
        label="Force banking sector analysis",
        value=False,
        info="Override auto-detection and run banking-specific analysis"
    )
```

Then in manager:
```python
if force_banking_analysis or should_analyze_banking_ratios(sector):
    banking_ratios = await self._extract_banking_ratios(ticker)
```

---

## Summary: Recommendation

**Use Option 1: Auto-Detect & Filter**

**Why:**
- ✅ Cleanest user experience
- ✅ Most cost-efficient
- ✅ Easiest to maintain
- ✅ Future-proof for other sectors

**Implementation:**
1. Add `sector_detection.py` utility (30 min)
2. Update manager to detect sector (15 min)
3. Conditionally run banking analysis (15 min)
4. Update Gradio UI for conditional tab (30 min)
5. **Total: 1.5 hours**

**Result:**
- Banks get full banking analysis
- Non-banks get standard analysis
- No cluttered NA fields
- Clear, professional output

---

## Want me to implement this?

I can add the sector detection as part of the banking ratios MVP (total time becomes 4.5 hours instead of 3 hours, but much better user experience).

**What do you think?**
