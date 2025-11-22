"""
Automated qualitative analysis of comprehensive reports.

Uses GPT-4.1 to evaluate and compare reports across multiple quality dimensions.

Usage:
    python analyze_report_quality.py <comparison_directory>

Example:
    python analyze_report_quality.py financial_research_agent/output/comparison_MSFT_20251122_184402
"""

import sys
import json
import os
from pathlib import Path
from openai import OpenAI

# Load environment variables
try:
    from dotenv import load_dotenv
    # Try loading from financial_research_agent/.env first
    env_path = Path("financial_research_agent/.env")
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # Try .env in current directory
except ImportError:
    pass

# Quality evaluation criteria
EVALUATION_CRITERIA = {
    "synthesis_quality": {
        "name": "Synthesis Quality",
        "description": "How well does the report connect insights from different sources (financial statements, metrics, risk factors)?",
        "weight": 1.5
    },
    "writing_quality": {
        "name": "Writing Quality",
        "description": "Is the writing coherent, professional, and investment-grade?",
        "weight": 1.2
    },
    "insight_depth": {
        "name": "Insight Depth",
        "description": "Does it identify non-obvious patterns, trends, or risks beyond surface-level observations?",
        "weight": 1.5
    },
    "executive_summary": {
        "name": "Executive Summary",
        "description": "Is the executive summary compelling, actionable, and well-structured?",
        "weight": 1.3
    },
    "structural_clarity": {
        "name": "Structural Clarity",
        "description": "Is the report well-organized, easy to follow, and logically structured?",
        "weight": 1.0
    },
    "completeness": {
        "name": "Completeness",
        "description": "Does it comprehensively cover financial performance, risks, and forward-looking indicators?",
        "weight": 1.0
    },
    "actionability": {
        "name": "Actionability",
        "description": "Does it provide clear, actionable insights for investment decision-making?",
        "weight": 1.4
    }
}


def evaluate_report(report_path: Path, config_label: str, client: OpenAI) -> dict:
    """Evaluate a single report using GPT-4.1."""

    report_content = report_path.read_text()

    # Create evaluation prompt
    criteria_desc = "\n".join([
        f"- **{c['name']}**: {c['description']}"
        for c in EVALUATION_CRITERIA.values()
    ])

    prompt = f"""You are an expert investment research analyst evaluating the quality of a financial analysis report.

Evaluate this report on the following criteria, scoring each from 1-10:

{criteria_desc}

For each criterion:
1. Provide a score (1-10)
2. Provide a brief justification (2-3 sentences)

Also provide:
- Overall impression (3-4 sentences)
- Key strengths (3-5 bullet points)
- Areas for improvement (3-5 bullet points)

Format your response as JSON with this structure:
{{
    "scores": {{
        "synthesis_quality": {{"score": 8, "justification": "..."}},
        "writing_quality": {{"score": 7, "justification": "..."}},
        ...
    }},
    "overall_impression": "...",
    "key_strengths": ["...", "..."],
    "areas_for_improvement": ["...", "..."]
}}

Here is the report to evaluate:

---
{report_content}
---
"""

    print(f"  Evaluating {config_label}...")

    response = client.chat.completions.create(
        model="gpt-4o",  # Use gpt-4o for evaluation (cheaper than gpt-4.1)
        messages=[
            {"role": "system", "content": "You are an expert investment research analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  # Lower temperature for more consistent evaluations
        response_format={"type": "json_object"}
    )

    evaluation = json.loads(response.choices[0].message.content)
    evaluation["config_label"] = config_label

    return evaluation


def calculate_weighted_score(evaluation: dict) -> float:
    """Calculate weighted overall score."""
    total_weighted_score = 0
    total_weight = 0

    for criterion, details in EVALUATION_CRITERIA.items():
        if criterion in evaluation["scores"]:
            score = evaluation["scores"][criterion]["score"]
            weight = details["weight"]
            total_weighted_score += score * weight
            total_weight += weight

    return total_weighted_score / total_weight if total_weight > 0 else 0


def compare_reports(evaluations: list) -> str:
    """Generate comparative analysis markdown."""

    # Calculate weighted scores
    for eval_data in evaluations:
        eval_data["weighted_score"] = calculate_weighted_score(eval_data)

    # Sort by weighted score (descending)
    evaluations_sorted = sorted(evaluations, key=lambda x: x["weighted_score"], reverse=True)

    # Generate markdown report
    md = "# Automated Quality Analysis Report\n\n"
    md += "## Overall Rankings\n\n"
    md += "| Rank | Config | Weighted Score | Rating |\n"
    md += "|------|--------|----------------|--------|\n"

    for i, eval_data in enumerate(evaluations_sorted, 1):
        label = eval_data["config_label"]
        score = eval_data["weighted_score"]

        # Rating based on score
        if score >= 9.0:
            rating = "⭐⭐⭐⭐⭐ Exceptional"
        elif score >= 8.0:
            rating = "⭐⭐⭐⭐ Excellent"
        elif score >= 7.0:
            rating = "⭐⭐⭐ Good"
        elif score >= 6.0:
            rating = "⭐⭐ Fair"
        else:
            rating = "⭐ Needs Improvement"

        md += f"| {i} | {label} | {score:.2f}/10 | {rating} |\n"

    md += "\n## Detailed Scores by Criterion\n\n"
    md += "| Criterion | Weight | " + " | ".join([e["config_label"] for e in evaluations]) + " |\n"
    md += "|-----------|--------|" + "|".join(["--------"] * len(evaluations)) + "|\n"

    for criterion, details in EVALUATION_CRITERIA.items():
        row = f"| {details['name']} | {details['weight']}x | "
        scores = []
        for eval_data in evaluations:
            if criterion in eval_data["scores"]:
                score = eval_data["scores"][criterion]["score"]
                scores.append(f"{score}/10")
            else:
                scores.append("N/A")
        row += " | ".join(scores) + " |\n"
        md += row

    md += "\n## Individual Report Evaluations\n\n"

    for eval_data in evaluations_sorted:
        label = eval_data["config_label"]
        score = eval_data["weighted_score"]

        md += f"### {label} (Score: {score:.2f}/10)\n\n"
        md += f"**Overall Impression:**\n{eval_data.get('overall_impression', 'N/A')}\n\n"

        md += "**Key Strengths:**\n"
        for strength in eval_data.get("key_strengths", []):
            md += f"- {strength}\n"
        md += "\n"

        md += "**Areas for Improvement:**\n"
        for area in eval_data.get("areas_for_improvement", []):
            md += f"- {area}\n"
        md += "\n"

        md += "**Detailed Scores:**\n\n"
        for criterion, details in EVALUATION_CRITERIA.items():
            if criterion in eval_data["scores"]:
                score_data = eval_data["scores"][criterion]
                md += f"- **{details['name']}**: {score_data['score']}/10\n"
                md += f"  - {score_data.get('justification', 'N/A')}\n"
        md += "\n---\n\n"

    md += "## Cost-Quality Analysis\n\n"
    md += "Comparing quality improvement vs cost increase:\n\n"
    md += "| Config | Quality Score | Writer Cost | Cost vs Baseline | Quality vs Baseline | Quality/Cost Ratio |\n"
    md += "|--------|---------------|-------------|------------------|---------------------|--------------------|\n"

    # Assume these costs from earlier analysis
    costs = {
        "gpt41": 0.0469,
        "gpt51_low": 0.0755,
        "gpt51_medium": 0.1297,
        "gpt51_high": 0.1781
    }

    baseline_score = next((e["weighted_score"] for e in evaluations if e["config_label"] == "gpt41"), None)
    baseline_cost = costs.get("gpt41", 0.0469)

    for eval_data in evaluations_sorted:
        label = eval_data["config_label"]
        score = eval_data["weighted_score"]
        cost = costs.get(label, 0)

        cost_vs_baseline = ((cost / baseline_cost) - 1) * 100 if baseline_cost else 0
        quality_vs_baseline = ((score / baseline_score) - 1) * 100 if baseline_score else 0
        quality_cost_ratio = score / cost if cost > 0 else 0

        md += f"| {label} | {score:.2f} | ${cost:.4f} | "
        md += f"{cost_vs_baseline:+.1f}% | {quality_vs_baseline:+.1f}% | {quality_cost_ratio:.1f} |\n"

    md += "\n**Interpretation:**\n"
    md += "- **Cost vs Baseline**: Percentage increase in writer agent cost\n"
    md += "- **Quality vs Baseline**: Percentage improvement in quality score\n"
    md += "- **Quality/Cost Ratio**: Higher is better (more quality per dollar)\n"

    md += "\n## Recommendation\n\n"

    # Find best quality/cost ratio
    best_ratio = max(evaluations, key=lambda e: e["weighted_score"] / costs.get(e["config_label"], 1))
    best_quality = evaluations_sorted[0]

    md += f"**Best Quality/Cost Balance**: `{best_ratio['config_label']}`\n\n"
    md += f"**Highest Quality**: `{best_quality['config_label']}` ({best_quality['weighted_score']:.2f}/10)\n\n"

    if best_ratio["config_label"] == best_quality["config_label"]:
        md += f"The `{best_ratio['config_label']}` configuration provides both the best quality "
        md += "and the best quality/cost ratio. This is the recommended configuration.\n"
    else:
        md += f"If maximum quality is required, use `{best_quality['config_label']}`.\n"
        md += f"If cost-efficiency is important, use `{best_ratio['config_label']}`.\n"

    return md


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_report_quality.py <comparison_directory>")
        print("Example: python analyze_report_quality.py financial_research_agent/output/comparison_MSFT_20251122_184402")
        sys.exit(1)

    comparison_dir = Path(sys.argv[1])

    if not comparison_dir.exists():
        print(f"Error: Directory not found: {comparison_dir}")
        sys.exit(1)

    # Find all comprehensive reports
    report_files = list(comparison_dir.glob("*_comprehensive_report.md"))

    if not report_files:
        print(f"Error: No comprehensive reports found in {comparison_dir}")
        sys.exit(1)

    print(f"Found {len(report_files)} reports to analyze")
    print("This will use OpenAI API (gpt-4o) for evaluation")
    print(f"Estimated cost: ${len(report_files) * 0.02:.2f}\n")

    # Initialize OpenAI client
    client = OpenAI()

    # Evaluate each report
    evaluations = []

    for report_file in sorted(report_files):
        # Extract config label from filename
        config_label = report_file.stem.replace("_comprehensive_report", "")

        try:
            evaluation = evaluate_report(report_file, config_label, client)
            evaluations.append(evaluation)
        except Exception as e:
            print(f"  ❌ Error evaluating {config_label}: {e}")
            continue

    if not evaluations:
        print("Error: No reports were successfully evaluated")
        sys.exit(1)

    print(f"\n✅ Successfully evaluated {len(evaluations)} reports")

    # Generate comparative analysis
    print("Generating comparative analysis...")
    analysis_md = compare_reports(evaluations)

    # Save analysis
    output_path = comparison_dir / "quality_analysis.md"
    output_path.write_text(analysis_md)

    # Save raw evaluations as JSON
    json_path = comparison_dir / "quality_analysis.json"
    with open(json_path, 'w') as f:
        json.dump(evaluations, f, indent=2)

    print(f"\n✅ Quality analysis saved to:")
    print(f"   {output_path}")
    print(f"   {json_path}")

    # Print summary
    print("\n" + "="*80)
    print("QUALITY ANALYSIS SUMMARY")
    print("="*80)

    for eval_data in sorted(evaluations, key=lambda x: calculate_weighted_score(x), reverse=True):
        score = calculate_weighted_score(eval_data)
        print(f"{eval_data['config_label']:15} {score:.2f}/10")

    print("\nSee quality_analysis.md for full report")


if __name__ == "__main__":
    main()
