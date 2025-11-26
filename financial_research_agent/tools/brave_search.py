"""
Brave Search API integration for OpenAI Agents SDK.

Provides web search capabilities with significant cost savings compared to OpenAI WebSearchTool:
- Cost: $0.003 per search (vs $0.03-0.035 for OpenAI)
- 10x cheaper with better performance
- Free tier: 2,000 searches/month

API Documentation: https://brave.com/search/api/
"""

import os
from typing import Any
import httpx
from agents.tool import function_tool


async def _brave_search_impl(query: str, count: int = 10) -> str:
    """
    Search the web using Brave Search API.

    Significantly cheaper and faster than OpenAI's WebSearchTool:
    - $0.003/search vs $0.03-0.035/search (10x cheaper)
    - 95% of requests < 1 second
    - No ads, privacy-focused
    - 30B+ page index

    Returns up-to-date information from across the internet.
    Use this for current events, news, company information, market data, etc.

    Args:
        query: The search query to execute
        count: Number of results to return (default: 10, max: 20)

    Returns:
        Formatted search results as a string
    """
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        return (
            "Error: BRAVE_API_KEY not found in environment. "
            "Please add it to your .env file. "
            "Get your API key at: https://brave.com/search/api/"
        )

    try:
        # Validate count
        count = max(1, min(count, 20))

        # Prepare API request
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key
        }

        params = {
            "q": query,
            "count": count,
            "text_decorations": False,  # Cleaner results
            "search_lang": "en",
            "result_filter": "web"  # Focus on web results for financial research
        }

        # Make API request with retry logic
        base_url = "https://api.search.brave.com/res/v1/web/search"

        # Retry up to 3 times for network errors
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:  # Increased timeout to 30s
                    response = await client.get(
                        base_url,
                        headers=headers,
                        params=params,
                        follow_redirects=True
                    )
                    response.raise_for_status()

                data = response.json()

                # Format and return results
                return _format_results(data, query)

            except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Wait before retry (exponential backoff)
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    # Last attempt failed
                    return f"Error: Brave API connection failed after {max_retries} attempts. Network issue: {str(e)}"

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return "Error: Invalid Brave API key. Please check your BRAVE_API_KEY in .env file."
                elif e.response.status_code == 429:
                    return "Error: Brave API rate limit exceeded. Please try again later."
                else:
                    return f"Error: Brave API returned status {e.response.status_code}: {e.response.text}"

    except Exception as e:
        return f"Error searching with Brave API: {str(e)}"


def _format_results(data: dict[str, Any], query: str) -> str:
    """
    Format Brave Search API results into readable text.

    Args:
        data: Raw API response
        query: Original search query

    Returns:
        Formatted search results string
    """
    output = f"Search results for: {query}\n\n"

    web_results = data.get("web", {}).get("results", [])

    if not web_results:
        return f"No results found for: {query}"

    # Format each result
    for i, result in enumerate(web_results, 1):
        title = result.get("title", "No title")
        url = result.get("url", "")
        description = result.get("description", "")

        output += f"{i}. {title}\n"
        output += f"   URL: {url}\n"
        if description:
            # Clean up description
            description = description.strip()
            output += f"   {description}\n"
        output += "\n"

    # Add any infoboxes or special results
    if "infobox" in data:
        infobox = data["infobox"]
        if "title" in infobox:
            output += f"\n--- Quick Info ---\n"
            output += f"{infobox.get('title', '')}\n"
            if "description" in infobox:
                output += f"{infobox['description']}\n"

    # Add query suggestions if available
    if "query" in data and "altered" in data["query"]:
        output += f"\n(Search was modified to: {data['query']['altered']})\n"

    return output.strip()


# Create the tool for Agent SDK
brave_search = function_tool(_brave_search_impl)

# Export the unwrapped implementation for direct testing
__all__ = ["brave_search", "_brave_search_impl"]
