#!/usr/bin/env python3
"""Archive a Harbor benchmark job tree into an inspectable runs/ folder.

Layout (explorer-friendly, timestamp-first directory name):

  evals/runs/
    RESULTS.txt                 # aligned table: Run | Pass | Runtime | Mode | …
    YYYY-MM-DD_HHMMSS__harness-…__mode-…__skills-…__separately-…__kN-nN/
      00-meta.json
      01-SUMMARY.txt
      02-command.txt
      Projects/<trial-name>/
        app/                    # cloned repo reset to the empty initial commit
        .worktrees/<project>/<dir>/   # worktree files (the actual work)
      harbor/                   # raw Harbor -o output (not /tmp)
      jobs/<job-name>/
        00-job-result.json
        00-harbor-config.yaml   # when present next to the job
        01-SUMMARY.txt
        trials/<trial-name>/
          00-trial-result.json
          01-reward.json
          02-reward-details.json
          03-reward-<skill>.json
          03-reward-<skill>-details.json
          10-test-stdout.txt
          20-exception.txt
          code/*.py
          agent/<log files>
"""

from __future__ import annotations

import sys

from archive_run.cli import main


if __name__ == "__main__":
    sys.exit(main())
