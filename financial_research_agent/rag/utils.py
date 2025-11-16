"""
Utility functions for RAG system.

Includes ticker extraction, date formatting, and helper functions.
"""

import re
from datetime import datetime
from pathlib import Path


def extract_tickers_from_query(query: str) -> list[str]:
    """
    Extract ticker symbols from natural language query.

    Examples:
        "What are Apple's revenues?" → ["AAPL"]
        "Compare AAPL and TSLA" → ["AAPL", "TSLA"]
        "How does Microsoft compare to Google?" → ["MSFT", "GOOGL"]

    Args:
        query: Natural language query

    Returns:
        List of uppercase ticker symbols (deduplicated)
    """
    # Explicit ticker patterns (e.g., "AAPL", "BRK.B", "aapl", "jpm")
    # Match case-insensitively and convert to uppercase
    explicit_tickers = re.findall(r'\b([A-Za-z]{1,5}(?:\.[A-Za-z])?)\b', query)
    explicit_tickers = [t.upper() for t in explicit_tickers]

    # Company name to ticker mapping
    company_map = {
        "apple": "AAPL",
        "microsoft": "MSFT",
        "msft": "MSFT",
        "tesla": "TSLA",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "amazon": "AMZN",
        "meta": "META",
        "facebook": "META",
        "nvidia": "NVDA",
        "amd": "AMD",
        "intel": "INTC",
        "netflix": "NFLX",
        "disney": "DIS",
        "berkshire": "BRK.B",
        "berkshire hathaway": "BRK.B",
        "jpmorgan": "JPM",
        "jp morgan": "JPM",
        "bank of america": "BAC",
        "wells fargo": "WFC",
        "goldman sachs": "GS",
        "morgan stanley": "MS",
        "citigroup": "C",
        "visa": "V",
        "mastercard": "MA",
        "paypal": "PYPL",
        "salesforce": "CRM",
        "oracle": "ORCL",
        "ibm": "IBM",
        "cisco": "CSCO",
        "walmart": "WMT",
        "costco": "COST",
        "target": "TGT",
        "home depot": "HD",
        "lowes": "LOW",
        "nike": "NKE",
        "adidas": "ADDYY",
        "starbucks": "SBUX",
        "mcdonald": "MCD",
        "mcdonalds": "MCD",
        "coca cola": "KO",
        "pepsi": "PEP",
        "pepsico": "PEP",
        "procter": "PG",
        "johnson": "JNJ",
        "pfizer": "PFE",
        "merck": "MRK",
        "abbvie": "ABBV",
        "eli lilly": "LLY",
        "exxon": "XOM",
        "chevron": "CVX",
        "conocophillips": "COP",
        "boeing": "BA",
        "lockheed": "LMT",
        "raytheon": "RTX",
        "ge": "GE",
        "general electric": "GE",
        "ford": "F",
        "gm": "GM",
        "general motors": "GM",
        "rivian": "RIVN",
        "lucid": "LCID",
        "palantir": "PLTR",
        "snowflake": "SNOW",
        "datadog": "DDOG",
        "mongodb": "MDB",
        "crowdstrike": "CRWD",
        "zoom": "ZM",
        "slack": "WORK",
        "docusign": "DOCU",
        "shopify": "SHOP",
        "square": "SQ",
        "block": "SQ",
        "coinbase": "COIN",
        "robinhood": "HOOD",
        "airbnb": "ABNB",
        "uber": "UBER",
        "lyft": "LYFT",
        "doordash": "DASH",
        "spotify": "SPOT",
        # Australian Banks (map to ADR tickers for SEC filings)
        "national australia bank": "NABZY",
        "nab": "NABZY",
        "anz": "ANZLY",
        "anz bank": "ANZLY",
        "westpac": "WBKCY",
        "commonwealth bank": "CMWAY",
        "cba": "CMWAY",
    }

    query_lower = query.lower()
    name_tickers = []

    # Check for multi-word company names first
    multi_word_companies = {k: v for k, v in company_map.items() if " " in k}
    for name, ticker in multi_word_companies.items():
        if name in query_lower:
            name_tickers.append(ticker)

    # Then check single-word company names
    single_word_companies = {k: v for k, v in company_map.items() if " " not in k}
    for name, ticker in single_word_companies.items():
        # Use word boundaries to avoid partial matches
        if re.search(rf'\b{re.escape(name)}\b', query_lower):
            name_tickers.append(ticker)

    # Combine and deduplicate
    all_tickers = list(set(explicit_tickers + name_tickers))

    # Filter out common false positives
    false_positives = {
        "IS", "IT", "OR", "IN", "AT", "TO", "BY", "ON", "AN", "AS",
        "BE", "DO", "GO", "HE", "IF", "ME", "MY", "NO", "OF", "SO",
        "UP", "US", "WE", "A", "I"
    }
    filtered_tickers = [t for t in all_tickers if t not in false_positives]

    # Normalize to ADR tickers for international companies
    from financial_research_agent.utils.sector_detection import normalize_ticker
    normalized_tickers = [normalize_ticker(t) for t in filtered_tickers]

    return normalized_tickers


def format_analysis_age(timestamp: str) -> dict:
    """
    Format analysis timestamp into human-readable age.

    Args:
        timestamp: Directory name like "20251106_115436"

    Returns:
        {
            "analysis_date": datetime object,
            "days_old": int,
            "formatted": "Nov 6, 2025 (2 days ago)",
            "formatted_short": "2d ago",
            "status_emoji": "🟢" | "🟡" | "🔴"
        }
    """
    try:
        # Parse timestamp from directory name
        analysis_datetime = datetime.strptime(timestamp[:8], "%Y%m%d")

        # Calculate age
        days_old = (datetime.now() - analysis_datetime).days

        # Format human-readable
        date_str = analysis_datetime.strftime("%b %d, %Y")

        if days_old == 0:
            age_str = "today"
            age_short = "today"
        elif days_old == 1:
            age_str = "1 day ago"
            age_short = "1d ago"
        else:
            age_str = f"{days_old} days ago"
            age_short = f"{days_old}d ago"

        # Determine status emoji (simplified - doesn't account for volatility)
        if days_old <= 7:
            status_emoji = "🟢"
        elif days_old <= 30:
            status_emoji = "🟡"
        else:
            status_emoji = "🔴"

        return {
            "analysis_date": analysis_datetime,
            "days_old": days_old,
            "formatted": f"{date_str} ({age_str})",
            "formatted_short": age_short,
            "status_emoji": status_emoji
        }
    except (ValueError, IndexError):
        # Invalid timestamp format
        return {
            "analysis_date": None,
            "days_old": 999,
            "formatted": "Unknown date",
            "formatted_short": "Unknown",
            "status_emoji": "⚪"
        }


def get_status_emoji(status: str) -> str:
    """
    Get emoji for staleness status.

    Args:
        status: "fresh" | "aging" | "stale" | "missing"

    Returns:
        Emoji string
    """
    status_map = {
        "fresh": "🟢",
        "aging": "🟡",
        "stale": "🔴",
        "missing": "❌"
    }
    return status_map.get(status, "⚪")


def format_company_status(company: dict) -> str:
    """
    Format company status for display.

    Args:
        company: Dict from get_companies_with_status()

    Returns:
        Formatted string like "AAPL (Apple Inc.) - 2d ago 🟢"
    """
    ticker = company["ticker"]
    company_name = company.get("company", "")
    days_old = company.get("days_old", 999)
    status = company.get("status", "unknown")

    # Format age
    if days_old == 0:
        age_str = "today"
    elif days_old == 1:
        age_str = "1d ago"
    elif days_old < 999:
        age_str = f"{days_old}d ago"
    else:
        age_str = "unknown age"

    # Get emoji
    emoji = get_status_emoji(status)

    # Build string
    if company_name:
        return f"{ticker} ({company_name}) - {age_str} {emoji}"
    else:
        return f"{ticker} - {age_str} {emoji}"
