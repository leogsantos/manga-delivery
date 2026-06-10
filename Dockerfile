FROM mcr.microsoft.com/playwright/python:v1.60.0-jammy

WORKDIR /app

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml .python-version ./
RUN uv sync --no-dev
RUN uv run playwright install chromium

COPY src/ ./src/

ENV PYTHONPATH=/app
