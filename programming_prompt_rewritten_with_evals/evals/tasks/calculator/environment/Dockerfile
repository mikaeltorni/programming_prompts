FROM ghcr.io/astral-sh/uv:0.11.26 AS uv

FROM python:3.12-slim

# Keep in sync with programming_prompt_rewritten_with_evals/evals/codex-version.txt
ARG CODEX_VERSION=0.147.0

COPY --from=uv /uv /uvx /bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && npm uninstall --global @openai/codex >/dev/null 2>&1 || true \
    && npm install --global "@openai/codex@${CODEX_VERSION}" \
    && codex --version \
    && rm -rf /root/.agents /root/.codex /etc/codex /var/lib/apt/lists/*

WORKDIR /app
