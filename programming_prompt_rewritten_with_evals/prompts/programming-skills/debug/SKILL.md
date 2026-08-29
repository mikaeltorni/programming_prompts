---
name: debug
description: >-
  Use whenever software is reported broken or misbehaving: read the logs
  before forming a hypothesis. Look in repo .log/ first. Apply on every
  debugging task, including small scripts.
---

# Read logs first

When software is reported broken, read the logs before forming a hypothesis.
Look in the repository `.log/` directory first. Do not guess the bug from
the instruction alone when logs are present.

When a log shows the output the program should produce (`want:`, `expected`,
or `exactly`), make the program produce that exact string, including prefixes
and labels. Do not keep the broken format if the log shows a different one.
