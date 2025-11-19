"""Debug script to inspect income statement DataFrame structure."""
import os
os.environ["SEC_EDGAR_USER_AGENT"] = "FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

from financial_research_agent.tools.edgar_tools import extract_financial_data_deterministic

# Extract Apple's financial data
result = extract_financial_data_deterministic("AAPL")

if result and 'income_statement_df' in result:
    df = result['income_statement_df']

    print("\n" + "="*80)
    print("INCOME STATEMENT DATAFRAME STRUCTURE")
    print("="*80)

    print("\nColumns:", df.columns.tolist())
    print("\nIndex (first 30 items):")
    for i, label in enumerate(df.index[:30]):
        print(f"{i:3d}. {label!r}")

    print("\nDataFrame shape:", df.shape)
    print("\nFirst few rows:")
    print(df.head(10))

    print("\n" + "="*80)
    print("SEARCHING FOR KEY LABELS")
    print("="*80)

    search_terms = [
        "Revenue", "Contract Revenue", "Net Sales",
        "Gross Profit", "Operating Income", "Net Income",
        "Products", "Services", "iPhone", "Mac", "iPad",
        "Americas", "Europe", "Greater China"
    ]

    for term in search_terms:
        matches = [label for label in df.index if term.lower() in label.lower()]
        if matches:
            print(f"\n'{term}' matches:")
            for match in matches:
                print(f"  - {match!r}")
        else:
            print(f"\n'{term}': NO MATCHES")
else:
    print("ERROR: No income_statement_df in result")
    print("Result keys:", result.keys() if result else "None")
