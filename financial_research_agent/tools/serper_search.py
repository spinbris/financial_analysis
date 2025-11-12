"""
Serper.dev API integration for web search.

Provides Google search results via Serper API:
- Cost: $1.50/1000 searches (free tier: 2,500 searches)
- Google-powered results
- Fast and reliable
- Good fallback for Brave Search

API Documentation: https://serper.dev/
"""

import os
from typing import Any
import httpx
from agents import function_tool


async def _serper_search_impl(query: str, count: int = 10) -> str:
    """
    Search the web using Serper API (Google results).

    Provides reliable Google search results as a backup/fallback option.

    Args:
        query: The search query to execute
        count: Number of results to return (default: 10, max: 100)

    Returns:
        Formatted search results as a string
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return (
            "Error: SERPER_API_KEY not found in environment. "
            "Please add it to your .env file. "
            "Get your API key at: https://serper.dev/"
        )

    try:
        # Validate count
        count = max(1, min(count, 100))

        # Prepare API request
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "q": query,
            "num": count,
            "gl": "us",  # Geolocation: US
            "hl": "en"   # Language: English
        }

        # Make API request
        base_url = "https://google.serper.dev/search"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                base_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

        data = response.json()

        # Format and return results
        return _format_results(data, query)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return "Error: Invalid Serper API key. Please check your SERPER_API_KEY in .env file."
        elif e.response.status_code == 429:
            return "Error: Serper API rate limit exceeded. Please try again later."
        else:
            return f"Error: Serper API returned status {e.response.status_code}: {e.response.text}"

    except Exception as e:
        return f"Error searching with Serper API: {str(e)}"


def _format_results(data: dict[str, Any], query: str) -> str:
    """
    Format Serper API results into readable text.

    Args:
        data: Raw API response
        query: Original search query

    Returns:
        Formatted search results string
    """
    output = f"Search results for: {query}\n\n"

    # Get organic results
    organic_results = data.get("organic", [])

    if not organic_results:
        return f"No results found for: {query}"

    # Format each result
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
serper_search = function_tool(_serper_search_impl)

# Export the unwrapped implementation for direct testing
__all__ = ["serper_search", "_serper_search_impl"]
