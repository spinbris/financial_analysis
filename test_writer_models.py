"""
Test script to compare different writer model configurations.

This script runs the same ticker analysis multiple times with different
WRITER_MODEL and WRITER_REASONING_EFFORT settings to compare quality vs cost.

Usage:
    python test_writer_models.py TICKER

Example:
    python test_writer_models.py MSFT
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import shutil

# Test configurations
# Format: (label, WRITER_MODEL, WRITER_REASONING_EFFORT, description)
CONFIGS = [
    ("gpt41", "gpt-4.1", "minimal", "GPT-4.1 baseline (current Railway config)"),
    ("gpt51_low", "gpt-5.1", "low", "GPT-5.1 with low reasoning (code default)"),
    ("gpt51_medium", "gpt-5.1", "medium", "GPT-5.1 with medium reasoning"),
    ("gpt51_high", "gpt-5.1", "high", "GPT-5.1 with high reasoning (max quality)"),
]


def run_analysis(ticker: str, config_label: str, writer_model: str, reasoning_effort: str):
    """Run a single analysis with specified writer model config."""
    print(f"\n{'='*80}")
    print(f"Running: {config_label}")
    print(f"Writer Model: {writer_model}")
    print(f"Reasoning Effort: {reasoning_effort}")
    print(f"{'='*80}\n")

    # Set environment variables for this run
    env = os.environ.copy()
    env["WRITER_MODEL"] = writer_model
    env["WRITER_REASONING_EFFORT"] = reasoning_effort

    # Find Python executable - prefer .venv if it exists
    # Use absolute path to ensure it works regardless of current directory
    script_dir = Path(__file__).parent
    venv_python = script_dir / ".venv" / "bin" / "python"
    python_exec = str(venv_python.absolute()) if venv_python.exists() else sys.executable

    print(f"Using Python: {python_exec}")
    print(f"Venv exists: {venv_python.exists()}")

    # Run the analysis
    try:
        result = subprocess.run(
            [python_exec, "-m", "financial_research_agent.main_enhanced"],
            env=env,
            input=f"{ticker}\n{ticker} comprehensive analysis\n",
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        if result.returncode != 0:
            print(f"❌ Analysis failed: {result.stderr}")
            return None

        print(f"✅ Analysis completed successfully")

        # Find the most recent output directory
        output_dir = Path("financial_research_agent/output")
        latest_dir = max(output_dir.glob("*"), key=lambda p: p.stat().st_mtime)

        return latest_dir

    except subprocess.TimeoutExpired:
        print(f"❌ Analysis timed out after 10 minutes")
        return None
    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        return None


def extract_cost_data(output_dir: Path):
    """Extract cost data from cost_report.json."""
    cost_json = output_dir / "cost_report.json"
    if not cost_json.exists():
        return None

    with open(cost_json) as f:
        data = json.load(f)

    # Find writer agent cost
    writer_cost = None
    for agent in data.get("agents", []):
        if agent.get("agent") == "writer":
            writer_cost = {
                "input_tokens": agent.get("input_tokens", 0),
                "output_tokens": agent.get("output_tokens", 0),
                "total_tokens": agent.get("total_tokens", 0),
                "cost": agent.get("cost", 0),
            }
            break

    return {
        "total_cost": data.get("total_cost", 0),
        "total_tokens": data.get("total_tokens", 0),
        "duration": data.get("duration_seconds", 0),
        "writer": writer_cost,
    }


def create_comparison_report(ticker: str, results: list):
    """Create a markdown comparison report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path("financial_research_agent/output") / f"comparison_{ticker}_{timestamp}"
    report_dir.mkdir(parents=True, exist_ok=True)

    # Copy comprehensive reports for side-by-side comparison
    for config_label, output_dir, cost_data, description in results:
        if output_dir:
            src = output_dir / "07_comprehensive_report.md"
            if src.exists():
                dst = report_dir / f"{config_label}_comprehensive_report.md"
                shutil.copy(src, dst)

    # Create comparison summary
    summary = f"""# Writer Model Comparison Report

**Ticker:** {ticker}
**Test Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Configuration Results

| Config | Writer Model | Reasoning | Total Cost | Writer Cost | Writer Tokens | Duration |
|--------|--------------|-----------|------------|-------------|---------------|----------|
"""

    for config_label, output_dir, cost_data, description in results:
        if cost_data and cost_data.get("writer"):
            writer = cost_data["writer"]
            summary += f"| {config_label} | {description.split('(')[0].strip()} | "

            # Extract reasoning effort from description
            if "low reasoning" in description:
                reasoning = "low"
            elif "medium reasoning" in description:
                reasoning = "medium"
            elif "high reasoning" in description:
                reasoning = "high"
            else:
                reasoning = "minimal"

            summary += f"{reasoning} | "
            summary += f"${cost_data['total_cost']:.4f} | "
            summary += f"${writer['cost']:.4f} | "
            summary += f"{writer['total_tokens']:,} | "
            summary += f"{cost_data['duration']:.1f}s |\n"
        else:
            summary += f"| {config_label} | - | - | FAILED | FAILED | FAILED | FAILED |\n"

    summary += f"""

## Cost Analysis

### Writer Agent Cost Comparison (Focus)
Compare the **Writer Cost** column above - this shows the incremental cost difference between models.

### Total Analysis Cost
The **Total Cost** includes all agents (planner, search, edgar, metrics, financials, risk, writer, verifier).
Writer cost is typically 10-20% of total cost.

## Quality Evaluation

Review the comprehensive reports in this directory:

"""

    for config_label, output_dir, cost_data, description in results:
        if output_dir:
            summary += f"- `{config_label}_comprehensive_report.md` - {description}\n"

    summary += """

### Evaluation Criteria

When comparing reports, consider:

1. **Synthesis Quality**: Does it effectively connect insights from different sources?
2. **Writing Quality**: Is it coherent, professional, investment-grade?
3. **Insight Depth**: Does it identify non-obvious patterns or risks?
4. **Executive Summary**: Is it compelling and actionable?
5. **Structural Clarity**: Is the report well-organized and easy to follow?
6. **Completeness**: Does it cover all key aspects comprehensively?

### Recommended Approach

1. Read all reports blind (without knowing which config)
2. Rank them by quality
3. Then reveal which config produced which report
4. Decide if the quality improvement justifies the cost increase

## Files in This Directory

"""

    for file in sorted(report_dir.glob("*.md")):
        if file.name != "comparison_summary.md":
            summary += f"- `{file.name}`\n"

    # Save summary
    summary_path = report_dir / "comparison_summary.md"
    summary_path.write_text(summary)

    print(f"\n✅ Comparison report saved to: {report_dir}")
    print(f"📄 Summary: {summary_path}")

    return report_dir


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_writer_models.py TICKER")
        print("Example: python test_writer_models.py MSFT")
        sys.exit(1)

    ticker = sys.argv[1].upper()

    print(f"""
{'='*80}
Writer Model Comparison Test
{'='*80}

Ticker: {ticker}
Configurations to test: {len(CONFIGS)}

This will run {len(CONFIGS)} analyses sequentially.
Estimated time: {len(CONFIGS) * 5}-{len(CONFIGS) * 7} minutes
Estimated cost: $0.30-0.50 in OpenAI API fees

""")

    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)

    results = []

    for config_label, writer_model, reasoning_effort, description in CONFIGS:
        output_dir = run_analysis(ticker, config_label, writer_model, reasoning_effort)
        cost_data = extract_cost_data(output_dir) if output_dir else None
        results.append((config_label, output_dir, cost_data, description))

    # Create comparison report
    report_dir = create_comparison_report(ticker, results)

    print(f"\n{'='*80}")
    print("Test Complete!")
    print(f"{'='*80}")
    print(f"\nComparison report: {report_dir / 'comparison_summary.md'}")
    print(f"\nNext steps:")
    print(f"1. Review {report_dir / 'comparison_summary.md'} for cost comparison")
    print(f"2. Read the comprehensive reports to evaluate quality")
    print(f"3. Decide which config provides best quality/cost balance")
    print(f"4. Update Railway env vars: WRITER_MODEL and WRITER_REASONING_EFFORT")


if __name__ == "__main__":
    main()
