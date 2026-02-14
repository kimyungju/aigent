# Web Interface Design: FastAPI + Next.js Chat UI

**Goal:** Add a full-stack web interface to aigent — FastAPI backend streaming agent events via SSE, Next.js frontend with a chat UI featuring inline HITL approval.

**Tech Stack:** FastAPI, uvicorn, sse-starlette, Next.js (TypeScript), Tailwind CSS

---

## Architecture

```
┌─────────────────────┐         SSE / REST         ┌─────────────────────┐
│   Next.js Frontend   │ ◄──────────────────────── │   FastAPI Backend    │
│                      │                            │                      │
│  /chat page          │ ── POST /sessions ───────► │  LangGraph Agent     │
│  Message bubbles     │ ◄── SSE /messages ──────── │  InMemorySaver       │
│  Approval buttons    │ ── POST /approve ────────► │  Tavily + tools      │
│  Receipt card        │                            │                      │
└─────────────────────┘                            └─────────────────────┘
```

- Backend manages agent state via LangGraph's `InMemorySaver` (keyed by `thread_id`/session)
- Frontend creates a session, sends messages, and opens SSE connections to stream events
- When the agent hits `interrupt_before=["tools"]`, the SSE stream emits an `approval_required` event
- User clicks approve/deny in the chat UI, which POSTs to `/approve`
- Agent resumes and continues streaming

---

## API Endpoints

### `POST /chat/sessions`
Create a new chat session.
- Response: `{ "session_id": "<uuid>" }`
- Backend creates a new LangGraph thread with InMemorySaver

### `POST /chat/sessions/{session_id}/messages`
Send a user message and stream the agent's response.
- Request body: `{ "content": "<user message>" }`
- Response: SSE stream

SSE event types:

| Event | Data | When |
|-------|------|------|
| `token` | `{ "content": "..." }` | Agent generates text |
| `tool_call` | `{ "id", "name", "args" }` | Agent wants to call a tool |
| `approval_required` | `{ "tool_calls": [...] }` | Agent paused, waiting for HITL |
| `tool_result` | `{ "name", "result" }` | Tool finished executing |
| `receipt` | `{ "product_name", "price", "currency" }` | Structured Receipt output |
| `done` | `{}` | Stream complete |
| `error` | `{ "message" }` | Error occurred |

### `POST /chat/sessions/{session_id}/approve`
Approve or deny pending tool execution.
- Request body: `{ "approved": true/false }`
- Response: SSE stream (agent resumes streaming)

---

## Frontend (Next.js)

### Project structure
`web/` directory at repo root, separate from the Python `src/` backend.

### Pages
Single page: `/` (chat interface)

### Message rendering
- **User message** — right-aligned bubble
- **Agent text** — left-aligned bubble, streams in token by token via SSE
- **Tool call card** — shows tool name + args, with Approve/Deny buttons when `approval_required`
- **Receipt card** — styled card with product name, price, currency

### State management
React `useState` + `useReducer`. No external state library.

### SSE handling
Custom `useChatStream` hook:
1. POSTs message to create SSE stream
2. Reads events via `fetch` + `ReadableStream` (not `EventSource`, to support POST)
3. Dispatches events to update chat state

### Styling
Tailwind CSS (included with Next.js).

---

## Error Handling

- **Backend:** FastAPI exception handlers return JSON errors. Mid-stream failures emit SSE `error` events.
- **Agent errors:** Tool failures and LLM errors are caught and streamed as `error` events, not connection crashes.
- **Frontend:** Error messages shown inline in the chat with a "Retry" option.
- **HTTP errors:** Session not found → 404, invalid input → 422 (FastAPI validation).

---

## Testing

- **Backend:** pytest with `httpx.AsyncClient` for API endpoint tests. Mock the LangGraph agent to test SSE streaming, approval flow, and error handling without real API keys.
- **Frontend:** Manual testing for the chat UI. Critical logic lives on the backend.

---

## Dev Experience

- `Makefile` with targets: `make backend` (uvicorn :8000), `make frontend` (next dev :3000), `make dev` (both)
- Next.js `rewrites` in `next.config.ts` proxy `/api/*` → `http://localhost:8000` for local dev
- Both apps in the same git repo (monorepo)

---

## File Structure (New)

```
aigent/
├── src/aigent/           # Existing agent code
│   ├── api/              # NEW: FastAPI app
│   │   ├── __init__.py
│   │   ├── app.py        # FastAPI app, CORS, lifespan
│   │   ├── routes.py     # /chat/* endpoints
│   │   └── streaming.py  # SSE event helpers
│   └── ...
├── web/                  # NEW: Next.js frontend
│   ├── package.json
│   ├── next.config.ts
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx       # Chat page
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ToolCallCard.tsx
│   │   │   ├── ReceiptCard.tsx
│   │   │   └── ChatInput.tsx
│   │   └── hooks/
│   │       └── useChatStream.ts
│   └── tailwind.config.ts
├── Makefile              # NEW: dev commands
├── main.py               # Existing CLI entrypoint
└── ...
```
