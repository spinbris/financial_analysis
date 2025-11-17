"""
Utility functions for RAG system.

Includes ticker extraction, date formatting, and helper functions.
"""

import re
from datetime import datetime
from pathlib import Path


def _validate_ticker_with_edgar(ticker: str) -> bool:
    """
    Validate if a ticker is real using edgartools Company lookup.

    Args:
        ticker: Potential ticker symbol to validate

    Returns:
        True if ticker represents a real company in SEC database
    """
    try:
        from edgar import Company
        company = Company(ticker)

        # Check if it's the placeholder entity that edgartools returns for invalid tickers
        if company.name and 'Entity -' in str(company.name):
            return False

        # If we got a company with a real name, it's valid
        return True
    except Exception:
        # Any exception means invalid ticker
        return False


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

    # Strategy: Combine company_map matches + explicit ticker matches

    # Common English words that will NEVER be tickers (fast filter before edgartools check)
    # IMPORTANT: Only include words that are guaranteed to NOT be ticker symbols
    # Don't include financial terms that might be tickers (e.g., KEY is KeyCorp, FLOW is Global X Funds)
    common_words = {
        # Basic English words (pronouns, articles, prepositions, conjunctions)
        "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN",
        "HAD", "HER", "WAS", "ONE", "OUR", "OUT", "DAY", "GET", "HAS",
        "HIM", "HIS", "HOW", "ITS", "MAY", "NEW", "NOW", "OLD", "SEE",
        "TWO", "WAY", "WHO", "BOY", "DID", "LET", "PUT", "SAY", "SHE",
        "TOO", "USE", "VIA", "WHAT", "WHEN", "WITH", "FROM", "THIS",
        "THAT", "HAVE", "THEY", "BEEN", "WERE", "SAID", "EACH", "THAN",
        "FIND", "MANY", "THEN", "THEM", "MAKE", "LIKE", "TIME", "VERY",
        "JUST", "KNOW", "TAKE", "YEAR", "SOME", "OVER", "SUCH", "ALSO",
        "BACK", "ONLY", "COME", "WORK", "SPEND", "MAJOR", "AMONG",
        # Generic business words (not specific financial terms that might be tickers)
        "COMPANIES", "COMPANY", "ABOUT", "INTO", "DOES", "WELL", "EVEN",
        "MADE", "GIVEN", "THEIR", "THESE", "THOSE", "WOULD", "COULD",
        "SHOULD", "BEING", "DOING", "GOING", "FIRST", "LAST"
    }

    # Known major tickers (Magnificent 7 / Big Tech + major indices)
    # These should always be recognized even if they match word patterns
    known_tickers = {
        # Magnificent 7 (new FAANG)
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA",
        # Other major tech
        "NFLX", "AMD", "INTC", "CSCO", "ORCL", "IBM", "CRM", "ADBE",
        # Major financials
        "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW",
        # Other S&P giants
        "BRK.A", "BRK.B", "V", "MA", "JNJ", "UNH", "XOM", "CVX", "PG", "KO", "PEP"
    }

    # Process explicit tickers - filter false positives
    validated_explicit_tickers = []
    # Build set of already-matched tickers from company names to avoid duplicates
    matched_from_names = set(name_tickers)

    for ticker in set(explicit_tickers):
        # Skip if we already matched this via company name
        # (e.g., "Apple" matched to AAPL, don't also add "APPLE" as ticker)
        if ticker in matched_from_names:
            continue

        # Whitelist: Known major tickers always pass (fast path)
        if ticker in known_tickers:
            validated_explicit_tickers.append(ticker)
            continue

        # Must be 3-5 characters
        if len(ticker) < 3 or len(ticker) > 5:
            continue

        # Quick filter: Skip very common English words to avoid unnecessary API calls
        if ticker in common_words:
            continue

        # Check if this might be a company name written in various cases
        # (e.g., "Apple", "apple", or even "APPLE" for the company)
        if ticker.lower() in company_map:
            # This word matches a known company name
            mapped_ticker = company_map[ticker.lower()]
            if mapped_ticker not in matched_from_names:
                # We haven't already added this ticker via company name matching
                validated_explicit_tickers.append(mapped_ticker)
            # Don't process further - we've handled this word
            continue

        # Skip if this looks like a company name (title case: Apple, Microsoft)
        # Real tickers are usually all-caps (AAPL) or specific patterns
        if ticker[0].isupper() and any(c.islower() for c in ticker[1:]):
            # Unknown title-case word, likely a company name we don't recognize
            # Skip it to avoid false positives
            continue

        # Final validation: Check with edgartools if this is a real SEC-registered ticker
        # This catches edge cases that aren't in our common_words list
        if _validate_ticker_with_edgar(ticker):
            validated_explicit_tickers.append(ticker)
        # If edgartools says it's invalid, skip it (silently filtered)

    # Combine name matches + explicit ticker matches (deduplicate)
    all_tickers = list(set(name_tickers + validated_explicit_tickers))

    # Normalize to ADR tickers for international companies
    from financial_research_agent.utils.sector_detection import normalize_ticker
    normalized_tickers = [normalize_ticker(t) for t in all_tickers]

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
