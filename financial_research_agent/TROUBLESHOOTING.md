# Troubleshooting Guide

## EDGAR Connection Issues

### Issue: "Timed out while waiting for response to ClientRequest"

**Full error:**
```
Warning: Could not initialize EDGAR server: Timed out while waiting for response
to ClientRequest. Waited 5.0 seconds.
Continuing without EDGAR data...
```

**Cause:** First run timeout - `uvx` needs to download the `sec-edgar-mcp` package.

**Solution:** Just run again! The package is now cached and will connect quickly.

```bash
# First run - may timeout (downloading package)
python -m financial_research_agent.main_budget

# Second run - will connect successfully (package cached)
python -m financial_research_agent.main_budget
```

**What we fixed:**
- ✅ Increased timeout from 5s to 60s
- ✅ Added helpful error messages
- ✅ Agent continues without EDGAR if timeout occurs

---

### Issue: "Strict JSON schema is enabled, but the output type is not valid"

**Full error:**
```
Warning: EDGAR data gathering failed: Strict JSON schema is enabled, but the output type is not valid.
Either make the output type strict, or wrap your type with
AgentOutputSchema(YourType, strict_json_schema=False)
```

**Cause:** OpenAI's strict JSON schema mode doesn't support `dict[str, Any]` in Pydantic models.

**Solution:** Already fixed in latest code. The agents now use:
```python
from agents.agent_output import AgentOutputSchema

output_type=AgentOutputSchema(YourModel, strict_json_schema=False)
```

This applies to:
- `agents/edgar_agent.py` (key_metrics field)
- `agents/financials_agent_enhanced.py` (key_metrics field)

See [JSON_SCHEMA_FIX.md](JSON_SCHEMA_FIX.md) for technical details.

---

### Issue: "MCPServerStdio.__init__() got an unexpected keyword argument 'command'"

**Cause:** Wrong initialization syntax (old error, now fixed).

**Solution:** Already fixed in latest code. Update to latest version.

---

### Issue: "SEC_EDGAR_USER_AGENT not configured"

**Cause:** Missing or invalid User-Agent header.

**Solution:** Set your User-Agent in `.env` or `.env.budget`:

```bash
SEC_EDGAR_USER_AGENT=YourCompany/1.0 (your-email@example.com)
```

**Important:** Use a real email address. The SEC requires this for contact.

---

## API Key Issues

### Issue: "OPENAI_API_KEY not set"

**Cause:** Missing OpenAI API key.

**Solution:** Add your API key to `.env` or `.env.budget`:

```bash
OPENAI_API_KEY=sk-proj-your-key-here
```

---

## Dependency Issues

### Issue: "No module named 'dotenv'"

**Cause:** Missing `python-dotenv` package.

**Solution:**
```bash
uv pip install python-dotenv
# or
pip install python-dotenv
```

---

### Issue: "No module named 'agents'"

**Cause:** Missing `openai-agents` package.

**Solution:**
```bash
uv pip install openai-agents
# or
pip install openai-agents
```

---

## Performance Issues

### Issue: Reports taking too long

**Expected times:**
- Budget mode: 4-6 minutes
- Standard mode: 6-8 minutes
- Without EDGAR: 2-4 minutes

**If longer:**
1. Check internet connection
2. Check if EDGAR is timing out (disable if needed)
3. Reduce number of searches (edit planner)

**Quick fix - Disable EDGAR:**
```bash
# In .env.budget
ENABLE_EDGAR_INTEGRATION=false
```

---

## Cost Issues

### Issue: Running out of budget too quickly

**Check actual costs:**
https://platform.openai.com/usage

**Solutions:**
1. Use budget mode instead of standard
2. Disable EDGAR for quick queries
3. Reduce number of searches
4. Use cheaper models (already optimized in budget mode)

See [COST_GUIDE.md](COST_GUIDE.md) for detailed cost optimization.

---

## Output Issues

### Issue: No output files generated

**Check:**
1. Did the agent complete? (Check terminal output)
2. Check output directory:
   ```bash
   ls -la financial_research_agent/output/
   ```
3. Look for error messages in terminal

**Expected output location:**
```
financial_research_agent/output/YYYYMMDD_HHMMSS/
```

---

### Issue: Reports missing EDGAR data

**Possible causes:**
1. EDGAR integration disabled
2. EDGAR connection timed out
3. Query about private company (no SEC filings)
4. Non-US company (EDGAR is US only)

**Check:**
- Look for "SEC EDGAR connected" in output
- Check `02_edgar_filings.md` exists
- Review error messages during run

---

## First Run Checklist

If you're having issues on first run:

✅ **1. Check .env file exists and has:**
```bash
OPENAI_API_KEY=sk-proj-...
ENABLE_EDGAR_INTEGRATION=true
SEC_EDGAR_USER_AGENT=YourCompany/1.0 (your@email.com)
```

✅ **2. Check dependencies installed:**
```bash
pip list | grep -E "openai-agents|rich|python-dotenv"
```

✅ **3. Check uvx is available:**
```bash
uvx --version
```

✅ **4. Test EDGAR manually:**
```bash
SEC_EDGAR_USER_AGENT="Test/1.0 (test@email.com)" uvx sec-edgar-mcp
```
(Press Ctrl+C to exit)

✅ **5. Run budget mode:**
```bash
python -m financial_research_agent.main_budget
```

---

## Common Warnings (Safe to Ignore)

### "First run may take 30-60s to download"
- Normal on first EDGAR connection
- Package being downloaded by uvx
- Subsequent runs will be fast

### "Continuing without EDGAR data"
- Agent works without EDGAR (uses web search only)
- Quality slightly reduced but still functional
- Fix EDGAR connection and run again for full quality

### Spelling warnings in IDE for API keys
- IDE doesn't recognize long random strings
- Safe to ignore if keys are correct

---

## Getting Help

### Check documentation:
1. [SETUP.md](SETUP.md) - Setup instructions
2. [QUICK_START_BUDGET.md](QUICK_START_BUDGET.md) - Quick start
3. [COST_GUIDE.md](COST_GUIDE.md) - Cost optimization
4. [EDGAR_INTEGRATION_GUIDE.md](EDGAR_INTEGRATION_GUIDE.md) - EDGAR details

### Still having issues?

**For EDGAR MCP issues:**
- GitHub: https://github.com/stefanoamorelli/sec-edgar-mcp/issues
- Email: stefano@amorelli.tech

**For OpenAI Agents SDK:**
- Docs: https://platform.openai.com/docs/agents
- GitHub: https://github.com/openai/openai-agents

**For SEC API:**
- Docs: https://www.sec.gov/os/accessing-edgar-data

---

## Quick Fixes Reference

| Issue | Quick Fix |
|-------|-----------|
| EDGAR timeout | Run again (package now cached) |
| No API key | Add to `.env` or `.env.budget` |
| Missing module | `pip install <module>` |
| Too slow | Disable EDGAR temporarily |
| Too expensive | Use budget mode |
| No output | Check terminal for errors |
| Private company | EDGAR won't work (no SEC filings) |

---

## Debug Mode

For detailed error information, check the terminal output while the agent runs. All errors are logged to stdout.

To test EDGAR connection separately:
```bash
SEC_EDGAR_USER_AGENT="Test/1.0 (test@email.com)" uvx sec-edgar-mcp
```

---

## Success Indicators

You know it's working when you see:

✅ "Loaded budget configuration from: ..."
✅ "EDGAR integration enabled"
✅ "Initializing SEC EDGAR connection..."
✅ "SEC EDGAR connected"
✅ "Planning searches..."
✅ "Searching... X/Y completed"
✅ "Gathering SEC filing data..."
✅ "Drafting comprehensive report..."
✅ "Outputs saved to: ..."

If you see all of these, everything is working perfectly! 🎉
