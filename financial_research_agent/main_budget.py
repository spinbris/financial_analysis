"""
Budget-Optimized Financial Research Agent - Entry Point

This version provides the same comprehensive 3-5 page reports at ~50% lower cost:
- Cost: ~$0.20-0.25 per report (vs $0.43 standard)
- Provides ~100 reports for $20 (vs ~46 standard)
- Uses gpt-4o-mini for searches, EDGAR, and verification
- Keeps gpt-4.1 for specialist analysts and writer (quality maintained)
- Requests 5-8 searches instead of 5-15

Usage:
    python -m financial_research_agent.main_budget

Or:
    python financial_research_agent/main_budget.py
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env.budget file
env_path = Path(__file__).parent / ".env.budget"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✓ Loaded budget configuration from: {env_path}")
else:
    # Fallback to regular .env
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"✓ Loaded configuration from: {env_path}")
        print("⚠️  Note: Using standard config. For budget mode, use .env.budget")
    else:
        print("⚠️  Warning: No .env file found. Using environment variables only.")

# Verify OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("\n❌ Error: OPENAI_API_KEY not set!")
    print("Please set your OpenAI API key in the .env.budget file or environment.")
    sys.exit(1)

# Check EDGAR configuration
edgar_enabled = os.getenv("ENABLE_EDGAR_INTEGRATION", "false").lower() == "true"
if edgar_enabled:
    user_agent = os.getenv("SEC_EDGAR_USER_AGENT", "")
    if not user_agent or user_agent == "FinancialResearchAgent/1.0 (your-email@example.com)":
        print("\n⚠️  Warning: EDGAR integration is enabled but SEC_EDGAR_USER_AGENT is not properly configured.")
        print("Continuing without EDGAR integration...")
        os.environ["ENABLE_EDGAR_INTEGRATION"] = "false"
        edgar_enabled = False
    else:
        print(f"✓ EDGAR integration enabled")

# Display budget mode info
print("\n" + "=" * 70)
print("  BUDGET-OPTIMIZED FINANCIAL RESEARCH AGENT")
print("  Same Comprehensive Quality at ~50% Lower Cost")
print("=" * 70)
print()
print("Budget optimizations:")
print("  • Searches: gpt-4o-mini (17x cheaper than gpt-4.1)")
print("  • EDGAR queries: gpt-4o-mini (17x cheaper)")
print("  • Verification: gpt-4o-mini (17x cheaper)")
print("  • Search count: 5-8 searches (vs 5-15 standard)")
print()
print("Quality maintained:")
print("  ✓ Writer: Still using gpt-4.1")
print("  ✓ Specialist analysis: Still 800-1200 words each")
print("  ✓ EDGAR integration: Still enabled" if edgar_enabled else "  ✓ Report depth: Still 3-5 pages comprehensive")
print("  ✓ Report structure: Still investment-grade")
print()
print("Cost comparison:")
print("  • Standard mode: ~$0.43 per report → ~46 reports for $20")
print("  • Budget mode:   ~$0.22 per report → ~90 reports for $20")
print("  • Savings:       ~50% cost reduction")
print()
print("Example queries:")
print("  • Analyze Apple's most recent quarterly performance")
print("  • What are the key risks facing Tesla?")
print("  • Compare Microsoft and Google's financial health")
print()
print("-" * 70)
print()

# Import after environment is configured
from .manager_enhanced import EnhancedFinancialResearchManager
from .agents.planner_agent_budget import planner_agent_budget


class BudgetFinancialResearchManager(EnhancedFinancialResearchManager):
    """Budget-optimized version using fewer searches."""

    async def _plan_searches(self, query):
        """Override to use budget planner (5-8 searches instead of 5-15)."""
        from agents import Runner

        self.printer.update_item("planning", "Planning searches (budget mode: 5-8 searches)...")
        result = await Runner.run(planner_agent_budget, f"Query: {query}")
        search_plan = result.final_output

        # Save the search plan
        plan_content = "# Search Plan (Budget Mode)\n\n"
        for i, item in enumerate(search_plan.searches, 1):
            plan_content += f"## Search {i}\n\n"
            plan_content += f"**Query:** {item.query}\n\n"
            plan_content += f"**Reason:** {item.reason}\n\n"
        self._save_output("01_search_plan.md", plan_content)

        self.printer.update_item(
            "planning",
            f"Will perform {len(search_plan.searches)} searches (budget optimized)",
            is_done=True,
        )
        return search_plan


async def main() -> None:
    """Main entry point for budget-optimized financial research agent."""
    # Get query from user
    query = input("Enter your financial research query: ").strip()

    if not query:
        print("❌ No query provided. Exiting.")
        return

    print()
    print("Starting budget-optimized comprehensive research...")
    print()

    # Create and run the budget manager
    mgr = BudgetFinancialResearchManager()

    try:
        await mgr.run(query)

        print("\n" + "=" * 70)
        print("💰 Budget Mode Summary")
        print("=" * 70)
        print("Estimated cost for this report: ~$0.22")
        print("Remaining budget with $20: ~$19.78 (~89 more reports)")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\n⚠️  Research interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error during research: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
