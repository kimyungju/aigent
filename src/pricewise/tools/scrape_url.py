"""URL scraper tool using TavilyExtract.

Lets the agent extract product information from a specific URL the user
provides, rather than relying solely on keyword search.
"""

from langchain_core.tools import tool
from langchain_tavily import TavilyExtract
from pydantic import BaseModel, Field

_extractor: TavilyExtract | None = None


def _get_extractor() -> TavilyExtract:
    global _extractor
    if _extractor is None:
        _extractor = TavilyExtract()
    return _extractor


class ScrapeUrlInput(BaseModel):
    """Input schema for the URL scraper tool."""

    url: str = Field(description="The product URL to extract information from")


@tool(args_schema=ScrapeUrlInput)
def scrape_url(url: str) -> str:
    """Extract product information from a specific URL.

    Use this when the user provides a direct link to a product page
    (e.g. an Amazon, Best Buy, or retailer URL).
    """
    try:
        extractor = _get_extractor()
        result = extractor.invoke({"urls": [url]})

        if isinstance(result, dict) and "results" in result:
            contents = []
            for r in result["results"]:
                raw = r.get("raw_content", r.get("content", ""))
                if raw:
                    contents.append(raw[:3000])

            if contents:
                return f"Content from {url}:\n\n" + "\n---\n".join(contents)

        return f"Could not extract useful content from {url}."
    except Exception as e:
        return f"Error extracting content from {url}: {e}"
