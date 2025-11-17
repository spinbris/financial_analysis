# Gradio UI Fixes

## Issues Fixed

### Issue 1: Report Headers Show "800-1200 words"

**Problem:** Risk and Financial Analysis tab headers displayed "(800-1200 words)" which is no longer accurate since we made the risk report length flexible.

**Fix Applied:**

**File:** [financial_research_agent/web_app.py](financial_research_agent/web_app.py)

**Lines 1615-1621: Financial Analysis Tab Header**
```python
# BEFORE
## Specialist Financial Analysis (800-1200 words)

# AFTER
## Specialist Financial Analysis
```

**Lines 1654-1660: Risk Analysis Tab Header**
```python
# BEFORE
## Specialist Risk Assessment (800-1200 words)

# AFTER
## Specialist Risk Assessment
```

**Rationale:**
- Risk reports now have flexible length (minimum 800 words, can expand to 1500-2500+ for complex risk profiles)
- Hardcoded word count limits are misleading
- Headers should describe the content, not prescribe the length

---

### Issue 2: Stock Price Chart Shows "USD" for Non-US Stocks

**Problem:** Westpac (Australian company) stock chart showed "Price (USD)" on y-axis and "$" in statistics, but prices are actually in AUD.

**Fix Applied:**

**File:** [financial_research_agent/web_app.py](financial_research_agent/web_app.py)

**Lines 853-862: Detect Currency from Stock Info**
```python
# Get company name and currency
try:
    company_name = stock.info.get('longName', ticker)
    if not company_name or company_name == ticker:
        company_name = stock.info.get('shortName', ticker)
    # Get currency from stock info
    currency = stock.info.get('currency', 'USD')  # ← Added
except:
    company_name = ticker
    currency = 'USD'  # ← Added fallback
```

**Lines 896-900: Dynamic Y-Axis Label**
```python
# BEFORE
yaxis_title='Price (USD)',

# AFTER
yaxis_title=f'Price ({currency})',
```

**Lines 922-936: Currency-Aware Statistics**
```python
# Format statistics with proper currency symbol
currency_symbol = {
    'USD': '$',
    'AUD': 'A$',  # ← Australian Dollar
    'EUR': '€',
    'GBP': '£',
    'JPY': '¥',
    'CAD': 'C$'
}.get(currency, currency + ' ')

stats_md = f"""
### Stock Statistics ({period.upper()})

**Current Price:** {currency_symbol}{current_price:.2f}
**Change:** {currency_symbol}{change:+.2f} ({change_pct:+.2f}%)
**52-Week High:** {currency_symbol}{high_52w:.2f}
**52-Week Low:** {currency_symbol}{low_52w:.2f}
**Avg Volume:** {avg_volume:,.0f}
"""
```

**How It Works:**
1. Fetch currency from `stock.info.get('currency', 'USD')` via yfinance
2. Map currency code to appropriate symbol (e.g., AUD → A$)
3. Use dynamic currency in:
   - Y-axis label: "Price (AUD)"
   - Statistics display: "A$123.45"
4. Falls back to 'USD' if currency detection fails

**Supported Currencies:**
- USD: $ (U.S. Dollar)
- AUD: A$ (Australian Dollar)
- EUR: € (Euro)
- GBP: £ (British Pound)
- JPY: ¥ (Japanese Yen)
- CAD: C$ (Canadian Dollar)
- Others: Shows currency code (e.g., "CHF 123.45")

---

## Testing

### Test 1: Verify Header Updates
```bash
# Launch Gradio
python launch_web_app.py

# Check tabs:
# - 💡 Analysis tab should show: "Specialist Financial Analysis" (no word count)
# - ⚠️ Risks tab should show: "Specialist Risk Assessment" (no word count)
```

### Test 2: Verify Currency Detection
```bash
# Test with various international stocks:

# Australian stock (AUD)
# Stock Charts tab → Enter: WBC.AX (Westpac)
# Expected: "Price (AUD)" on y-axis, "A$" in statistics

# European stock (EUR)
# Stock Charts tab → Enter: ASML (ASML Holding)
# Expected: "Price (EUR)" on y-axis, "€" in statistics

# UK stock (GBP)
# Stock Charts tab → Enter: HSBA.L (HSBC)
# Expected: "Price (GBP)" on y-axis, "£" in statistics

# US stock (USD)
# Stock Charts tab → Enter: AAPL
# Expected: "Price (USD)" on y-axis, "$" in statistics
```

---

## Related Issues

### Banking Ratio Analysis

**User Note:** "as a bank our ratio analysis is not well suited"

**Context:**
Banks have different financial structures than typical companies:
- High leverage is normal (debt-to-equity ratios that would be concerning for non-banks)
- Different liquidity requirements (regulatory capital ratios matter more)
- Revenue recognition is different (net interest margin vs gross margin)

**Potential Future Enhancement:**
Could add industry-specific ratio interpretation in the financials agent prompt for:
- Banks (focus on Tier 1 capital, loan-to-deposit ratio, net interest margin)
- Insurance (focus on combined ratio, loss ratio, expense ratio)
- REITs (focus on FFO, NAV, occupancy rates)
- Utilities (focus on rate base growth, allowed ROE, regulatory environment)

**Current Workaround:**
The financials agent should acknowledge in its analysis when standard ratios may not apply well to the industry, as noted in the prompt (lines 191-192):
> "Be transparent: If data is limited (e.g., foreign filer), state this clearly and focus on qualitative analysis"

Could extend this to:
> "Be transparent: If standard ratios don't suit the industry (e.g., banks, insurance), acknowledge limitations and focus on industry-specific metrics"

---

## Files Changed

1. ✅ [web_app.py](financial_research_agent/web_app.py) lines 1615-1621 - Financial Analysis header
2. ✅ [web_app.py](financial_research_agent/web_app.py) lines 1654-1660 - Risk Analysis header
3. ✅ [web_app.py](financial_research_agent/web_app.py) lines 853-862 - Currency detection
4. ✅ [web_app.py](financial_research_agent/web_app.py) line 899 - Dynamic y-axis label
5. ✅ [web_app.py](financial_research_agent/web_app.py) lines 922-936 - Currency-aware statistics

---

**Fixed:** November 13, 2024
**Impact:** Better UI accuracy for international stocks and flexible-length reports
**Breaking Changes:** None
