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

### ❌ **5. Groq Integration - NOT COMPATIBLE (On Hold)**

**Status**: Attempted but not currently working with Agent SDK

**What Happened**:
- Standard Llama models don't support `json_schema` (required by Agent SDK)
- GPT-OSS models (`openai/gpt-oss-120b`) DO support `json_schema`
- BUT: Agent SDK strips the `"openai/"` prefix, causing 404 errors
- **Result**: Reverted to OpenAI GPT-5 as default provider

See [docs/GROQ_INTEGRATION_STATUS.md](docs/GROQ_INTEGRATION_STATUS.md) for full technical details.

#### Why Groq Was Attempted (Goals)

**Original Goals**:
- 10-100x faster than OpenAI (LPU vs GPU)
- 90% cost reduction ($0.05-0.08/1M vs $1-3/1M)
- Use Llama 3.3 70B or Mixtral models

**What We Learned**:
- ✅ Groq API works fine with standard OpenAI client
- ✅ Speed and cost benefits are real
- ❌ Agent SDK requires `json_schema` for structured outputs
- ❌ Only specific Groq models support `json_schema`
- ❌ Agent SDK strips provider prefixes, breaking GPT-OSS models

#### Current Status: Reverted to OpenAI GPT-5

**Provider**: OpenAI (GPT-5, o3-mini, gpt-5-nano)
**Cost**: ~$1.50 per comprehensive analysis
**Speed**: Standard OpenAI API (~40 tokens/sec)
**Quality**: Excellent

#### Potential Future Solutions

**Option 1**: Wait for Agent SDK update to preserve provider prefixes
**Option 2**: Wait for Groq to add `json_schema` to standard Llama models
**Option 3**: Fork Agent SDK (maintenance burden)
**Option 4**: Rewrite agents without SDK (lose structured outputs)

**Recommendation**: Monitor for Agent SDK or Groq updates, stay with OpenAI for now

---

## Updated Implementation Roadmap (Post-Groq)

### **Week 1: React Integration + User-Provided Keys** (5 days)

| Task | Effort | Priority |
|------|--------|----------|
| Deploy Modal FastAPI bridge | 1 day | CRITICAL |
| Set up React frontend with API client | 1 day | CRITICAL |
| User-provided API keys (session-only, OpenAI) | 2 days | CRITICAL |
| Enable web search toggle | 1 day | HIGH |

**Result**: Users can access financial data from React UI using their own OpenAI keys

---

### **Week 2: Source-Rich UI + Polish** (5 days)

| Task | Effort | Priority |
|------|--------|----------|
| Prominent source citation display | 2 days | CRITICAL |
| Data age warnings & confidence badges | 1 day | HIGH |
| Expandable raw source metadata | 1 day | MEDIUM |
| Update Figma to match data structure | 1 day | MEDIUM |

**Result**: React UI showcases verifiable SEC EDGAR sources (competitive advantage!)

---

### **Week 3: Production Deployment** (5 days)

| Task | Effort | Priority |
|------|--------|----------|
| Deploy React to Vercel | 1 day | CRITICAL |
| Configure custom domain (analysis.sjpconsulting.com) | 0.5 days | HIGH |
| Update CORS in Modal FastAPI | 0.5 days | HIGH |
| Deploy main website (sjp-consulting-site) | 1 day | HIGH |
| End-to-end production testing | 1 day | HIGH |
| User documentation | 1 day | MEDIUM |

**Result**: Production system live at analysis.sjpconsulting.com

---

### **Phase 2 (Future): Feature Enhancements**

| Task | Effort | Priority |
|------|--------|----------|
| 20-F filing support (Australian/foreign companies) | 2 days | MEDIUM |
| Agent composability (multi-company comparison) | 2 days | MEDIUM |
| Groq integration (if/when compatible) | 1 day | LOW |

**Result**: Extended functionality based on user demand

---

## Revised Technology Stack (Post-Groq)

### LLM Providers

**Current**: OpenAI (GPT-5, o3-mini, gpt-5-nano)
- Cost: ~$1.50 per analysis
- Speed: Standard OpenAI (~40 tokens/sec)
- Quality: Excellent
- **User-provided keys**: Session-only, never stored

**Future**: Groq (if Agent SDK compatibility resolved)
- Potential 90% cost savings
- 10-100x faster
- Monitoring for SDK updates

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

## Cost Analysis: Free Tier with User Keys (Updated)

### User-Provided Keys (Recommended Model)

**Per Analysis** (comprehensive):
- OpenAI GPT-5 LLM: ~$1.50
- Brave Search: ~$0.015 (5 searches, optional)
- SEC API: Free
- **Total: ~$1.50-1.52 per analysis** (user pays via their OpenAI key)

**For 100 analyses/month**: ~$150 (user pays directly to OpenAI, not to you)

### System-Provided Keys (Fallback - Not Recommended)

**Rate Limits** (to prevent abuse):
- Free tier: 3 analyses/month per user
- System pays: ~$4.50 ($1.50 × 3)
- Only sustainable with strict rate limits

**Pro tier** (if you add subscription model):
- Option A: User provides OpenAI key → Unlimited → Your cost: $0
- Option B: $19.99/mo → 20 analyses → Your cost: $30, profit: -$10 (loss!)
- Option C: $49.99/mo → 50 analyses → Your cost: $75, profit: -$25 (loss!)

**Conclusion**: User-provided keys are CRITICAL for sustainability

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

## Final Recommendations (Revised Post-Groq)

### ✅ **Do Immediately - Week 1** (5 days)

**Focus**: Get React integration working with user-provided keys

1. **Modal FastAPI Bridge** - 1 day
   - Deploy modal_fastapi_bridge.py from docs/integration/
   - Test /api/health and /api/query endpoints

2. **React Frontend Setup** - 1 day
   - Copy react_api_integration.ts to Gradioappfrontend/src/api/
   - Create .env.local with Modal URL
   - Test connection

3. **User-Provided API Keys** - 2 days
   - Add API key input in React UI
   - Session-only storage (never disk)
   - Clear user instructions for key management

4. **Web Search Toggle** - 1 day
   - Add checkbox in React UI
   - Pass `enable_web_search` to FastAPI
   - Test Brave Search fallback

**Deliverable**: Working React app at localhost:3000 querying Modal API with user's OpenAI key

### ✅ **Do Next - Week 2** (5 days)

**Focus**: Source-rich UI that showcases verifiability

5. **Prominent Source Display** - 2 days
   - Source citations card (not footnote!)
   - Confidence badges
   - Data age warnings

6. **Expandable Source Metadata** - 1 day
   - Accordion for chunk-level details
   - Distance scores, timestamps, sections

7. **Figma Updates** - 1 day
   - Adapt Figma to match data structure
   - Add source cards, confidence badges

8. **Polish & Testing** - 1 day
   - End-to-end testing
   - Bug fixes

**Deliverable**: Beautiful source-rich UI showcasing SEC EDGAR data quality

### ✅ **Do Last - Week 3** (5 days)

**Focus**: Production deployment

9. **Deploy to Production** - 3 days
   - React to Vercel
   - Custom domain (analysis.sjpconsulting.com)
   - Main website updates

10. **Documentation & Launch** - 2 days
    - User documentation
    - Launch announcement

**Deliverable**: Live production system

### 📋 **Do Later - Phase 2** (Future)

11. **20-F Support** - Australian/foreign companies (2 days)
12. **Agent Composability** - Multi-company comparison (2 days)
13. **Groq Integration** - If/when Agent SDK compatible (1 day)

### ❌ **Skip** (As Discussed)

- ~~Groq integration~~ (not compatible with Agent SDK)
- ML forecasting (your decision)
- Tavily (you have Brave)
- Full Gradio→React migration (keep both)
- PostgreSQL (SQLite is fine)

---

## Key Decision: User-Provided Keys are CRITICAL

**With Groq unavailable**, OpenAI costs make system-provided keys unsustainable:

| Model | Per User | 100 Users | 1000 Users |
|-------|----------|-----------|------------|
| System provides keys (3 free analyses/mo) | $4.50/mo | $450/mo | $4,500/mo |
| User provides keys | $0 | $0 | $0 |

**Recommendation**: Make user-provided keys **required** (not optional) until Groq is available.

---

## Next Steps

**Ready to start Week 1?**

1. Deploy Modal FastAPI bridge (docs/integration/modal_fastapi_bridge.py)
2. Set up React frontend with API client
3. Add user API key input
4. Enable web search toggle

**Estimated time to first working demo**: 30 minutes (Modal + React connection)
**Estimated time to production**: 3 weeks
