from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from pricewise.agent import build_agent
from pricewise.api.routes import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    load_dotenv()

    app = FastAPI(title="Pricewise API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Shared state: one checkpointer, one agent
    checkpointer = InMemorySaver()
    agent = build_agent(checkpointer=checkpointer)
    app.state.agent = agent
    app.state.sessions = {}  # session_id -> thread config

    app.include_router(router, prefix="/chat")

    return app
