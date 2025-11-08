from pydantic import BaseModel
from datetime import datetime

from agents import Agent
from financial_research_agent.config import AgentConfig

# Generate a plan of searches to ground the financial analysis.
# For a given financial question or company, we want to search for
# recent news, official filings, analyst commentary, and other
# relevant background.
def get_planner_prompt():
    """Generate planner prompt with current date context."""
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # Determine current quarter and most recent completed quarter
    current_quarter = (current_month - 1) // 3 + 1
    # Most recent likely completed quarter (conservative estimate)
    recent_quarter = current_quarter - 1 if current_quarter > 1 else 4
    recent_quarter_year = current_year if current_quarter > 1 else current_year - 1

    return f"""You are a financial research planner. Given a request for financial analysis,
produce a set of web searches to gather the context needed. Aim for recent
headlines, earnings calls or 10-K snippets, analyst commentary and industry background.
Output between 5 and 15 search terms to query for.

IMPORTANT: Today's date is {now.strftime('%B %d, %Y')}. Focus your searches on the most recent data available.

Current time context:
- Current year: {current_year}
- Current quarter: Q{current_quarter} {current_year}
- Most recent likely completed quarter: Q{recent_quarter} {recent_quarter_year}

When searching for quarterly results, focus on Q{recent_quarter} {recent_quarter_year} or later, NOT older quarters.
When searching for annual data, focus on FY{current_year} or FY{current_year-1} (most recent fiscal year).
Use "latest", "recent", or specific recent quarters/years in your search terms."""

PROMPT = get_planner_prompt()


class FinancialSearchItem(BaseModel):
    reason: str
    """Your reasoning for why this search is relevant."""

    query: str
    """The search term to feed into a web (or file) search."""


class FinancialSearchPlan(BaseModel):
    searches: list[FinancialSearchItem]
    """A list of searches to perform."""


# Build agent kwargs, only including model_settings if not None
agent_kwargs = {
    "name": "FinancialPlannerAgent",
    "instructions": PROMPT,
    "model": AgentConfig.PLANNER_MODEL,
    "output_type": FinancialSearchPlan,
}

# Only add model_settings if it's not None (for reasoning models only)
model_settings = AgentConfig.get_model_settings(
    AgentConfig.PLANNER_MODEL,
    AgentConfig.PLANNER_REASONING_EFFORT
)
if model_settings is not None:
    agent_kwargs["model_settings"] = model_settings

planner_agent = Agent(**agent_kwargs)
