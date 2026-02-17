from langchain_core.tools import tool
from pricewise.schemas import ProductQuery
from pricewise.tools._client import get_tavily, parse_tavily_response, format_results


@tool(args_schema=ProductQuery)
def search_product(query: str, max_results: int = 3) -> str:
    """Search for a product online using Tavily and return formatted results."""
    response = get_tavily().invoke(query)

    results, error = parse_tavily_response(response)
    if error:
        return error

    if not results:
        return "No products found for this query."

    return format_results(results, max_results)
