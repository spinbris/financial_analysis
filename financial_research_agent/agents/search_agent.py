from agents import Agent
from agents.model_settings import ModelSettings
from financial_research_agent.config import AgentConfig
from financial_research_agent.tools import brave_search

# Given a search term, use web search to pull back a brief summary.
# Summaries should be concise but capture the main financial points.
# Now using Brave Search API for 10x cost savings and better performance.
INSTRUCTIONS = (
    "You are a research assistant specializing in financial topics. "
    "Given a search term, use web search to retrieve up‑to‑date context and "
    "produce a short summary of at most 300 words. Focus on key numbers, events, "
    "or quotes that will be useful to a financial analyst."
)

# Build agent kwargs, only including model_settings if not None
agent_kwargs = {
    "name": "FinancialSearchAgent",
    "model": AgentConfig.SEARCH_MODEL,
    "instructions": INSTRUCTIONS,
    "tools": [brave_search],  # 10x cheaper than OpenAI WebSearchTool
}

# Only add model_settings if it's not None (for reasoning models only)
model_settings = AgentConfig.get_model_settings(
    AgentConfig.SEARCH_MODEL,
    AgentConfig.SEARCH_REASONING_EFFORT
)
if model_settings is not None:
    agent_kwargs["model_settings"] = model_settings

search_agent = Agent(**agent_kwargs)
