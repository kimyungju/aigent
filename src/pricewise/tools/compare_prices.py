from langchain_core.tools import tool
from pricewise.schemas import PriceComparisonQuery
from pricewise.tools._client import get_tavily, parse_tavily_response, format_results


@tool(args_schema=PriceComparisonQuery)
def compare_prices(product_name: str, max_sources: int = 5) -> str:
    """Compare prices for a product across multiple online retailers."""
    response = get_tavily().invoke(f"{product_name} price buy")

    results, error = parse_tavily_response(response)
    if error:
        return error

    if not results:
        return "No price information found."

    return format_results(results, max_sources)
