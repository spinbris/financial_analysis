"""
RAG Synthesis Agent for synthesizing ChromaDB query results into coherent responses.

This lightweight agent is optimized for conversational Q&A over the indexed financial analyses.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from agents.agent import Agent
from agents.run import Runner
from agents.agent_output import AgentOutputSchema

# Import config to ensure .env is loaded
from financial_research_agent import config  # noqa: F401


RAG_SYNTHESIS_PROMPT = """You are a financial research assistant specializing in synthesizing
information from financial analysis documents stored in a knowledge base.

## Your Role

You will receive:
1. **User's question** - A specific question about one or more companies
2. **Relevant excerpts** - Chunks retrieved from financial analyses via semantic search
3. **Metadata** - Information about each excerpt (company ticker, analysis type, period, filing)

## Available Tools

You have access to the following tools:
- **brave_search**: Use this when knowledge base data is insufficient, stale (>30 days), or missing entirely
  - Only use for factual gaps (e.g., recent stock price, latest news, current market cap)
  - Do NOT use for questions already answered by knowledge base
  - Cite web sources clearly as: "[Source: Website Name]"

## When to Use Web Search

Use brave_search ONLY when:
1. **Knowledge base is empty** - No relevant documents found
2. **Data is very stale** - Analysis is >30 days old AND query asks for "latest", "current", "recent"
3. **Specific gaps** - KB has partial data but missing key facts (e.g., has revenue but missing stock price)

Do NOT use web search when:
- KB has comprehensive recent data (<30 days old)
- Question can be fully answered from existing excerpts
- User asks about historical data already in KB

## Your Task

Synthesize the excerpts into a clear, accurate, and well-cited answer that:

1. **Directly answers the question** - Focus on what the user asked
2. **Cites sources properly** - KB sources: `[Ticker - Analysis Type, Period]`, Web sources: `[Source: Website]`
3. **Reconciles discrepancies** - If excerpts conflict, explain why (different periods, filing types, etc.)
4. **Acknowledges limitations** - If information is incomplete or missing, state what's not available
5. **Maintains context** - Always mention the time period of data being discussed
6. **Prioritizes KB over web** - Always prefer knowledge base data; use web only to fill gaps

## Response Guidelines

### Formatting Rules:
- **NEVER use tilde (`~`) for approximations** - it causes strikethrough rendering in Markdown
- Use "approximately", "about", or "roughly" instead (e.g., "approximately $134.2B", NOT "~$134.2B")

### For Single-Company Queries:
- Keep responses **concise** (2-4 paragraphs)
- Lead with the direct answer
- **Use tables when showing trends or multiple metrics**
  - Example: Revenue/profit over multiple quarters
  - Example: Comparing multiple financial ratios
  - Tables clarify numerical data better than prose
- **Suggest visualizations when appropriate** (describe what graph would help)
  - Trends over time → Line chart (e.g., "Revenue growth over 4 quarters would be clearer as a line chart")
  - Composition/breakdown → Pie or bar chart (e.g., "Revenue by segment shown as a pie chart")
  - Comparisons → Bar chart (e.g., "Comparing margins across divisions as a bar chart")
  - Example: "📊 *Visualization suggestion: A line chart showing quarterly revenue and net income trends would illustrate the growth trajectory clearly.*"
- Follow with supporting details and context
- End with relevant caveats or additional considerations

### For Multi-Company Comparisons:
- **ALWAYS use markdown tables** when comparing metrics across companies
- Tables make numerical comparisons much clearer and easier to read
- Example format:
  ```
  | Company | Revenue | Net Income | Profit Margin |
  |---------|---------|-----------|---------------|
  | AAPL    | $85.8B  | $21.4B    | 24.9%         |
  | MSFT    | $56.2B  | $22.3B    | 39.7%         |
  ```
- **Generate visualizations for comparison data**
  - Side-by-side comparisons → Grouped bar chart
  - Performance over time → Multi-line chart
  - Market share/proportions → Pie chart
  - **When you have numeric data suitable for charts, populate the `chart_data` field**:
    - Extract numeric values from your analysis
    - Choose appropriate chart type
    - Provide clean labels in `categories` (e.g., company tickers, quarters)
    - Put ONLY numeric values in `data` (e.g., {'Gross Margin': [46.8, 69.1, 66.6]})
    - **CRITICAL**: `data` values MUST be numbers (float/int), NOT strings
    - Example: Comparing profit margins → grouped_bar with categories=['AAPL', 'MSFT', 'NVDA'] and data={'Gross Margin': [46.8, 69.1, 66.6], 'Net Margin': [27.0, 35.7, 49.7]}
    - **BAD Example**: data={'Type': ['Products', 'Services']} ❌ (strings not allowed)
    - **GOOD Example**: categories=['Products', 'Services'], data={'Revenue': [200.5, 85.2]} ✅
- Normalize for different periods if needed (note any adjustments in a footnote)
- Highlight key differences and similarities in text after the table
- Note any limitations in comparability

### Source Citation:
- **Every factual claim** should have a citation
- **Knowledge Base sources**: Use format `[TICKER - Analysis Type, Period]`
  - Example: "Apple's Q3 2024 revenue was $85.8B [AAPL - Financial Statements, Q3 FY2024]"
  - For multiple KB sources, cite all: "[AAPL - Financial Analysis, Q3 2024; AAPL - Risk Analysis, Q3 2024]"
- **Web Search sources**: Use format `[Source: Web Search, {{date}}]` or `[Source: {{Website Name}}]`
  - Example: "Apple announced $100B AI investment [Source: Web Search, 2025-01-15]"
  - If URL is notable (e.g., CNBC, Bloomberg), use: "[Source: CNBC]"
  - ALWAYS clearly distinguish web sources from KB sources

### Confidence Assessment:
- **High**: Multiple consistent sources, recent data (≤30 days), complete information
- **Medium**: Single source, or aging data (30-90 days), or partial information, or mix of KB + web sources
- **Low**: Conflicting sources, stale data (>90 days), or significant gaps, or only web sources (no KB data)

### Data Age Assessment:
- Check the relevance score and metadata to estimate data age
- If data appears to be >30 days old, include a `data_age_warning` field
- Example: "Analysis data is approximately 45 days old. More recent SEC filings may be available."
- For time-sensitive queries (e.g., "latest", "recent", "current"), be especially vigilant about data age

### Financial Data Priorities:
1. **Most authoritative**: Financial statements (balance_sheet, income_statement, cash_flow)
2. **Risk information**: Risk analyses (based on SEC Form 10-K/10-Q risk factors)
3. **Derived metrics**: Financial metrics (calculated ratios and trends)
4. **Narrative analysis**: Financial analysis, comprehensive reports
5. **Supplementary**: Web search results (web_search) - use to fill gaps or provide recent context

### Handling Edge Cases:
- **No relevant data**: "I don't have information about [topic] for [company] in my current knowledge base."
- **Outdated data**: "The most recent analysis I have is from [date]. More recent data may be available."
- **Conflicting data**: "There appears to be a discrepancy: [source A] reports X while [source B] reports Y. This may be due to [different periods/restatements/etc.]"

## Output Format

Your response should be professional, accurate, and conversational - suitable for both
financial professionals and educated investors.

Current datetime: {current_time}
"""


class ChartData(BaseModel):
    """Data for generating a chart visualization."""

    chart_type: str = Field(
        description="Type of chart: 'bar', 'grouped_bar', 'line', 'multi_line', 'pie'"
    )

    title: str = Field(
        description="Chart title"
    )

    x_label: str = Field(
        description="X-axis label"
    )

    y_label: str = Field(
        description="Y-axis label"
    )

    data: dict[str, list[float]] = Field(
        description="Chart data as {series_name: [numeric_values]}. MUST contain only numbers (float/int), NOT strings. For bar/line: single series. For grouped_bar/multi_line: multiple series. Example: {'Revenue': [100.5, 120.3, 95.7]}"
    )

    categories: list[str] = Field(
        description="X-axis category labels (e.g., company tickers, quarters, dates). These are the STRING labels for each data point. Example: ['AAPL', 'MSFT', 'GOOGL'] or ['Q1', 'Q2', 'Q3']"
    )


class RAGResponse(BaseModel):
    """Structured response from RAG synthesis agent."""

    answer: str = Field(
        description="The synthesized answer to the user's question, with proper citations"
    )

    sources_cited: list[str] = Field(
        description="List of sources cited in the answer (e.g., 'AAPL - Financial Statements, Q3 FY2024')"
    )

    confidence: str = Field(
        description="Confidence level in the answer: 'high', 'medium', or 'low'"
    )

    data_age_warning: str | None = Field(
        default=None,
        description="Warning about data age if analysis is stale (e.g., 'Data is 30 days old')"
    )

    limitations: str | None = Field(
        default=None,
        description="Any limitations, caveats, or missing information the user should be aware of"
    )

    suggested_followup: list[str] | None = Field(
        default=None,
        description="1-3 suggested follow-up questions the user might want to ask"
    )

    chart_data: ChartData | None = Field(
        default=None,
        description="Optional chart data if the query would benefit from visualization (comparisons, trends, etc.)"
    )


def create_rag_synthesis_agent(enable_web_search: bool = True) -> Agent:
    """
    Create a RAG synthesis agent configured for financial Q&A.

    Args:
        enable_web_search: Whether to enable Brave Search fallback (default: True)

    Returns:
        Agent configured with RAG synthesis prompt, fast model, and optional web search
    """
    from financial_research_agent.tools.brave_search import brave_search
    from financial_research_agent.config import AgentConfig

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Build instructions by replacing current_time placeholder
    # Don't use .format() to avoid errors with curly braces in user queries/context
    instructions = RAG_SYNTHESIS_PROMPT.replace('{current_time}', current_time)

    # Build agent configuration
    # Use WRITER_MODEL from config (gpt-5 for quality synthesis)
    # Wrap output type to disable strict JSON schema (dict types not supported in strict mode)
    agent_config = {
        "name": "RAG Synthesis Agent",
        "instructions": instructions,
        "model": AgentConfig.WRITER_MODEL,  # Use configured model (gpt-5 for OpenAI)
        "output_type": AgentOutputSchema(RAGResponse, strict_json_schema=False)
    }

    # Add model settings if applicable (for GPT-5 reasoning models)
    model_settings = AgentConfig.get_model_settings(
        AgentConfig.WRITER_MODEL,
        AgentConfig.WRITER_REASONING_EFFORT
    )
    if model_settings is not None:
        agent_config["model_settings"] = model_settings

    # Add web search tool if enabled
    if enable_web_search:
        agent_config["tools"] = [brave_search]

    return Agent(**agent_config)


def synthesize_rag_results(
    query: str,
    search_results: dict,
    max_turns: int = 3
) -> RAGResponse:
    """
    Synthesize RAG search results into a coherent answer.

    Args:
        query: The user's question
        search_results: Raw results from ChromaDB query (documents, metadatas, distances)
        max_turns: Maximum agent turns (default: 3 for quick responses)

    Returns:
        RAGResponse with synthesized answer, sources, confidence, and limitations
    """
    import asyncio

    # Format the context for the synthesis agent
    context = _format_search_results(search_results)

    # Create the agent
    agent = create_rag_synthesis_agent()

    # Build the prompt
    prompt = f"""## User's Question

{query}

## Relevant Excerpts from Knowledge Base

{context}

---

Please synthesize these excerpts into a clear, well-cited answer to the user's question.
"""

    # Run the agent - handle event loop properly for Gradio worker threads
    # Always run in a separate thread to avoid event loop conflicts
    # This works in all contexts: command-line, Gradio, Jupyter, etc.
    import concurrent.futures
    import threading

    # Check if we're in the main thread
    is_main_thread = threading.current_thread() is threading.main_thread()

    if not is_main_thread:
        # We're in a worker thread (like Gradio's AnyIO worker thread)
        # Run the agent in a separate thread with its own event loop
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(_run_agent_sync, agent, prompt, max_turns)
            result = future.result()
    else:
        # We're in the main thread - check if there's a running loop
        try:
            asyncio.get_running_loop()
            # There's a running loop, use a separate thread
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_run_agent_sync, agent, prompt, max_turns)
                result = future.result()
        except RuntimeError:
            # No running loop in main thread - safe to run directly
            result = Runner.run_sync(agent, prompt, max_turns=max_turns)

    # Extract the structured response
    return result.final_output_as(RAGResponse)


def _run_agent_sync(agent, prompt, max_turns):
    """Helper to run agent in a new event loop."""
    import asyncio

    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Run the agent using the new loop
        return Runner.run_sync(agent, prompt, max_turns=max_turns)
    finally:
        # Clean up the loop
        loop.close()
        asyncio.set_event_loop(None)


def _format_search_results(search_results: dict) -> str:
    """
    Format ChromaDB search results for the synthesis agent.

    Args:
        search_results: Dictionary with 'documents', 'metadatas', 'distances' keys

    Returns:
        Formatted string with excerpts and metadata
    """
    if not search_results or 'documents' not in search_results:
        return "No relevant excerpts found."

    documents = search_results['documents'][0] if search_results['documents'] else []
    metadatas = search_results['metadatas'][0] if search_results.get('metadatas') else []
    distances = search_results['distances'][0] if search_results.get('distances') else []

    if not documents:
        return "No relevant excerpts found."

    formatted_excerpts = []

    for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances), 1):
        # Extract metadata fields
        ticker = metadata.get('ticker', 'Unknown')
        analysis_type = metadata.get('analysis_type', 'Unknown').replace('_', ' ').title()
        period = metadata.get('period', 'Unknown')
        company = metadata.get('company', '')
        section = metadata.get('section', '')

        # Format relevance score (lower distance = higher relevance)
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        relevance_pct = max(0, (1 - distance/2) * 100)

        # Build excerpt header
        header = f"**Excerpt {i}** [{ticker}"
        if company:
            header += f" - {company}"
        header += f"]"

        # Add metadata details
        details = f"- **Source**: {analysis_type}"
        if period:
            details += f"\n- **Period**: {period}"
        if section:
            details += f"\n- **Section**: {section}"
        details += f"\n- **Relevance**: {relevance_pct:.1f}%"

        # Add the excerpt content
        excerpt_text = f"\n\n```\n{doc.strip()}\n```"

        formatted_excerpts.append(f"{header}\n{details}{excerpt_text}")

    return "\n\n---\n\n".join(formatted_excerpts)


# Convenience function for backward compatibility
def synthesize_rag_response(query: str, search_results: dict) -> RAGResponse:
    """
    Convenience wrapper for synthesize_rag_results.

    Args:
        query: User's question
        search_results: Raw ChromaDB search results

    Returns:
        RAGResponse object
    """
    return synthesize_rag_results(query, search_results)
