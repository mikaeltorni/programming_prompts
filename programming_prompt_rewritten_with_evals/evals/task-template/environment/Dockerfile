FROM ghcr.io/astral-sh/uv:0.11.26 AS uv

FROM python:3.12-slim

# Keep in sync with evals/codex-version.txt, evals/claude-version.txt,
# and evals/grok-version.txt
ARG CODEX_VERSION=0.147.0
ARG CLAUDE_VERSION=2.1.227
ARG GROK_VERSION=1.0.4

COPY --from=uv /uv /uvx /bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm git curl procps \
    && npm uninstall --global @openai/codex @anthropic-ai/claude-code >/dev/null 2>&1 || true \
    && npm install --global "@openai/codex@${CODEX_VERSION}" \
    && npm install --global "@anthropic-ai/claude-code@${CLAUDE_VERSION}" \
    && curl -fsSL https://x.ai/cli/install.sh | bash -s "${GROK_VERSION}" \
    && ln -sfn /root/.grok/bin/grok /usr/local/bin/grok \
    && export PATH="/root/.grok/bin:$HOME/.local/bin:/usr/local/bin:$PATH" \
    && codex --version \
    && claude --version \
    && grok --version \
    && git config --system user.email "eval@local" \
    && git config --system user.name "Eval Agent" \
    && rm -rf /root/.agents /root/.codex /root/.claude /etc/codex \
         /root/.grok/skills /root/.grok/installed-plugins /var/lib/apt/lists/* \
    && mkdir -p /root/.grok \
    && : > /root/.grok/auth.json

# Simulated host layout: a cloned repo beside the shared worktree store.
# /app is a symlink so coding-prompt paths (/app/*.py) still resolve.
RUN mkdir -p /Projects/app /Projects/.worktrees \
    && ln -sfn /Projects/app /app
WORKDIR /Projects/app
# Fresh trial image starts as a git repo with only an empty initial commit.
# Agents must add a sibling /Projects/.worktrees/app/<dir> worktree (never push).
RUN git init -b master \
    && git commit --allow-empty -m "Initial empty commit"
