"""
Multi-provider web search with automatic fallback.

Strategy:
1. Try Brave Search first (cheapest, $0.003/search)
2. Fall back to Serper on Brave rate limits (Google results, $0.0015/search)
3. Provides resilient search with cost optimization

This ensures uninterrupted research even when one provider hits limits.
"""

import os
from typing import Any
import httpx
from agents import function_tool


async def _multi_search_impl(query: str, count: int = 10) -> str:
    """
    Search the web using multiple providers with automatic fallback.

    Tries Brave Search first for cost efficiency, then falls back to Serper
    (Google results) if Brave hits rate limits.

    Args:
        query: The search query to execute
        count: Number of results to return (default: 10)

    Returns:
        Formatted search results as a string
    """
    # Try Brave first
    brave_result = await _try_brave_search(query, count)

    # Check if Brave failed due to rate limit
    if "rate limit" in brave_result.lower() or "Error:" in brave_result:
        # Fall back to Serper
        serper_result = await _try_serper_search(query, count)

        # If Serper also fails, return both error messages
        if "Error:" in serper_result:
            return f"[Both search providers failed]\n\nBrave: {brave_result}\n\nSerper: {serper_result}"

        # Serper succeeded, return results with provider note
        return f"[Using Serper - Brave rate limited]\n\n{serper_result}"

    # Brave succeeded, return results
    return f"[Using Brave Search]\n\n{brave_result}"


async def _try_brave_search(query: str, count: int) -> str:
    """Try searching with Brave API."""
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        return "Error: BRAVE_API_KEY not found"

    try:
        count = max(1, min(count, 20))

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key
        }

        params = {
            "q": query,
            "count": count,
            "text_decorations": False,
            "search_lang": "en",
            "result_filter": "web"
        }

        base_url = "https://api.search.brave.com/res/v1/web/search"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                base_url,
                headers=headers,
                params=params,
                follow_redirects=True
            )
            response.raise_for_status()

        data = response.json()
        return _format_brave_results(data, query)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return "Error: Brave API rate limit exceeded"
        return f"Error: Brave API status {e.response.status_code}"
    except Exception as e:
        return f"Error: Brave API failed - {str(e)}"


async def _try_serper_search(query: str, count: int) -> str:
    """Try searching with Serper API (Google results)."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "Error: SERPER_API_KEY not found"

    try:
        count = max(1, min(count, 100))

        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "q": query,
            "num": count,
            "gl": "us",
            "hl": "en"
        }

        base_url = "https://google.serper.dev/search"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                base_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

        data = response.json()
        return _format_serper_results(data, query)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return "Error: Serper API rate limit exceeded"
        return f"Error: Serper API status {e.response.status_code}"
    except Exception as e:
        return f"Error: Serper API failed - {str(e)}"


def _format_brave_results(data: dict[str, Any], query: str) -> str:
    """Format Brave Search results."""
    output = f"Search results for: {query}\n\n"

    web_results = data.get("web", {}).get("results", [])
    if not web_results:
        return f"No results found for: {query}"

    for i, result in enumerate(web_results, 1):
        title = result.get("title", "No title")
        url = result.get("url", "")
        description = result.get("description", "")

        output += f"{i}. {title}\n"
        output += f"   URL: {url}\n"
        if description:
            output += f"   {description.strip()}\n"
        output += "\n"

    return output.strip()


def _format_serper_results(data: dict[str, Any], query: str) -> str:
    """Format Serper API results."""
    output = f"Search results for: {query}\n\n"

    organic_results = data.get("organic", [])
    if not organic_results:
        return f"No results found for: {query}"

    for i, result in enumerate(organic_results, 1):
        title = result.get("title", "No title")
        link = result.get("link", "")
        snippet = result.get("snippet", "")

        output += f"{i}. {title}\n"
        output += f"   URL: {link}\n"
        if snippet:
            output += f"   {snippet.strip()}\n"
        output += "\n"

    # Add knowledge graph if available
    if "knowledgeGraph" in data:
        kg = data["knowledgeGraph"]
        if "title" in kg:
            output += f"\n--- Quick Info ---\n"
            output += f"{kg.get('title', '')}\n"
            if "description" in kg:
                output += f"{kg['description']}\n"

    return output.strip()


# Create the tool for Agent SDK
multi_search = function_tool(_multi_search_impl)

# Export the unwrapped implementation for direct testing
__all__ = ["multi_search", "_multi_search_impl"]
