# Eval result verification (temp job dirs)

After a Harbor run, jobs land under a `/tmp/tmp.*` directory. These scripts
open a **new terminal window** and ask an agent to verify positive vs baseline
results against the skill + judge files.

## Usage

```bash
cd programming_prompt_rewritten_with_evals/evals/testing
./verify_with_ca.sh  /tmp/tmp.POSITIVE /tmp/tmp.BASELINE
./verify_with_cca.sh /tmp/tmp.POSITIVE /tmp/tmp.BASELINE
```

Parameters:

1. `positive_jobs_tmp_dir` — job root from a with-skill run
2. `baseline_jobs_tmp_dir` — job root from a `--baseline` run

`verify_with_ca.sh` runs `ca -h -sol "…"`.
`verify_with_cca.sh` runs `cca -opus -h "…"`.

Both require a graphical terminal (`gnome-terminal` preferred).
