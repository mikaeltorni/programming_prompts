# Oracle solutions

Reference Python implementations used by Harbor’s oracle agent. Each
`oracles/<name>.py` is installed via a generated `solve.sh` that creates a
sibling `/Projects/.worktrees/app/oracle` worktree, commits there, and merges
back to `/Projects/app` (never pushes). Keep these aligned with the matching
`../coding-prompts/<name>.md` API.
