---
artifact: /Projects/hotkey_tools/hotkey.py
description: Route implementation from a setup bundle into a separate repository.
oracle: none
---
Follow every provided programming skill.
This checkout is a setup bundle; the implementation belongs to a separate sibling repository named `hotkey_tools`.
For this isolated fixture, create `/Projects/hotkey_tools` as a Git repository on `master` with an empty initial commit, then implement the request there.
Write `/Projects/hotkey_tools/hotkey.py` with `run_hotkey(command: str) -> str`: `binding` returns `<Super>t`, and `binding <accelerator>` stores that text and returns it, retaining the selected binding across calls in one process.
