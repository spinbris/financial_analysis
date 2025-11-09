# GPT-5 with Minimal Reasoning - Fast Mode

## Discovery

GPT-5 has a `reasoning_effort` parameter that controls how much thinking the model does:

| Level | Speed | Quality | Use Case |
|-------|-------|---------|----------|
| **minimal** | ⚡⚡ Very fast | Good | Extraction, formatting, simple tasks |
| **low** | ⚡ Fast | Better | Standard tasks |
| **medium** | 🐌 Slow | Great | Default (complex tasks) |
| **high** | 🐌🐌 Very slow | Best | Maximum quality |

**Key insight:** `reasoning_effort="minimal"` makes GPT-5 competitive with GPT-4o for speed!

## Performance Comparison

From OpenAI's data:

**GPT-5 with minimal reasoning:**
- Uses **23x fewer tokens** than high reasoning
- **Much faster time-to-first-token**
- Quality score: 44 (close to GPT-4.1)

**GPT-5 with medium reasoning (default):**
- Uses 23x more tokens
- Much slower
- Quality score: 67 (close to o3)

## How to Use in Agents SDK

```python
from agents import Agent, ModelSettings
from openai.types.shared import Reasoning

agent = Agent(
    name="FastAgent",
    instructions="Your instructions",
    model="gpt-5",
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="minimal"),
        verbosity="low"
    )
)
```

## Updated Configuration Options

### Option 1: GPT-4o (Current Default) ✅ FASTEST
```bash
PLANNER_MODEL=gpt-4o-mini
SEARCH_MODEL=gpt-4o-mini
ALL_OTHERS=gpt-4o
# No reasoning parameter needed

Performance: 5-7 minutes
Cost: ~$0.15 per report
```

### Option 2: GPT-5 with Minimal Reasoning ⚡ FAST + CHEAPER
```bash
PLANNER_MODEL=gpt-5-nano
SEARCH_MODEL=gpt-5-nano
ALL_OTHERS=gpt-5
REASONING_EFFORT=minimal

Performance: 5-8 minutes (estimated)
Cost: ~$0.08 per report (50% cheaper!)
```

### Option 3: GPT-5 with Medium Reasoning 🐌 SLOW
```bash
ALL_OTHERS=gpt-5
REASONING_EFFORT=medium  # or leave unset

Performance: 15-20 minutes
Cost: ~$0.08 per report
Not recommended for this use case
```

## Implementation Status

### Configuration Added ✅
- Added `REASONING_EFFORT` config option in [config.py](financial_research_agent/config.py)
- Default: `"minimal"` for speed

### Agent Updates Needed
Need to update all agent files to use `ModelSettings` when GPT-5 is selected:

1. **planner_agent.py** - Planning
2. **search_agent.py** - Web search
3. **edgar_agent.py** - EDGAR analysis
4. **financial_metrics_agent.py** - Metrics calculation
5. **financials_agent_enhanced.py** - Financial analysis
6. **risk_agent_enhanced.py** - Risk assessment
7. **writer_agent_enhanced.py** - Report writing
8. **verifier_agent.py** - Verification

Example update needed:
```python
# OLD:
agent = Agent(
    name="MyAgent",
    model=AgentConfig.PLANNER_MODEL,
    ...
)

# NEW (when model is gpt-5*):
from agents import ModelSettings
from openai.types.shared import Reasoning

model_settings = None
if AgentConfig.PLANNER_MODEL.startswith("gpt-5"):
    model_settings = ModelSettings(
        reasoning=Reasoning(effort=AgentConfig.REASONING_EFFORT),
        verbosity="low"
    )

agent = Agent(
    name="MyAgent",
    model=AgentConfig.PLANNER_MODEL,
    model_settings=model_settings,
    ...
)
```

## Testing Plan

1. **Update config.py** ✅ Done
2. **Add helper function** to create ModelSettings
3. **Update all 8 agent files** to use helper
4. **Test with GPT-5 + minimal reasoning**
5. **Compare performance:**
   - GPT-4o: 5-7 min baseline
   - GPT-5 minimal: ? min (to be tested)
   - GPT-5 medium: 15-20 min (confirmed slow)

## Expected Outcome

With `reasoning_effort="minimal"`:
- **Speed:** Competitive with GPT-4o (5-8 min estimate)
- **Cost:** 50% cheaper ($0.08 vs $0.15)
- **Quality:** Good (score 44, similar to GPT-4.1)

This could be the optimal configuration!

## Recommendation

**Test GPT-5 with minimal reasoning before choosing:**

1. Implement `model_settings` support in agents
2. Run benchmark test:
   - GPT-4o (baseline): 5-7 min
   - GPT-5 minimal: ? min
3. If GPT-5 minimal is <8 min: **Switch to it!** (50% cost savings)
4. If GPT-5 minimal is >10 min: **Stay with GPT-4o** (speed matters)

## Files to Update

1. **[config.py](financial_research_agent/config.py)** - ✅ Added REASONING_EFFORT
2. **[.env.example](.env.example)** - Need to add REASONING_EFFORT docs
3. **All agent files** - Need to add model_settings support
4. **Helper module** - Create `get_model_settings()` function

## Next Steps

1. Create helper function for ModelSettings
2. Update planner_agent.py as proof-of-concept
3. Test single agent with GPT-5 minimal
4. If fast enough, update all agents
5. Document final performance numbers

---

**Date:** 2025-11-04
**Status:** Configuration added, agent updates needed
**Potential:** 50% cost savings if performance is acceptable
**Key Finding:** reasoning_effort="minimal" could make GPT-5 fast!
