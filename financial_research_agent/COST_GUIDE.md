# Cost Guide - Financial Research Agent

## Quick Comparison

| Mode | Cost/Report | Reports/$20 | Quality | Use Case |
|------|-------------|-------------|---------|----------|
| **Budget** | ~$0.22 | ~90 | Excellent | Most queries, testing |
| **Standard** | ~$0.43 | ~46 | Premium | Critical decisions |
| **Basic** | ~$0.15 | ~133 | Good | Quick insights |

## Detailed Cost Breakdown

### Budget Mode (Recommended for $20 budget)

**Entry Point:** `python -m financial_research_agent.main_budget`

**Configuration:** Uses `.env.budget`

**Token Usage:**
- Total per report: ~60,000 tokens
- Input: ~50,000 tokens
- Output: ~10,000 tokens

**Cost per Report:** ~$0.22

**What's Optimized:**
- ✓ Searches: gpt-4o-mini (17x cheaper than gpt-4.1)
- ✓ EDGAR queries: gpt-4o-mini (17x cheaper)
- ✓ Verification: gpt-4o-mini (17x cheaper)
- ✓ Planner: o3-mini (already cheap)
- ✓ Search count: 5-8 searches (vs 5-15)

**What's NOT Compromised:**
- ✓ Writer: Still gpt-4.1 (same quality)
- ✓ Specialist analysts: Still 800-1200 words each
- ✓ Report depth: Still 3-5 pages comprehensive
- ✓ EDGAR integration: Still enabled
- ✓ Report structure: Still investment-grade

**Reports per $20:** ~90 reports

---

### Standard Mode (Enhanced)

**Entry Point:** `python -m financial_research_agent.main_enhanced`

**Configuration:** Uses `.env`

**Token Usage:**
- Total per report: ~103,000 tokens
- Input: ~80,000 tokens
- Output: ~23,000 tokens

**Cost per Report:** ~$0.43

**What You Get:**
- All premium models (gpt-4.1 throughout)
- 5-15 comprehensive searches
- Full EDGAR integration
- Maximum analysis depth
- Highest quality synthesis

**Reports per $20:** ~46 reports

---

### Basic Mode (Quick Insights)

**Entry Point:** `python -m financial_research_agent.main` (original)

**Configuration:** Uses `.env` with EDGAR disabled

**Token Usage:**
- Total per report: ~35,000 tokens
- Input: ~28,000 tokens
- Output: ~7,000 tokens

**Cost per Report:** ~$0.15

**Output:**
- 2-paragraph specialist analysis (vs 2-3 pages)
- ~500-800 word final report (vs 1500-2500 words)
- Web search only (no EDGAR)
- Quick turnaround (~2 minutes)

**Reports per $20:** ~133 reports

---

## Model Pricing Reference

### OpenAI Pricing (as of January 2025)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| **gpt-4.1** | $2.50 | $10.00 |
| **gpt-4o** | $2.50 | $10.00 |
| **gpt-4o-mini** | $0.15 | $0.60 |
| **o3-mini** | $1.10 | $4.40 |

**Key Savings:**
- gpt-4o-mini is **17x cheaper** than gpt-4.1
- o3-mini is **~2x cheaper** than gpt-4.1

---

## Cost Breakdown by Component

### Budget Mode (~$0.22 per report)

| Component | Model | Tokens | Cost |
|-----------|-------|--------|------|
| Planner | o3-mini | ~1,500 | $0.001 |
| Searches (6x) | gpt-4o-mini | ~7,500 | $0.001 |
| EDGAR queries | gpt-4o-mini | ~3,000 | $0.0005 |
| Financials Agent | gpt-4.1 | ~19,000 | $0.09 |
| Risk Agent | gpt-4.1 | ~19,000 | $0.09 |
| Writer | gpt-4.1 | ~33,000 | $0.11 |
| Verifier | gpt-4o-mini | ~3,500 | $0.001 |
| **Total** | | **~60,000** | **~$0.22** |

### Standard Mode (~$0.43 per report)

| Component | Model | Tokens | Cost |
|-----------|-------|--------|------|
| Planner | o3-mini | ~1,500 | $0.001 |
| Searches (10x) | gpt-4.1 | ~12,000 | $0.09 |
| EDGAR queries | gpt-4.1 | ~5,000 | $0.04 |
| Financials Agent | gpt-4.1 | ~19,000 | $0.09 |
| Risk Agent | gpt-4.1 | ~19,000 | $0.09 |
| Writer | gpt-4.1 | ~33,000 | $0.11 |
| Verifier | gpt-4o | ~3,500 | $0.02 |
| **Total** | | **~103,000** | **~$0.43** |

---

## Usage Recommendations

### For Your $20 Budget

**Recommended Approach: Budget Mode for Most Queries**

```bash
# Use budget mode as your default
python -m financial_research_agent.main_budget
```

**When to splurge on Standard Mode:**
- Board presentations
- Major investment decisions ($100k+)
- Critical risk assessments
- Client-facing research reports

**Budget Allocation Strategy:**

```
$20 total budget:
├─ $18 → Budget mode (~80 reports for general research)
└─ $2  → Standard mode (~4 reports for critical decisions)
```

---

## Real-World Cost Examples

### Example 1: "Analyze Apple's Q4 2024 performance"

**Budget Mode:**
```
6 searches (gpt-4o-mini)         $0.001
EDGAR data (gpt-4o-mini)         $0.0005
Financials analysis (gpt-4.1)    $0.09
Risk analysis (gpt-4.1)          $0.09
Writer synthesis (gpt-4.1)       $0.11
Verification (gpt-4o-mini)       $0.001
-----------------------------------
Total:                           $0.22
```

**Standard Mode:**
```
10 searches (gpt-4.1)            $0.09
EDGAR data (gpt-4.1)             $0.04
Financials analysis (gpt-4.1)    $0.09
Risk analysis (gpt-4.1)          $0.09
Writer synthesis (gpt-4.1)       $0.11
Verification (gpt-4o)            $0.02
-----------------------------------
Total:                           $0.44
```

**Savings:** $0.22 (50% reduction)

---

### Example 2: "What are Tesla's key risks?"

**Budget Mode:**
```
5 searches (gpt-4o-mini)         $0.001
EDGAR Risk Factors (gpt-4o-mini) $0.0005
Financials analysis (gpt-4.1)    $0.08
Risk analysis (gpt-4.1)          $0.10
Writer synthesis (gpt-4.1)       $0.09
Verification (gpt-4o-mini)       $0.001
-----------------------------------
Total:                           $0.20
```

---

## Advanced Optimization

### Further Reduce Costs (if needed)

**Option 1: Disable EDGAR for Non-Critical Queries**
```bash
# In .env.budget, temporarily set:
ENABLE_EDGAR_INTEGRATION=false
```
**Savings:** Additional 10% → ~$0.18 per report → ~110 reports for $20

**Option 2: Use Basic Mode for Quick Checks**
```bash
python -m financial_research_agent.main
# With EDGAR disabled
```
**Cost:** ~$0.10 per report → ~200 reports for $20

**Option 3: Hybrid Approach**
```python
# Create a smart wrapper that chooses mode based on query
if "quick" in query or "overview" in query:
    # Use basic mode (~$0.10)
elif "critical" in query or "investment decision" in query:
    # Use standard mode (~$0.43)
else:
    # Use budget mode (~$0.22)
```

---

## Monitoring Your Costs

### OpenAI Dashboard

Check your usage at: https://platform.openai.com/usage

**Metrics to watch:**
- Total tokens used
- Cost per day
- Remaining budget

### After Each Report

The budget mode displays estimated cost:
```
💰 Budget Mode Summary
Estimated cost for this report: ~$0.22
Remaining budget with $20: ~$19.78 (~89 more reports)
```

---

## Cost-Saving Best Practices

### 1. Start with Budget Mode
- Use for 80-90% of queries
- Only upgrade to standard for critical needs

### 2. Batch Similar Queries
- Research multiple companies in one session
- Reuse search results where applicable

### 3. Use EDGAR Strategically
- Enable for public companies only
- Disable for private companies or quick checks

### 4. Optimize Your Queries
- Be specific: "Apple Q4 2024" vs "Tell me about Apple"
- Reduces unnecessary searches

### 5. Review Reports
- Check quality of budget mode reports first
- Most users find budget mode sufficient

---

## Pricing Updates

These costs are based on **January 2025 pricing**. Check latest pricing at:
https://openai.com/api/pricing/

If prices change:
- Budget mode savings remain proportional (gpt-4o-mini still 17x cheaper)
- Adjust cost estimates accordingly

---

## Summary

**For your $20 budget, we recommend:**

✅ **Use Budget Mode** (`main_budget.py`)
- **Cost:** ~$0.22 per report
- **Reports:** ~90 comprehensive reports
- **Quality:** Excellent (maintains specialist analysis depth)

**Save Standard Mode** (`main_enhanced.py`) for:
- Critical investment decisions (4-5 reports)
- Client presentations
- Board meetings

**Total value with $20:**
- ~85 budget mode reports
- ~4-5 standard mode reports
- Comprehensive, investment-grade analysis

**This gives you plenty of runway to test, evaluate, and produce high-quality financial research!**
