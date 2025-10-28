import asyncio

from .manager import FinancialResearchManager
import os
from dotenv import load_dotenv
load_dotenv(override=True  )

openai_api_key = os.getenv("OPENAI_API_KEY")
# Entrypoint for the financial bot example.
# Run this as `python -m examples.financial_research_agent.main` and enter a
# financial research query, for example:
# "Write up an analysis of Apple Inc.'s most recent quarter."
async def main() -> None:
    query = input("Enter a financial research query: ")
    mgr = FinancialResearchManager()
    await mgr.run(query)


if __name__ == "__main__":
    asyncio.run(main())
