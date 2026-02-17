from langchain_core.tools import tool
from pricewise.schemas import CouponQuery
from pricewise.tools._client import get_tavily, parse_tavily_response, format_results


@tool(args_schema=CouponQuery)
def find_coupons(product_or_retailer: str, max_results: int = 5) -> str:
    """Find active coupons, discount codes, and deals for a product or retailer.

    Use this when the user wants to find promotional codes, special offers,
    or current deals for a specific product or from a specific retailer.
    """
    response = get_tavily().invoke(f"{product_or_retailer} coupon discount code promo deal")

    results, error = parse_tavily_response(response)
    if error:
        return error
    if not results:
        return f"No active coupons or deals found for '{product_or_retailer}'."

    return format_results(results, max_results, url_label="Source")
