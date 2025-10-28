from pydantic import BaseModel
from datetime import datetime

from agents import Agent

# Budget-optimized planner: requests 5-8 searches instead of 5-15
# This reduces cost by ~30% while maintaining good coverage
PROMPT = (
    "You are a financial research planner. Given a request for financial analysis, "
    "produce a set of web searches to gather the context needed. Aim for recent "
    "headlines, earnings calls or 10‑K snippets, analyst commentary, and industry background. "
    "Output between 5 and 8 search terms to query for. Focus on the most important searches only. "
    "The current datetime is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
)


class FinancialSearchItem(BaseModel):
    reason: str
    """Your reasoning for why this search is relevant."""

    query: str
    """The search term to feed into a web (or file) search."""


class FinancialSearchPlan(BaseModel):
    searches: list[FinancialSearchItem]
    """A list of searches to perform."""


planner_agent_budget = Agent(
    name="BudgetFinancialPlannerAgent",
    instructions=PROMPT,
    model="o3-mini",
    output_type=FinancialSearchPlan,
)
