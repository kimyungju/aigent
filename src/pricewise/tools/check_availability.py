from langchain_core.tools import tool
from pricewise.schemas import AvailabilityQuery
from pricewise.tools._client import get_tavily, parse_tavily_response, format_results


@tool(args_schema=AvailabilityQuery)
def check_availability(product_name: str, max_sources: int = 5) -> str:
    """Check product availability and stock status across multiple retailers.

    Use this when the user wants to know if a product is in stock,
    where it can be purchased, or its availability across different stores.
    """
    response = get_tavily().invoke(f"{product_name} in stock available buy now")

    results, error = parse_tavily_response(response)
    if error:
        return error
    if not results:
        return f"No availability information found for '{product_name}'."

    return format_results(results, max_sources, url_label="Retailer")
