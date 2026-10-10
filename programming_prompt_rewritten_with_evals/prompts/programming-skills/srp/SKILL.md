---
name: srp
description: >-
  v1.0.24 — Keep raw-command parsing and operation logic in separate helpers
  from the first working slice. Public entrypoints delegate; small scripts
  and new files follow the same boundaries on every coding task.
---

# Separate parsing, operations and dispatch

From the first working slice, give raw-command parsing, operation logic and
public dispatch separate owners. This applies to small scripts and repairs of
mixed existing entrypoints. Keep the public signature and extract locally.

- The parser receives the raw command once and returns its operation selector
  and parsed arguments. A single-operation interface may return arguments only.
  All raw stripping, splitting, slicing, regex matching, command-shape checks
  and token conversion belong here, including zero-argument commands. Smaller
  parsing helpers may compose inside this boundary.
- Operation helpers own arithmetic, computed results, state changes and domain
  validation: resource existence, uniqueness, funds/capacity, sign, finite-only,
  magnitude and integral-value acceptance. Numeric conversion establishes a
  representation; it does not decide which values an operation accepts.
- The public entrypoint parses once, dispatches using parsed data, then
  returns/formats the result. It passes converted values unchanged, without
  converting them back to text or inspecting the raw command again. It may
  directly read/format existing state; a pass-through getter is unnecessary.
  Universal representation guards on parsed values may stay in dispatch;
  operation-specific ranges belong with the operation.

Before extending an operation, read existing related owners. Reuse genuinely
shared classification, calculation and domain-validation decisions in one
called helper, removing their old copies in the same edit. Distinct arithmetic
operations or domain rules need no common helper. Sharing a state variable does
not make different updates the same decision. Dedicated operation helpers
choose their own delta and output label; dispatch only chooses the operation.

Do not repeat shape guards after the parser already enforces them. Formatting
alone does not extract operation logic still left in dispatch. Avoid parallel
parsers, speculative frameworks and unrelated renaming or rewrites.

With selected feature cycles, extend only the current capability through the
existing routing path. Check new and retained public behavior; remove branches
made obsolete by the requested change. Before committing, inspect the actual
parser, dispatcher and related operations for these boundaries. With selected
logging, the dispatcher's own parameter print comes before its parse call.
