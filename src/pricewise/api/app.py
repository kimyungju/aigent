import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from pricewise.agent import build_agent
from pricewise.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    use_memory = os.getenv("USE_MEMORY_SAVER", "false").lower() == "true"

    if use_memory:
        checkpointer = InMemorySaver()
        app.state.agent = build_agent(checkpointer=checkpointer)
        app.state.sessions = {}
        yield
    else:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        conn_string = os.environ["CHECKPOINT_POSTGRES_URI"]
        async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
            await checkpointer.setup()
            app.state.agent = build_agent(checkpointer=checkpointer)
            app.state.sessions = {}
            yield


def create_app() -> FastAPI:
    load_dotenv()
    app = FastAPI(title="Pricewise API", lifespan=lifespan)

    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000"
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    app.include_router(router, prefix="/chat")
    return app
