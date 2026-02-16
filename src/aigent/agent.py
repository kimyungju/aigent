"""Agent graph construction.

Uses LangGraph's create_react_agent — the functional, graph-based successor
to the old class-based AgentExecutor. Key advantages:
  - Declarative graph: nodes and edges are explicit, not hidden in a loop
  - Native checkpointing: state persists across invocations via configurable thread IDs
  - Built-in interrupt: human-in-the-loop via interrupt_before, no custom chains needed
  - Composable hooks: pre_model_hook for message management, response_format for output
"""
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

from aigent.schemas import Receipt
from aigent.tools import (
    search_product,
    compare_prices,
    get_reviews,
    calculate_budget,
    add_to_wishlist,
    get_wishlist,
    scrape_url,
)
from aigent.middleware.summarization import create_summarization_hook
from aigent.middleware.selective_interrupt import with_approval


def build_agent(checkpointer=None):
    """Build and return the compiled agent graph.

    The agent:
      1. Uses gpt-4o via init_chat_model (provider-agnostic initialization)
      2. Has tools for search, price comparison, reviews, budget, wishlist, and URL scraping
      3. Summarizes conversation history after 5 messages (pre_model_hook)
      4. Selectively pauses for approval: web-calling tools require HITL, safe tools auto-execute
      5. Returns a structured Receipt as its final output (response_format)
    """
    model = init_chat_model("gpt-4o", model_provider="openai")
    if checkpointer is None:
        checkpointer = InMemorySaver()

    # Summarization hook: compresses history when messages exceed threshold
    summarization_hook = create_summarization_hook(model, max_messages=5)

    # Unsafe tools (external API calls) require human approval.
    # Safe tools (pure computation, local state) auto-execute.
    tools = [
        with_approval(search_product),
        with_approval(compare_prices),
        with_approval(get_reviews),
        with_approval(scrape_url),
        calculate_budget,    # safe: pure math
        add_to_wishlist,     # safe: local state
        get_wishlist,        # safe: local state
    ]

    agent = create_react_agent(
        model=model,
        tools=tools,
        checkpointer=checkpointer,
        pre_model_hook=summarization_hook,
        response_format=Receipt,
    )

    return agent
