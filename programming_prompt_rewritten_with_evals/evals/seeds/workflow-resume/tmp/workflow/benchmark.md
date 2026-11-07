# Workflow

## Goal
Write notification.txt containing Ready followed by a newline.

## Enabled skills
workflow only; no worktree, commits, docs or testing companions selected.

## Tasks
| Order | Task | Status | Details |
| --- | --- | --- | --- |
| 1 | Establish worktree | complete | Live /Projects/app verified; no isolation selected. |
| 2 | Plan | complete | Assigned plan /Projects/app/tmp/workflow/benchmark.md retained. |
| 3 | Write code | in_progress | Resume the notification artifact. |
| 4 | Write documentation | skipped | Docs not selected. |

## Microsteps
| Step | Phase | Feature | Stage | Action | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Establish worktree | - | - | Inspect live checkout | complete | /Projects/app exists on master. |
| 2 | Plan | - | - | Save authoritative plan | complete | Retained task after interruption. |
| 3 | Write code | notify | 3.1 | Check notification.txt contents | complete | Interrupted baseline: file is absent. |
| 4 | Write code | notify | 3.2 | Write notification.txt and verify exact contents | in_progress | Continue from here after restart. |
| 5 | Write code | notify | 3.3 | Commit notification artifact | skipped | Commits not selected. |
| 6 | Write documentation | - | - | Write and verify README | skipped | Docs not selected. |
| 7 | Write documentation | - | - | Commit documentation | skipped | Docs and commits not selected. |
