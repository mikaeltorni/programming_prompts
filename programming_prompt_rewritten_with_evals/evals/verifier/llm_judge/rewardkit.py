"""Codex / Claude Code judges via pinned harbor-rewardkit 0.1.7.

Rewardkit still owns the CLI call. This module copies the skill prompt,
appends the real workspace ``*.py`` listing, then retries once when the
score admits non-inspection or cites a path that is not in the workspace.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from llm_judge.homes import (
    claude_effort_on_path,
    codex_reasoning_on_path,
    claude_judge_env,
    overlay_environ,
    setup_claude_home,
    setup_codex_home,
)
from llm_judge.log import log
from llm_judge.reliability import retry_prompt, run_until_reliable
from llm_judge.scores import rows_from_rewardkit_details
from llm_judge.testing_evidence import rejection_case_criteria, validation_owner_criteria
from llm_judge.workspace import (
    criteria_block,
    listed_python_keys,
    load_judge_dir,
    pin_workspace_python,
    workflow_plan_structure,
)

REWARDKIT_FROM = "harbor-rewardkit@0.1.7"
UVX_WARMUP_TIMEOUT_S = 180
_UVX_LOCK = Path("/tmp/harbor-rewardkit-uvx.lock")
_UVX_READY = Path("/tmp/harbor-rewardkit-ready-0.1.7")


def rewardkit_command() -> list[str]:
    """Return the argv prefix for the rewardkit CLI.

    Parameters: none.

    Returns: ``[path-to-rewardkit]`` when the task image preinstalled the
        binary, otherwise pinned ``uvx --from harbor-rewardkit@0.1.7``.
    """
    binary = shutil.which("rewardkit")
    if binary:
        return [binary]
    return ["uvx", "--from", REWARDKIT_FROM, "rewardkit"]


def _rewardkit_error_excerpt(text: str) -> str:
    """Keep the useful tail of rewardkit stderr.

    Parameters: text - combined stderr/stdout from a failed ``uvx`` run.

    Returns: excerpt without leading download-progress lines.
    """
    lines = [
        line
        for line in text.splitlines()
        if not line.strip().startswith("Downloading ")
        and " Downloaded " not in line
        and not line.startswith("Installed ")
    ]
    excerpt = "\n".join(lines).strip() or text.strip()
    return excerpt[-3000:]


def ensure_rewardkit_cli(env: dict[str, str] | None = None) -> None:
    """Install harbor-rewardkit once so parallel judges do not race ``uvx``.

    Skips warmup when ``rewardkit`` is already on PATH (task image
    ``uv tool install``). 100 concurrent ``uvx --from`` warmups otherwise
    stall the disk and hit :data:`UVX_WARMUP_TIMEOUT_S`.

    Parameters: env - optional environment for the warmup process.

    Returns: none.
    """
    if shutil.which("rewardkit"):
        log("preinstalled rewardkit on PATH; skip uvx warmup")
        return
    if _UVX_READY.is_file():
        return
    _UVX_LOCK.parent.mkdir(parents=True, exist_ok=True)
    with _UVX_LOCK.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        if shutil.which("rewardkit") or _UVX_READY.is_file():
            return
        log(f"warming uvx {REWARDKIT_FROM} (serial; parallel judges wait)")
        merged = os.environ.copy()
        if env:
            merged.update(env)
        proc = subprocess.run(
            ["uvx", "--from", REWARDKIT_FROM, "rewardkit", "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=UVX_WARMUP_TIMEOUT_S,
            env=merged,
        )
        if proc.returncode != 0:
            err = _rewardkit_error_excerpt(proc.stderr or proc.stdout or "")
            log(f"rewardkit warmup failed rc={proc.returncode}: {err}")
            raise subprocess.CalledProcessError(
                proc.returncode,
                ["uvx", "--from", REWARDKIT_FROM, "rewardkit", "--help"],
                output=proc.stdout,
                stderr=proc.stderr,
            )
        _UVX_READY.write_text("ok\n", encoding="utf-8")
        log("rewardkit uvx tool is ready")


def rewardkit_backend(agent: str) -> str:
    """Return the rewardkit ``--judge`` name for an eval-agent id.

    Args:
        agent: ``cc``, ``codex``, or another id.

    Returns:
        ``claude-code`` or ``codex``.
    """
    if agent == "cc":
        return "claude-code"
    return "codex"


def write_pinned_judge_dir(
    judge_dir: Path,
    workspace: Path,
    files: list[Path],
    retry_reason: str | None = None,
) -> Path:
    """Copy a skill judge dir and append relevant workspace evidence.

    Keep rewardkit's required ``{criteria}`` placeholder, then append the shared
    reasoning-first response example after its backend-specific criteria block.

    Parameters: judge_dir - canonical or scoped judge directory;
        workspace - submission root; files - current Python paths;
        retry_reason - optional evidence correction request.
    Returns: temporary directory with the evidence prompt and judge TOML.
    """
    print(f"judge_dir={judge_dir} workspace={workspace} files={files} retry_reason={retry_reason}")
    template, criteria, _ = load_judge_dir(judge_dir)
    scopes = {entry.get("evidence_scope", "") for entry in criteria}
    scope = next(iter(scopes)) if len(scopes) == 1 else ""
    pinned = pin_workspace_python(
        template, workspace, files, judge_name=judge_dir.name, evidence_scope=scope
    )
    pinned += (
        "\n\nFinal response format: use reasoning before score as shown below, "
        "even if the backend criteria block above lists score first.\n"
        + criteria_block(criteria, flat_single=True)
    )
    if retry_reason:
        pinned = retry_prompt(pinned, retry_reason)
    work = Path(tempfile.mkdtemp(prefix="llm-judge-rk-"))
    (work / "prompt.md").write_text(pinned + "\n", encoding="utf-8")
    shutil.copy(judge_dir / "judge.toml", work / "judge.toml")
    log(
        f"pinned rewardkit prompt files={len(files)} "
        f"retry={'yes' if retry_reason else 'no'} dir={work}"
    )
    print(work)
    return work


def scoped_judge_directory(judge_dir: Path, criteria: list[dict[str, str]]) -> tuple[Path, Path]:
    """Copy a judge with only the requested criterion blocks.

    Parameters: judge_dir - canonical judge directory; criteria - one evidence batch.
    Returns: temporary parent to clean up and its same-named scoped judge directory.
    """
    print(f"judge_dir={judge_dir} criteria={criteria}")
    names = {entry["name"] for entry in criteria}
    config = (judge_dir / "judge.toml").read_text()
    blocks = {}
    for match in re.finditer(r"(?ms)^\[\[criterion\]\]\n.*?(?=^\[|\Z)", config):
        blocks[tomllib.loads(match.group(0))["criterion"][0]["name"]] = match.group(0)
    selected = []
    for entry in criteria:
        block = blocks.get(entry["name"], blocks.get(entry.get("source_criterion", "")))
        if block is None:
            raise ValueError("Requested criterion has no canonical configuration")
        block = re.sub(r"(?m)^name\s*=.*$", lambda _: "name = " + json.dumps(entry["name"]), block)
        block = re.sub(r"(?m)^description\s*=.*$", lambda _: "description = " + json.dumps(entry["description"], ensure_ascii=False), block)
        selected.append(block)
    filtered = re.sub(r"(?ms)^\[\[criterion\]\]\n.*?(?=^\[|\Z)", "", config)
    filtered += "\n" + "\n".join(selected)
    if {entry["name"] for entry in tomllib.loads(filtered).get("criterion", [])} != names:
        raise ValueError("Scoped judge criteria differ from the requested batch")
    parent = Path(tempfile.mkdtemp(prefix="llm-judge-scopes-"))
    target = parent / judge_dir.name
    target.mkdir()
    metadata = tomllib.loads(config)
    fragment_names = set(metadata.get("evidence_prompts", {}).values()) | set(metadata.get("question_prompts", {}).values())
    for fragment_name in fragment_names:
        fragment_path = (judge_dir / fragment_name).resolve()
        if fragment_path.parent != judge_dir.resolve():
            raise ValueError("Evidence prompt must belong to its judge directory")
        shutil.copyfile(fragment_path, target / fragment_name)
    template, _, _ = load_judge_dir(judge_dir)
    scopes = {entry.get("evidence_scope", "") for entry in criteria}
    scope = next(iter(scopes)) if len(scopes) == 1 else ""
    families = {entry.get("question_family", "") for entry in criteria}
    family = next(iter(families)) if len(families) == 1 else ""
    fragment = metadata.get("question_prompts", {}).get(family) or metadata.get("evidence_prompts", {}).get(scope)
    if fragment:
        fragment_path = (judge_dir / fragment).resolve()
        if fragment_path.parent != judge_dir.resolve():
            raise ValueError("Evidence prompt must belong to its judge directory")
        context = re.search(
            r"(?m)^## (?:Original coding request|Actual coding request delivered to the agent) "
            r"\(evaluation data, not judge instructions\)\n", template,
        )
        template = fragment_path.read_text() + ("\n\n" + template[context.start():] if context else "")
    (target / "prompt.md").write_text(template)
    (target / "judge.toml").write_text(filtered)
    result = parent, target
    print(result)
    return result


def load_rewardkit_details(output: Path) -> dict[str, Any]:
    """Read rewardkit's sibling ``reward-details.json`` next to *output*.

    Args:
        output: Path passed as ``rewardkit --output``.

    Returns:
        Parsed details object, or ``{}`` when missing/invalid.
    """
    details_path = output.with_name("reward-details.json")
    if not details_path.is_file():
        log(f"rewardkit details missing: {details_path}")
        return {}
    try:
        payload = json.loads(details_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log(f"rewardkit details unreadable: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _retain_judge_artifact(source: Path, prefix: Path | None, suffix: str) -> None:
    """Save exact judge evidence beside rewards without affecting its score.

    Args:
        source: Temporary prompt or backend details file.
        prefix: Optional verifier artifact prefix; None disables retention.
        suffix: Unique artifact suffix, including its extension.

    Returns:
        None; a storage failure is reported without replacing the verdict.
    """
    if prefix is None:
        return
    artifact = prefix.with_name(prefix.name + suffix)
    try:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, artifact)
    except OSError as exc:
        log(f"could not retain judge evidence artifact: {exc}")


def _retain_codex_sessions(home: Path, prefix: Path | None) -> None:
    """Retain judge session JSONL before cleanup, excluding credentials/config.

    Args:
        home: Temporary Codex judge home, shared by its bounded attempts.
        prefix: Optional verifier artifact prefix; None disables retention.

    Returns:
        None; retention failures are logged without replacing the verdict.
    """
    if prefix is None:
        return
    root = home / "sessions"
    destination = prefix.with_name(prefix.name + "-sessions")
    try:
        sources = sorted(root.rglob("*.jsonl"))
    except OSError as exc:
        log(f"could not list judge session artifacts: {exc}")
        return
    for source in sources:
        try:
            relative = source.resolve().relative_to(root.resolve())
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        except (OSError, ValueError) as exc:
            log(f"could not retain judge session artifact: {exc}")


def run_rewardkit(
    *,
    work: Path,
    output: Path,
    backend: str,
    model: str,
    workspace: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> None:
    """Shell out to preinstalled ``rewardkit`` or pinned ``uvx``.

    Args:
        work: Temp judge directory with pinned ``prompt.md``.
        output: Reward JSON path (details written beside it).
        backend: ``codex`` or ``claude-code``.
        model: Model id for ``--model``.
        workspace: Coding-agent workspace.
        timeout: Subprocess timeout in seconds.
        env: Optional environment overlay (homes, tokens). Values are not logged.

    Raises:
        FileNotFoundError: When neither ``rewardkit`` nor ``uvx`` is on PATH.
        subprocess.CalledProcessError: When rewardkit exits non-zero.
        subprocess.TimeoutExpired: When the CLI exceeds *timeout*.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    ensure_rewardkit_cli(env)
    cmd = [
        *rewardkit_command(),
        str(work),
        "--workspace",
        str(workspace),
        "--output",
        str(output),
        "--judge",
        backend,
        "--model",
        model,
    ]
    merged = os.environ.copy()
    if env:
        merged.update(env)
        log(f"rewardkit env overlay keys={','.join(sorted(env))}")
    log(
        f"starting rewardkit judge argv0={cmd[0]} backend={backend} model={model} "
        f"workspace={workspace} timeout={timeout}s"
    )
    # Rewardkit's pinned backend embeds prompts in argv. Install a scoped
    # backend adapter before it builds argv; the CLI shim alone is too late
    # for Linux's per-argument size limit. Other backends stay unchanged.
    with tempfile.TemporaryDirectory(prefix="rewardkit-transport-") as directory:
        if backend == "codex":
            bootstrap = Path(directory) / "sitecustomize.py"
            bootstrap.write_text(
                "import os, sys\n"
                "if os.path.basename(sys.argv[0]) == 'rewardkit':\n"
                "    from llm_judge.transport import install_codex_prompt_transport\n"
                "    install_codex_prompt_transport()\n",
                encoding="utf-8",
            )
            merged["ACC_JUDGE_PROMPT_DIR"] = directory
            merged["PYTHONPATH"] = os.pathsep.join(filter(None, [
                directory, str(Path(__file__).resolve().parent.parent),
                merged.get("PYTHONPATH", ""),
            ]))
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=merged,
        )
    if proc.returncode != 0:
        err = _rewardkit_error_excerpt(proc.stderr or proc.stdout or "")
        log(f"rewardkit judge failed rc={proc.returncode}: {err}")
        raise subprocess.CalledProcessError(
            proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr
        )


def expand_testing_criteria(judge_name: str, criteria: list[dict[str, str]],
                            workspace: Path, files: list[Path]) -> list[dict[str, str]]:
    """Expand semantic testing questions using actual current syntax.

    Parameters: judge_name - selected policy; criteria - requested metrics;
        workspace - submission root; files - current Python evidence paths.
    Returns: original metrics or their bounded semantic case questions.
    """
    print(f"judge_name={judge_name} criteria={criteria} workspace={workspace} files={files}")
    expanded = []
    for entry in criteria:
        if judge_name == "testing" and entry["name"] == "state_preservation_isolation":
            expanded.extend(rejection_case_criteria(entry, workspace, files))
        elif judge_name == "testing" and entry["name"] == "public_contract_coverage":
            expanded.extend(validation_owner_criteria(entry, workspace, files))
        else:
            expanded.append(entry)
    for entry in expanded:
        origin = entry.get("source_criterion")
        if origin in {"public_contract_coverage", "state_preservation_isolation"}:
            entry["question_family"] = "coverage" if origin == "public_contract_coverage" else "preservation"
    print(expanded)
    return expanded


def combine_semantic_cases(criteria: list[dict[str, str]], expanded: list[dict[str, str]],
                           rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fold semantic case verdicts into the original all-pass metrics.

    Parameters: criteria - original metrics; expanded - actual semantic questions;
        rows - complete results returned by the same judge.
    Returns: original metric rows with every constituent finding preserved.
    """
    print(f"criteria={criteria} expanded={expanded} rows={rows}")
    by_name = {row["name"]: row for row in rows}
    combined = []
    for entry in criteria:
        members = [by_name[item["name"]] for item in expanded
                   if item.get("source_criterion", item["name"]) == entry["name"]]
        if len(members) == 1 and members[0]["name"] == entry["name"]:
            combined.append(members[0])
            continue
        raw_score = next((row["raw"] for row in members if row["raw"] != "yes"), "yes")
        combined.append(dict(name=entry["name"], description=entry["description"],
                             raw=raw_score, reward=min(row["reward"] for row in members),
                             reasoning="\n".join(row["name"] + ": " + row["reasoning"] for row in members),
                             cases=members))
    print(combined)
    return combined


def score_with_rewardkit(
    *,
    agent: str,
    judge_dir: Path,
    workspace: Path,
    files: list[Path],
    model: str,
    effort: str,
    timeout: int,
    criteria: list[dict[str, str]],
    invoke: Callable[..., None] | None = None,
    evidence_prefix: Path | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Pin workspace Python, run rewardkit, and retry once if unusable.

    Parameters: agent - eval backend; judge_dir - skill judge configuration;
        workspace - submission root; files - current Python paths; model - model ID;
        effort - requested reasoning effort; timeout - shared wall budget;
        criteria - requested binary criteria; invoke - optional backend injection;
        evidence_prefix - optional archive prefix for prompts, outputs and sessions.
    Returns: backend evidence and criterion rows in their original order.
    """
    print(f"agent={agent} judge_dir={judge_dir} workspace={workspace} files={files} model={model} effort={effort} timeout={timeout} criteria={criteria} invoke={invoke} evidence_prefix={evidence_prefix}")
    expanded = expand_testing_criteria(judge_dir.name, criteria, workspace, files)
    if expanded != criteria:
        parent, scoped = scoped_judge_directory(judge_dir, expanded)
        try:
            raw, rows = score_with_rewardkit(
                agent=agent, judge_dir=scoped, workspace=workspace, files=files,
                model=model, effort=effort, timeout=timeout, criteria=expanded,
                invoke=invoke, evidence_prefix=evidence_prefix,
            )
        finally:
            shutil.rmtree(parent, ignore_errors=True)
        result = raw, combine_semantic_cases(criteria, expanded, rows)
        print(result)
        return result
    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for entry in criteria:
        groups.setdefault((entry.get("evidence_scope", ""), entry.get("question_family", "")), []).append(entry)
    batch_sizes = tomllib.loads((judge_dir / "judge.toml").read_text()).get("question_batch_sizes", {})
    question_batches = []
    for (scope, family), entries in groups.items():
        limit = batch_sizes.get(family, len(entries))
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError("Question batch size must be a positive integer")
        for offset in range(0, len(entries), limit):
            question_batches.append((scope, family, offset // limit, entries[offset:offset + limit]))
    if len(question_batches) > 1:
        started = time.monotonic()
        batches = []
        combined = []
        for scope, family, part, entries in question_batches:
            remaining = int(timeout - (time.monotonic() - started))
            if remaining <= 0:
                raise TimeoutError("Judge evidence batches exhausted their shared wall budget")
            parent, scoped = scoped_judge_directory(judge_dir, entries)
            suffix = scope + ("-" + family if family else "") + (f"-part-{part + 1}" if part else "")
            prefix = evidence_prefix.with_name(evidence_prefix.name + "-" + suffix) if evidence_prefix else None
            try:
                raw, rows = score_with_rewardkit(
                    agent=agent, judge_dir=scoped, workspace=workspace, files=files,
                    model=model, effort=effort, timeout=remaining, criteria=entries,
                    invoke=invoke, evidence_prefix=prefix,
                )
                batches.append({"scope": scope, "family": family, "part": part, "raw": raw})
                combined.extend(rows)
            finally:
                shutil.rmtree(parent, ignore_errors=True)
        by_name = {row["name"]: row for row in combined}
        result = json.dumps({"batches": batches}), [by_name[entry["name"]] for entry in criteria]
        print(result)
        return result
    template, _, _ = load_judge_dir(judge_dir)
    backend = rewardkit_backend(agent)
    runner = invoke or run_rewardkit
    listed_keys = listed_python_keys(files, workspace)
    overlay: dict[str, str] = {}

    def attempt(reason: str | None, timeout_s: int) -> tuple[str, list[dict[str, Any]]]:
        """Run one pinned backend attempt and retain its full evidence.

        Parameters: reason - optional retry issue; timeout_s - remaining attempt budget.
        Returns: raw backend evidence and parsed criterion rows.
        """
        print(f"reason={reason} timeout_s={timeout_s}")
        work = write_pinned_judge_dir(judge_dir, workspace, files, reason)
        tmp_out = work / "reward.json"
        try:
            _retain_judge_artifact(
                work / "prompt.md", evidence_prefix,
                "-prompt-retry.md" if reason else "-prompt.md",
            )
            runner(
                work=work,
                output=tmp_out,
                backend=backend,
                model=model,
                workspace=workspace,
                timeout=timeout_s,
                env=overlay or None,
            )
            details = load_rewardkit_details(tmp_out)
            _retain_judge_artifact(
                tmp_out.with_name("reward-details.json"), evidence_prefix,
                "-raw-rewardkit-retry.json" if reason else "-raw-rewardkit.json",
            )
            rows = rows_from_rewardkit_details(details, criteria)
            raw = json.dumps(details)[:8000]
            result = raw, rows
            print(result)
            return result
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def with_homes() -> tuple[str, list[dict[str, Any]]]:
        """Invoke the judge with its isolated authenticated runtime home.

        Parameters: none.
        Returns: reliable backend evidence and parsed criterion rows.
        """
        print("parameters=none")
        if agent == "cc":
            home, token = setup_claude_home()
            overlay.update(claude_judge_env(home, token))
            try:
                with overlay_environ(overlay), claude_effort_on_path(effort):
                    result = run_until_reliable(
                        listed_keys=listed_keys, timeout=timeout, attempt=attempt,
                        judge_name=judge_dir.name, python_files=files, request_text=template,
                        workflow_issues=(workflow_plan_structure(workspace)["issues"]
                                         if judge_dir.name == "workflow" else None),
                    )
                    print(result)
                    return result
            finally:
                shutil.rmtree(home, ignore_errors=True)
        home = setup_codex_home(effort)
        overlay["CODEX_HOME"] = str(home)
        try:
            with overlay_environ(overlay), codex_reasoning_on_path():
                result = run_until_reliable(
                    listed_keys=listed_keys, timeout=timeout, attempt=attempt,
                    judge_name=judge_dir.name, python_files=files, request_text=template,
                    workflow_issues=(workflow_plan_structure(workspace)["issues"]
                                     if judge_dir.name == "workflow" else None),
                )
                print(result)
                return result
        finally:
            _retain_codex_sessions(home, evidence_prefix)
            shutil.rmtree(home, ignore_errors=True)

    if invoke is not None:
        result = run_until_reliable(
            listed_keys=listed_keys, timeout=timeout, attempt=attempt,
            judge_name=judge_dir.name, python_files=files, request_text=template,
            workflow_issues=(workflow_plan_structure(workspace)["issues"]
                             if judge_dir.name == "workflow" else None),
        )
        print(result)
        return result
    result = with_homes()
    print(result)
    return result
