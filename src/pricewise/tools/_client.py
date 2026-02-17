from langchain_tavily import TavilySearch

_tavily = None


def get_tavily():
    global _tavily
    if _tavily is None:
        _tavily = TavilySearch(max_results=5, topic="general")
    return _tavily


def parse_tavily_response(response):
    """Parse a TavilySearch response, handling both dict and list formats."""
    if isinstance(response, dict):
        if "error" in response:
            return None, f"Search error: {response['error']}"
        return response.get("results", []), None
    elif isinstance(response, list):
        return response, None
    else:
        return None, f"Unexpected response format: {type(response)}"


def format_results(results, max_items, url_label="URL"):
    """Format Tavily results into a numbered list."""
    formatted = []
    for i, r in enumerate(results[:max_items], 1):
        url = r.get("url", "N/A")
        content = r.get("content", "No description")
        formatted.append(f"{i}. {content}\n   {url_label}: {url}")
    return "\n\n".join(formatted)
