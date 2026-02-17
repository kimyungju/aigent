import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.tools import tool
from pricewise.schemas import DelegationQuery, ProductResearchItem
from pricewise.tools._client import get_tavily, parse_tavily_response


def _research_one(item: ProductResearchItem) -> dict:
    """Research a single product via Tavily (sync, runs in thread)."""
    query = item.product_name
    if item.budget:
        query += f" under ${item.budget}"

    response = get_tavily().invoke(query)
    results, error = parse_tavily_response(response)

    if error or not results:
        return {"product": item.product_name, "success": False, "error": error or "No results found"}

    top = results[0]
    return {
        "product": item.product_name,
        "success": True,
        "content": top.get("content", ""),
        "url": top.get("url", ""),
        "budget": item.budget,
    }


@tool(args_schema=DelegationQuery)
def delegate_research(products: list, total_budget: float | None = None) -> str:
    """Research multiple products in parallel and synthesize results.

    Use this when the user asks about multiple product categories in one query
    (e.g. "I need a laptop, monitor, and keyboard for under $2000").
    Each product is researched independently and results are combined.
    """
    items = [
        p if isinstance(p, ProductResearchItem) else ProductResearchItem(**p)
        for p in products
    ]

    # Fan out via thread pool (Tavily client is sync)
    with ThreadPoolExecutor(max_workers=min(len(items), 5)) as pool:
        futures = {pool.submit(_research_one, item): item for item in items}
        results = []
        for future in as_completed(futures):
            results.append(future.result())

    # Format output
    lines = [f"Multi-Product Research ({len(items)} items):\n"]
    total_cost = 0.0

    for res in results:
        lines.append(f"--- {res['product']} ---")
        if res["success"]:
            lines.append(f"  {res['content']}")
            lines.append(f"  Source: {res['url']}")
            price_match = re.search(r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)", res["content"])
            if price_match:
                price = float(price_match.group(1).replace(",", ""))
                total_cost += price
                lines.append(f"  Estimated price: ${price:.2f}")
            if res.get("budget"):
                lines.append(f"  Budget: ${res['budget']:.2f}")
        else:
            lines.append(f"  Could not find results: {res['error']}")
        lines.append("")

    if total_budget and total_cost > 0:
        lines.append(f"Estimated total: ${total_cost:.2f} / ${total_budget:.2f} budget")
        diff = total_budget - total_cost
        if diff >= 0:
            lines.append(f"Under budget by ${diff:.2f}")
        else:
            lines.append(f"Over budget by ${-diff:.2f}")

    return "\n".join(lines)
