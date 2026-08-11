# Prompts

The current prompt is the [`programming-skill`](programming-skill/SKILL.md).
Inject that directory into Harbor runs with `--skill`, or use
[`../evals/run_codex_benchmark.sh`](../evals/run_codex_benchmark.sh) so the clean
BenchmarkCodex agent installs only the configured skills at the pinned Codex CLI
version. Harbor discovers the `SKILL.md` file automatically.

For the negative control, run `./run_codex_benchmark.sh --negative`. That
auto-inverts `programming-skill/SKILL.md` into a temporary anti-skill — do not
maintain a separate negative skill file. Edit only:

- `programming-skill/SKILL.md`
- `../evals/judge/judge-prompt.md`
