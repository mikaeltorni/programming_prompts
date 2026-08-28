#!/usr/bin/env bash
# Materialize Harbor task dirs from coding-prompts/*.md + shared template/oracles.
# Edit only coding-prompts/<name>.md (and oracles/<name>.py for oracle runs).
# Generated output lives under .generated/tasks/ (gitignored) — never hand-edit it.
# Usage: ./sync_tasks.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"
PROMPTS_DIR="$SCRIPT_DIR/coding-prompts"
ORACLES_DIR="$SCRIPT_DIR/oracles"
TEMPLATE_DIR="$SCRIPT_DIR/task-template"
TASKS_DIR="${TASKS_DIR:-$SCRIPT_DIR/.generated/tasks}"

if [[ ! -d "$PROMPTS_DIR" ]]; then
  echo "Missing coding prompts: $PROMPTS_DIR" >&2
  exit 1
fi
if [[ ! -d "$TEMPLATE_DIR" ]]; then
  echo "Missing task template: $TEMPLATE_DIR" >&2
  exit 1
fi

python3 - "$PROMPTS_DIR" "$ORACLES_DIR" "$TEMPLATE_DIR" "$TASKS_DIR" <<'PY'
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from harbor_agents.clean_skills import (
    load_claude_version,
    load_codex_version,
    load_grok_version,
)
from harbor_agents.log import log

prompts_dir = Path(sys.argv[1])
oracles_dir = Path(sys.argv[2])
template_dir = Path(sys.argv[3])
tasks_dir = Path(sys.argv[4])

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.S)
DOCKER_ARG_RE = {
    "CODEX_VERSION": re.compile(r"^ARG CODEX_VERSION=.*$", re.M),
    "CLAUDE_VERSION": re.compile(r"^ARG CLAUDE_VERSION=.*$", re.M),
    "GROK_VERSION": re.compile(r"^ARG GROK_VERSION=.*$", re.M),
}


def patch_dockerfile_versions(path: Path) -> None:
    """Bake the instance-start CLI versions into a generated task Dockerfile.

    Args:
        path: Copied ``environment/Dockerfile`` under a generated task.
    """
    versions = {
        "CODEX_VERSION": load_codex_version(),
        "CLAUDE_VERSION": load_claude_version(),
        "GROK_VERSION": load_grok_version(),
    }
    text = path.read_text(encoding="utf-8")
    for arg, version in versions.items():
        updated, count = DOCKER_ARG_RE[arg].subn(f"ARG {arg}={version}", text, count=1)
        if count != 1:
            raise SystemExit(f"{path}: missing ARG {arg}= in template Dockerfile")
        text = updated
    path.write_text(text, encoding="utf-8")


def parse_prompt(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise SystemExit(f"{path}: expected YAML frontmatter with artifact/description")
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    body = match.group(2).strip() + "\n"
    if "artifact" not in meta:
        raise SystemExit(f"{path}: frontmatter missing artifact")
    if "description" not in meta:
        meta["description"] = f"Write-from-scratch task {path.stem}"
    return meta, body


def write_task_toml(dest: Path, name: str, description: str) -> None:
    dest.write_text(
        f'''schema_version = "1.4"

[task]
name = "programming-prompts/{name}"
version = "0.4.0"
description = "{description}"

[verifier]
timeout_sec = 300.0

[agent]
timeout_sec = 300.0

[environment]
network_mode = "public"
build_timeout_sec = 300.0
cpus = 1
memory_mb = 2048
storage_mb = 2048
''',
        encoding="utf-8",
    )


def write_solve_sh(dest: Path, artifact: str, oracle_name: str) -> None:
    # Copies the sibling oracle.py into /Projects/.worktrees/app/oracle,
    # commits there, then merges back so the artifact exists in /Projects/app.
    # Never pushes.
    artifact_name = Path(artifact).name
    dest.write_text(
        f'''#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="/Projects/app"
NAME="$(basename "$REPO")"
PARENT="$(dirname "$REPO")"
STORE="$PARENT/.worktrees/$NAME"
WT="$STORE/oracle"
if [[ ! -e "$REPO/.git" ]]; then
  git -C "$REPO" init -b master
  git -C "$REPO" commit --allow-empty -m "Initial empty commit"
fi
mkdir -p "$STORE"
if ! git -C "$REPO" worktree list --porcelain | grep -qx "worktree $WT"; then
  git -C "$REPO" worktree add -b feat/oracle "$WT"
fi
install -m 644 "$HERE/oracle.py" "$WT/{artifact_name}"
git -C "$WT" add -A
if ! git -C "$WT" diff --cached --quiet; then
  git -C "$WT" commit -m "feat(oracle): add {oracle_name} reference solution"
fi
git -C "$REPO" checkout master
git -C "$REPO" merge --no-ff feat/oracle -m "Merge feat/oracle: {oracle_name} reference solution"
''',
        encoding="utf-8",
    )
    dest.chmod(0o755)


if tasks_dir.exists():
    shutil.rmtree(tasks_dir)
tasks_dir.mkdir(parents=True)

prompt_files = sorted(prompts_dir.glob("*.md"))
prompt_files = [p for p in prompt_files if p.name.lower() != "readme.md"]
if not prompt_files:
    raise SystemExit(f"No coding-prompts/*.md under {prompts_dir}")

compose_src = template_dir / "environment" / "docker-compose.yaml"
if not compose_src.is_file():
    raise SystemExit(
        f"{compose_src}: missing; Harbor would create one Docker "
        "network per trial and exhaust stock IPAM"
    )

for prompt_path in prompt_files:
    name = prompt_path.stem
    meta, body = parse_prompt(prompt_path)
    artifact = meta["artifact"]
    description = meta["description"].replace('"', '\\"')
    features_text = meta.get("features", "1").strip()
    try:
        feature_count = int(features_text)
    except ValueError as exc:
        raise SystemExit(f"{prompt_path}: features must be an integer, got {features_text!r}") from exc
    if feature_count < 1:
        raise SystemExit(f"{prompt_path}: features must be >= 1, got {feature_count}")
    oracle_src = oracles_dir / f"{name}.py"
    if not oracle_src.is_file():
        raise SystemExit(f"Missing oracle for '{name}': {oracle_src}")

    task_dir = tasks_dir / name
    (task_dir / "environment").mkdir(parents=True)
    (task_dir / "solution").mkdir(parents=True)
    (task_dir / "tests").mkdir(parents=True)

    (task_dir / "instruction.md").write_text(body, encoding="utf-8")
    (task_dir / "artifact.txt").write_text(artifact + "\n", encoding="utf-8")
    write_task_toml(task_dir / "task.toml", name, description)
    shutil.copy2(template_dir / "environment" / "Dockerfile", task_dir / "environment" / "Dockerfile")
    patch_dockerfile_versions(task_dir / "environment" / "Dockerfile")
    shutil.copy2(compose_src, task_dir / "environment" / "docker-compose.yaml")
    shutil.copy2(template_dir / "tests" / "test.sh", task_dir / "tests" / "test.sh")
    (task_dir / "tests" / "test.sh").chmod(0o755)
    (task_dir / "tests" / "feature_count.txt").write_text(
        f"{feature_count}\n", encoding="utf-8"
    )
    shutil.copy2(oracle_src, task_dir / "solution" / "oracle.py")
    write_solve_sh(task_dir / "solution" / "solve.sh", artifact, name)
    print(f"materialized task {name} -> {task_dir}", flush=True)

log(
    "baked CLI versions into generated Dockerfiles: "
    f"Codex={load_codex_version()} Claude={load_claude_version()} "
    f"Grok={load_grok_version()}; compose overlay network_mode=bridge tmpfs scratch cpus=1"
)
print(f"Synced {len(prompt_files)} coding prompt(s) into {tasks_dir}", flush=True)
PY
