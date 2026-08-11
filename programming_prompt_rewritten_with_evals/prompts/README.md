# Prompts

Injectable Codex skills live under
[`programming-skills/`](programming-skills/README.md). Each skill directory
contains one `SKILL.md` and pairs with `../evals/judges/<name>/`.

Coding-task instructions (what to build) live under
[`../evals/coding-prompts/`](../evals/coding-prompts/) — one `.md` per task.

Current skills: `srp`, `commenting`.

Use [`../evals/run_codex_benchmark.sh`](../evals/run_codex_benchmark.sh) so the
clean BenchmarkCodex agent installs only the selected skills at the pinned
Codex CLI version.

After a run, audit `/tmp` job roots with
[`../evals/testing/`](../evals/testing/) (`verify_with_ca.sh` /
`verify_with_cca.sh`). Console summaries include each judge’s answer and
reasoning text from `reward-details.json`.
