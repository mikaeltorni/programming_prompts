FROM ghcr.io/astral-sh/uv:0.11.26 AS uv

FROM python:3.12-slim

COPY --from=uv /uv /uvx /bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && npm install --global @openai/codex@0.147.0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY calculator.py /app/calculator.py
