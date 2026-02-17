FROM python:3.12-slim

RUN pip install uv

ENV UV_PYTHON_PREFERENCE=only-system

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["sh", "-c", "uv run uvicorn pricewise.api.app:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
