# Web Interface Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a FastAPI backend with SSE streaming and a Next.js chat frontend to the existing aigent LangGraph agent.

**Architecture:** FastAPI serves three endpoints (create session, send message, approve tool). The message and approve endpoints return SSE streams using LangGraph's `astream(stream_mode=["messages", "updates"])`. A Next.js frontend connects via a `useChatStream` hook that reads SSE events and renders chat bubbles, tool approval cards, and receipt cards.

**Tech Stack:** FastAPI, uvicorn, sse-starlette, httpx (test), Next.js 15, TypeScript, Tailwind CSS

---

### Task 1: Add backend dependencies

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add FastAPI and SSE dependencies**

Run: `uv add fastapi uvicorn sse-starlette`
Expected: Dependencies added to `pyproject.toml`, lock updated

**Step 2: Add httpx as dev dependency for testing**

Run: `uv add --dev httpx`
Expected: httpx added under `[dependency-groups]` dev

**Step 3: Create API package directories**

Run:
```bash
mkdir -p src/aigent/api
touch src/aigent/api/__init__.py
```

**Step 4: Commit**

```bash
git add pyproject.toml src/aigent/api/__init__.py
git commit -m "chore: add FastAPI, uvicorn, sse-starlette dependencies"
```

---

### Task 2: SSE streaming helpers

**Files:**
- Create: `src/aigent/api/streaming.py`
- Create: `tests/test_streaming.py`

**Step 1: Write failing tests for SSE event formatting**

```python
# tests/test_streaming.py
from aigent.api.streaming import format_sse_event


def test_format_token_event():
    result = format_sse_event("token", {"content": "Hello"})
    assert result == 'event: token\ndata: {"content": "Hello"}\n\n'


def test_format_approval_required_event():
    tool_calls = [{"id": "1", "name": "search_product", "args": {"query": "headphones"}}]
    result = format_sse_event("approval_required", {"tool_calls": tool_calls})
    assert "approval_required" in result
    assert "search_product" in result


def test_format_done_event():
    result = format_sse_event("done", {})
    assert result == 'event: done\ndata: {}\n\n'


def test_format_error_event():
    result = format_sse_event("error", {"message": "Something went wrong"})
    assert "error" in result
    assert "Something went wrong" in result
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_streaming.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aigent.api.streaming'`

**Step 3: Implement streaming helpers**

```python
# src/aigent/api/streaming.py
import json


def format_sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event string.

    Args:
        event: Event type name (e.g. "token", "approval_required", "done")
        data: Event payload dict, will be JSON-serialized

    Returns:
        Formatted SSE string: "event: <type>\\ndata: <json>\\n\\n"
    """
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_streaming.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add src/aigent/api/streaming.py tests/test_streaming.py
git commit -m "feat: add SSE event formatting helpers"
```

---

### Task 3: Refactor build_agent to accept external checkpointer

**Files:**
- Modify: `src/aigent/agent.py`
- Modify: `tests/test_agent.py`

The current `build_agent()` creates its own `InMemorySaver`. The API needs to share
one checkpointer across sessions. Refactor to accept an optional checkpointer parameter.

**Step 1: Update test to verify optional checkpointer**

```python
# tests/test_agent.py
import os
from unittest.mock import patch
from langgraph.checkpoint.memory import InMemorySaver
from aigent.agent import build_agent


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test", "TAVILY_API_KEY": "tvly-test"})
def test_build_agent_returns_compiled_graph():
    agent = build_agent()
    assert hasattr(agent, "invoke")
    assert hasattr(agent, "ainvoke")
    assert hasattr(agent, "get_state")


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test", "TAVILY_API_KEY": "tvly-test"})
def test_build_agent_accepts_external_checkpointer():
    checkpointer = InMemorySaver()
    agent = build_agent(checkpointer=checkpointer)
    assert hasattr(agent, "ainvoke")
```

**Step 2: Run tests to verify new test fails**

Run: `uv run pytest tests/test_agent.py -v`
Expected: `test_build_agent_accepts_external_checkpointer` FAIL with `TypeError: build_agent() got an unexpected keyword argument 'checkpointer'`

**Step 3: Update build_agent signature**

Replace the `build_agent` function in `src/aigent/agent.py`:

```python
def build_agent(checkpointer=None):
    """Build and return the compiled agent graph.

    Args:
        checkpointer: Optional checkpoint saver. If None, creates an InMemorySaver.
    """
    model = init_chat_model("gpt-4o", model_provider="openai")
    if checkpointer is None:
        checkpointer = InMemorySaver()

    summarization_hook = create_summarization_hook(model, max_messages=5)

    agent = create_react_agent(
        model=model,
        tools=[search_product, compare_prices, get_reviews, calculate_budget],
        checkpointer=checkpointer,
        pre_model_hook=summarization_hook,
        interrupt_before=["tools"],
        response_format=Receipt,
    )

    return agent
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_agent.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add src/aigent/agent.py tests/test_agent.py
git commit -m "refactor: allow build_agent to accept external checkpointer"
```

---

### Task 4: FastAPI app with session endpoint

**Files:**
- Create: `src/aigent/api/app.py`
- Create: `src/aigent/api/routes.py`
- Create: `tests/test_api.py`

**Step 1: Write failing test for session creation**

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from aigent.api.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_create_session(client):
    response = await client.post("/chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], str)


@pytest.mark.asyncio
async def test_create_two_sessions_different_ids(client):
    r1 = await client.post("/chat/sessions")
    r2 = await client.post("/chat/sessions")
    assert r1.json()["session_id"] != r2.json()["session_id"]
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aigent.api.app'`

**Step 3: Implement the FastAPI app**

```python
# src/aigent/api/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from aigent.agent import build_agent
from aigent.api.routes import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="aigent API")

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
```

```python
# src/aigent/api/routes.py
import uuid
from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/sessions")
async def create_session(request: Request):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    request.app.state.sessions[session_id] = {
        "thread_id": session_id,
    }
    return {"session_id": session_id}
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_api.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add src/aigent/api/app.py src/aigent/api/routes.py tests/test_api.py
git commit -m "feat: add FastAPI app with session creation endpoint"
```

---

### Task 5: Message streaming endpoint

**Files:**
- Modify: `src/aigent/api/routes.py`
- Modify: `tests/test_api.py`

**Step 1: Write failing test for message endpoint**

Append to `tests/test_api.py`:

```python
@pytest.mark.asyncio
async def test_send_message_returns_sse_stream(client):
    # Create session first
    session_resp = await client.post("/chat/sessions")
    session_id = session_resp.json()["session_id"]

    # Send message — should get SSE stream back
    response = await client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "Hello"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    # Should contain at least a done event
    assert "event: done" in response.text or "event: error" in response.text


@pytest.mark.asyncio
async def test_send_message_invalid_session(client):
    response = await client.post(
        "/chat/sessions/nonexistent/messages",
        json={"content": "Hello"},
    )
    assert response.status_code == 404
```

**Step 2: Run tests to verify new tests fail**

Run: `uv run pytest tests/test_api.py -v`
Expected: New tests FAIL with 404 (route not found) or similar

**Step 3: Implement the message endpoint**

Add to `src/aigent/api/routes.py`:

```python
import uuid
import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import AIMessageChunk, HumanMessage

from aigent.api.streaming import format_sse_event

router = APIRouter()


class MessageRequest(BaseModel):
    content: str


@router.post("/sessions")
async def create_session(request: Request):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    request.app.state.sessions[session_id] = {
        "thread_id": session_id,
    }
    return {"session_id": session_id}


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, body: MessageRequest, request: Request):
    """Send a user message and stream the agent's response via SSE."""
    if session_id not in request.app.state.sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = request.app.state.agent
    config = {"configurable": {"thread_id": session_id}}

    async def event_generator():
        try:
            async for event in agent.astream(
                {"messages": [("user", body.content)]},
                config=config,
                stream_mode=["messages", "updates"],
            ):
                mode, payload = event

                if mode == "messages":
                    message, metadata = payload
                    # Only stream AI message chunks (tokens)
                    if isinstance(message, AIMessageChunk) and message.content:
                        yield format_sse_event("token", {"content": message.content})

                    # Check for tool calls in the message
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tc in message.tool_calls:
                            yield format_sse_event("tool_call", {
                                "id": tc.get("id", ""),
                                "name": tc.get("name", ""),
                                "args": tc.get("args", {}),
                            })

                elif mode == "updates":
                    # Check if we hit an interrupt (updates will stop, state.next will be set)
                    pass

            # After streaming, check if agent is waiting for approval
            state = await agent.aget_state(config)
            if state.next:
                last_msg = state.values["messages"][-1]
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    tool_calls = [
                        {"id": tc["id"], "name": tc["name"], "args": tc["args"]}
                        for tc in last_msg.tool_calls
                    ]
                    yield format_sse_event("approval_required", {"tool_calls": tool_calls})
                    return

            # Check for structured receipt output
            state = await agent.aget_state(config)
            if not state.next:
                structured = state.values.get("structured_response")
                if structured:
                    yield format_sse_event("receipt", {
                        "product_name": structured.product_name,
                        "price": structured.price,
                        "currency": structured.currency,
                    })

            yield format_sse_event("done", {})

        except Exception as e:
            yield format_sse_event("error", {"message": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_api.py -v`
Expected: 4 passed

Note: The `test_send_message_returns_sse_stream` test uses a mocked agent via fake API keys, so it may produce an error event. The test checks for either `done` or `error` — both confirm the SSE stream works. If the test fails because the agent can't initialize without real keys, add this fixture override:

```python
@pytest.fixture
def app():
    import os
    os.environ.setdefault("OPENAI_API_KEY", "sk-test")
    os.environ.setdefault("TAVILY_API_KEY", "tvly-test")
    return create_app()
```

**Step 5: Commit**

```bash
git add src/aigent/api/routes.py tests/test_api.py
git commit -m "feat: add message streaming endpoint with SSE"
```

---

### Task 6: Approval endpoint

**Files:**
- Modify: `src/aigent/api/routes.py`
- Modify: `tests/test_api.py`

**Step 1: Write failing test for approval endpoint**

Append to `tests/test_api.py`:

```python
@pytest.mark.asyncio
async def test_approve_invalid_session(client):
    response = await client.post(
        "/chat/sessions/nonexistent/approve",
        json={"approved": True},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_approve_endpoint_exists(client):
    session_resp = await client.post("/chat/sessions")
    session_id = session_resp.json()["session_id"]

    response = await client.post(
        f"/chat/sessions/{session_id}/approve",
        json={"approved": True},
    )
    # Should return SSE stream (even if agent has nothing to resume)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
```

**Step 2: Run tests to verify new tests fail**

Run: `uv run pytest tests/test_api.py -v`
Expected: New tests FAIL (route not found)

**Step 3: Implement the approval endpoint**

Add to `src/aigent/api/routes.py`:

```python
class ApprovalRequest(BaseModel):
    approved: bool


@router.post("/sessions/{session_id}/approve")
async def approve_tool(session_id: str, body: ApprovalRequest, request: Request):
    """Approve or deny pending tool execution, then stream the result."""
    if session_id not in request.app.state.sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = request.app.state.agent
    config = {"configurable": {"thread_id": session_id}}

    async def event_generator():
        try:
            if not body.approved:
                yield format_sse_event("error", {"message": "Tool execution denied by user"})
                yield format_sse_event("done", {})
                return

            # Resume the agent from the interrupt by passing None
            async for event in agent.astream(
                None,
                config=config,
                stream_mode=["messages", "updates"],
            ):
                mode, payload = event

                if mode == "messages":
                    message, metadata = payload
                    if isinstance(message, AIMessageChunk) and message.content:
                        yield format_sse_event("token", {"content": message.content})

            # After streaming, check if agent needs another approval or is done
            state = await agent.aget_state(config)
            if state.next:
                last_msg = state.values["messages"][-1]
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    tool_calls = [
                        {"id": tc["id"], "name": tc["name"], "args": tc["args"]}
                        for tc in last_msg.tool_calls
                    ]
                    yield format_sse_event("approval_required", {"tool_calls": tool_calls})
                    return

            # Check for structured receipt
            state = await agent.aget_state(config)
            if not state.next:
                structured = state.values.get("structured_response")
                if structured:
                    yield format_sse_event("receipt", {
                        "product_name": structured.product_name,
                        "price": structured.price,
                        "currency": structured.currency,
                    })

            yield format_sse_event("done", {})

        except Exception as e:
            yield format_sse_event("error", {"message": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_api.py -v`
Expected: 6 passed

**Step 5: Update api __init__.py**

```python
# src/aigent/api/__init__.py
from aigent.api.app import create_app

__all__ = ["create_app"]
```

**Step 6: Commit**

```bash
git add src/aigent/api/
git commit -m "feat: add approval endpoint and complete API routes"
```

---

### Task 7: Next.js scaffolding

**Files:**
- Create: `web/` directory via `create-next-app`
- Create: `Makefile`

**Step 1: Scaffold Next.js app**

Run:
```bash
cd C:\NUS\Projects\aigent
npx create-next-app@latest web --typescript --tailwind --eslint --app --src-dir --no-import-alias --use-npm
```

Expected: `web/` directory created with Next.js boilerplate

**Step 2: Create Makefile**

```makefile
# Makefile
.PHONY: backend frontend dev

backend:
	uv run uvicorn aigent.api.app:create_app --factory --reload --port 8000

frontend:
	cd web && npm run dev

dev:
	$(MAKE) backend & $(MAKE) frontend
```

**Step 3: Create next.config.ts with API proxy**

Replace `web/next.config.ts` with:

```typescript
// web/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
```

**Step 4: Verify Next.js starts**

Run: `cd web && npm run dev` (then Ctrl+C to stop)
Expected: Next.js dev server starts on port 3000

**Step 5: Commit**

```bash
git add web/ Makefile
git commit -m "chore: scaffold Next.js frontend and Makefile"
```

---

### Task 8: TypeScript types and useChatStream hook

**Files:**
- Create: `web/src/types.ts`
- Create: `web/src/hooks/useChatStream.ts`

**Step 1: Define TypeScript types**

```typescript
// web/src/types.ts
export type MessageRole = "user" | "assistant";

export interface ToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
}

export interface Receipt {
  product_name: string;
  price: number;
  currency: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  toolCalls?: ToolCall[];
  receipt?: Receipt;
  isStreaming?: boolean;
  isApprovalRequired?: boolean;
}

export type ChatStatus = "idle" | "streaming" | "awaiting_approval" | "error";
```

**Step 2: Implement useChatStream hook**

```typescript
// web/src/hooks/useChatStream.ts
"use client";

import { useState, useCallback, useRef } from "react";
import { ChatMessage, ChatStatus, ToolCall, Receipt } from "@/types";

const API_BASE = "/api/chat";

function generateId(): string {
  return Math.random().toString(36).substring(2, 10);
}

async function readSSEStream(
  response: Response,
  handlers: {
    onToken: (content: string) => void;
    onApprovalRequired: (toolCalls: ToolCall[]) => void;
    onReceipt: (receipt: Receipt) => void;
    onToolCall: (toolCall: ToolCall) => void;
    onDone: () => void;
    onError: (message: string) => void;
  }
) {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEvent = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ") && currentEvent) {
        const data = JSON.parse(line.slice(6));
        switch (currentEvent) {
          case "token":
            handlers.onToken(data.content);
            break;
          case "tool_call":
            handlers.onToolCall(data);
            break;
          case "approval_required":
            handlers.onApprovalRequired(data.tool_calls);
            break;
          case "receipt":
            handlers.onReceipt(data);
            break;
          case "done":
            handlers.onDone();
            break;
          case "error":
            handlers.onError(data.message);
            break;
        }
        currentEvent = "";
      }
    }
  }
}

export function useChatStream() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<ChatStatus>("idle");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const pendingToolCallsRef = useRef<ToolCall[]>([]);

  const createSession = useCallback(async () => {
    const resp = await fetch(`${API_BASE}/sessions`, { method: "POST" });
    const data = await resp.json();
    setSessionId(data.session_id);
    return data.session_id;
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      let sid = sessionId;
      if (!sid) {
        sid = await createSession();
      }

      // Add user message
      const userMsg: ChatMessage = {
        id: generateId(),
        role: "user",
        content,
      };
      const assistantId = generateId();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setStatus("streaming");

      const response = await fetch(`${API_BASE}/sessions/${sid}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });

      await readSSEStream(response, {
        onToken: (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + token }
                : m
            )
          );
        },
        onToolCall: (toolCall) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, toolCalls: [...(m.toolCalls || []), toolCall] }
                : m
            )
          );
        },
        onApprovalRequired: (toolCalls) => {
          pendingToolCallsRef.current = toolCalls;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    isStreaming: false,
                    isApprovalRequired: true,
                    toolCalls: toolCalls,
                  }
                : m
            )
          );
          setStatus("awaiting_approval");
        },
        onReceipt: (receipt) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, receipt } : m
            )
          );
        },
        onDone: () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, isStreaming: false } : m
            )
          );
          setStatus("idle");
        },
        onError: (message) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content || `Error: ${message}`, isStreaming: false }
                : m
            )
          );
          setStatus("error");
        },
      });
    },
    [sessionId, createSession]
  );

  const approveToolCall = useCallback(
    async (approved: boolean) => {
      if (!sessionId) return;

      setStatus("streaming");

      // Find the last assistant message to continue streaming into
      const assistantId = generateId();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        isStreaming: true,
      };

      // Mark previous approval as handled, add new assistant message
      setMessages((prev) => [
        ...prev.map((m) =>
          m.isApprovalRequired ? { ...m, isApprovalRequired: false } : m
        ),
        assistantMsg,
      ]);

      const response = await fetch(
        `${API_BASE}/sessions/${sessionId}/approve`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ approved }),
        }
      );

      await readSSEStream(response, {
        onToken: (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + token }
                : m
            )
          );
        },
        onToolCall: (toolCall) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, toolCalls: [...(m.toolCalls || []), toolCall] }
                : m
            )
          );
        },
        onApprovalRequired: (toolCalls) => {
          pendingToolCallsRef.current = toolCalls;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, isStreaming: false, isApprovalRequired: true, toolCalls: toolCalls }
                : m
            )
          );
          setStatus("awaiting_approval");
        },
        onReceipt: (receipt) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, receipt } : m
            )
          );
        },
        onDone: () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, isStreaming: false } : m
            )
          );
          setStatus("idle");
        },
        onError: (message) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content || `Error: ${message}`, isStreaming: false }
                : m
            )
          );
          setStatus("error");
        },
      });
    },
    [sessionId]
  );

  return { messages, status, sendMessage, approveToolCall };
}
```

**Step 3: Create hooks directory**

Run: `mkdir -p web/src/hooks`

**Step 4: Commit**

```bash
git add web/src/types.ts web/src/hooks/useChatStream.ts
git commit -m "feat: add TypeScript types and useChatStream SSE hook"
```

---

### Task 9: Chat UI components

**Files:**
- Create: `web/src/components/ChatMessage.tsx`
- Create: `web/src/components/ToolCallCard.tsx`
- Create: `web/src/components/ReceiptCard.tsx`
- Create: `web/src/components/ChatInput.tsx`

**Step 1: Create components directory**

Run: `mkdir -p web/src/components`

**Step 2: Implement ChatMessage**

```tsx
// web/src/components/ChatMessage.tsx
"use client";

import { ChatMessage as ChatMessageType } from "@/types";
import { ToolCallCard } from "./ToolCallCard";
import { ReceiptCard } from "./ReceiptCard";

interface Props {
  message: ChatMessageType;
  onApprove?: () => void;
  onDeny?: () => void;
}

export function ChatMessage({ message, onApprove, onDeny }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-900"
        }`}
      >
        {message.content && (
          <p className="whitespace-pre-wrap">{message.content}</p>
        )}

        {message.isStreaming && !message.content && (
          <span className="animate-pulse text-gray-400">Thinking...</span>
        )}

        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-2 space-y-2">
            {message.toolCalls.map((tc) => (
              <ToolCallCard
                key={tc.id}
                toolCall={tc}
                showApproval={!!message.isApprovalRequired}
                onApprove={onApprove}
                onDeny={onDeny}
              />
            ))}
          </div>
        )}

        {message.receipt && (
          <div className="mt-2">
            <ReceiptCard receipt={message.receipt} />
          </div>
        )}
      </div>
    </div>
  );
}
```

**Step 3: Implement ToolCallCard**

```tsx
// web/src/components/ToolCallCard.tsx
"use client";

import { ToolCall } from "@/types";

interface Props {
  toolCall: ToolCall;
  showApproval: boolean;
  onApprove?: () => void;
  onDeny?: () => void;
}

export function ToolCallCard({ toolCall, showApproval, onApprove, onDeny }: Props) {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm">
      <div className="font-medium text-amber-800">
        Tool: {toolCall.name}
      </div>
      <pre className="mt-1 text-xs text-amber-700 overflow-x-auto">
        {JSON.stringify(toolCall.args, null, 2)}
      </pre>

      {showApproval && (
        <div className="mt-2 flex gap-2">
          <button
            onClick={onApprove}
            className="rounded-md bg-green-600 px-3 py-1 text-xs font-medium text-white hover:bg-green-700"
          >
            Approve
          </button>
          <button
            onClick={onDeny}
            className="rounded-md bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700"
          >
            Deny
          </button>
        </div>
      )}
    </div>
  );
}
```

**Step 4: Implement ReceiptCard**

```tsx
// web/src/components/ReceiptCard.tsx
"use client";

import { Receipt } from "@/types";

interface Props {
  receipt: Receipt;
}

export function ReceiptCard({ receipt }: Props) {
  return (
    <div className="rounded-lg border border-green-200 bg-green-50 p-4">
      <h3 className="text-sm font-semibold text-green-800">Receipt</h3>
      <div className="mt-2 space-y-1 text-sm text-green-700">
        <div className="flex justify-between">
          <span>Product</span>
          <span className="font-medium">{receipt.product_name}</span>
        </div>
        <div className="flex justify-between">
          <span>Price</span>
          <span className="font-medium">
            {receipt.price} {receipt.currency}
          </span>
        </div>
      </div>
    </div>
  );
}
```

**Step 5: Implement ChatInput**

```tsx
// web/src/components/ChatInput.tsx
"use client";

import { useState, FormEvent } from "react";

interface Props {
  onSend: (content: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask about products..."
        disabled={disabled}
        className="flex-1 rounded-xl border border-gray-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className="rounded-xl bg-blue-600 px-6 py-3 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        Send
      </button>
    </form>
  );
}
```

**Step 6: Commit**

```bash
git add web/src/components/
git commit -m "feat: add chat UI components (message, tool card, receipt, input)"
```

---

### Task 10: Chat page

**Files:**
- Modify: `web/src/app/page.tsx`
- Modify: `web/src/app/layout.tsx`

**Step 1: Update layout.tsx**

Replace `web/src/app/layout.tsx`:

```tsx
// web/src/app/layout.tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "aigent - Product Search Agent",
  description: "AI-powered product search with human-in-the-loop approval",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-white antialiased">{children}</body>
    </html>
  );
}
```

**Step 2: Implement the chat page**

Replace `web/src/app/page.tsx`:

```tsx
// web/src/app/page.tsx
"use client";

import { useEffect, useRef } from "react";
import { useChatStream } from "@/hooks/useChatStream";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";

export default function Home() {
  const { messages, status, sendMessage, approveToolCall } = useChatStream();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const isDisabled = status === "streaming" || status === "awaiting_approval";

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="border-b border-gray-200 px-6 py-4">
        <h1 className="text-lg font-semibold text-gray-900">aigent</h1>
        <p className="text-sm text-gray-500">Product search assistant</p>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <p className="text-gray-400">
              Ask me to find products, compare prices, or check reviews.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            message={msg}
            onApprove={() => approveToolCall(true)}
            onDeny={() => approveToolCall(false)}
          />
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 px-6 py-4">
        <ChatInput onSend={sendMessage} disabled={isDisabled} />
        {status === "streaming" && (
          <p className="mt-2 text-xs text-gray-400">Agent is thinking...</p>
        )}
        {status === "awaiting_approval" && (
          <p className="mt-2 text-xs text-amber-600">
            Waiting for your approval to run the tool above.
          </p>
        )}
      </div>
    </div>
  );
}
```

**Step 3: Verify frontend builds**

Run: `cd web && npm run build`
Expected: Build succeeds with no errors

**Step 4: Commit**

```bash
git add web/src/app/
git commit -m "feat: implement chat page with streaming and HITL approval"
```

---

### Task 11: Integration smoke test

**Files:** None (manual verification)

**Step 1: Start backend**

Run: `uv run uvicorn aigent.api.app:create_app --factory --reload --port 8000`
Expected: Server starts on http://localhost:8000

**Step 2: Start frontend (in separate terminal)**

Run: `cd web && npm run dev`
Expected: Next.js starts on http://localhost:3000

**Step 3: Test the flow**

1. Open http://localhost:3000
2. Type "Find me wireless headphones under $100"
3. Verify: agent streams tokens, then shows tool approval card
4. Click "Approve"
5. Verify: agent resumes, searches, returns a Receipt card

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: complete web interface integration"
```

---

## Summary of files created/modified

| File | Purpose |
|------|---------|
| `src/aigent/api/__init__.py` | API package init |
| `src/aigent/api/app.py` | FastAPI app factory, CORS, shared state |
| `src/aigent/api/routes.py` | /chat/* endpoints (sessions, messages, approve) |
| `src/aigent/api/streaming.py` | SSE event formatting helper |
| `src/aigent/agent.py` | Modified: accept optional checkpointer |
| `tests/test_streaming.py` | SSE helper unit tests |
| `tests/test_api.py` | API endpoint integration tests |
| `web/` | Next.js frontend (scaffolded via create-next-app) |
| `web/src/types.ts` | TypeScript types for chat messages |
| `web/src/hooks/useChatStream.ts` | SSE client hook |
| `web/src/components/ChatMessage.tsx` | Chat message bubble component |
| `web/src/components/ToolCallCard.tsx` | Tool approval card component |
| `web/src/components/ReceiptCard.tsx` | Receipt display card |
| `web/src/components/ChatInput.tsx` | Chat text input + send button |
| `web/src/app/page.tsx` | Main chat page |
| `web/src/app/layout.tsx` | App layout |
| `web/next.config.ts` | API proxy rewrites |
| `Makefile` | Dev commands (backend, frontend, dev) |
