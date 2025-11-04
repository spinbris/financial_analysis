# Financial Research Agent - Quick Reference

## 🚀 Launch Web Interface

```bash
python launch_web_app.py
```

Opens at: http://localhost:7860

## ⚡ Performance Specs (GPT-5 Optimized)

| Metric | Value |
|--------|-------|
| **Analysis Time** | 3-5 minutes (first run) |
| **Cached Analysis** | 2-3 minutes (repeat company) |
| **Cost per Report** | ~$0.08 |
| **Report Length** | 3-5 pages (1500-2500 words) |
| **Reports per $20** | ~250 comprehensive reports |
| **Speed Improvement** | 70% faster than original (15 min → 3-5 min) |
| **Cost Reduction** | 47% cheaper than GPT-4o |

## 🎯 Model Configuration (GPT-5 Optimized)

| Agent | Model | Why |
|-------|-------|-----|
| **Planner** | gpt-5-nano | Simple task - fastest, cheapest |
| **Search** | gpt-5-nano | Web summarization - fastest |
| **Financial Analysis** | gpt-5 | Critical task - better than GPT-4o, 50% cheaper! |
| **Risk Analysis** | gpt-5 | Critical task - superior quality |
| **Report Writing** | gpt-5 | Critical task - improved reasoning |
| **Verification** | gpt-5 | Critical task - better accuracy |

**GPT-5 Pricing (August 2025):**
- gpt-5: $1.25/$10 per 1M tokens (50% cheaper input than gpt-4o)
- gpt-5-nano: $0.15/$1.50 per 1M tokens (cheapest option)

**No .env file needed!** GPT-5 defaults are now built-in.

## 📊 Supported Companies

✅ **Any US public company** in SEC's database (thousands!)

**Examples:**
- **Tech:** Apple, Microsoft, Google, Amazon, Meta, NVIDIA, Tesla, Adobe
- **Finance:** JPMorgan, Bank of America, Wells Fargo, Goldman Sachs
- **Retail:** Walmart, Target, Costco, Home Depot
- **Industrial:** Boeing, Caterpillar, 3M, General Electric
- **Healthcare:** Johnson & Johnson, UnitedHealth, Pfizer, Merck
- **Energy:** ExxonMobil, Chevron, ConocoPhillips
- **Consumer:** Procter & Gamble, Coca-Cola, PepsiCo, Nike

## 🔍 Example Queries

```
✓ "Analyze Tesla's Q3 2025 financial performance"
✓ "What are the key risks facing Apple?"
✓ "Compare Microsoft and Google's financial health"
✓ "Is Walmart a good investment based on recent financials?"
✓ "Analyze Boeing's profitability trends"
```

## 📈 Progress Updates & Streaming Reports

During the 3-5 minute analysis, you'll see real-time updates:

**Progress bar:**
```
[05%] Initializing SEC EDGAR connection...
[10%] Starting comprehensive financial research...
[15%] Planning search strategy... ⚡
[20%] Gathering data from web and SEC EDGAR in parallel... ⚡
[40%] Extracting financial statements (40+ line items)...
[55%] Running specialist financial analyses...
[70%] Synthesizing comprehensive research report...
[85%] Validating financial data quality...
[90%] Verifying report accuracy...
[95%] Finalizing reports...
[100%] Analysis complete! ✅
```

**🆕 Streaming reports appear as they complete:**
- **~2 min:** Financial Statements tab populates ✅
- **~3 min:** Metrics & Ratios tab populates ✅
- **~4 min:** Comprehensive Report tab populates ✅
- **~5 min:** Verification tab populates ✅

**No more waiting until the end - reports stream in real-time!**

## 📄 Report Contents

Each analysis generates 4 comprehensive reports:

### 1. Comprehensive Report (3-5 pages)
- Executive summary
- Financial performance analysis
- Risk assessment
- Investment considerations
- Key metrics and ratios
- Forward-looking commentary

### 2. Financial Statements
- Income Statement (40+ line items)
- Balance Sheet (40+ line items)
- Cash Flow Statement (40+ line items)
- Multiple periods (quarterly and annual)
- Extracted directly from SEC EDGAR filings

### 3. Financial Metrics
- Profitability ratios (Gross margin, Operating margin, Net margin, ROE, ROA)
- Liquidity ratios (Current ratio, Quick ratio, Working capital)
- Efficiency ratios (Asset turnover, Inventory turnover)
- Leverage ratios (Debt-to-equity, Interest coverage)
- Growth metrics (Revenue growth, Earnings growth)

### 4. Verification Report
- Data completeness checks
- Balance sheet equation validation
- Period-over-period consistency
- Critical line item verification
- XBRL precision confirmation

## 🛠️ Troubleshooting

### Analysis Running Slow?
**Expected:** 5-7 minutes
**If slower:** Check model configuration:
```bash
python -c "from financial_research_agent.config import AgentConfig; \
print(f'Planner: {AgentConfig.PLANNER_MODEL}'); \
print(f'Search: {AgentConfig.SEARCH_MODEL}')"
```
**Should show:** gpt-4o-mini for both

### Company Not Found?
**Error:** "No companies found matching: XYZ"
**Solution:** Try using the ticker symbol directly:
```
Instead of: "Analyze XYZ Corporation"
Try: "Analyze XYZ's latest quarterly results"
```

### Reports Not Loading?
**Check:** Output directory exists:
```bash
ls -la financial_research_agent/output/
```
**Should see:** Timestamp-named directories with .md files

### Theme Switching to Dark?
**Cause:** Browser/OS dark mode preference
**Impact:** Cosmetic only - doesn't affect functionality
**Solution:** Monitor if it happens again after performance fix

## 💾 Caching System

**Cache location:** `financial_research_agent/cache/`
**TTL:** 24 hours
**What's cached:** SEC filing data (financial statements)

### View Cache
```bash
ls -lh financial_research_agent/cache/
```

### Clear Cache
```python
from financial_research_agent.cache import FinancialDataCache
cache = FinancialDataCache()
cache.clear_expired()  # Remove expired entries
# or
cache.clear_all()  # Remove all entries
```

## 🔧 Advanced Configuration

### Create Custom .env (Optional)

```bash
cp .env.example .env
# Edit with your preferred settings
```

**Key settings:**
```bash
# Required: Your SEC EDGAR identity
SEC_EDGAR_USER_AGENT="YourApp/1.0 (your@email.com)"

# Optional: Override model selection
PLANNER_MODEL=gpt-4o-mini
SEARCH_MODEL=gpt-4o-mini
FINANCIALS_MODEL=gpt-4o

# Optional: Adjust limits
MAX_AGENT_TURNS=25
MAX_SEARCH_RETRIES=3
```

## 📊 Performance Optimizations Active

✅ **Parallel execution** - Web search + EDGAR run concurrently (saves 2-3 min)
✅ **Fast models** - gpt-4o-mini for simple tasks (10x faster)
✅ **Quality models** - gpt-4o for critical analysis (best results)
✅ **Caching** - 24-hour cache for repeat analyses (saves 2-3 min)
✅ **Progress feedback** - Real-time status updates

## 🎓 Data Quality

- **Source:** Official SEC EDGAR filings
- **Precision:** XBRL-level accuracy (exact to the penny)
- **Validation:** Balance sheet equations verified
- **Methodology:** Deterministic extraction (no LLM hallucination)
- **Coverage:** 40+ line items per financial statement
- **Periods:** Multiple quarters and annual comparisons

## 📞 Support

**Documentation:**
- [WEB_APP_GUIDE.md](WEB_APP_GUIDE.md) - Complete usage guide
- [PERFORMANCE_OPTIMIZATIONS.md](PERFORMANCE_OPTIMIZATIONS.md) - Technical details
- [COMPANY_LOOKUP_FIX.md](COMPANY_LOOKUP_FIX.md) - Company search info
- [PERFORMANCE_FIX_SUMMARY.md](PERFORMANCE_FIX_SUMMARY.md) - Latest fixes

**Files:**
- [README.md](README.md) - Project overview
- [.env.example](.env.example) - Configuration template

---

**Version:** 1.0.0
**Status:** Production Ready
**Last Updated:** 2025-11-03
**Performance:** 5-7 minutes per comprehensive analysis
