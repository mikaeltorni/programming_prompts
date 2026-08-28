# Task seeds

Optional planted files for a coding prompt, copied into the Harbor image as a
second git commit after the empty initial commit (`Seed task files`).

```text
seeds/<task>/
  greeter.py      # becomes /Projects/app/greeter.py
  log/greeter.log # becomes /Projects/app/.log/greeter.log
```

A `log/` folder is renamed to `.log/` in the image so this repository can
track the files (repo-root `.gitignore` ignores `.log/`). The commits checker
skips the seed subject, so Feature-commit counts start after it.
