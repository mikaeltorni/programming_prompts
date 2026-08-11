FROM ghcr.io/astral-sh/uv:0.11.26 AS uv

FROM python:3.12-slim

# Keep in sync with evals/codex-version.txt and evals/claude-version.txt
ARG CODEX_VERSION=0.147.0
ARG CLAUDE_VERSION=2.1.227

COPY --from=uv /uv /uvx /bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && npm uninstall --global @openai/codex @anthropic-ai/claude-code >/dev/null 2>&1 || true \
    && npm install --global "@openai/codex@${CODEX_VERSION}" \
    && npm install --global "@anthropic-ai/claude-code@${CLAUDE_VERSION}" \
    && codex --version \
    && export PATH="$HOME/.local/bin:/usr/local/bin:$PATH" \
    && claude --version \
    && rm -rf /root/.agents /root/.codex /root/.claude /etc/codex /var/lib/apt/lists/*

WORKDIR /app
