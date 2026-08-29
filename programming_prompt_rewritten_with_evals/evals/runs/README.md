# Benchmark run archives

Each `./run_benchmark.sh` invocation writes an inspectable folder here.
Harbor jobs land in this folder too (`harbor/`), not under `/tmp`.

Directory names sort by start time in the file explorer:

```text
YYYY-MM-DD_HHMMSS_<pid>__harness-…__mode-…__skills-…__separately-…__tasks-…__kN-nN/
```

Harbor job dirs under `harbor/` use the same stamp suffix
(`codex-skills__YYYY-MM-DD_HHMMSS_<pid>`) so sharing one run across terminals
is unnecessary — each invocation gets its own archive.

## Layout

```text
00-meta.json              # timestamp, harness, mode, skills, separately, k/n, command
01-SUMMARY.txt            # console summaries (appended per job)
02-command.txt            # exact argv used
03-COMBINED-SUMMARY.txt   # present when multiple jobs were rolled up
Projects/<trial-name>/
  app/                    # cloned repo at the empty initial commit
  .worktrees/<project>/<dir>/   # worktree with the agent's files
harbor/                   # raw Harbor -o output (not /tmp)
jobs/<harbor-job-name>/
  00-job-result.json
  00-harbor-config.yaml
  00-job-index.json
  01-SUMMARY.txt
  trials/<task>__<id>/
    00-trial-index.json
    00-trial-result.json
    01-reward.json
    02-reward-details.json
    03-reward-<skill>.json
    03-reward-<skill>-details.json
    10-test-stdout.txt
    20-exception.txt        # only on failures
    code/*.py               # downloaded agent artifacts
    agent/                  # trajectory / agent logs (sessions trimmed)
```

The runner prints `written to: <absolute-path>` when the archive is ready.

Open `Projects/<trial>/` to see the simulated host: the cloned `app` repo
beside `.worktrees/app/<worktree>/`.

