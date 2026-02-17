# main.py
"""Async entrypoint demonstrating the LangGraph autonomous agent.

This uses the functional create_react_agent approach instead of the legacy
AgentExecutor. The key difference: instead of an opaque while-loop that
calls the LLM and tools in sequence, we have a compiled state graph with
explicit nodes, edges, and checkpointing — making the execution fully
inspectable, interruptible, and resumable.
"""
import asyncio
import os

from dotenv import load_dotenv
from langgraph.types import Command

from aigent.agent import build_agent
from aigent.middleware.human_approval import prompt_for_approval


async def main():
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set in .env")
        return
    if not os.getenv("TAVILY_API_KEY"):
        print("Error: TAVILY_API_KEY not set in .env")
        return

    agent = build_agent()

    # Thread config enables checkpointing — the agent remembers state
    # across invocations within the same thread, which powers the
    # interrupt/resume flow for human-in-the-loop approval.
    config = {"configurable": {"thread_id": "demo-session-1"}}

    user_query = "Find me wireless headphones under $100, compare prices, check reviews, and calculate total with 8% tax"
    print(f"\nUser: {user_query}\n")

    # First invocation: the agent reasons and decides to call a tool.
    # Per-tool interrupt() calls pause execution before wrapped tools run.
    result = await agent.ainvoke(
        {"messages": [("user", user_query)]},
        config=config,
    )

    # Check if the agent is at an interrupt point (pending tool execution)
    state = await agent.aget_state(config)

    while state.next:
        # Read interrupt data from state.tasks (per-tool interrupt() pattern)
        tool_calls = []
        for task in state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                for intr in task.interrupts:
                    if isinstance(intr.value, dict) and "tool" in intr.value:
                        tool_calls.append(intr.value)

        if tool_calls:
            approved = prompt_for_approval(tool_calls)
        else:
            # No interrupt data found — auto-approve to avoid getting stuck
            approved = True

        # Resume with Command(resume=...) so interrupt() receives the value
        result = await agent.ainvoke(Command(resume=approved), config=config)
        state = await agent.aget_state(config)

    # Extract the structured Receipt output
    receipt = result.get("structured_response")

    if receipt:
        print("\n=== Final Receipt ===")
        print(f"  Product: {receipt.product_name}")
        print(f"  Price:   {receipt.price} {receipt.currency}")
        if receipt.average_rating is not None:
            print(f"  Rating:  {receipt.average_rating}/5")
        if receipt.price_range:
            print(f"  Range:   {receipt.price_range}")
        if receipt.recommendation_reason:
            print(f"  Reason:  {receipt.recommendation_reason}")
        print("=====================")
    else:
        # Fallback: print the last agent message
        last_msg = result["messages"][-1]
        print(f"\nAgent: {last_msg.content}")


if __name__ == "__main__":
    asyncio.run(main())
