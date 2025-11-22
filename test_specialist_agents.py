"""
Test script to compare different Risk and Financials agent configurations.

This script runs the same ticker analysis multiple times with different
RISK_REASONING_EFFORT and FINANCIALS_REASONING_EFFORT settings to compare
quality vs cost for the specialist agents that do the analytical heavy lifting.

Usage:
    python test_specialist_agents.py TICKER

Example:
    python test_specialist_agents.py MSFT
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import shutil

# Test configurations - 2x2 grid
# Format: (label, RISK_REASONING, FINANCIALS_REASONING, description)
CONFIGS = [
    ("baseline", "low", "low", "Current config: both low reasoning"),
    ("risk_boost", "medium", "low", "Boost risk analysis reasoning"),
    ("financials_boost", "low", "medium", "Boost financials analysis reasoning"),
    ("both_medium", "medium", "medium", "Both agents medium reasoning"),
]


def run_analysis(ticker: str, config_label: str, risk_reasoning: str, financials_reasoning: str):
    """Run a single analysis with specified specialist agent configs."""
    print(f"\n{'='*80}")
    print(f"Running: {config_label}")
    print(f"Risk Reasoning: {risk_reasoning}")
    print(f"Financials Reasoning: {financials_reasoning}")
    print(f"{'='*80}\n")

    # Set environment variables for this run
    env = os.environ.copy()
    env["RISK_REASONING_EFFORT"] = risk_reasoning
    env["FINANCIALS_REASONING_EFFORT"] = financials_reasoning

    # Keep writer at gpt-4.1 (we already proved it's best)
    env["WRITER_MODEL"] = "gpt-4.1"
    env["WRITER_REASONING_EFFORT"] = "minimal"

    # Find Python executable - prefer .venv if it exists
    # Use absolute path to ensure it works regardless of current directory
    script_dir = Path(__file__).parent
    venv_python = script_dir / ".venv" / "bin" / "python"
    python_exec = str(venv_python.absolute()) if venv_python.exists() else sys.executable

    print(f"Using Python: {python_exec}")

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

    # Find risk and financials agent costs
    risk_cost = None
    financials_cost = None

    for agent in data.get("agents", []):
        if agent.get("agent") == "risk":
            risk_cost = {
                "input_tokens": agent.get("input_tokens", 0),
                "output_tokens": agent.get("output_tokens", 0),
                "total_tokens": agent.get("total_tokens", 0),
                "cost": agent.get("cost", 0),
            }
        elif agent.get("agent") == "financials":
            financials_cost = {
                "input_tokens": agent.get("input_tokens", 0),
                "output_tokens": agent.get("output_tokens", 0),
                "total_tokens": agent.get("total_tokens", 0),
                "cost": agent.get("cost", 0),
            }

    return {
        "total_cost": data.get("total_cost", 0),
        "total_tokens": data.get("total_tokens", 0),
        "duration": data.get("duration_seconds", 0),
        "risk": risk_cost,
        "financials": financials_cost,
    }


def create_comparison_report(ticker: str, results: list):
    """Create a markdown comparison report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path("financial_research_agent/output") / f"specialist_comparison_{ticker}_{timestamp}"
    report_dir.mkdir(parents=True, exist_ok=True)

    # Copy specialist reports for comparison
    for config_label, output_dir, cost_data, description in results:
        if output_dir:
            # Copy risk analysis
            risk_src = output_dir / "06_risk_analysis.md"
            if risk_src.exists():
                risk_dst = report_dir / f"{config_label}_risk_analysis.md"
                shutil.copy(risk_src, risk_dst)

            # Copy financial analysis
            fin_src = output_dir / "05_financial_analysis.md"
            if fin_src.exists():
                fin_dst = report_dir / f"{config_label}_financial_analysis.md"
                shutil.copy(fin_src, fin_dst)

            # Copy comprehensive report (to see how better inputs improve synthesis)
            comp_src = output_dir / "07_comprehensive_report.md"
            if comp_src.exists():
                comp_dst = report_dir / f"{config_label}_comprehensive_report.md"
                shutil.copy(comp_src, comp_dst)

    # Create comparison summary
    summary = f"""# Specialist Agent Comparison Report

**Ticker:** {ticker}
**Test Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Configuration Results

### Cost Comparison

| Config | Risk Reasoning | Financials Reasoning | Risk Cost | Financials Cost | Combined Cost | Total Cost | Duration |
|--------|----------------|---------------------|-----------|-----------------|---------------|------------|----------|
"""

    for config_label, output_dir, cost_data, description in results:
        if cost_data and cost_data.get("risk") and cost_data.get("financials"):
            risk = cost_data["risk"]
            financials = cost_data["financials"]

            # Extract reasoning levels from description
            parts = description.split(":")
            if len(parts) > 1:
                reasoning_desc = parts[1].strip()
            else:
                reasoning_desc = description

            risk_reasoning = "low" if "both low" in description or "Boost financials" in description else "medium"
            fin_reasoning = "low" if "both low" in description or "Boost risk" in description else "medium"

            combined_cost = risk["cost"] + financials["cost"]

            summary += f"| {config_label} | {risk_reasoning} | {fin_reasoning} | "
            summary += f"${risk['cost']:.4f} | ${financials['cost']:.4f} | "
            summary += f"${combined_cost:.4f} | ${cost_data['total_cost']:.4f} | "
            summary += f"{cost_data['duration']:.1f}s |\n"
        else:
            summary += f"| {config_label} | - | - | FAILED | FAILED | FAILED | FAILED | FAILED |\n"

    summary += f"""

### Token Usage Detail

| Config | Risk Input | Risk Output | Fin Input | Fin Output | Combined Tokens |
|--------|-----------|-------------|-----------|------------|-----------------|
"""

    for config_label, output_dir, cost_data, description in results:
        if cost_data and cost_data.get("risk") and cost_data.get("financials"):
            risk = cost_data["risk"]
            financials = cost_data["financials"]
            combined_tokens = risk["total_tokens"] + financials["total_tokens"]

            summary += f"| {config_label} | {risk['input_tokens']:,} | {risk['output_tokens']:,} | "
            summary += f"{financials['input_tokens']:,} | {financials['output_tokens']:,} | "
            summary += f"{combined_tokens:,} |\n"

    summary += """

## Cost Analysis

### Key Questions to Answer:

1. **Does higher reasoning in Risk agent identify more/better risks?**
   - Compare `baseline` vs `risk_boost` risk analysis reports
   - Look for: non-obvious risks, interconnected risks, nuanced interpretations

2. **Does higher reasoning in Financials agent provide better insights?**
   - Compare `baseline` vs `financials_boost` financial analysis reports
   - Look for: trend identification, anomaly detection, business context

3. **Is there synergy from boosting both agents?**
   - Compare `both_medium` vs individual boosts
   - Does the comprehensive report improve when both inputs are better?

4. **What's the cost/quality tradeoff?**
   - Are the insights worth the cost increase?
   - Which config provides the best value?

## Quality Evaluation

Review the reports in this directory:

### Risk Analysis Reports
"""

    for config_label, output_dir, cost_data, description in results:
        if output_dir and (report_dir / f"{config_label}_risk_analysis.md").exists():
            summary += f"- `{config_label}_risk_analysis.md` - {description}\n"

    summary += "\n### Financial Analysis Reports\n"

    for config_label, output_dir, cost_data, description in results:
        if output_dir and (report_dir / f"{config_label}_financial_analysis.md").exists():
            summary += f"- `{config_label}_financial_analysis.md` - {description}\n"

    summary += "\n### Comprehensive Reports (Final Synthesis)\n"

    for config_label, output_dir, cost_data, description in results:
        if output_dir and (report_dir / f"{config_label}_comprehensive_report.md").exists():
            summary += f"- `{config_label}_comprehensive_report.md` - {description}\n"

    summary += """

### Evaluation Criteria

**For Risk Analysis:**
1. **Depth**: Does it identify non-obvious, interconnected risks?
2. **Context**: Are risks explained with business implications?
3. **Prioritization**: Are the most material risks highlighted?
4. **Nuance**: Does it avoid generic risk statements?

**For Financial Analysis:**
1. **Insight**: Beyond numbers - what do trends mean?
2. **Anomalies**: Does it spot unusual patterns?
3. **Context**: Business drivers explained clearly?
4. **Forward-looking**: Implications for future performance?

**For Comprehensive Report:**
1. **Synthesis**: Does better specialist input → better final report?
2. **Coherence**: Are insights from specialists well-integrated?
3. **Actionability**: Investment-grade decision-making value?

### Recommended Approach

1. **Blind comparison**: Read risk/financials reports without knowing config
2. **Rank by quality**: Which provides best insights?
3. **Reveal configs**: Check which reasoning level produced which report
4. **Cost-benefit**: Decide if quality improvement justifies cost increase
5. **Run automated quality analysis**: Use `analyze_report_quality.py` on this directory

## Next Steps

After manual review, run automated quality analysis:

```bash
python analyze_report_quality.py {report_dir}
```

This will provide quantitative scoring across multiple quality dimensions.
"""

    # Save summary
    summary_path = report_dir / "comparison_summary.md"
    summary_path.write_text(summary)

    print(f"\n✅ Comparison report saved to: {report_dir}")
    print(f"📄 Summary: {summary_path}")

    return report_dir


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_specialist_agents.py TICKER")
        print("Example: python test_specialist_agents.py MSFT")
        sys.exit(1)

    ticker = sys.argv[1].upper()

    print(f"""
{'='*80}
Specialist Agent Comparison Test (Risk + Financials)
{'='*80}

Ticker: {ticker}
Configurations to test: {len(CONFIGS)}

This will run {len(CONFIGS)} analyses sequentially with different reasoning
levels for Risk and Financials agents (writer fixed at gpt-4.1).

Estimated time: {len(CONFIGS) * 5}-{len(CONFIGS) * 7} minutes
Estimated cost: $0.30-0.50 in OpenAI API fees

""")

    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)

    results = []

    for config_label, risk_reasoning, financials_reasoning, description in CONFIGS:
        output_dir = run_analysis(ticker, config_label, risk_reasoning, financials_reasoning)
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
    print(f"2. Read the specialist reports to evaluate quality differences")
    print(f"3. Run automated analysis: python analyze_report_quality.py {report_dir}")
    print(f"4. Decide which config provides best quality/cost balance")
    print(f"5. Update Railway env vars accordingly")


if __name__ == "__main__":
    main()
