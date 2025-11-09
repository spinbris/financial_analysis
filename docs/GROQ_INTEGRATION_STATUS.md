# Groq Integration Status - NOT WORKING

## Final Status: ❌ NOT COMPATIBLE WITH AGENT SDK

After extensive testing and debugging, **Groq integration with the OpenAI Agent SDK is not currently possible**.

---

## Root Cause: Agent SDK Model Name Processing

### The Problem

The OpenAI Agent SDK **strips provider prefixes** from model names before sending API requests, but Groq **requires** the full provider prefix for GPT-OSS models.

**What Happens:**
1. We configure: `model="openai/gpt-oss-120b"`
2. Agent SDK strips prefix and sends: `model="gpt-oss-120b"`
3. Groq API returns: `404 - The model 'gpt-oss-120b' does not exist`

**What's Required:**
- Groq API expects: `"openai/gpt-oss-120b"` (with prefix)
- Agent SDK sends: `"gpt-oss-120b"` (without prefix)

### Evidence

```bash
# Groq's actual model IDs (from API):
$ curl -H "Authorization: Bearer $GROQ_API_KEY" https://api.groq.com/openai/v1/models
{
  "data": [
    {"id": "openai/gpt-oss-120b"},   # ← Requires prefix
    {"id": "openai/gpt-oss-20b"},
    {"id": "llama-3.3-70b-versatile"}  # ← No prefix
  ]
}

# What works directly with OpenAI client:
from openai import OpenAI
client = OpenAI(api_key="...", base_url="https://api.groq.com/openai/v1")
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",  # ✓ Works
    messages=[...]
)

# What fails with Agent SDK:
from agents import Agent, Runner
agent = Agent(model="openai/gpt-oss-120b", ...)
Runner.run_sync(agent, "...")
# Error: 404 - The model `gpt-oss-120b` does not exist
#                      ^^^^^^^^^^^^^ Prefix stripped!
```

---

## Why Groq Was Attempted

### Original Plan: Use Standard Llama Models

**Goal**: 10-100x faster + 90% cheaper than GPT-5
- Llama 3.3 70B: $0.05/$0.08 per 1M tokens
- Expected cost: ~$0.15/report vs ~$1.50 with GPT-5

**Problem**: Standard Llama models do NOT support `json_schema` (structured outputs)

```python
# These models are available but DON'T support json_schema:
- llama-3.3-70b-versatile  ❌
- llama-3.1-70b-versatile  ❌ (also decommissioned)
- llama-3.1-8b-instant     ❌
- mixtral-8x7b-32768       ❌ (decommissioned)
```

### Fallback: Try GPT-OSS Models

**Discovery**: Groq hosts OpenAI's open-source models that DO support `json_schema`:
- `openai/gpt-oss-120b` - 120B parameters, supports structured outputs
- `openai/gpt-oss-20b` - 20B parameters, supports structured outputs

**Problem**: Agent SDK strips the `"openai/"` prefix, causing 404 errors

---

## Technical Details

### Why Agent SDK Requires Structured Outputs

The Agent SDK uses `output_type` parameter to ensure agents return data in a specific format:

```python
agent = Agent(
    name="FinancialPlannerAgent",
    model="gpt-5",
    output_type=FinancialSearchPlan,  # ← Requires json_schema support
    instructions="..."
)
```

This translates to OpenAI's `json_schema` response format:

```json
{
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "FinancialSearchPlan",
      "schema": {...}
    }
  }
}
```

**Without json_schema support, the Agent SDK cannot guarantee agents return properly structured data.**

### Why Standard Llama Models Don't Support It

As of November 2025, Groq's documentation states:
- **Only specific models** support structured outputs (json_schema)
- Standard Llama models use "JSON Object Mode" instead
- JSON Object Mode returns valid JSON but **doesn't guarantee schema compliance**

See: https://console.groq.com/docs/structured-outputs#supported-models

---

## Attempted Solutions

### 1. ✅ Try GPT-OSS Models
- **Result**: Models exist and support json_schema
- **Problem**: Agent SDK strips prefix

### 2. ❌ Configure Base URL
- **Attempted**: Set `OPENAI_BASE_URL=https://api.groq.com/openai/v1`
- **Result**: URL works, but model name still stripped

### 3. ❌ Use Environment Variables
- **Attempted**: Set all config at module import time
- **Result**: Config works, but SDK still processes model names

### 4. ❌ Override Model Name
- **Attempted**: Various ways to preserve the prefix
- **Result**: Agent SDK internals always strip it

---

## Current Configuration

### Reverted to OpenAI GPT-5 (Default)

**File**: `financial_research_agent/.env`
```bash
# Groq currently NOT WORKING - Agent SDK strips "openai/" prefix
LLM_PROVIDER=openai
```

**Models** (from [config.py](financial_research_agent/config.py:68-76)):
```python
if DEFAULT_PROVIDER == "openai":
    PLANNER_MODEL = "o3-mini"          # Reasoning-optimized
    SEARCH_MODEL = "gpt-5-nano"        # Fast, cheap
    WRITER_MODEL = "gpt-5"             # Quality
    VERIFIER_MODEL = "gpt-5-nano"      # Fast
    EDGAR_MODEL = "gpt-5-nano"         # Data extraction
    FINANCIALS_MODEL = "gpt-5"         # Quality analysis
    RISK_MODEL = "gpt-5"               # Quality analysis
    METRICS_MODEL = "gpt-5"            # Complex extraction
```

**Cost**: ~$1.50 per comprehensive analysis
**Speed**: Standard OpenAI API speeds (~40 tokens/sec)

---

## Potential Future Solutions

### Option 1: Wait for Agent SDK Update

**IF** the Agent SDK adds support for provider-prefixed model names, we could re-enable Groq.

**How to Check**:
```bash
# Test if SDK preserves prefix:
from agents import Agent, Runner
agent = Agent(model="openai/gpt-oss-120b", instructions="Say hello")
Runner.run_sync(agent, "test")
# If no 404 error → SDK fixed!
```

### Option 2: Fork/Patch Agent SDK

**Modify** the SDK to preserve provider prefixes for Groq models.

**Pros**: Would enable Groq immediately
**Cons**: Maintenance burden, might break with SDK updates

### Option 3: Use Groq Without Agent SDK

**Rewrite** agents to use raw OpenAI client instead of Agent SDK.

**Pros**: Full control over API calls
**Cons**: Lose Agent SDK features (structured outputs, tool use, etc.)

### Option 4: Use Different Groq Models

**IF** Groq adds json_schema support to standard Llama models (llama-3.3-70b, etc.), we wouldn't need the `openai/` prefix.

**Check Periodically**:
```python
from groq import Groq
client = Groq(api_key="...")
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    response_format={"type": "json_schema", "json_schema": {...}}
)
# If no error → Llama models now support json_schema!
```

---

## Files Modified During Investigation

### Configuration Files
1. [financial_research_agent/config.py](financial_research_agent/config.py:51-66)
   - Added Groq model selection (lines 51-66)
   - Module-level provider setup (lines 15-23)

2. [financial_research_agent/.env](financial_research_agent/.env:1-6)
   - Added `LLM_PROVIDER=openai` (reverted from groq)
   - Added `GROQ_API_KEY` (for future use)

3. [financial_research_agent/llm_provider.py](financial_research_agent/llm_provider.py:147-201)
   - Added Groq model configurations
   - Added session-based API key manager

### Documentation Created
1. [GROQ_INTEGRATION_COMPLETE.md](GROQ_INTEGRATION_COMPLETE.md) - Original integration plan
2. [GROQ_QUALITY_TESTING_PLAN.md](GROQ_QUALITY_TESTING_PLAN.md) - Testing methodology
3. [GROQ_INTEGRATION_FIXED.md](GROQ_INTEGRATION_FIXED.md) - Attempted fix documentation
4. GROQ_INTEGRATION_STATUS.md (this file) - Final status and findings

---

## Summary for User

### What We Tried
1. ✅ Integrate Groq as fast/cheap alternative to OpenAI GPT-5
2. ✅ Configure session-based API key management
3. ✅ Set up module-level provider detection
4. ❌ Make it work with Agent SDK

### What We Learned
1. ✅ Standard Llama models don't support json_schema
2. ✅ GPT-OSS models on Groq DO support json_schema
3. ❌ Agent SDK strips provider prefixes, breaking Groq GPT-OSS models
4. ❌ No workaround currently available

### Current Status
- **Provider**: OpenAI GPT-5 (working)
- **Cost**: ~$1.50/report
- **Speed**: Standard (not 10-100x faster)
- **Groq**: Not compatible (yet)

### Next Steps
1. **Monitor** Agent SDK updates for provider prefix support
2. **Check** if Groq adds json_schema to standard Llama models
3. **Consider** forking Agent SDK if Groq support is critical
4. **Keep** Groq integration code for future re-enablement

---

## How to Re-Enable Groq (When Fixed)

```bash
# In .env file:
LLM_PROVIDER=groq  # Change from "openai"

# Test with:
python -c "
from financial_research_agent.agents.planner_agent import planner_agent
from agents import Runner
result = Runner.run_sync(planner_agent, 'Test query')
print('✓ Groq working!' if result else '✗ Still broken')
"
```

---

**Updated**: 2025-11-09
**Status**: ❌ NOT WORKING - Agent SDK incompatible with Groq provider prefixes
**Resolution**: Reverted to OpenAI GPT-5 as default provider
