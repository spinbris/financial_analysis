# Strikethrough Text Fix (Tilde Character Issue)

## Problem

Text in the comprehensive report was appearing with strikethrough formatting in Gradio, making it look crossed out. For example, in the executive summary:
- `~14%` appeared as ~~14%~~
- `~$1.9bn` appeared as ~~$1.9bn~~
- `~5 bps` appeared as ~~5 bps~~

The user couldn't copy/paste the strikethrough text successfully because it's a rendering issue.

## Root Cause

The writer agent was using the tilde character `~` to mean "approximately" (common in financial writing), but Gradio's markdown renderer interprets single tildes as strikethrough formatting in certain contexts.

**Standard Markdown Strikethrough:**
- Double tildes: `~~text~~` → ~~text~~
- Single tilde: Some renderers (including Gradio) interpret `~text` as strikethrough in certain patterns

**Example from Report (line 5):**
```markdown
3Q25 statutory NPAT was approximately A$1.9bn, up ~14% versus 1H25, with revenue up ~4% year-on-year
```

The `~14%` and `~4%` were being rendered with strikethrough.

## Fix Applied

**File:** [writer_agent_enhanced.py](financial_research_agent/agents/writer_agent_enhanced.py) lines 148-151

Added explicit instruction to the writer agent prompt:

```python
- **IMPORTANT - Markdown Formatting**: DO NOT use tilde (~) for "approximately" as it renders as strikethrough in some markdown viewers. Instead use:
  - "approximately" or "approx." (e.g., "approximately $1.9bn" not "~$1.9bn")
  - "around" (e.g., "around 14%" not "~14%")
  - "about" (e.g., "about 5 bps" not "~5 bps")
```

## Examples

### Before (Incorrect)
```markdown
CET1 (APRA) was ~12.3% at 30 June 2025
3Q25 statutory NPAT ~A$1.9bn, up ~14% versus 1H25
Credit quality remains benign: 3Q25 impairment ~5 bps
UNITE modernization spend (~A$600m in FY25)
```

**Renders as:** (strikethrough on numbers)
- CET1 (APRA) was ~~12.3%~~ at 30 June 2025
- 3Q25 statutory NPAT ~~A$1.9bn~~, up ~~14%~~ versus 1H25

### After (Correct)
```markdown
CET1 (APRA) was approximately 12.3% at 30 June 2025
3Q25 statutory NPAT approximately A$1.9bn, up around 14% versus 1H25
Credit quality remains benign: 3Q25 impairment around 5 bps
UNITE modernization spend (approximately A$600m in FY25)
```

**Renders as:** (clean text, no strikethrough)
- CET1 (APRA) was approximately 12.3% at 30 June 2025
- 3Q25 statutory NPAT approximately A$1.9bn, up around 14% versus 1H25

## Alternative Approaches Considered

### Option 1: Fix in Post-Processing ❌
Replace all `~` with "approximately" in the output before saving.

**Rejected because:**
- Might break legitimate tilde usage
- Better to fix at the source (agent behavior)
- Doesn't teach the LLM the correct pattern

### Option 2: Escape Tildes ❌
Replace `~` with `\~` to escape markdown rendering.

**Rejected because:**
- Would show backslash in output: `\~14%`
- Not professional looking
- Doesn't solve the readability issue

### Option 3: Instruct Agent (✅ Selected)
Add explicit instruction to the agent prompt to avoid tildes.

**Selected because:**
- Fixes the root cause
- Professional output
- LLM learns the correct pattern
- Most maintainable solution

## Why This Matters

1. **Readability**: Strikethrough text looks like an error or deleted content
2. **Professionalism**: Investment-grade reports shouldn't have formatting artifacts
3. **Accessibility**: Screen readers may not handle strikethrough well
4. **Copy/Paste**: Users reported they couldn't successfully copy the crossed-out text

## Testing

To verify the fix works in future reports:

```bash
# Run a new analysis
python launch_web_app.py
# Analyze any company
# Check 07_comprehensive_report.md

# Should NOT contain tildes
grep "~[0-9]" output/*/07_comprehensive_report.md
# Should return no matches

# Should contain "approximately", "around", or "about" instead
grep -E "(approximately|around|about) [0-9]" output/*/07_comprehensive_report.md
# Should return multiple matches
```

## Related Files

The writer agent prompt in the examples (lines 102, 109) also uses tildes:
```python
- You'll receive ~1000 words of detailed financial analysis
- You'll receive ~1000 words of detailed risk analysis
```

These are fine because they're in the prompt itself (instruction text), not in the output the agent generates. The key is preventing tildes in the **generated report content**.

## Impact

- ✅ Future comprehensive reports will use "approximately", "around", or "about" instead of `~`
- ✅ No strikethrough formatting artifacts in Gradio UI
- ✅ Professional, readable financial reports
- ⚠️ **Existing reports** will still have the issue (only new analyses use the updated prompt)

---

**Fixed:** November 13, 2024
**Impact:** Resolves strikethrough formatting artifacts in comprehensive reports
**Breaking Changes:** None (improves readability)
