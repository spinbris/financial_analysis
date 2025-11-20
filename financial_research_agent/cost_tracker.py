"""
Cost Tracking Module for Financial Research Agent

Tracks token usage and calculates costs per analysis based on model pricing.
Integrates with OpenAI Agent SDK to capture usage from RunResult objects.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict


# Model pricing per 1M tokens (as of Nov 2025) - Standard tier
MODEL_PRICING = {
    # O-series reasoning models
    "o3-mini": {"input": 1.10, "output": 4.40},
    "o3": {"input": 10.00, "output": 40.00},
    "o1-pro": {"input": 150.00, "output": 600.00},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 1.10, "output": 4.40},
    "o4-mini": {"input": 1.10, "output": 4.40},

    # GPT-5 family (cheaper input, expensive output)
    "gpt-5": {"input": 1.25, "output": 10.00},
    "gpt-5.1": {"input": 1.25, "output": 10.00},
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
    "gpt-5-nano": {"input": 0.05, "output": 0.40},
    "gpt-5-pro": {"input": 15.00, "output": 120.00},

    # GPT-4 family (gpt-4.1 is reasoning-optimized, more expensive input)
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4.5-preview": {"input": 75.00, "output": 150.00},

    # Legacy
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
}


@dataclass
class AgentUsage:
    """Token usage for a single agent run."""
    agent_name: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0


@dataclass
class AnalysisCostReport:
    """Complete cost report for an analysis run."""
    timestamp: str
    ticker: str
    query: str
    config_mode: str  # "standard", "budget", etc.
    agents: list = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    duration_seconds: float = 0.0

    def add_agent_usage(self, usage: AgentUsage):
        """Add agent usage to the report."""
        self.agents.append(asdict(usage))
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens
        self.total_tokens += usage.total_tokens
        self.total_cost += usage.total_cost


class CostTracker:
    """
    Tracks costs across an analysis run.

    Usage:
        tracker = CostTracker(ticker="AAPL", query="...", config_mode="budget")

        # After each agent run
        tracker.track_agent_run("planner", "o3-mini", result)
        tracker.track_agent_run("search", "gpt-4o-mini", result)
        ...

        # At the end
        report = tracker.finalize()
        tracker.save_report(output_dir)
    """

    def __init__(self, ticker: str, query: str, config_mode: str = "standard"):
        self.ticker = ticker
        self.query = query
        self.config_mode = config_mode
        self.start_time = datetime.now()
        self.report = AnalysisCostReport(
            timestamp=self.start_time.isoformat(),
            ticker=ticker,
            query=query,
            config_mode=config_mode
        )

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> tuple[float, float]:
        """Calculate cost for given token counts."""
        # Normalize model name (remove version suffixes if needed)
        model_key = model.lower()

        # Find matching pricing
        pricing = None
        for key in MODEL_PRICING:
            if key in model_key or model_key.startswith(key):
                pricing = MODEL_PRICING[key]
                break

        if not pricing:
            # Default to gpt-4o pricing if unknown
            print(f"Warning: Unknown model '{model}', using gpt-4o pricing")
            pricing = MODEL_PRICING["gpt-4o"]

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost, output_cost

    def track_agent_run(self, agent_name: str, model: str, result) -> AgentUsage:
        """
        Track token usage from an Agent SDK RunResult.

        Args:
            agent_name: Name of the agent (e.g., "planner", "search")
            model: Model used (e.g., "gpt-4o-mini")
            result: RunResult from Agent SDK Runner.run()

        Returns:
            AgentUsage with calculated costs
        """
        # Extract usage from result
        input_tokens = 0
        output_tokens = 0

        # The Agent SDK stores usage in result.raw_responses
        if hasattr(result, 'raw_responses') and result.raw_responses:
            for response in result.raw_responses:
                if hasattr(response, 'usage') and response.usage:
                    input_tokens += getattr(response.usage, 'input_tokens', 0)
                    output_tokens += getattr(response.usage, 'output_tokens', 0)

        # Calculate costs
        input_cost, output_cost = self.calculate_cost(model, input_tokens, output_tokens)

        usage = AgentUsage(
            agent_name=agent_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost
        )

        self.report.add_agent_usage(usage)
        return usage

    def track_manual(self, agent_name: str, model: str, input_tokens: int, output_tokens: int) -> AgentUsage:
        """
        Manually track token usage when RunResult is not available.

        Args:
            agent_name: Name of the agent
            model: Model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            AgentUsage with calculated costs
        """
        input_cost, output_cost = self.calculate_cost(model, input_tokens, output_tokens)

        usage = AgentUsage(
            agent_name=agent_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost
        )

        self.report.add_agent_usage(usage)
        return usage

    def finalize(self) -> AnalysisCostReport:
        """Finalize the report with duration."""
        end_time = datetime.now()
        self.report.duration_seconds = (end_time - self.start_time).total_seconds()
        return self.report

    def save_report(self, output_dir: str) -> str:
        """
        Save cost report to output directory.

        Returns:
            Path to saved report
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save JSON report
        json_path = output_path / "cost_report.json"
        with open(json_path, 'w') as f:
            json.dump(asdict(self.report), f, indent=2)

        # Save markdown summary
        md_path = output_path / "09_cost_report.md"
        md_content = self._generate_markdown_report()
        with open(md_path, 'w') as f:
            f.write(md_content)

        return str(json_path)

    def _generate_markdown_report(self) -> str:
        """Generate markdown cost report."""
        report = self.report

        md = f"""# Cost Report

**Analysis:** {report.ticker} - {report.query[:100]}...
**Config Mode:** {report.config_mode}
**Timestamp:** {report.timestamp}
**Duration:** {report.duration_seconds:.1f} seconds

## Summary

| Metric | Value |
|--------|-------|
| Total Input Tokens | {report.total_input_tokens:,} |
| Total Output Tokens | {report.total_output_tokens:,} |
| **Total Tokens** | **{report.total_tokens:,}** |
| **Total Cost** | **${report.total_cost:.4f}** |

## Per-Agent Breakdown

| Agent | Model | Input | Output | Total | Cost |
|-------|-------|-------|--------|-------|------|
"""

        for agent in report.agents:
            md += f"| {agent['agent_name']} | {agent['model']} | {agent['input_tokens']:,} | {agent['output_tokens']:,} | {agent['total_tokens']:,} | ${agent['total_cost']:.4f} |\n"

        md += f"""
## Cost Analysis

- **Cost per 1K tokens:** ${(report.total_cost / (report.total_tokens / 1000)) if report.total_tokens > 0 else 0:.4f}
- **Estimated reports per $20:** {int(20 / report.total_cost) if report.total_cost > 0 else 0}
"""

        return md

    def print_summary(self):
        """Print cost summary to console."""
        report = self.report

        print("\n" + "=" * 60)
        print("COST REPORT")
        print("=" * 60)
        print(f"Config: {report.config_mode}")
        print(f"Ticker: {report.ticker}")
        print(f"Duration: {report.duration_seconds:.1f}s")
        print("-" * 60)
        print(f"{'Agent':<20} {'Model':<15} {'Tokens':>10} {'Cost':>10}")
        print("-" * 60)

        for agent in report.agents:
            print(f"{agent['agent_name']:<20} {agent['model']:<15} {agent['total_tokens']:>10,} ${agent['total_cost']:>8.4f}")

        print("-" * 60)
        print(f"{'TOTAL':<20} {'':<15} {report.total_tokens:>10,} ${report.total_cost:>8.4f}")
        print("=" * 60)
        print(f"Estimated reports per $20: {int(20 / report.total_cost) if report.total_cost > 0 else 0}")
        print("=" * 60 + "\n")


# Global tracker instance for easy access
_current_tracker: Optional[CostTracker] = None


def start_tracking(ticker: str, query: str, config_mode: str = "standard") -> CostTracker:
    """Start tracking costs for an analysis run."""
    global _current_tracker
    _current_tracker = CostTracker(ticker, query, config_mode)
    return _current_tracker


def get_tracker() -> Optional[CostTracker]:
    """Get the current cost tracker."""
    return _current_tracker


def track_agent(agent_name: str, model: str, result) -> Optional[AgentUsage]:
    """Track an agent run using the global tracker."""
    if _current_tracker:
        return _current_tracker.track_agent_run(agent_name, model, result)
    return None
