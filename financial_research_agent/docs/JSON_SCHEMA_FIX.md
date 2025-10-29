# JSON Schema Strict Mode Fix

## Issue

The EDGAR agent and financials agent were failing with this error:

```
Warning: EDGAR data gathering failed: Strict JSON schema is enabled, but the output type is not valid.
Either make the output type strict, or wrap your type with
AgentOutputSchema(YourType, strict_json_schema=False)
```

## Root Cause

OpenAI's strict JSON schema mode doesn't support `dict[str, Any]` type annotations in Pydantic models. While this type is valid Python and Pydantic, it's not supported when generating strict JSON schemas for the OpenAI API.

## Solution

Wrap the output type with `AgentOutputSchema` and set `strict_json_schema=False`:

```python
from agents.agent_output import AgentOutputSchema

# Before (causes error)
edgar_agent = Agent(
    name="EdgarFilingAgent",
    instructions=EDGAR_PROMPT,
    output_type=EdgarAnalysisSummary,  # Has dict[str, Any] field
)

# After (works correctly)
edgar_agent = Agent(
    name="EdgarFilingAgent",
    instructions=EDGAR_PROMPT,
    output_type=AgentOutputSchema(EdgarAnalysisSummary, strict_json_schema=False),
)
```

## Files Modified

1. **agents/edgar_agent.py**
   - Added `from agents.agent_output import AgentOutputSchema` import
   - Wrapped `output_type` with `AgentOutputSchema(..., strict_json_schema=False)`
   - Model contains `key_metrics: dict[str, Any]`

2. **agents/financials_agent_enhanced.py**
   - Added `from agents.agent_output import AgentOutputSchema` import
   - Wrapped `output_type` with `AgentOutputSchema(..., strict_json_schema=False)`
   - Model contains `key_metrics: dict[str, Any]`

## Why dict[str, Any] is Used

The `key_metrics` field needs to store flexible financial data:
- Strings for text values (e.g., company name, fiscal period)
- Numbers for financial figures (e.g., revenue: 119575000000)
- None/empty for unavailable data

This flexibility is essential for EDGAR data which varies significantly between filings and companies.

## Trade-offs

**Strict Mode (default):**
- ✅ Guarantees valid JSON
- ✅ Stronger type validation
- ❌ Doesn't support dict[str, Any]
- ❌ Doesn't support union types in dict values

**Non-Strict Mode (our choice):**
- ✅ Supports dict[str, Any]
- ✅ More flexible for variable SEC filing data
- ⚠️ Slightly less validation (but still validates against Pydantic model)

For financial research with variable EDGAR data, non-strict mode is the right choice.

## Testing

After this fix, the EDGAR integration should work without schema validation errors. Test with:

```bash
cd financial_research_agent
python main_enhanced.py "AAPL financial analysis"
```

The EDGAR agent will successfully retrieve and analyze SEC filings with structured output.
