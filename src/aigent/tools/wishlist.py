"""Session-scoped wishlist tools.

Products are stored in a module-level dict keyed by session ID.
The session ID is passed via a ``ContextVar`` that the API layer sets
before invoking the agent.
"""

import contextvars

from langchain_core.tools import tool

session_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "session_id", default="default"
)

_wishlists: dict[str, list[dict]] = {}


@tool
def add_to_wishlist(
    product_name: str,
    price: float | None = None,
    url: str | None = None,
    notes: str | None = None,
) -> str:
    """Save a product to the user's wishlist for later reference.

    Call this when the user wants to bookmark or save a product they like.
    """
    sid = session_id_var.get()
    if sid not in _wishlists:
        _wishlists[sid] = []

    item = {
        "product_name": product_name,
        "price": price,
        "url": url,
        "notes": notes,
    }
    _wishlists[sid].append(item)

    count = len(_wishlists[sid])
    return f"Added '{product_name}' to wishlist. ({count} item{'s' if count != 1 else ''} total)"


@tool
def get_wishlist() -> str:
    """Retrieve all products currently saved in the user's wishlist."""
    sid = session_id_var.get()
    items = _wishlists.get(sid, [])

    if not items:
        return "Wishlist is empty."

    lines = []
    for i, item in enumerate(items, 1):
        line = f"{i}. {item['product_name']}"
        if item.get("price") is not None:
            line += f" — ${item['price']:.2f}"
        if item.get("url"):
            line += f" ({item['url']})"
        if item.get("notes"):
            line += f" [{item['notes']}]"
        lines.append(line)

    return "Wishlist:\n" + "\n".join(lines)
