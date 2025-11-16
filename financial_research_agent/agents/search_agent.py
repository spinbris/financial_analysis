from agents import Agent
from agents.model_settings import ModelSettings
from financial_research_agent.config import AgentConfig
from financial_research_agent.tools.multi_search import multi_search

# Given a search term, use web search to pull back a brief summary.
# Summaries should be concise but capture the main financial points.
# Now using multi-provider search with Brave (primary) and Serper (fallback).
INSTRUCTIONS = (
    "You are a research assistant specializing in financial topics. "
    "Given a search term, use web search to retrieve up‑to‑date context and "
    "produce a short summary of at most 300 words. Focus on key numbers, events, "
    "or quotes that will be useful to a financial analyst.\n\n"
    "IMPORTANT: This is a standalone report section. Do NOT include conversational "
    "phrases like 'If you want, I can...' or 'Let me know if...' or any offers to "
    "provide additional analysis. Simply present the factual information found."
)

# Build agent kwargs, only including model_settings if not None
agent_kwargs = {
    "name": "FinancialSearchAgent",
    "model": AgentConfig.SEARCH_MODEL,
    "instructions": INSTRUCTIONS,
    "tools": [multi_search],  # Multi-provider search with automatic fallback
}

# Only add model_settings if it's not None (for reasoning models only)
model_settings = AgentConfig.get_model_settings(
    AgentConfig.SEARCH_MODEL,
    AgentConfig.SEARCH_REASONING_EFFORT
)
if model_settings is not None:
    agent_kwargs["model_settings"] = model_settings

search_agent = Agent(**agent_kwargs)
