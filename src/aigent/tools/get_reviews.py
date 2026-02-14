from langchain_core.tools import tool
from aigent.schemas import ReviewQuery
from aigent.tools._client import get_tavily, parse_tavily_response, format_results


@tool(args_schema=ReviewQuery)
def get_reviews(product_name: str, max_reviews: int = 3) -> str:
    """Fetch product reviews and ratings from the web."""
    response = get_tavily().invoke(f"{product_name} review rating")

    results, error = parse_tavily_response(response)
    if error:
        return error

    if not results:
        return "No reviews found for this product."

    return format_results(results, max_reviews, url_label="Source")
