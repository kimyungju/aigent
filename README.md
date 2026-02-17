# Pricewise

An AI-powered shopping assistant that searches for products, compares prices across retailers, analyzes reviews, and calculates totals — all through a conversational interface with human-in-the-loop approval.

## Features

- **Product Search** — Finds products matching your criteria using real-time web search via Tavily
- **Price Comparison** — Compares prices across multiple retailers to surface the best deals
- **Review Analysis** — Fetches and summarizes product reviews and ratings
- **Budget Calculator** — Computes totals with tax and checks against your budget
- **Human-in-the-Loop** — Every tool call requires your approval before execution, keeping you in control
- **Structured Output** — Returns a clean receipt with product name, price, rating, price range, and purchase reasoning
- **Conversation Summarization** — Automatically compresses long conversations to maintain context without hitting token limits
- **Web Interface** — Chat-based UI built with Next.js for an accessible, real-time experience

## Architecture

```
┌─────────────┐     SSE      ┌──────────────┐    LangGraph    ┌────────────┐
│   Next.js   │◄────────────►│   FastAPI     │◄──────────────►│  AI Agent   │
│   Frontend  │              │   Backend     │                │  (gpt-4o)   │
└─────────────┘              └──────────────┘                └──────┬─────┘
                                                                    │
                                                  ┌─────────────────┼─────────────────┐
                                                  │                 │                 │
                                           ┌──────▼───┐    ┌───────▼──┐    ┌─────────▼──┐
                                           │  Tavily   │    │  Budget  │    │  Summarize │
                                           │  Search   │    │  Calc    │    │  Middleware │
                                           └──────────┘    └──────────┘    └────────────┘
```

The agent is built with LangGraph's `create_react_agent` and orchestrates four tools:

| Tool | Description |
|------|-------------|
| `search_product` | Searches for products via Tavily web search |
| `compare_prices` | Compares prices across multiple retailers |
| `get_reviews` | Fetches product reviews and ratings |
| `calculate_budget` | Computes totals with tax and validates against budget |

A **pre-model summarization hook** compresses conversation history when it exceeds a configurable threshold, and **human-in-the-loop interrupts** pause execution before each tool call for user approval.

## Tech Stack

**Backend:** Python 3.12+, LangGraph, LangChain, OpenAI (gpt-4o), Tavily, Pydantic v2, FastAPI, SSE
**Frontend:** Next.js, TypeScript, React
**Tooling:** uv (package manager), pytest

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) package manager
- [OpenAI API key](https://platform.openai.com/api-keys)
- [Tavily API key](https://tavily.com/)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/kimyungju/Pricewise.git
   cd Pricewise
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:

   ```
   OPENAI_API_KEY=sk-your-key-here
   TAVILY_API_KEY=tvly-your-key-here
   ```

3. **Install backend dependencies**

   ```bash
   uv sync
   ```

4. **Install frontend dependencies**

   ```bash
   cd web && npm install
   ```

## Usage

### Web Interface

Start both servers in separate terminals:

```bash
# Terminal 1 — Backend
uv run uvicorn aigent.api.app:create_app --factory --reload --port 8000

# Terminal 2 — Frontend
cd web && npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and start chatting.

### CLI

```bash
uv run python main.py
```

The CLI runs a demo query and prompts for tool approval at each step.

### Running Tests

```bash
uv run pytest -v
```
