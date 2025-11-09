# Updated Development Recommendations - November 9, 2025

**Based on**: User feedback and existing infrastructure review
**Updates**: Brave Search reuse, Australian companies, user-provided API keys, Groq integration

---

## Key Updates from Discussion

### ✅ **1. Brave Search - Already Implemented!**

**Current State**: You already have Brave Search integrated via `@function_tool` decorator
**Location**: `financial_research_agent/tools/brave_search.py`
**Cost**: $0.003/search (vs Tavily $0.01/search) - 3x cheaper!

**Recommendation**: Reuse existing Brave Search for KB enhancement

#### Implementation Plan

**Option A: Add Brave Search to KB Query Flow** (Quick - 1 day)

```python
# financial_research_agent/rag/synthesis_agent.py

from financial_research_agent.tools.brave_search import _brave_search_impl

class SynthesisAgent:
    def __init__(self, enable_web_search=False):
        self.enable_web_search = enable_web_search

    async def synthesize_with_web_context(self, query, ticker, kb_results):
        """Augment KB results with recent web search"""
        synthesis = self.synthesize_from_kb(kb_results)  # Existing KB synthesis

        if self.enable_web_search:
            # Search for recent news/context
            search_query = f"{ticker} latest news financial performance"
            web_results = await _brave_search_impl(search_query, count=5)

            # Append web context with clear attribution
            synthesis += "\n\n---\n\n"
            synthesis += "### 🌐 Recent Web Context (Last 7 Days)\n\n"
            synthesis += "⚠️ *The following information is from web sources, not SEC filings:*\n\n"
            synthesis += web_results
            synthesis += "\n\n*Sources: Web search via Brave Search API*"

        return synthesis
```

**UI Integration** (add checkbox to KB query tab):

```python
# In web_app.py, KB query section
with gr.Accordion("🔍 Advanced Search Options", open=False):
    enable_web_search = gr.Checkbox(
        label="Enhance with web search (recent news, non-SEC data)",
        value=False,
        info="Adds recent news and context from trusted sources. Sources will be clearly cited."
    )

# Update KB query handler
def query_kb_with_web(query, ticker, enable_web):
    results = self.query_knowledge_base(query, ticker)  # Existing KB query

    if enable_web:
        # Use existing Brave Search tool
        results = asyncio.run(
            self.synthesis_agent.synthesize_with_web_context(
                query, ticker, results
            )
        )

    return results
```

**Source Attribution Template**:
```markdown
## Answer from Knowledge Base

[KB synthesis here based on SEC filings]

**Sources**: SEC 10-K/10-Q filings indexed in database

---

## Recent Web Context

⚠️ **Note**: The following information is from web sources and has not been verified against SEC filings.

### News & Updates (Last 7 Days)

1. **Reuters** - [Title]
   URL: [url]
   > [Description]

2. **Bloomberg** - [Title]
   URL: [url]
   > [Description]

**Web Sources**: Brave Search API (searched: "[query]")
**Retrieved**: [timestamp]
```

**Effort**: 1 day
**Cost**: $0.003 per enhanced query (very cheap!)
**Value**: HIGH - fills knowledge gaps for recent events

---

### ✅ **2. Australian Companies (ASX-listed)**

**Your Requirement**: Access local Australian company data if US-listed

**Good News**: Many Australian companies have ADRs (American Depositary Receipts) listed in US

#### ASX Companies with US Listings

**Already Accessible** (via SEC):
| Australian Company | ASX Ticker | US Ticker | SEC Filings |
|-------------------|------------|-----------|-------------|
| BHP Group | BHP | BHP | 20-F (foreign issuer) |
| Rio Tinto | RIO | RIO | 20-F |
| CSL Limited | CSL | CSLLY | OTC/20-F |
| Westpac Banking | WBC | WBK | 20-F |
| Commonwealth Bank | CBA | CMWAY | OTC |
| Macquarie Group | MQG | MQBKY | OTC |
| Wesfarmers | WES | WFAFF | OTC |
| Woolworths | WOW | WOLWF | OTC |

**Implementation**: Add 20-F support (already recommended in DEVNOTES_RESPONSE)

```python
# In SEC filing search
SUPPORTED_FORMS = ['10-K', '10-Q', '8-K', '20-F', '6-K']  # Add 20-F, 6-K

def get_company_filings(ticker):
    """Get filings for both US and foreign companies"""
    company = Company(ticker)

    # Try 10-K/Q first (US companies)
    filings = company.get_filings(form=['10-K', '10-Q'])

    # If no 10-K found, try 20-F (foreign companies)
    if not filings:
        filings = company.get_filings(form=['20-F', '6-K'])

    return filings
```

**Australian-Specific Considerations**:

1. **IFRS vs GAAP**: 20-F filings use International Financial Reporting Standards
   - Most fields map cleanly
   - May need currency conversion (AUD → USD)
   - Fiscal year often ends June 30 (not Dec 31)

2. **Currency Handling**:
```python
def normalize_currency(amount, from_currency='AUD', to_currency='USD'):
    """Convert to USD for comparison"""
    if from_currency == to_currency:
        return amount

    # Use exchange rate at filing date
    rate = get_exchange_rate(from_currency, to_currency, filing_date)
    return amount * rate

# Note: 20-F filings typically already report in USD for convenience
```

**Effort**: 2-3 days (20-F support + IFRS parsing)
**Value**: HIGH for Australian users

---

#### Pure ASX Companies (Not US-Listed)

For companies **only** on ASX with no US listing:

**Option A**: ASX Data via Web Search (Immediate)

```python
async def get_asx_company_info(ticker_asx):
    """Get ASX company info via Brave Search"""
    # Search for annual reports
    query = f"{ticker_asx} ASX annual report financial results site:asx.com.au OR site:marketindex.com.au"
    results = await _brave_search_impl(query, count=10)

    # Parse ASX announcements (they're public)
    # ASX companies must disclose material info publicly
    return results
```

**Option B**: ASX API Integration (Future - Phase 4)

ASX provides public data feeds:
- Company announcements (free)
- Price data (free, 20-min delay)
- Historical financials (subscription required)

**Recommendation**: Use Option A (web search) for now, consider Option B if demand is high

**Effort**: 1 day (web search), 5 days (full ASX API)

---

### ✅ **3. Agents as Tools with Decorators**

**Your Question**: Do we use agents as tools? Would this apply to writer and search agents for multiple purposes?

**Current State**: Yes! You're already using `@function_tool` decorator

**How It Works**:

```python
from agents import function_tool

# This decorator converts a function into an agent-callable tool
@function_tool
async def brave_search(query: str, count: int = 10) -> str:
    """Search the web..."""
    # Implementation

# The agent can now call this like any other tool
```

**Applied to Your Agents**:

#### Current Architecture

```python
# Standalone agents (current)
planner_agent = Agent(
    name="Planner",
    instructions="...",
    tools=[brave_search, sec_filing_search]  # Tools passed explicitly
)

writer_agent = Agent(
    name="Writer",
    instructions="...",
    tools=[]  # No tools, just writes
)
```

#### Enhanced Architecture (Multi-Purpose Tools)

```python
# Make agents reusable as tools for other agents

@function_tool
async def research_company(ticker: str, aspect: str = "comprehensive") -> str:
    """
    Research a company using the full research pipeline.

    Args:
        ticker: Stock ticker symbol
        aspect: What to research ('comprehensive', 'risk', 'financials')

    Returns:
        Research report as markdown
    """
    # Run the full agent workflow
    from financial_research_agent.agents.planner_agent import plan_research
    from financial_research_agent.agents.writer_agent import write_report

    plan = await plan_research(ticker, aspect)
    report = await write_report(plan)

    return report

# Now other agents can call research_company as a tool!
comparison_agent = Agent(
    name="Comparison Analyst",
    instructions="Compare companies...",
    tools=[research_company, brave_search]  # Can research multiple companies
)
```

**Use Case Example**:

```python
# User query: "Compare MSFT vs GOOGL profitability"

comparison_agent.run(
    """
    Compare Microsoft and Google profitability.

    Tools available:
    - research_company(ticker, aspect='financials')
    - brave_search(query)
    """
)

# Agent thinks:
# 1. I need financial data for both companies
# 2. Call research_company('MSFT', 'financials')
# 3. Call research_company('GOOGL', 'financials')
# 4. Compare the results
# 5. Return synthesis
```

**Benefits**:
- ✅ **Composability**: Agents can use other agents
- ✅ **Reusability**: Same agent logic for different purposes
- ✅ **Parallelism**: Can research multiple companies at once
- ✅ **Modularity**: Each agent is a self-contained tool

**Recommendation**: Create tool-wrapped versions of key agents

```python
# financial_research_agent/tools/agent_tools.py

from agents import function_tool
from financial_research_agent.agents import planner_agent, writer_agent, risk_agent

@function_tool
async def analyze_company_comprehensive(ticker: str) -> str:
    """Full comprehensive analysis of a company"""
    # Runs full workflow
    return await run_full_analysis(ticker)

@function_tool
async def analyze_company_risk(ticker: str) -> str:
    """Risk-focused analysis of a company"""
    return await risk_agent.analyze(ticker)

@function_tool
async def compare_companies(ticker1: str, ticker2: str, metric: str = "all") -> str:
    """Compare two companies side by side"""
    # Use other tool-agents
    report1 = await analyze_company_comprehensive(ticker1)
    report2 = await analyze_company_comprehensive(ticker2)

    # Synthesize comparison
    return create_comparison_report(report1, report2, metric)
```

**Effort**: 2-3 days to refactor
**Value**: HIGH - enables multi-company analysis

---

### ✅ **4. User-Provided API Keys (Critical for Free Tier)**

**Your Requirement**: Don't pay for all LLMs, use user-provided keys, don't save them

**Perfect Approach**: Ephemeral Session Keys

#### Implementation

```python
# financial_research_agent/auth/key_manager.py

class SessionKeyManager:
    def __init__(self):
        self.session_keys = {}  # In-memory only, never persisted

    def set_session_key(self, session_id: str, provider: str, api_key: str):
        """Store API key for this session only"""
        if session_id not in self.session_keys:
            self.session_keys[session_id] = {}

        self.session_keys[session_id][provider] = api_key

        # Keys expire after 24 hours or on logout
        self.schedule_expiry(session_id, hours=24)

    def get_session_key(self, session_id: str, provider: str) -> str:
        """Retrieve key for current session"""
        return self.session_keys.get(session_id, {}).get(provider)

    def clear_session(self, session_id: str):
        """Delete all keys for this session"""
        if session_id in self.session_keys:
            # Overwrite with random data before deleting (security)
            import secrets
            for provider in self.session_keys[session_id]:
                self.session_keys[session_id][provider] = secrets.token_hex(32)

            del self.session_keys[session_id]

# Global instance (in-memory)
key_manager = SessionKeyManager()
```

#### UI Integration

```python
# In web_app.py - Add settings panel

with gr.Accordion("⚙️ API Settings (Optional)", open=False):
    gr.Markdown("""
    ### Bring Your Own API Keys

    To use this tool for free, provide your own API keys below.
    **Security**: Keys are stored in memory only and never saved to disk.
    **Privacy**: Delete keys from your provider account when done.

    [Get OpenAI Key](https://platform.openai.com/api-keys) | [Get Groq Key](https://console.groq.com/keys)
    """)

    with gr.Row():
        provider_choice = gr.Radio(
            ["OpenAI", "Groq (Recommended - Faster & Cheaper)", "Anthropic"],
            label="LLM Provider",
            value="Groq (Recommended - Faster & Cheaper)"
        )

    with gr.Row():
        api_key_input = gr.Textbox(
            label="API Key",
            type="password",
            placeholder="sk-...",
            info="Never saved - only kept in memory for this session"
        )

        save_key_btn = gr.Button("Save for This Session")

    with gr.Row():
        key_status = gr.Markdown("*No key provided - using system default (limited)*")

def save_session_key(provider, api_key, session_id):
    """Save key for this session only"""
    key_manager.set_session_key(session_id, provider.split()[0], api_key)

    return f"✅ {provider} key saved for this session. Will be deleted on logout or after 24 hours."

save_key_btn.click(
    fn=save_session_key,
    inputs=[provider_choice, api_key_input, session_id],
    outputs=[key_status]
)
```

#### Usage in Agents

```python
# When creating agent instances

def get_llm_client(session_id: str, provider: str = "openai"):
    """Get LLM client with session key or system default"""
    user_key = key_manager.get_session_key(session_id, provider)

    if user_key:
        # Use user's key
        if provider == "openai":
            return OpenAI(api_key=user_key)
        elif provider == "groq":
            return Groq(api_key=user_key)
    else:
        # Use system default (rate-limited)
        return get_default_client(provider)
```

**Security Features**:
1. ✅ Keys never written to disk
2. ✅ Keys overwritten with random data before deletion
3. ✅ Keys auto-expire after 24 hours
4. ✅ Keys deleted on logout
5. ✅ Clear user warning to delete from provider

**User Instructions**:
```markdown
## How to Delete Your API Key

After finishing your session:

1. **OpenAI**: Go to https://platform.openai.com/api-keys
   - Find the key you created
   - Click "Revoke" or "Delete"

2. **Groq**: Go to https://console.groq.com/keys
   - Find the key you created
   - Click "Delete"

3. **Why?** Even though we don't save your key, deleting it ensures
   it can't be used if your device is compromised.
```

**Effort**: 2 days
**Value**: CRITICAL - enables free tier without cost burden

---

### ✅ **5. Groq Integration (Excellent Choice!)**

**Your Link**: https://console.groq.com/docs/mcp

**Groq Advantages**:
- ✅ **10-100x faster** than OpenAI (LPU vs GPU)
- ✅ **Cheaper**: $0.10/1M tokens (vs OpenAI $1-3/1M)
- ✅ **Great models**: Llama 3.3 70B, Mixtral 8x7B
- ✅ **MCP support**: Can use Brave Search via MCP

#### Groq vs OpenAI Comparison

| Feature | OpenAI GPT-4 | Groq Llama 3.3 70B |
|---------|--------------|-------------------|
| Cost (1M input tokens) | $2.50 | $0.05 (50x cheaper!) |
| Cost (1M output tokens) | $10.00 | $0.08 (125x cheaper!) |
| Speed (tokens/sec) | ~40 | ~300 (7.5x faster!) |
| Quality | Excellent | Very Good |
| Context Window | 128k | 32k |

**For Your Use Case**:
- Financial analysis: Llama 3.3 70B is excellent
- Speed matters: Groq's LPU is perfect for real-time UI
- Cost: ~$0.50 per full analysis vs ~$5 on OpenAI

#### Implementation

```python
# financial_research_agent/llm/groq_client.py

from groq import Groq

def create_groq_agent(model="llama-3.3-70b-versatile", api_key=None):
    """Create agent using Groq"""
    client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))

    return Agent(
        name="Financial Analyst",
        model=model,  # or "mixtral-8x7b-32768" for even faster
        instructions="...",
        tools=[brave_search, sec_filing_search],
        client=client
    )
```

**Groq + MCP + Brave Search**:

According to the Groq MCP docs, you can use MCP tools directly:

```python
# Via MCP
from mcp import MCPClient

groq_agent = Agent(
    model="llama-3.3-70b-versatile",
    tools=[
        MCPTool("brave-search"),  # MCP-wrapped Brave Search
        MCPTool("sec-filing-retrieval")
    ]
)
```

**Recommendation**: Use Groq as primary LLM, OpenAI as fallback

```python
# Config
DEFAULT_PROVIDER = "groq"  # Change from "openai"
FALLBACK_PROVIDER = "openai"

def get_agent(session_id):
    """Get agent with Groq primary, OpenAI fallback"""
    try:
        return create_groq_agent(key_manager.get_session_key(session_id, "groq"))
    except Exception as e:
        print(f"Groq unavailable, using OpenAI: {e}")
        return create_openai_agent(key_manager.get_session_key(session_id, "openai"))
```

**Effort**: 1 day to add Groq support
**Savings**: ~90% cost reduction!

---

## Updated Implementation Roadmap

### **Phase 2A: Free Tier Enablement** (Week 1 - 3 days)

| Task | Effort | Priority |
|------|--------|----------|
| User-provided API keys (session-only) | 2 days | CRITICAL |
| Groq integration as primary LLM | 1 day | HIGH |

**Result**: Users can use tool for free with their own keys

---

### **Phase 2B: KB Enhancement** (Week 1-2 - 2 days)

| Task | Effort | Priority |
|------|--------|----------|
| Add Brave Search to KB queries (reuse existing) | 1 day | HIGH |
| Source attribution UI | 0.5 days | HIGH |
| "Enhance with web search" checkbox | 0.5 days | MEDIUM |

**Result**: KB can answer questions about recent events, non-SEC data

---

### **Phase 2C: Australian Companies** (Week 2 - 3 days)

| Task | Effort | Priority |
|------|--------|----------|
| 20-F filing support (foreign companies) | 2 days | MEDIUM |
| IFRS parsing enhancements | 1 day | LOW |
| ASX web search fallback | included | LOW |

**Result**: Can analyze Australian companies with US listings

---

### **Phase 3: Agent Composability** (Week 3 - 3 days)

| Task | Effort | Priority |
|------|--------|----------|
| Wrap agents as reusable tools | 2 days | MEDIUM |
| Multi-company comparison agent | 1 day | MEDIUM |

**Result**: Can compare companies side-by-side

---

## Revised Technology Stack

### LLM Providers (User Choice)

**Primary**: Groq (Llama 3.3 70B)
- Speed: 300+ tokens/sec
- Cost: $0.05-0.08 per 1M tokens
- Quality: Excellent for financial analysis

**Fallback**: OpenAI (GPT-4o)
- Higher quality for complex reasoning
- Slower, more expensive
- Use for edge cases only

**Future**: Anthropic Claude (if user provides key)

### Search & Data

**Web Search**: Brave Search (existing)
- Cost: $0.003/search
- Quality: Excellent, no ads
- Already integrated!

**SEC Data**: edgartools (existing)
- Free (SEC EDGAR API)
- Excellent XBRL parsing

**Price Data**: yfinance (future)
- Free (unofficial Yahoo Finance)
- Good enough for charts

### Storage

**Vectors**: ChromaDB (existing)
- Free, local
- Good for embeddings

**Metadata**: SQLite (add)
- Free, local
- Perfect for caching, users

**Future**: PostgreSQL (if scaling)

---

## Cost Analysis: Free Tier with User Keys

### User-Provided Keys (Your Preferred Model)

**Per Analysis** (comprehensive):
- Groq LLM: ~$0.01 (vs $0.50 OpenAI)
- Brave Search: ~$0.015 (5 searches)
- SEC API: Free
- **Total: ~$0.025 per analysis**

**For 100 analyses/month**: ~$2.50 (user pays via their Groq key)

### System-Provided Keys (Fallback)

**Rate Limits** (to prevent abuse):
- Free tier: 5 analyses/month per user
- System pays: ~$0.125 ($0.025 × 5)
- Affordable for demo/trial

**Pro tier** (if you add later):
- 50 analyses/month
- User provides key OR subscribes ($9.99/mo)
- Your cost: $0 (they provide key) or ~$1.25 if you provide

**Enterprise**:
- Unlimited
- Must provide own keys
- Your cost: $0

---

## Security & Privacy - Final Design

### User-Provided API Keys

**Storage**: In-memory only (never disk)
**Lifetime**: 24 hours or logout (whichever comes first)
**Deletion**: Overwritten with random data, then deleted
**User Warning**: Clear instructions to revoke key from provider

### Session Management

**Authentication**: Gradio built-in (username/password)
**Sessions**: Server-side, in-memory
**Logout**: Deletes all session data including keys

### Data Ownership

**User Analyses**: Stored locally, user can export/delete
**KB Data**: Shared (SEC filings), but access controlled
**API Keys**: Never stored, never logged

---

## Final Recommendations

### ✅ **Do Immediately** (Next 3 Days)

1. **Groq Integration** - 1 day
   - Add Groq as primary LLM
   - 90% cost savings
   - Much faster

2. **User-Provided Keys** - 2 days
   - Session-only key storage
   - Enable free tier
   - Clear deletion instructions

### ✅ **Do Next Week** (Days 4-7)

3. **Brave Search KB Enhancement** - 1 day
   - Reuse existing Brave Search
   - Add to KB queries
   - Source attribution

4. **20-F Support** - 2 days
   - Australian companies
   - Other foreign companies
   - IFRS parsing

### 📋 **Do Later** (Week 2-3)

5. **Agent Composability** - 2 days
   - Wrap agents as tools
   - Enable multi-company comparison

6. **UX Polish** - 2 days
   - Tab reorganization
   - Template fixes
   - Settings panel

### ❌ **Skip**

- ML forecasting (your decision - agreed!)
- Tavily (you have Brave)
- React migration (stay with Gradio - agreed!)
- PostgreSQL (SQLite is fine for now)

---

## Questions for You

1. **Groq Models**: Which model preference?
   - Llama 3.3 70B (best quality, $0.08/1M out)
   - Mixtral 8x7B (faster, $0.024/1M out)
   - Both (let user choose)?

2. **Free Tier Limits**: Without user key, how many analyses?
   - 5/month (conservative)
   - 10/month (generous)
   - Unlimited (risky)?

3. **Australian Companies**: Priority level?
   - High (do in Phase 2)
   - Medium (do in Phase 3)
   - Low (do later if requested)

4. **Agent Composability**: Needed now or later?
   - Phase 2 (for multi-company)
   - Phase 3 (after basics work)
   - Phase 4 (nice to have)

---

**Ready to start implementation?** Shall we begin with Groq integration + user-provided keys (3 days)?
