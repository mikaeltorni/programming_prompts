# Prompts

The current prompt is the [`programming-skill`](programming-skill/SKILL.md).
Inject that directory into Harbor runs with `--skill`, or use
[`../evals/harbor.codex.yaml`](../evals/harbor.codex.yaml) /
[`../evals/run_codex_benchmark.sh`](../evals/run_codex_benchmark.sh) so the clean
BenchmarkCodex agent installs only the configured skills at the pinned Codex CLI
version. Harbor discovers the `SKILL.md` file automatically.
