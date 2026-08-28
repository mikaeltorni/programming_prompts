# Task seeds

Optional planted files for a coding prompt, copied into the Harbor image as a
second git commit after the empty initial commit (`Seed task files`).

```text
seeds/<task>/
  greeter.py          # becomes /Projects/app/greeter.py
  log/greeter.log     # becomes /Projects/app/.log/greeter.log
  debug_tokens.txt    # copied to tests/ only — not into the agent workspace
```

A `log/` folder is renamed to `.log/` in the image so this repository can
track the files (repo-root `.gitignore` ignores `.log/`). `debug_tokens.txt`
is the hidden diagnosis list for the debug checker (`twilight`, `hi=`); it
must not land in the seed commit. The commits checker skips the seed subject,
so Feature-commit counts start after it.
