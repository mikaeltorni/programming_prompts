# Benchmark run archives

Each `./run_benchmark.sh` invocation writes an inspectable folder here.

Directory names sort by start time in the file explorer:

```text
YYYY-MM-DD_HHMMSS_<pid>__harness-…__mode-…__skills-…__separately-…__tasks-…__kN-nN/
```

Harbor job dirs under the temp `$JOBS` tree use the same stamp suffix
(`codex-skills__YYYY-MM-DD_HHMMSS_<pid>`) so sharing `$JOBS` across terminals
is safe.
## Layout

```text
00-meta.json              # timestamp, harness, mode, skills, separately, k/n, command
01-SUMMARY.txt            # console summaries (appended per job)
02-command.txt            # exact argv used
03-COMBINED-SUMMARY.txt   # present when multiple jobs were rolled up
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

Harbor still uses a temp `$JOBS` tree for execution; this folder is the durable
copy under the rewritten-prompts package.
