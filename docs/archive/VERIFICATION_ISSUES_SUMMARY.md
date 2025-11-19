# Verification Issues Summary & Recommended Fixes

**Generated:** November 17, 2025
**Based on:** Analysis of 10+ verification files from output folder
**Status:** All recent analyses have failed verification or have critical gaps

---

## Executive Summary

**Critical Finding:** 100% of analyzed reports (Disney, NAB, JP Morgan, Apple) failed the verification agent's institutional standards.

**Common Pattern:** The verification agent consistently identifies the same 5-6 critical gaps across all companies:

1. **Balance sheet equation not verified** (100% of reports)
2. **Missing Free Cash Flow calculation** (100% of reports)
3. **Insufficient primary source citations** (100% of reports)
4. **Incomplete comparative period data** (90% of reports)
5. **Missing segment/geographic quantification** (80% of reports)

---

## Critical Errors (Must Fix Immediately)

### 1. Balance Sheet Equation Verification ⚠️ **HIGHEST PRIORITY**

**Problem:**
- Balance sheet equation (Assets = Liabilities + Equity) cannot be verified
- `data_verification.md` consistently shows: "Could not verify balance sheet equation - missing key line items"
- Missing line items: Total Assets, Total Liabilities, Total Stockholders' Equity

**Example Error Messages:**
```
Assets: Total Assets_Current
Liabilities: None
Equity: Total Stockholders' Equity_Current
```

**Root Cause:**
The XBRL extraction in [financial_statements_agent.py](financial_research_agent/agents/financial_statements_agent.py) is not capturing the balance sheet totals correctly. The verification logic in [tools/edgartools_wrapper.py](financial_research_agent/tools/edgartools_wrapper.py) looks for specific line item names that don't match what's being extracted.

**Recommended Fix:**

**Step 1:** Update XBRL extraction logic to explicitly capture totals:
```python
# In financial_statements_agent.py or edgartools_wrapper.py
def extract_balance_sheet_totals(financials):
    """Extract explicit totals for verification."""
    totals = {
        'total_assets': None,
        'total_liabilities': None,
        'total_equity': None
    }

    # Try multiple common XBRL tag patterns
    total_assets_tags = [
        'Assets',
        'AssetsCurrent',
        'Assets_Total',
        'TotalAssets'
    ]

    total_liabilities_tags = [
        'Liabilities',
        'LiabilitiesAndStockholdersEquity',
        'TotalLiabilities'
    ]

    total_equity_tags = [
        'StockholdersEquity',
        'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
        'TotalEquity'
    ]

    # Search for tags in XBRL presentation order
    for tag in total_assets_tags:
        if tag in financials.balance_sheet:
            totals['total_assets'] = financials.balance_sheet[tag]
            break

    # Similar logic for liabilities and equity

    return totals
```

**Step 2:** Update verification logic to use these totals:
```python
# In tools/edgartools_wrapper.py or data verification logic
def verify_balance_sheet_equation(totals, tolerance=0.001):
    """Verify Assets = Liabilities + Equity within tolerance."""
    if not all([totals['total_assets'], totals['total_liabilities'], totals['total_equity']]):
        return False, "Missing balance sheet totals"

    assets = totals['total_assets']
    liabilities_equity = totals['total_liabilities'] + totals['total_equity']

    diff_pct = abs(assets - liabilities_equity) / assets

    if diff_pct <= tolerance:
        return True, f"✅ Verified: {diff_pct:.4%} difference"
    else:
        return False, f"❌ Failed: {diff_pct:.4%} difference (>{tolerance:.1%})"
```

**Step 3:** Test with known companies:
```bash
# Test extraction with Apple (known good data)
python -m financial_research_agent.main_enhanced
# Input: AAPL
# Verify balance sheet totals appear in data_verification.md
```

**Files to Modify:**
- [financial_research_agent/agents/financial_statements_agent.py](financial_research_agent/agents/financial_statements_agent.py)
- [financial_research_agent/tools/edgartools_wrapper.py](financial_research_agent/tools/edgartools_wrapper.py)
- Potentially: verification logic (may be in writer/verifier agent)

**Impact:** HIGH - This is blocking institutional use of all reports

---

### 2. Missing Revenue in Income Statement ⚠️ **CRITICAL**

**Problem:**
- Recent Disney analyses show: "Income statement missing critical item: revenue"
- Affects 20251116_130925 and 20251116_122915 outputs

**Example:**
```
Status: ❌ FAILED - Critical errors found
Critical Errors:
1. Income statement missing critical item: revenue
```

**Root Cause:**
The wrapper in [edgartools_wrapper.py](financial_research_agent/tools/edgartools_wrapper.py) lines 117 & 129 uses `endswith()` matching to find revenue concepts:
```python
'revenue': get_value('Revenues', current_date) or
           get_value('RevenueFromContractWithCustomerExcludingAssessedTax', current_date)
```

**The problem:**
1. **Segmented companies** (like Disney) don't have a single consolidated "Revenues" line item in the XBRL presentation
2. Disney shows segment breakdowns (Entertainment $42B, Sports $17B, Experiences $36B) but **no total revenue line**
3. The `get_value()` function (lines 56-61) uses `endswith()` which fails for segmented presentations

**Evidence from Disney analysis:**
```
Entertainment Segment: $42,466M
Sports Segment: $17,672M
Experiences Segment: $36,156M
Total (calculated): $96,294M
```

**Recommended Fix:**

**Option 1: Use label-based extraction** (matches edgartools best practices)
```python
# In edgartools_wrapper.py
def get_revenue_smart(df, date_col):
    """
    Extract revenue using multiple strategies for segmented vs consolidated.

    Strategy priority:
    1. Look for consolidated "Revenues" concept (level <= 3, no dimension)
    2. Look for "RevenueFromContractWithCustomer*" concepts
    3. For segmented: find segment revenues and sum them
    4. Fallback: first non-abstract item with "Revenue" in label
    """
    # Strategy 1: Direct concept match (consolidated companies)
    for concept in ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax']:
        match = df[df['concept'].str.endswith(concept) &
                   (df['level'] <= 3) &
                   (df['abstract'] == False)]
        if not match.empty:
            return match.iloc[0][date_col]

    # Strategy 2: Sum segment revenues (segmented companies like Disney)
    # Look for items with "Segment" in label and level 3-4
    segment_revenues = df[
        (df['label'].str.contains('Segment', case=False, na=False)) &
        (df['concept'].str.endswith('Revenues')) &
        (df['level'] >= 3) &
        (df['abstract'] == False) &
        (~df['label'].str.contains('Eliminations|Third Party', case=False, na=False))
    ]
    if not segment_revenues.empty:
        # Sum the segment revenues (e.g., Entertainment, Sports, Experiences)
        total = segment_revenues[date_col].sum()
        if total > 0:
            return total

    # Strategy 3: Fallback - find any Revenue concept at top level
    revenue_items = df[
        (df['concept'].str.contains('Revenue', case=False, na=False)) &
        (df['level'] <= 4) &
        (df['abstract'] == False)
    ]
    if not revenue_items.empty:
        # Return the first non-segment, non-elimination item
        for idx, row in revenue_items.iterrows():
            label = row['label'].lower()
            if not any(exclude in label for exclude in ['elimination', 'third party', 'advertising']):
                return row[date_col]

    return None
```

**Option 2: Use edgartools' Entity Facts API** (RECOMMENDED ✅ VERIFIED WORKING)

EdgarTools' `company.income_statement()` method **automatically handles segmented companies**:

```python
# SOLUTION: Use Entity Facts API instead of XBRL parsing
from edgar import Company, set_identity
set_identity("Your Name your@email.com")

company = Company("DIS")
income = company.income_statement(periods=1)  # Returns Statement object

# This automatically shows:
# │ Total Revenue                          $94,425,000,000 │
# Even though Disney's XBRL has segmented presentation!

print(income)  # Renders formatted statement with Total Revenue
```

**Why this works:**
- Entity Facts API aggregates data from SEC Company Facts endpoint
- Pre-aggregated by SEC, not from individual filing XBRL
- Automatically handles consolidated totals for segmented presentations
- Much faster than parsing XBRL (single API call)

**The wrapper should migrate from XBRL DataFrame parsing to Entity Facts API.**

**Files to Modify:**
- [financial_research_agent/tools/edgartools_wrapper.py](financial_research_agent/tools/edgartools_wrapper.py) lines 97-144
- Update `get_income_statement_data()` method
- Update `get_value()` helper function to handle segmented presentations

**Testing:**
```bash
# Test with segmented company (Disney)
python -m financial_research_agent.tools.edgartools_wrapper
# Should show DIS revenue ~$96B (sum of segments)

# Test with consolidated company (Apple)
# Should show AAPL revenue directly
```

**Impact:** CRITICAL - Revenue is the most important line item

**Related Documentation:** See [docs/edgartools_analysis.md](docs/edgartools_analysis.md) for edgartools standardized concept discussion

---

### 3. Free Cash Flow Calculation Not Shown ⚠️ **HIGH PRIORITY**

**Problem:**
Verification agent requires explicit FCF calculation: `FCF = OCF - CapEx`

All reports lack this explicit calculation with source citations.

**Verification Requirement:**
```
FCF calculation: From the 10-K/quarterly releases, extract Operating Cash Flow (OCF)
and Net Capital Expenditures (CapEx) for FY2025 and compute FCF = OCF – CapEx.
Present as: FCF = $X.XXB (OCF $Y.ZZB – CapEx $Z.ZZB = $X.XXB).
```

**Current State:**
- OCF and CapEx are extracted (in cash flow statement)
- FCF is not explicitly calculated
- No dedicated FCF section in reports

**Recommended Fix:**

**Option 1:** Add FCF calculation to financial_metrics_agent.py:
```python
# In financial_metrics_agent.py
def calculate_free_cash_flow(cash_flow_data):
    """Calculate Free Cash Flow with explicit formula."""
    ocf = cash_flow_data.get('OperatingCashFlow') or \
          cash_flow_data.get('NetCashProvidedByUsedInOperatingActivities')

    capex = cash_flow_data.get('PaymentsToAcquirePropertyPlantAndEquipment') or \
            cash_flow_data.get('CapitalExpenditures')

    if ocf and capex:
        fcf = ocf - abs(capex)  # CapEx is usually negative
        return {
            'operating_cash_flow': ocf,
            'capital_expenditures': abs(capex),
            'free_cash_flow': fcf,
            'fcf_calculation': f"FCF = OCF ${ocf/1e9:.2f}B - CapEx ${abs(capex)/1e9:.2f}B = ${fcf/1e9:.2f}B"
        }

    return None
```

**Option 2:** Add FCF section to report template in writer_agent.py:
```markdown
## Free Cash Flow Analysis

**Calculation:**
- Operating Cash Flow (OCF): ${ocf}B
- Capital Expenditures (CapEx): ${capex}B
- **Free Cash Flow (FCF) = ${fcf}B**

**Formula:** FCF = OCF - CapEx = ${ocf}B - ${capex}B = ${fcf}B

**Source:** [10-Q/10-K filing date, Accession number]
```

**Files to Modify:**
- [financial_research_agent/agents/financial_metrics_agent.py](financial_research_agent/agents/financial_metrics_agent.py)
- [financial_research_agent/agents/writer.py](financial_research_agent/agents/writer.py)
- Report template in writer agent

**Impact:** HIGH - Required for institutional investment analysis

---

## Material Gaps (Fix Next)

### 4. Primary Source Citation Standards ⚠️ **MEDIUM-HIGH**

**Problem:**
Reports reference SEC filings but lack precise citations:
- No accession numbers
- No page numbers
- No XBRL tag names
- Generic references like "2024 10-K" without specifics

**Verification Requirement:**
```
Example citation format:
"Total assets $XX.XB; total liabilities $YY.YB; total equity $ZZ.ZB
(Company FY2025 Form 10-K, filed 2025-11-13, Accession: 0001628280-25-045968, page 4)"
```

**Current State:**
- Financial data is extracted from edgartools
- Filing metadata is available but not included in reports
- No citation tracking in agent pipeline

**Recommended Fix:**

**Step 1:** Capture filing metadata in edgar_agent.py:
```python
# In edgar_agent.py
def get_filing_metadata(company, form_type):
    """Get filing metadata for citations."""
    filings = company.get_filings(form=form_type).latest(1)
    if filings:
        filing = filings[0]
        return {
            'form_type': filing.form,
            'filing_date': filing.filing_date,
            'accession_number': filing.accession_number,
            'document_url': filing.document.url
        }
    return None
```

**Step 2:** Pass metadata through agent pipeline:
```python
# In main_enhanced.py
context = {
    'ticker': ticker,
    'filing_metadata': {
        '10K': get_filing_metadata(company, '10-K'),
        '10Q': get_filing_metadata(company, '10-Q')
    },
    'financial_data': {...}
}
```

**Step 3:** Add citation formatter utility:
```python
# In financial_research_agent/utils/citations.py
def format_sec_citation(value, line_item, filing_metadata, page=None):
    """Format SEC filing citation."""
    citation = f"({filing_metadata['form_type']} filed {filing_metadata['filing_date']}, "
    citation += f"Accession: {filing_metadata['accession_number']}"
    if page:
        citation += f", page {page}"
    citation += f", line item: {line_item})"
    return citation
```

**Step 4:** Update report templates to include citations:
```markdown
**Total Assets:** $4.0 trillion (2024 Form 10-K, 12/31/2024, Accession: 0000019616-25-000123, Balance Sheet, line item 'Assets')
```

**Files to Create/Modify:**
- Create: [financial_research_agent/utils/citations.py](financial_research_agent/utils/citations.py)
- Modify: [financial_research_agent/agents/edgar.py](financial_research_agent/agents/edgar.py)
- Modify: [financial_research_agent/main_enhanced.py](financial_research_agent/main_enhanced.py)
- Modify: [financial_research_agent/agents/writer.py](financial_research_agent/agents/writer.py)

**Impact:** MEDIUM-HIGH - Required for professional/institutional use

---

### 5. Comparative Period Data Completeness ⚠️ **MEDIUM**

**Problem:**
Reports mention YoY changes but don't show prior period figures explicitly.

**Example Issue:**
- States "Q3 revenue up 13% YoY"
- Doesn't show: Q3 2024 revenue = $X.XB, Q3 2025 revenue = $Y.YB
- Can't verify calculation: ($Y.X - $X.X) / $X.X = 13%

**Verification Requirement:**
```
Provide explicit prior-period numbers and YoY calculations or ensure they
are clearly cited from primary sources. Include explicit prior-year figures
for each line item mentioned to allow calculation of YoY growth.
```

**Recommended Fix:**

**Step 1:** Extract both current and prior period in financial_statements_agent:
```python
# Already doing this! Check if data is being passed through
def extract_financial_statements(financials):
    """Extract current and prior period data."""
    return {
        'balance_sheet': {
            'current': financials.balance_sheet.current,
            'prior': financials.balance_sheet.prior
        },
        'income_statement': {
            'current': financials.income_statement.current,
            'prior': financials.income_statement.prior
        },
        'cash_flow': {
            'current': financials.cash_flow.current,
            'prior': financials.cash_flow.prior
        }
    }
```

**Step 2:** Update report template to show comparative data:
```markdown
## Revenue Analysis

| Metric | Q3 2024 | Q3 2025 | Change | YoY % |
|--------|---------|---------|--------|-------|
| Total Revenue | $85.8B | $94.0B | +$8.2B | +9.5% |
| Services | $24.2B | $27.4B | +$3.2B | +13.2% |
| Products | $61.6B | $66.6B | +$5.0B | +8.1% |

**YoY Growth Calculation:**
- Revenue: ($94.0B - $85.8B) / $85.8B = 9.5%
```

**Files to Modify:**
- [financial_research_agent/agents/financial_statements_agent.py](financial_research_agent/agents/financial_statements_agent.py) (verify prior period extraction)
- [financial_research_agent/agents/writer.py](financial_research_agent/agents/writer.py) (add comparative tables)
- [financial_research_agent/agents/financials.py](financial_research_agent/agents/financials.py) (update prompt to require comparative data)

**Impact:** MEDIUM - Important for trend analysis

---

### 6. Segment and Geographic Detail Requirements ⚠️ **MEDIUM**

**Problem:**
Reports mention segments (e.g., "CCB", "CIB", "AWM" for JP Morgan) but don't provide:
- Actual revenue figures per segment
- Margin data per segment
- Geographic breakdowns

**Verification Requirement:**
```
Provide quantified segment data with explicit figures. Include actual
revenues and margins by segment for the latest period with YoY changes,
and provide regional breakdown if discussing international growth.
```

**Current State:**
- Segment data IS available in edgartools (via `financials.segment_data`)
- Not being extracted or included in reports

**Recommended Fix:**

**Step 1:** Extract segment data in financial_statements_agent:
```python
# In financial_statements_agent.py
def extract_segment_data(financials):
    """Extract segment revenue and operating income."""
    if hasattr(financials, 'segment_data'):
        segments = []
        for segment in financials.segment_data:
            segments.append({
                'name': segment.name,
                'revenue_current': segment.revenue_current,
                'revenue_prior': segment.revenue_prior,
                'operating_income_current': segment.operating_income_current,
                'operating_income_prior': segment.operating_income_prior
            })
        return segments
    return None
```

**Step 2:** Add segment section to report:
```markdown
## Segment Performance

| Segment | Revenue (Current) | Revenue (Prior) | YoY Change | Operating Income |
|---------|-------------------|-----------------|------------|------------------|
| Consumer & Community Banking (CCB) | $XX.XB | $YY.YB | +Z.Z% | $AA.AB |
| Corporate & Investment Bank (CIB) | $XX.XB | $YY.YB | +Z.Z% | $AA.AB |
| Asset & Wealth Management (AWM) | $XX.XB | $YY.YB | +Z.Z% | $AA.AB |

**Source:** [10-Q filed DATE, Accession: XXXXX, Note X - Segment Information]
```

**Files to Modify:**
- [financial_research_agent/agents/financial_statements_agent.py](financial_research_agent/agents/financial_statements_agent.py)
- [financial_research_agent/agents/writer.py](financial_research_agent/agents/writer.py)

**Impact:** MEDIUM - Important for diversified companies

---

## Minor Issues

### 7. Calculated Metrics Verification

**Problem:**
Reports state ratios (ROE, ROTCE, margins) but don't show calculations.

**Fix:**
```markdown
**Return on Equity (ROE):**
- Net Income: $XX.XB
- Average Shareholders' Equity: $YY.YB
- ROE = Net Income / Avg Equity = $XX.X / $YY.Y = Z.Z%
```

### 8. Formatting Consistency

**Issues:**
- Inconsistent use of "B" for billions
- "Approximately $132B" vs precise figures
- Mixing "around" with exact numbers

**Fix:** Standardize formatting in writer agent prompt:
```
- Always use "B" for billions (e.g., $94.4B)
- Use exact figures from filings, not approximations
- If a range is given in source, cite it exactly
```

---

## Summary of Fixes by Priority

### Immediate (This Week)

| Priority | Issue | Files to Modify | Effort | Impact |
|----------|-------|-----------------|--------|--------|
| 1 | Balance sheet equation | financial_statements_agent.py, edgartools_wrapper.py | 4-6h | CRITICAL |
| 2 | Missing revenue | financial_statements_agent.py | 2-3h | CRITICAL |
| 3 | FCF calculation | financial_metrics_agent.py, writer.py | 3-4h | HIGH |

**Total Effort:** 9-13 hours

### Next Week

| Priority | Issue | Files to Modify | Effort | Impact |
|----------|-------|-----------------|--------|--------|
| 4 | Source citations | edgar.py, citations.py (new), writer.py | 6-8h | MED-HIGH |
| 5 | Comparative data | writer.py, financials.py | 3-4h | MEDIUM |
| 6 | Segment data | financial_statements_agent.py, writer.py | 4-6h | MEDIUM |

**Total Effort:** 13-18 hours

### Later (Formatting/Polish)

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| 7 | Metric calculations | 2-3h | LOW-MED |
| 8 | Formatting consistency | 1-2h | LOW |

---

## Testing Plan

### For Each Fix:

1. **Test with known-good company (AAPL)**
   ```bash
   python -m financial_research_agent.main_enhanced
   # Input: AAPL
   # Check data_verification.md for ✅ status
   ```

2. **Test with banking company (JPM)**
   ```bash
   # Banking companies have different XBRL structure
   python -m financial_research_agent.main_enhanced
   # Input: JPM
   ```

3. **Test with recent failure (DIS)**
   ```bash
   # Disney recently failed - verify it now passes
   python -m financial_research_agent.main_enhanced
   # Input: DIS
   ```

4. **Verify all checks pass:**
   - Balance sheet equation: ✅ < 0.1% difference
   - Critical items present: revenue, assets, liabilities, equity
   - FCF calculation: explicit formula shown
   - Citations: accession numbers present
   - Comparative data: prior period shown

### Success Criteria:

```
✅ PASSED - Data is complete and valid

Balance Sheet Verification:
✅ Assets = Liabilities + Equity (0.03% difference)
✅ Total Assets: $XXX.XB
✅ Total Liabilities: $YYY.YB
✅ Total Equity: $ZZZ.ZB

Critical Items:
✅ Revenue present
✅ FCF calculation shown
✅ Primary sources cited

Comparative Data:
✅ Prior period data present
✅ YoY calculations verified
```

---

## Implementation Roadmap

### Phase 1: Critical Fixes (Week 1)
- [ ] Fix balance sheet equation verification
- [ ] Fix missing revenue extraction
- [ ] Add explicit FCF calculation
- [ ] Test with 5 companies (AAPL, MSFT, JPM, DIS, GOOG)

### Phase 2: Material Gaps (Week 2)
- [ ] Implement SEC citation system
- [ ] Add comparative period tables
- [ ] Extract and display segment data
- [ ] Test with 3 diverse companies

### Phase 3: Polish (Week 3)
- [ ] Show metric calculations explicitly
- [ ] Standardize formatting
- [ ] Update report templates
- [ ] Final verification testing

---

## Root Cause Analysis

### Why These Issues Exist:

1. **XBRL Tag Variability**
   - Different companies use different XBRL tags
   - Current extraction is too rigid (single tag name)
   - Solution: Multi-tag fallback logic

2. **Agent Pipeline Gaps**
   - Filing metadata extracted but not passed to writer
   - Prior period data extracted but not used in reports
   - Solution: Improve context passing between agents

3. **Report Template Limitations**
   - Writer agent prompt doesn't emphasize verification requirements
   - No template sections for FCF, citations, comparative tables
   - Solution: Update writer agent prompt and template

4. **Verification Logic Mismatch**
   - Verification expects specific format/content
   - Agents don't produce that format
   - Solution: Align agent outputs with verifier expectations

---

## Related Documentation

- [CURRENT_PRIORITIES.md](CURRENT_PRIORITIES.md) - Overall development priorities
- [docs/CODE_REVIEW.md](docs/CODE_REVIEW.md) - Comprehensive code review
- [EDGAR_INTEGRATION_GUIDE.md](EDGAR_INTEGRATION_GUIDE.md) - XBRL details
- [README.md](README.md) - Project overview

---

## Questions for Review

1. Should we create a dedicated "DataQualityChecker" class or keep verification in agents?
2. Should citations be in-line or in a sources section at the end?
3. Should we fail the analysis if balance sheet doesn't balance, or just warn?
4. Should FCF be in its own section or integrated into cash flow analysis?

---

**Next Steps:**
1. Review this summary with stakeholders
2. Prioritize fixes based on impact/effort
3. Create GitHub issues for each fix (optional)
4. Begin Phase 1 implementation
5. Set up regression testing to prevent re-introduction of issues

---

**Last Updated:** November 17, 2025
**Status:** Ready for implementation
